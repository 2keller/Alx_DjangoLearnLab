from django.urls import path
from . import views


urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('follow/<str:username>/', views.FollowUserView.as_view(), name='follow'),
    path('unfollow/<str:username>/', views.UnfollowUserView.as_view(), name='unfollow'), 
]