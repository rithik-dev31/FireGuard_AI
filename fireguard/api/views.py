from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone

import json
import time
import base64
import logging
from collections import defaultdict

import cv2
import numpy as np
from ultralytics import YOLO

from .models import FireAlert  # 🔥 ALERT MODEL

# 🔥 WEBSOCKET IMPORTS (NEW!)
try:
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False
    print("⚠️  Install 'channels': pip install channels")

logger = logging.getLogger(__name__)

# ==========================
# 🔥 MODEL INITIALIZATION
# ==========================
model = YOLO(str(settings.ML_MODEL_PATH), task="detect")

# ==========================
# 🔥 FIRE CONFIRMATION CONFIG
# ==========================
FIRE_PERSISTENCE_SECONDS = 2.0
MIN_FIRE_AREA = 2500
MIN_FLICKER_CONF = 0.5

# 🔥 NEW: CONTINUOUS DETECTION CONFIG
CONTINUOUS_DETECTION_SECONDS = 5  # Change to 10 if you want 10 seconds
LOCATION_TOLERANCE = 0.0001  # ~11 meters tolerance for GPS drift

# 🔥 Track continuous fire detections per location
# Structure: {location_key: {'first_seen': timestamp, 'last_seen': timestamp, 'count': int, 'alerted': bool}}
fire_tracking = defaultdict(lambda: {
    'first_seen': 0,
    'last_seen': 0,
    'count': 0,
    'alerted': False
})

def get_location_key(lat, lon):
    """Create a location key rounded to tolerance level"""
    lat_rounded = round(lat / LOCATION_TOLERANCE) * LOCATION_TOLERANCE
    lon_rounded = round(lon / LOCATION_TOLERANCE) * LOCATION_TOLERANCE
    return f"{lat_rounded:.6f},{lon_rounded:.6f}"

def cleanup_old_tracking():
    """Remove stale tracking entries older than 30 seconds"""
    current_time = time.time()
    expired_keys = [
        key for key, data in fire_tracking.items()
        if current_time - data['last_seen'] > 30
    ]
    for key in expired_keys:
        del fire_tracking[key]

# ==========================
# 🔥 MAIN DASHBOARD
# ==========================
@csrf_exempt
@require_http_methods(["GET"])
def dashboard(request):
    return render(request, "dashboard.html")

