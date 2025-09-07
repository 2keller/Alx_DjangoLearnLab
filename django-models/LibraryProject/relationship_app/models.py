from django.db import models

# Create your models here.
class Aurthur(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Aurthur, on_delete=models.CASCADE, related_name='books')

    def __str__(self):
        return self.title
    
class Library(models.Model):
    name = models.CharField(max_length=100)
    books = models.ManyToManyField(Book, related_name='libraries')

    def __str__(self):
        return self.name

    
class Librian(models.Model):
    name = models.CharField(max_length=100)
    library = models.OneToOneField(Library, on_delete=models.CASCADE, related_name='librarian')

    def __str__(self):
        return self.name
    

    