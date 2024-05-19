from django.contrib.auth import get_user_model
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
import uuid
import logging
from .serializers import UserSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from django.contrib.auth.hashers import make_password

User = get_user_model()
logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        self.send_verification_email(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def send_verification_email(self, user):
        verification_code = str(uuid.uuid4())
        user.verification_code = verification_code
        user.save()
        verification_url = reverse("user-verify", args=[verification_code])
        full_url = f"http://{settings.SITE_DOMAIN}{verification_url}"
        send_mail(
            "Verify your account",
            f"Please verify your account by clicking this link: {full_url}",
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )

    @action(
        detail=False, methods=["get"], url_path="verify/(?P<verification_code>[^/.]+)"
    )
    def verify_email(self, request, verification_code=None):
        user = User.objects.filter(verification_code=verification_code).first()
        if user and not user.is_active:
            user.is_active = True
            user.save()
            return Response(
                {"message": "Email successfully verified and account activated."}
            )
        else:
            return Response(
                {"error": "Invalid verification code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["put"], url_path="update-profile")
    def update_profile(self, request, pk=None):
        user = self.get_object()
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "profile updated"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="change-password")
    def change_password(self, request, pk=None):
        user = self.get_object()
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        if not user.check_password(old_password):
            return Response(
                {"error": "Incorrect password"}, status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(new_password)
        user.save()
        return Response({"status": "password updated"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="reset-password")
    def reset_password(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )
        new_password = User.objects.make_random_password()
        user.set_password(new_password)
        user.save()
        send_mail(
            "Your new password",
            f"Your new password is: {new_password}",
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
        return Response(
            {"status": "password reset and emailed"}, status=status.HTTP_200_OK
        )


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        logger.debug("CustomAuthToken POST request received")
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            token, created = Token.objects.get_or_create(user=user)
            logger.debug(f"Token created for user {user.username}")
            return Response({"token": token.key})
        else:
            logger.debug("Invalid data received")
            return Response(serializer.errors, status=400)


class ValidateTokenView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logger.debug(f"Token validated for user: {request.user}")
        return Response({"valid": True})


class Logout(APIView):
    permission_classes = [IsAuthenticated]

    # Define a simple serializer to satisfy the schema generator
    class DummySerializer(serializers.Serializer):
        message = serializers.CharField(
            read_only=True, default="Logged out successfully"
        )

    serializer_class = DummySerializer  # Assign the dummy serializer

    def get(self, request):
        return self.logout(request)

    def post(self, request):
        return self.logout(request)

    def logout(self, request):
        if hasattr(request.user, "auth_token"):
            request.user.auth_token.delete()
        return Response(
            {"message": "Logged out successfully"}, status=status.HTTP_204_NO_CONTENT
        )
