# views.py
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from .models import Book
from .serializers import BookSerializer

# 📚 List and Create Books
class BookListCreateAPIView(generics.ListCreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        title = serializer.validated_data.get('title')
        if Book.objects.filter(title=title).exists():
            raise ValidationError({'title': 'Book with this title already exists.'})
        serializer.save()

# 🔍 Retrieve, Update, and Delete a Book
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