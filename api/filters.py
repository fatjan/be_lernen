import django_filters
from .models import Word
from django.db.models import Q

class WordFilter(django_filters.FilterSet):
    word = django_filters.CharFilter(method='filter_search_fields')
    translation = django_filters.CharFilter(method='filter_search_fields')
    example_sentence = django_filters.CharFilter(method='filter_search_fields')
    gender = django_filters.CharFilter(field_name="gender", lookup_expr="iexact")
    category = django_filters.CharFilter(field_name="category", lookup_expr="iexact")
    difficulty_level = django_filters.CharFilter(field_name="difficulty_level", lookup_expr="iexact")

    def filter_search_fields(self, queryset, name, value):
        return queryset.filter(
            Q(word__icontains=value) |
            Q(translation__icontains=value) |
            Q(example_sentence__icontains=value)
        )

    class Meta:
        model = Word
        fields = ["word", "translation", "example_sentence", "gender", "category", "difficulty_level"]
