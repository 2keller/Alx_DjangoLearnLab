from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import PostCreateView, PostListView, PostDetailView, PostDeleteView, PostUpdateView
from .views import CommentCreateView, CommentDeleteView, CommentListView, CommentUpdateView, CommentListView
urlpatterns = [
    path('', PostListView.as_view(), name='home'),
    path('post/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('post/new/', PostCreateView.as_view(), name='post-create'),
    path('post/<int:pk>/update/', PostUpdateView.as_view(), name='post-update'),
    path('post/<int:pk>/delete/', PostDeleteView.as_view(), name='post-delete'),
    path('post/<int:pk>/comment/', CommentListView.as_view(), name='comment-list'),




    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
    path('register/', views.Register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('post/<int:pk>/comment/', CommentCreateView.as_view(), name='comment-create'),
    path('comment/<int:pk>/update/', CommentUpdateView.as_view(), name='comment-update'),
    path('comment/<int:pk>/delete/', CommentDeleteView.as_view(), name='comment-delete'),
    path('post/<int:pk>/comment/', CommentListView.as_view(), name='comment-list'),

]