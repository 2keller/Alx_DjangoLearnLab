




import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LibraryProject.settings')
django.setup()

from relationship_app.models import Author, Book, Library, Librarian

def get_books_by_author(author_name):
    try:
        author = Author.objects.get(name=author_name)
        books = Book.objects.filter(author=author)
        print(f"Books by {author.name}:")
        for book in books:
            print(book.title)
    except Author.DoesNotExist:
        print(f"No author found with name '{author_name}'")

def list_books_in_library(library_name):
    try:
        library = Library.objects.get(name=library_name)
        books = library.books.all()
        print(f"Books in {library.name}:")
        for book in books:
            print(book.title)
    except Library.DoesNotExist:
        print(f"No library found with name '{library_name}'")

def get_librarian_for_library(library_name):
    try:
        library = Library.objects.get(name=library_name)
        librarian = Librarian.objects.get(library=library)
        print(f"Librarian for {library.name}: {librarian.name}")
    except (Library.DoesNotExist, Librarian.DoesNotExist):
        print(f"No librarian found for library '{library_name}'")

if __name__ == "__main__":
    get_books_by_author("Kelvin Elvin")
    list_books_in_library("Central Library")
    get_librarian_for_library("Central Library")