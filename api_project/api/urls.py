
from django.contrib import admin
from django.urls import path, include
from api.views import book_list
from rest_framework import routers,defaultRouter
from api.views import BookViewSet

router = defaultRouter()
router.register(r'books', BookViewSet)

urlpatterns = [
    path('book/', book_list, name='book-list'),
    path('', include(router.urls)),
]
