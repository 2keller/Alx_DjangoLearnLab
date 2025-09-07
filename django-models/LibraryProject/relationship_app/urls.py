from django.urls import path
from .views import (
    list_books,
    LibraryDetailView,
    CustomLoginView,
    CustomLogoutView,
    RegisterView,
)

app_name = 'relationship_app'

urlpatterns = [
    # Book views
    path('books/', list_books, name='list_books'),
    path('library/<int:pk>/', LibraryDetailView.as_view(), name='library_detail'),

    # Authentication views
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
]
