from django.shortcuts import render
from .models import Post, Comment
#import create, read, update, delete
from rest_framework import viewsets
from .serializers import PostSerializer, CommentSerializer

# Create your views here.


#crud operations for post and comment
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer