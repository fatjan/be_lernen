from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from ..services.exercise_generator import ExerciseGenerator
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from ..models import ReadingContent
from . import ReadingContentSerializer, Language
from django.db.models import Count
from ..services.content_generator import ContentGenerator

class ReadingContentViewSet(viewsets.ModelViewSet):
    queryset = ReadingContent.objects.all()
    serializer_class = ReadingContentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['language', 'level', 'topic']
    search_fields = ['title', 'content', 'topic']
    ordering_fields = ['created_at', 'title', 'level']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def topics(self):
        topics = ReadingContent.objects.values_list('topic', flat=True).distinct()
        return Response(topics)

    @action(detail=False, methods=['get'])
    def by_level(self, request):
        level = request.query_params.get('level')
        readings = self.get_queryset().filter(level=level)
        serializer = self.get_serializer(readings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_language(self, request):
        language = request.query_params.get('language')
        readings = self.get_queryset().filter(language__code=language)
        serializer = self.get_serializer(readings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        total = self.get_queryset().count()
        by_level = self.get_queryset().values('level').annotate(count=Count('id'))
        by_language = self.get_queryset().values('language__name').annotate(count=Count('id'))
        
        return Response({
            'total': total,
            'by_level': by_level,
            'by_language': by_language
        })

    def get_queryset(self):
        queryset = ReadingContent.objects.all()
        language = self.request.query_params.get('language', None)
        level = self.request.query_params.get('level', None)
        topic = self.request.query_params.get('topic', None)

        if language:
            queryset = queryset.filter(language__code=language)
        if level:
            queryset = queryset.filter(level=level)
        if topic:
            queryset = queryset.filter(topic=topic)

        return queryset

    @action(detail=False, methods=['post'])
    def generate(self, request):
        language = request.data.get('language')
        level = request.data.get('level')
        topic = request.data.get('topic')

        if not language or not level:
            return Response(
                {"error": "Language and level are required"}, 
                status=400
            )

        generator = ContentGenerator(
            api_key=settings.HF_API_KEY,
            url=settings.MODEL_URL
        )
        
        try:
            content = generator.generate_reading_content(language, level, topic)
            language_id = Language.objects.get(code=language).id
            content['language'] = language_id
            serializer = self.get_serializer(data=content)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)