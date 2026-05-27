from django.urls import path, include
from rest_framework import routers
from payments.views import PaymentViewSet

app_name = "payment"

router = routers.DefaultRouter()
router.register("payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("", include(router.urls)),
]
