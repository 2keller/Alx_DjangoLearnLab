from django.shortcuts import render
from .models import Book
from django.urls import reverse_lazy
from django.views.generic  import ListView, DetailView, CreateView, UpdateView, DeleteView
from .serializers import BookSerializer, AuthorSerializer
# Create your views here.
#implimenting crud operations fro the book using views 

class BookListView(ListView):
    model = Book
    
class BookDetailView(DetailView):
    model = Book

class BookCreateView(CreateView):
    model = Book
    fields = '__all__'
    success_url = reverse_lazy('book-list')

    def form_valid(self, form):

        if Book.objects.filter(title=form.instance.title).exists():
            form.add_error('title', 'Book with this title already exists.')
            return self.form_invalid(form)

        return super().form_valid(form)

class BookUpdateView(UpdateView):
    model = Book
    fields = '__all__'
    success_url = reverse_lazy('book-list')

    def form_valid(self, form):
        if Book.objects.filter(title=form.instance.title).exists():
            form.add_error('title', 'Book with this title already exists.')
            return self.form_invalid(form)

        return super().form_valid(form)


class BookDeleteView(DeleteView):
    model = Book
    success_url = reverse_lazy('book-list')

