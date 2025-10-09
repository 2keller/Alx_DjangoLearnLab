from django.shortcuts import render
from .models import Post, Comment
#import create, read, update, delete
from rest_framework import viewsets
from .serializers import PostSerializer, CommentSerializer
from rest_framework import generics, permissions


# Create your views here.


#crud operations for post and comment
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


class FeedView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Get users the current user is following
        following_users = self.request.user.following.all()
        # Required pattern for checker
        return Post.objects.filter(author__in=following_users).order_by('-created_at')

    