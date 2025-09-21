from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('view/', login_required(views.view_logs), name='view_logs'),
    path('create/', views.create_log, name='log'),
    path('view/', login_required(views.view_logs), name='view_logs'),
    path('create/', login_required(views.create_log), name='create_log'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home, name='home'),
]
