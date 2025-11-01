from . import (
    viewsets, Response, status,
    Exercise, ExerciseSerializer,
    ExerciseGenerator, action, settings,
    IsAuthenticated, Language, ExerciseResultSerializer,
    Word
)
from api.services.matching_exercise import MatchingExerciseGenerator

class ExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseResultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ExerciseResult.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def matching(self, request):
        language_code = request.query_params.get('language')
        count = int(request.query_params.get('count', 10))

        if not language_code:
            return Response(
                {"error": "Language parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get words for the specified language (randomized)
        # Admin users get all words, regular users get only their words
        if request.user.is_staff:
            words = Word.objects.filter(
                language__code=language_code
            ).values('word', 'translation').order_by('?')[:count]
        else:
            words = Word.objects.filter(
                user=request.user,
                language__code=language_code
            ).values('word', 'translation').order_by('?')[:count]

        if not words:
            return Response({})

        # Generate exercise
        exercise_generator = MatchingExerciseGenerator()
        exercise = exercise_generator.generate(list(words))

        return Response(exercise)

    @action(detail=False, methods=['post'])
    def submit_result(self, request):
        try:
            language = Language.objects.get(code=request.data.get('language'))
            result = ExerciseResult.objects.create(
                user=request.user,
                exercise_type=request.data.get('exercise_type'),
                correct_answers=request.data.get('correct_answers', 0),
                incorrect_answers=request.data.get('incorrect_answers', 0),
                language=language
            )
            
            serializer = self.get_serializer(result)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Language.DoesNotExist:
            return Response(
                {"error": "Invalid language code"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )