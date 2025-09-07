from django.urls import path
from .views import (
    list_books,
    LibraryDetailView,
    CustomLoginView,
    CustomLogoutView,
    RegisterView
)

urlpatterns = [
    path('books/', list_books, name='book-list'),
    path('libraries/<int:pk>/', LibraryDetailView.as_view(), name='library-detail'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
]