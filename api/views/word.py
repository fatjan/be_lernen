from . import (
    viewsets, authentication, status, filters, 
    IsAuthenticated, AllowAny, Response, action,
    PageNumberPagination, DjangoFilterBackend,
    IntegrityError, ConflictError,
    Word, WordSerializer, Language,
    ValidationError, APIView
)
from api.filters import WordFilter
import os
import json
from openai import OpenAI

class WordPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size' 
    max_page_size = 100 

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
        core = self.request.query_params.get('core')
        filters = {} if (self.request.user.is_staff or core == 'true') else {"user": self.request.user}

        language_code = self.request.query_params.get("language")
        if language_code:
            filters["language__code"] = language_code

        if core:
            filters["core"] = core.lower() == 'true'

        if self.request.query_params.get('random'):
            paginator = WordPagination()
            paginator.page_size = 100
            self.pagination_class = paginator.__class__
            return Word.objects.select_related('language', 'user').filter(**filters).order_by('?')
        
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
        successful_words = []

        if not isinstance(words_data, list):
            raise ValidationError("Expected a list of words")

        language_code = words_data[0].get('language')
        if language_code:
            try:
                language = Language.objects.get(code=language_code)
                language_id = language.id
            except Language.DoesNotExist:
                raise ValidationError(f"Language with code '{language_code}' does not exist")

        for word_data in words_data:
            word_data['user'] = user.id
            word_data['language'] = language_id
            
            # Check if word already exists
            if not Word.objects.filter(
                user=user,
                language=language_id,
                word=word_data['word']
            ).exists():
                serializer = WordSerializer(data=word_data, context={'request': request})
                if serializer.is_valid():
                    try:
                        word = serializer.save()
                        successful_words.append(word)
                    except Exception as e:
                        continue

        if successful_words and hasattr(user, 'userprofile'):
            user.userprofile.onboarded = True
            user.userprofile.save()

        return Response({
            "message": f"Added {len(successful_words)} words successfully!"
        }, status=201)

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
    
    def update(self, request, *args, **kwargs):
        data = request.data.copy()
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
        
        request._full_data = data
        return super().update(request, *args, **kwargs)


# Ensure API key exists
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key in environment variables")

client = OpenAI(api_key=OPENAI_API_KEY)

LANGUAGE_MAP = {"en": "English", "de": "German", "jp": "Japanese"}
MODEL = "gpt-4-turbo"
TEMPERATURE = 0.6
MAX_TOKENS = 1500


class GenerateWordsView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            data = request.data
            categories = data.get("categories")
            proficiency = data.get("proficiency")
            language = data.get("language")

            # Validate categories
            if not isinstance(categories, list) or not (1 <= len(categories) <= 3):
                return Response(
                    {"message": "Categories must be an array with 1 to 3 items only."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            total_words = len(categories) * 5
            language_chosen = LANGUAGE_MAP.get(language, "English")

            # Build prompt
            if len(categories) == 1:
                distribution = "5 words"
            elif len(categories) == 2:
                distribution = "5 words per category (10 total)"
            else:
                distribution = "5 words per category (15 total)"

            prompt = f"""
            Generate exactly {total_words} {language_chosen} words in total, distributed as follows:
            - {distribution} 
            for each category: {', '.join(categories)}.

            Return a clean JSON array with exactly {total_words} objects. Each object must follow this structure:
            {{
              "language": "{language}",
              "word": "The {language_chosen} word",
              "translation": "English translation",
              "category": "category name",
              "difficulty_level": "{proficiency}",
              "gender": "der/die/das or n/a for non-nouns or English words",
              "example_sentence": "{language_chosen} example sentence",
              "plural_form": "plural form if any",
              "part_of_speech": "noun/verb/adjective/adverb/preposition"
            }}
            """

            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": f"Respond with a valid JSON array only—exactly {total_words} items, no extra text.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )

            content = response.choices[0].message.content.strip() if response.choices else None
            if not content:
                raise ValueError("No content received from OpenAI.")

            # Try to parse OpenAI response
            try:
                generated_words = json.loads(content)
                if not isinstance(generated_words, list) or len(generated_words) != total_words:
                    raise ValueError(
                        f"Expected {total_words} items but received {len(generated_words)}"
                    )
            except json.JSONDecodeError as e:
                print("Parse error:", e, "\nContent:", content)
                raise ValueError("Failed to parse generated words")
            
            successful_words = []
            language_code = generated_words[0].get("language")

            try:
                language_obj = Language.objects.get(code=language_code)
                language_id = language_obj.id
            except Language.DoesNotExist:
                raise ValidationError(f"Language with code '{language_code}' does not exist")

            user = request.user
            for word_data in generated_words:
                word_data["user"] = user.id
                word_data["language"] = language_id

                if not Word.objects.filter(
                    user=user,
                    language=language_id,
                    word=word_data["word"]
                ).exists():
                    serializer = WordSerializer(data=word_data, context={"request": request})
                    if serializer.is_valid():
                        try:
                            word = serializer.save()
                            successful_words.append(word)
                        except Exception:
                            continue

            # Update user profile
            if successful_words and hasattr(user, "userprofile"):
                user.userprofile.onboarded = True
                user.userprofile.save()

            return Response(
                {
                    "message": f"Generated and added {len(successful_words)} words successfully!",
                    "data": generated_words,
                },
                status=status.HTTP_201_CREATED,
            )

            return Response(generated_words, status=status.HTTP_200_OK)

        except Exception as e:
            print("Error:", str(e))
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
