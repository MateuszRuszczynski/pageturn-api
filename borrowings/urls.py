from django.urls import path, include
from rest_framework import routers
from borrowings.views import BorrowingViewSet

app_name = "borrowing"

router = routers.DefaultRouter()
router.register("borrowings", BorrowingViewSet, basename="borrowing")

urlpatterns = [path("", include(router.urls))]
