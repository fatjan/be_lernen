from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ..services.exercise_generator import ExerciseGenerator
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from ..models import ReadingContent
from . import ReadingContentSerializer, Language
from django.db.models import Count
from ..services.content_generator import ContentGenerator
from ..filters import ReadingContentFilter
from rest_framework.pagination import PageNumberPagination
from openai import OpenAI
import os
import json

class ReadingPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

class ReadingContentViewSet(viewsets.ModelViewSet):
    queryset = ReadingContent.objects.all()
    serializer_class = ReadingContentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ReadingPagination  
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ReadingContentFilter
    search_fields = ['title', 'content', 'topic']
    ordering_fields = ['created_at', 'title', 'level']
    ordering = ['level', '-created_at']

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
        """
        Optimize queryset with select_related for language
        """
        filters = {}
        
        language_code = self.request.query_params.get('language')
        level = self.request.query_params.get('level')
        topic = self.request.query_params.get('topic')

        if language_code:
            filters['language__code'] = language_code
        if level:
            filters['level'] = level
        if topic:
            filters['topic'] = topic

        queryset = ReadingContent.objects.select_related('language').filter(**filters)
        
        return queryset

    @action(detail=False, methods=['post'])
    def generate(self, request):
        language = request.data.get('language')
        level = request.data.get('level')
        topic = request.data.get('topic', '')

        print('language', language)
        print('level', level)
        print('topic', topic)
        if language == 'ja':
            level_map = {
                'A1': 'N5',
                'A2': 'N4',
                'B1': 'N3',
                'B2': 'N2',
            }
            level = level_map.get(level, level)

        if not language or not level:
            return Response(
                {"error": "Language and level are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Initialize OpenAI client
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not OPENAI_API_KEY:
            raise ValueError("Missing OpenAI API key in environment variables")
        
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Prepare prompt
        language_name = {
            "en": "English",
            "de": "German",
            "jp": "Japanese",
        }.get(language, "English")

        prompt = f"""
        Generate a short {language_name} reading passage suitable for a {level} learner.
        Topic: {topic or "any everyday situation"}.

        The response must be valid JSON with the following structure:
        {{
          "title": "Short descriptive title in {language_name}",
          "text": "A coherent {language_name} reading passage of about 100-150 words, suitable for the given proficiency level.",
        }}
        """

        try:
            # Generate text using OpenAI
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Respond with a valid JSON object only. No explanations, no markdown.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=800,
            )
            print('response', response)

            content = response.choices[0].message.content.strip()
            data = None
            try:
                data = json.loads(content)
                print('ini data', data)
            except json.JSONDecodeError:
                return Response(
                    {"error": "Failed to parse OpenAI response", "raw": content},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Attach language id
            try:
                language_id = Language.objects.get(code=language).id
            except Language.DoesNotExist:
                return Response(
                    {"error": f"Language with code '{language}' does not exist"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Map OpenAI response to model fields
            serializer_data = {
                "title": data.get("title", ""),
                "content": data.get("text", ""),  # Map 'text' to 'content'
                "language": language_id,
                "level": level,
                "topic": topic or ""
            }

            # Serialize and save
            serializer = self.get_serializer(data=serializer_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                print('Serializer errors:', serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def create_manual(self, request):
        """
        Manually create reading content without using AI generation
        """
        try:
            reading = ReadingContent.create_reading(
                title=request.data.get('title'),
                content=request.data.get('content'),
                language_code=request.data.get('language'),
                level=request.data.get('level'),
                topic=request.data.get('topic')
            )
            serializer = self.get_serializer(reading)
            return Response(serializer.data, status=201)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    
    def update(self, request, *args, **kwargs):
        language_code = request.data.get('language')
        if language_code:
            try:
                language = Language.objects.get(code=language_code)
                request.data['language'] = language.id
            except Language.DoesNotExist:
                return Response(
                    {"error": f"Language with code '{language_code}' does not exist"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return super().update(request, *args, **kwargs)