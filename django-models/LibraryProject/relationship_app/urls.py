#urls 
from django.urls import path
from .views import list_books, LibraryDetailView, logout_view, login_view
urlpatterns = [
    path('books/', list_books, name='book-list'),
    path('libraries/<int:pk>/', LibraryDetailView.as_view(), name='library-detail'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]