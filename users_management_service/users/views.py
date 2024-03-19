from rest_framework import viewsets, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from rest_framework.views import APIView
from .serializers import UserSerializer, LoginSerializer
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .tokens import account_activation_token
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # The response can be customized as needed
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        user = serializer.save()  # This saves the User instance and returns it


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data["username"],
                password=serializer.validated_data["password"],
            )
            if user is not None:
                login(request, user)
                # If using token authentication, generate and return the token here
                return Response(
                    {"message": "User logged in successfully"},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"message": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    def get(self, request, uidb64, token, format=None):
        try:
            # Decode the user ID from base64
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        # Check that the user exists and the token is valid
        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True  # Activate the user account
            user.save()
            user.profile.email_confirmed = True
            user.profile.save()
            return HttpResponse(
                "Email verified successfully. Please log in.", status=status.HTTP_200_OK
            )

        else:
            # If the token is invalid or expired, return an error
            return HttpResponse(
                {"message": "Invalid verification link"},
                status=status.HTTP_400_BAD_REQUEST,
            )
