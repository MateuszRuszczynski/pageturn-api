# users/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from . import views

app_name = "user"


@extend_schema(
    tags=["Authentication"],
    summary="Obtain access and refresh tokens",
    description="""
Authenticates a user with credentials and returns a short-lived **access token**
and a long-lived **refresh token**.

- Access token expires in **60 minutes**
- Refresh token expires in **1 days**
- On expiry, use `/user/token/refresh/` to get a new access token
    """,
    responses={
        200: OpenApiResponse(
            description="Tokens issued successfully",
            examples=[
                OpenApiExample(
                    name="Success",
                    value={
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    },
                )
            ],
        ),
        401: OpenApiResponse(
            description="Invalid credentials",
            examples=[
                OpenApiExample(
                    name="Invalid credentials",
                    value={
                        "detail": "No active account found with the given credentials"
                    },
                )
            ],
        ),
    },
    examples=[
        OpenApiExample(
            name="Login request",
            request_only=True,
            value={"email": "john.doe@example.com", "password": "secret123"},
        )
    ],
)
class DecoratedTokenObtainPairView(TokenObtainPairView):
    pass


@extend_schema(
    tags=["Authentication"],
    summary="Refresh access token",
    description="""
Issues a new **access token** using a valid refresh token.

Call this when the access token has expired (HTTP 401).

> ⚠️ If the refresh token is also expired, re-authenticate via `/user/token/`.
    """,
    responses={
        200: OpenApiResponse(
            description="New access token issued",
            examples=[
                OpenApiExample(
                    name="Success",
                    value={"access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
                )
            ],
        ),
        401: OpenApiResponse(
            description="Refresh token is invalid or expired",
            examples=[
                OpenApiExample(
                    name="Expired token",
                    value={
                        "detail": "Token is invalid or expired",
                        "code": "token_not_valid",
                    },
                )
            ],
        ),
    },
    examples=[
        OpenApiExample(
            name="Refresh request",
            request_only=True,
            value={"refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
        )
    ],
)
class DecoratedTokenRefreshView(TokenRefreshView):
    pass


urlpatterns = [
    path("", views.UserViewSet.as_view(), name="create"),
    path("me/", views.UserMangeViewSet.as_view(), name="user_account"),
    path("token/", DecoratedTokenObtainPairView.as_view(), name="token"),
    path("token/refresh/", DecoratedTokenRefreshView.as_view(), name="token_refresh"),
]