# ==========================
# 🔥 FIRE DETECTION API (WITH CONTINUOUS DETECTION)
# ==========================
@csrf_exempt
@require_http_methods(["POST"])
def detect_fire(request):
    """
    Expects JSON payload:
    {
        "image": "data:image/jpeg;base64,...",
        "latitude": 12.3456,
        "longitude": 78.9012
    }
    
    Only saves alert if fire detected continuously for CONTINUOUS_DETECTION_SECONDS
    """
    try:
        data = json.loads(request.body)
        img_data = data["image"].split(",")[1]
        nparr = np.frombuffer(base64.b64decode(img_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return JsonResponse({"error": "Invalid image data"}, status=400)

        # Get GPS from frontend
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        if latitude is None or longitude is None:
            latitude, longitude = 13.0827, 80.2707  # fallback

        img_h, img_w = img.shape[:2]
        results = model(img, verbose=False)

        fire_detected = False
        fire_size = 0
        flicker_confidence = 0.0
        bounding_boxes = []

        # 🔥 ANALYZE DETECTIONS
        for r in results:
            if r.boxes is None:
                continue

            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())

                x1 = int(max(0, min(x1, img_w - 1)))
                y1 = int(max(0, min(y1, img_h - 1)))
                x2 = int(max(0, min(x2, img_w)))
                y2 = int(max(0, min(y2, img_h)))

                w = max(1, x2 - x1)
                h = max(1, y2 - y1)
                area = w * h

                if area < 600 or area > 120000:
                    continue

                aspect_ratio = w / h
                if aspect_ratio < 0.35 or aspect_ratio > 4.5:
                    continue

                roi = img[y1:y2, x1:x2]
                if roi.size == 0:
                    continue

                std_dev = float(np.std(roi))
                current_flicker_conf = min(std_dev / 60.0, 1.0)
                if current_flicker_conf < 0.25:
                    continue

                hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                lower_fire = np.array([5, 120, 120])
                upper_fire = np.array([35, 255, 255])
                mask = cv2.inRange(hsv, lower_fire, upper_fire)

                fire_color_ratio = float(np.sum(mask > 0) / mask.size)
                if fire_color_ratio < 0.12:
                    continue

                fire_detected = True
                fire_size = max(fire_size, area)
                flicker_confidence = max(flicker_confidence, current_flicker_conf)

                bounding_boxes.append({
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "confidence": round(conf, 2),
                    "area": area,
                    "fire_color_ratio": round(fire_color_ratio, 2),
                })

        # 🔥 CONTINUOUS DETECTION LOGIC
        current_time = time.time()
        location_key = get_location_key(latitude, longitude)
        should_save_alert = False
        
        # Clean up old entries periodically
        cleanup_old_tracking()

        if fire_detected and fire_size >= MIN_FIRE_AREA and flicker_confidence >= MIN_FLICKER_CONF:
            tracking = fire_tracking[location_key]
            
            # First detection at this location
            if tracking['first_seen'] == 0:
                tracking['first_seen'] = current_time
                tracking['last_seen'] = current_time
                tracking['count'] = 1
                logger.info(f"🔥 First fire detection at {location_key}")
            
            # Continuous detection
            elif current_time - tracking['last_seen'] < 3.0:  # Within 3 seconds = continuous
                tracking['last_seen'] = current_time
                tracking['count'] += 1
                
                duration = current_time - tracking['first_seen']
                logger.info(f"🔥 Continuous fire at {location_key} for {duration:.1f}s (count: {tracking['count']})")
                
                # 🔥 CONFIRMED: Fire detected continuously for required duration
                if duration >= CONTINUOUS_DETECTION_SECONDS and not tracking['alerted']:
                    should_save_alert = True
                    tracking['alerted'] = True
                    logger.warning(f"🚨 ALERT CONFIRMED: Fire at {location_key} for {duration:.1f}s!")
            
            # Gap too long, reset tracking
            else:
                logger.info(f"🔥 Fire detection gap at {location_key}, resetting")
                tracking['first_seen'] = current_time
                tracking['last_seen'] = current_time
                tracking['count'] = 1
                tracking['alerted'] = False
        
        # No fire detected, but check if we need to reset
        else:
            if location_key in fire_tracking:
                tracking = fire_tracking[location_key]
                if current_time - tracking['last_seen'] > 3.0:
                    logger.info(f"🔥 Fire stopped at {location_key}, clearing tracking")
                    del fire_tracking[location_key]

        # 🔥 SAVE ALERT ONLY AFTER CONTINUOUS DETECTION
        if should_save_alert:
            alert_obj = FireAlert.objects.create(
                location_name=f"🔥 LAT:{latitude:.4f}, LNG:{longitude:.4f}",
                latitude=float(latitude),
                longitude=float(longitude),
                fire_size=int(fire_size),
                flicker_confidence=round(flicker_confidence, 2),
            )
            
            logger.warning(f"💾 SAVED: Fire alert #{alert_obj.id} at {location_key}")
            
            # 🔥 WEBSOCKET NOTIFICATION
            if CHANNELS_AVAILABLE:
                try:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        "fire_alerts", {
                            'type': 'fire_alert_received',
                            'alert': {
                                'id': alert_obj.id,
                                'location_name': alert_obj.location_name,
                                'latitude': float(alert_obj.latitude),
                                'longitude': float(alert_obj.longitude),
                                'fire_size': int(alert_obj.fire_size),
                                'flicker_confidence': float(alert_obj.flicker_confidence),
                                'created_at': alert_obj.created_at.isoformat()
                            }
                        }
                    )
                    logger.info(f"📡 WEBSOCKET: Alert #{alert_obj.id} sent to all dashboards!")
                except Exception as e:
                    logger.error(f"WebSocket send failed: {e}")

        # Calculate detection duration for response
        detection_duration = 0
        if location_key in fire_tracking:
            tracking = fire_tracking[location_key]
            detection_duration = current_time - tracking['first_seen']

        return JsonResponse({
            "fire_detected": bool(fire_detected),
            "fire_size": fire_size,
            "flicker_confidence": round(flicker_confidence, 2),
            "alert": bool(should_save_alert),
            "send_alert": bool(should_save_alert),
            "bounding_boxes": bounding_boxes,
            "detection_duration": round(detection_duration, 1),  # New field
            "required_duration": CONTINUOUS_DETECTION_SECONDS,  # New field
        })

    except json.JSONDecodeError:
        logger.error("Invalid JSON payload")
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except KeyError:
        logger.error("Missing image key")
        return JsonResponse({"error": "Missing image data"}, status=400)
    except Exception:
        logger.exception("Fire detection failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

# ==========================
# 🗺️ ADMIN ALERTS (WEBSOCKET READY)
# ==========================
@csrf_exempt
def admin_alerts(request):
    alerts = FireAlert.objects.order_by("-created_at")[:50]
    return render(request, "admin_firealerts.html", {
        "alerts": alerts
    })