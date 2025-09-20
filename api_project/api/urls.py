
from django.contrib import admin
from django.urls import path, include
from api.views import book_list
from rest_framework.routers import DefaultRouter
from api.views import BookViewSet, BookList, BookDetail

router = DefaultRouter()
router.register(r'books', BookViewSet)

urlpatterns = [
    path('book/', BookList.as_view(), name='book-list'),
    path('', include(router.urls)),
    path('book/<int:pk>/', BookDetail.as_view(), name='book-detail'),
]
