from rest_framework import viewsets, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from rest_framework.views import APIView
from .serializers import UserSerializer, LoginSerializer


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
        # Serializer.save() triggers the email logic in the serializer
        serializer.save()


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

