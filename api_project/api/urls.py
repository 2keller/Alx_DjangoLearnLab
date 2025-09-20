
from django.contrib import admin
from django.urls import path, include
from api.views import book_list
from rest_framework import routers


urlpatterns = [
    path('book/', book_list, name='book-list'),
]
