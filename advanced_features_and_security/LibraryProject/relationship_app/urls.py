from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views
from django.urls import path
from .views import admin_view, librarian_view, member_view
from .views import add_book, edit_book, delete_book


urlpatterns = [
    path('login/', LoginView.as_view(template_name='relationship_app/login.html'), name='login'),
    path('logout/', LogoutView.as_view(template_name='relationship_app/logout.html'), name='logout'),
    path('register/', views.register, name='register'),
    path('admin-view/', admin_view, name='admin-view'),
    path('librarian-view/', librarian_view, name='librarian-view'),
    path('member-view/', member_view, name='member-view'),
]



urlpatterns += [
    path('books/add/', add_book, name='add-book'),
    path('books/<int:pk>/edit/', edit_book, name='edit-book'),
    path('books/<int:pk>/delete/', delete_book, name='delete-book'),
]