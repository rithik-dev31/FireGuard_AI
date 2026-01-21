from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("detect-fire/", views.detect_fire, name="detect_fire"),
    path("admin-alerts/", views.admin_alerts, name="admin_alerts"),
]
