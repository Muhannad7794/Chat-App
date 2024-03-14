from django.contrib.auth.models import User
from django.core.mail import send_mail
from rest_framework import serializers
from django.conf import settings
from .models import UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)

        # Send confirmation email
        send_mail(
            "Welcome to the Chat App!",
            "Hello, thanks for registering. Please confirm your email address.",
            settings.EMAIL_HOST_USER,  # Dynamically fetch the sender email address
            [validated_data["email"]],
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
