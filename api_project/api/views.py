from django.shortcuts import render
from rest_framework import viewsets
from .models import Book
from .serializer import BookSerializer
from rest_framework.generics import ListAPIView, RetrieveDestroyAPIView, RetrieveAPIView
from rest_framework.viewsets import ModelViewSet
from django.views.generic import CreateView, UpdateView, DeleteView
# Create your views here.

def book_list(request):
    books = Book.objects.all()
    serializer = BookSerializer(books, many=True)
    return render(request, 'book_list.html', {'books': serializer.data})

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    class ModelCreateView(CreateView):
        model = Book
        template_name = "book_form.html"
        fields = ['title', 'author', 'published_date']
        success_url = "/books/"
      
    class ModelUpdateView(UpdateView):
        model = Book
        template_name = "book_form.html"
        fields = ['title', 'author', 'published_date']
        success_url = "/books/"

    class ModelDestroyView(DeleteView):
        model = Book
        template_name = "book_confirm_delete.html"
        success_url = "/books/"

    class ModelRetrieveView(RetrieveAPIView):
        queryset = Book.objects.all()
        serializer_class = BookSerializer