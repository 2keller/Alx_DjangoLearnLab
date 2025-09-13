# Update the title of the book "1984" to "Nineteen Eighty-Four"
book = Book.objects.get(title="1984", author="George Orwell", publication_year=1949)
book.title = "Nineteen Eighty-Four"
book.save()

# Expected Output:
# The book title is now updated and saved in the database.
print(book.title)  # Output: Nineteen Eighty-Four
