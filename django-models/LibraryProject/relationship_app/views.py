from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, request
from .models import Book, Author, Library, Librarian
from django.views import View
from django.views.generic.detail import DetailView


def list_books(request):
    books = Book.objects.all().select_related('author')
    return render(request, 'relationship_app/list_books.html', {'books': books})








# Class-based view (no template, just database -> response)
class LibraryDetailView(DetailView):
    model = Library
    template_name = 'relationship_app/library_detail.html'
    context_object_name = 'library'

    def get_object(self):
        return get_object_or_404(Library, pk=self.kwargs['pk'])

    