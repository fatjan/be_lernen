from . import (
    viewsets, authentication, status, filters, 
    IsAuthenticated, AllowAny, Response, action,
    PageNumberPagination, DjangoFilterBackend,
    IntegrityError, ConflictError,
    Word, WordSerializer, Language
)
from api.filters import WordFilter

class WordPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size' 
    max_page_size = 50 

class WordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing words.
    Requires token authentication.
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = WordSerializer
    pagination_class = WordPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = WordFilter
    search_fields = ['word', 'translation', 'example_sentence']
    ordering_fields = ['added_at', 'updated_at', 'word']
    ordering = ['-added_at']  # default ordering

    def get_queryset(self):
        """
        Optimize queryset with select_related for language and user
        """
        filters = {} if self.request.user.is_staff else {"user": self.request.user}

        language_code = self.request.query_params.get("language")
        if language_code:
            filters["language__code"] = language_code  # Changed from language to language__code

        return Word.objects.select_related('language', 'user').filter(**filters)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        language_code = data.get('language')
        if language_code:
            try:
                language = Language.objects.get(code=language_code)
                data['language'] = language.id
            except Language.DoesNotExist:
                return Response(
                    {"error": f"Language with code '{language_code}' does not exist"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            raise ConflictError("A word with this user and language already exists.")
        except Exception as e:
            raise ValidationError(f"An error occurred: {str(e)}")

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def featured(self, request):
        featured_words = Word.objects.select_related('language', 'user').filter(category='featured')
        page = self.paginate_queryset(featured_words)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(featured_words, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def batch(self, request):
        user = request.user
        words_data = request.data

        if not isinstance(words_data, list):
            raise ValidationError("Expected a list of words")

        for word in words_data:
            word['user'] = user.id

        serializer = WordSerializer(data=words_data, many=True)
        if serializer.is_valid():
            try:
                words = serializer.save()
                if words and hasattr(user, 'userprofile'):
                    user.userprofile.onboarded = True
                    user.userprofile.save()

                return Response({
                    "message": "Words added successfully!",
                    "data": WordSerializer(words, many=True).data
                }, status=201)
            except IntegrityError:
                raise ConflictError("One or more words already exist for this user and language")
            except Exception as e:
                raise ValidationError(f"Error creating words: {str(e)}")

        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def suggestions(self, request):
        query = request.query_params.get('query', '').strip()
        language_code = request.query_params.get('language')
        limit = min(int(request.query_params.get('limit', 3)), 5)

        if not query:
            return Response([])

        queryset = Word.objects.select_related('language')
        
        if language_code:
            queryset = queryset.filter(language__code=language_code)
        
        # Get full word objects instead of just the word field
        suggestions = (
            queryset.filter(word__istartswith=query)
            .distinct()
            [:limit]
        )

        # Serialize the word objects
        serializer = self.get_serializer(suggestions, many=True)
        return Response(serializer.data)