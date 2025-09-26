from django.db import models
from django.contrib.auth.models import User
from rest_framework import viewsets, filters

# Create your models here.
class Author(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Book(models.Model):
    title = models.CharField(max_length=100)
    publication_year = models.IntegerField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    #allow user to Search by title and author name
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'author__name']

    def __str__(self):
        return self.title