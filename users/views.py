from rest_framework import generics, permissions

from . import serializers
from drf_spectacular.utils import extend_schema, extend_schema_view


@extend_schema_view(
    post=extend_schema(
        summary="Register a new user",
        description="Allows anonymous visitors to register a new account on the library platform using their email.",
    )
)
@extend_schema(tags=["Users & Authentication"])
class UserViewSet(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.UserSerializer


@extend_schema_view(
    get=extend_schema(
        summary="Get current user profile",
        description="Retrieve profile details for the currently authenticated user session.",
    ),
    put=extend_schema(
        summary="Update profile completely",
        description="Fully update the current user's registration details (PUT).",
    ),
    patch=extend_schema(
        summary="Update profile partially",
        description="Partially modify specific account profile values (PATCH).",
    ),
)
@extend_schema(tags=["Users & Authentication"])
class UserMangeViewSet(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.UserManageSerializer

    def get_object(self):
        return self.request.user
