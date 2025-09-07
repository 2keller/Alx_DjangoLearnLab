from django.shortcuts import render
from django.http import HttpResponse, request
from .models import Book, Author, Library, Librarian
from django.views import View


def list_books(request):
    books = Book.objects.all().select_related('author')
    return render(request, 'relationship_app/list_books.html', {'books': books})








# Class-based view (no template, just database -> response)
class LibraryDetailView(View):
    def get(self, request, pk):
        library = Library.objects.get(pk=pk)          # Get library by its ID
        books = library.books.all()                   # All books in that library
        response = f"Library: {library.name}, Books: " + ", ".join(
            [f"{book.title} by {book.author}" for book in books]
        )
        return render(request, 'library_detail.html', {'library': library, 'books': books})

    