from django.urls import path

from trips.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
]
