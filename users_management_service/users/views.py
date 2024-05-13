from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
import uuid
from .serializers import UserSerializer
from rest_framework import serializers, views

# authintication imports:
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.forms import AuthenticationForm

User = get_user_model()


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


class CustomAuthToken(ObtainAuthToken):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return Response(
                {"detail": "You are already logged in."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Return a login form for GET requests
        form = AuthenticationForm()
        return Response({"form": form}, template_name="rest_framework/login.html")

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": user.pk, "email": user.email})


class Logout(views.APIView):
    permission_classes = [IsAuthenticated]

    class DummySerializer(serializers.Serializer):
        pass

    serializer_class = DummySerializer  # Add a dummy serializer

    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
