retrieved = Book.objects.get(id=book.id)
print(retrieved.title)