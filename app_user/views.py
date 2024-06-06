from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import CustomUser
from .serializers import RegisterUserSerializer


class UserRegisterView(generics.CreateAPIView):
    """Представление для регистрации пользователя"""
    queryset = CustomUser.get_all_users()
    permission_classes = (AllowAny,)
    serializer_class = RegisterUserSerializer
