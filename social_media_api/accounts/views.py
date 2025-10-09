from django.shortcuts import render
from django.http import HttpResponse
from .models import CustomUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, LoginSerializer
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated


# Create your views here.
#create account and login logic 
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'User registered successfully',
                'username': user.username,
                'email': user.email,
                'token': user.auth_token.key
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token = serializer.validated_data['token']
            return Response({
                'message': 'Login successful',
                'username': user.username,
                'token': token
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class follow_user(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        current_user = request.user
        try:
            user_to_follow = CustomUser.objects.get(username=username)
            current_user.following.add(user_to_follow)
            return Response({'message': 'User followed successfully'}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
    def delete(self, request, username):
        current_user = request.user
        try:
            user_to_unfollow = CustomUser.objects.get(username=username)
            current_user.following.remove(user_to_unfollow)
            return Response({'message': 'User unfollowed successfully'}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)