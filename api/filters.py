import django_filters
from .models import Word, ReadingContent
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


class ReadingContentFilter(django_filters.FilterSet):
    language = django_filters.CharFilter(field_name='language__code')
    level = django_filters.CharFilter(field_name='level')
    topic = django_filters.CharFilter(field_name='topic', lookup_expr='icontains')
    search = django_filters.CharFilter(method='filter_search_fields')

    def filter_search_fields(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(content__icontains=value) |
            Q(topic__icontains=value)
        )

    class Meta:
        model = ReadingContent
        fields = ['language', 'level', 'topic']
