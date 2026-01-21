from django.db import models

class FireAlert(models.Model):
    location_name = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    fire_size = models.IntegerField()
    flicker_confidence = models.FloatField()

    status = models.CharField(
        max_length=20,
        choices=[
            ("ACTIVE", "Active"),
            ("RESOLVED", "Resolved")
        ],
        default="ACTIVE"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"🔥 Fire at {self.location_name} ({self.status})"
