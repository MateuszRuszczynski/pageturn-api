from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

app_name = "user"

urlpatterns = [
    path("", views.UserViewSet.as_view(), name="create"),
    path("me/", views.UserMangeViewSet.as_view(), name="user_account"),
    path("token/", TokenObtainPairView.as_view(), name="token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh")

]

