from rest_framework import generics, permissions
from . import serializers


class UserViewSet(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.UserSerializer


class UserMangeViewSet(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.UserManageSerializer

    def get_object(self):
        return self.request.user
