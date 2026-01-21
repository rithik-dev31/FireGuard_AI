from django.contrib import admin
from django.urls import path
from api import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('api/detect/', views.detect_fire, name='detect_fire'),
    path('api/admin-alerts/', views.admin_alerts, name='admin_alerts'),
]
