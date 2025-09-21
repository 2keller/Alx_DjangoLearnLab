# feelings/urls.py
from django.urls import path
from . import views

app_name = 'feelings'

urlpatterns = [
    path('', views.feed_view, name='feed'),                 # feed page
    path('post/new/', views.create_post_view, name='post_new'),
    path('post/<int:post_id>/edit/', views.edit_post_view, name='edit_post'),
    path('post/<int:post_id>/delete/', views.delete_post_view, name='delete_post'),
    path('reaction/<int:post_id>/<str:reaction>/', views.react_view, name='react'),
    path('post/<int:post_id>/comment/', views.add_comment_view, name='add_comment'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
]
