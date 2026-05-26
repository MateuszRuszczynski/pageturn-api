from rest_framework import serializers
from books.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "inventory", "daily_fee")

    def validate_title(self, value):
        if not value[0].isupper():
            raise serializers.ValidationError(
                "Title must start with an uppercase letter."
            )
        return value

    def validate_author(self, value):
        stripped_value = value.strip()

        if not stripped_value:
            raise serializers.ValidationError("Author name cannot be empty.")

        parts = stripped_value.split()
        if len(parts) < 2:
            raise serializers.ValidationError(
                "Author must include both a name and a surname."
            )

        for part in parts:
            if not part[0].isupper():
                raise serializers.ValidationError(
                    f"Each part of the author's name ('{part}') must start with an uppercase letter."
                )

        return stripped_value

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["cover"] = instance.get_cover_display()
        return representation
