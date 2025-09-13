from django.shortcuts import render

# Create your views here.
from forms import ExampleForm
from django.contrib.auth.decorators import permission_required

@permission_required('advanced_features_and_security.can_edit', raise_exception=True)
def book_list(request, book):
    book.all()
    return render(request, 'bookshelf/book_list.html', {'book': book})