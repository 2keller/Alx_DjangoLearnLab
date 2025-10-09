from django.urls import path, include
from django.contrib import admin
from rest_framework.routers import DefaultRouter
from posts.views import PostViewSet, CommentViewSet

from .views import FeedView


router = DefaultRouter()
router.register('posts', PostViewSet)
router.register('comments', CommentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('feed/', FeedView.as_view(), name='feed'), 
    
]