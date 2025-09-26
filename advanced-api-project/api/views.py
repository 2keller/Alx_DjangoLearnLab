# views.py
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from .models import Book
from .serializers import BookSerializer
from django.filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from rest_framework import filters.OrderingFilter 
#  List and Create Books
class BookListCreateAPIView(generics.ListCreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['author__name', 'publication_year']
    search_fields = ['title', 'author__name']
    ordering_fields = ['publication_year', 'title']
    ordering = ['publication_year', 'title']

    def perform_create(self, serializer):
        title = serializer.validated_data.get('title')
        if Book.objects.filter(title=title).exists():
            raise ValidationError({'title': 'Book with this title already exists.'})
        serializer.save()

#  Retrieve, Update, and Delete a Book
class BookRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        title = serializer.validated_data.get('title')
        book_id = self.get_object().id
        if Book.objects.exclude(id=book_id).filter(title=title).exists():
            raise ValidationError({'title': 'Another book with this title already exists.'})
        serializer.save()