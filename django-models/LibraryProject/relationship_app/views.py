from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Library, Book
from django.contrib.auth import login, authenticate

# -----------------------
# Book Views
# -----------------------

@login_required(login_url='relationship_app:login')
def list_books(request):
    books = Book.objects.all().select_related('author')
    libraries = Library.objects.all()
    return render(request, 'relationship_app/list_books.html', {
        'books': books,
        'libraries': libraries
    })

class LibraryDetailView(LoginRequiredMixin, DetailView):
    model = Library
    template_name = 'relationship_app/library_detail.html'
    context_object_name = 'library'
    login_url = 'relationship_app:login'

    def get_object(self):
        return get_object_or_404(Library, pk=self.kwargs['pk'])

# -----------------------
# Authentication Views
# -----------------------

class CustomLoginView(LoginView):
    template_name = 'relationship_app/login.html'

    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().username}!')
        return super().form_valid(form)

class CustomLogoutView(LogoutView):
    template_name = 'relationship_app/logout.html'

class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'relationship_app/register.html'
    success_url = '/login/'  # redirect to login page after registration

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Registration successful! Please log in.')
        return response
