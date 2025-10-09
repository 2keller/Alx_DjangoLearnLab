
        #IMPORT ESSENTILAS

from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth import authenticate, get_user_model
from rest_framework.authtoken.models import Token


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30)
    email = serializers.EmailField()
    password = serializers.CharField(max_length=30)

    def create(self, validated_data):
        user = get_user_model().objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        Token.objects.create(user=user)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user:
            Token, created = Token.objects.get_or_create(user=user)
            return {
                'user': user,
                'token': Token.key
            }
        raise serializers.ValidationError('Invalid Credentials')
    
