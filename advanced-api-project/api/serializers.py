from rest_framework import serializers
from .models import Book

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

    def Validate(self, Data):
        pub_year = Data.get('publication_year')
        if pub_year > 2025:
            raise serializers.ValidationError("Publication year cannot be greater than 2022")
        return Data

class AuthorSerializer(serializers.ModelSerializer):
    book = serializers.StringRelatedField(many=True, read_only=True)
    class Meta:
        model = Book
        fields = '__all__'

