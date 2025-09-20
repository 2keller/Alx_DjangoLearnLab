from django.shortcuts import render
from rest_framework import viewsets
from .models import Book
from .serializer import BookSerializer
from rest_framework.generics import ListAPIView, RetrieveDestroyAPIView

# Create your views here.
def book_list(request):
    books = Book.objects.all()
    serializer = BookSerializer(books, many=True)
    return render(request, 'book_list.html', {'books': serializer.data})