import django_filters
from .models import Word

class WordFilter(django_filters.FilterSet):
    gender = django_filters.CharFilter(field_name="gender", lookup_expr="iexact")
    category = django_filters.CharFilter(field_name="category", lookup_expr="iexact")
    difficulty_level = django_filters.CharFilter(field_name="difficulty_level", lookup_expr="iexact")

    class Meta:
        model = Word
        fields = ["gender", "category", "difficulty_level"]
