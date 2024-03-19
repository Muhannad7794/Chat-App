from django.contrib.auth.models import User
from django.core.mail import send_mail
from rest_framework import serializers
from django.conf import settings
from .models import UserProfile
from .tokens import account_activation_token
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        user.is_active = False
        user.save()

        # Generate a token and uid
        token = account_activation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Create verification link
        verification_link = "http://localhost:8000/user/verify/{uid}/{token}/".format(
            uid=uid, token=token
        )

        # Send confirmation email
        send_mail(
            subject="Verify your Chat App account",
            message="Please click the following link to verify your account: {0}".format(
                verification_link
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserProfile
        fields = ("user", "email_confirmed")

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        user = UserSerializer.create(UserSerializer(), validated_data=user_data)
        user_profile, created = UserProfile.objects.update_or_create(
            user=user, defaults=validated_data
        )
        return user_profile


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
