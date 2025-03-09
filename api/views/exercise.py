from . import (
    viewsets, Response, status,
    Exercise, ExerciseSerializer,
    ExerciseGenerator, action, settings,
    IsAuthenticated, Language
)

class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def generate(self, request):
        generator = ExerciseGenerator(
            api_key=settings.HF_API_KEY,
            url=settings.MODEL_URL
        )
        
        try:
            exercise_type = request.data.get('type')
            language_code = request.data.get('language')
            level = request.data.get('level')
            
            if not all([exercise_type, language_code, level]):
                return Response(
                    {"error": "Missing required fields: type, language, level"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get language name from code
            try:
                language = Language.objects.get(code=language_code)
                language_name = language.name
            except Language.DoesNotExist:
                return Response(
                    {"error": f"Invalid language code: {language_code}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if exercise_type == 'reading':
                topic = request.data.get('topic')
                exercise_data = generator.generate_reading_exercise(language_name, level, topic)
            elif exercise_type == 'grammar':
                grammar_point = request.data.get('grammar_point')
                if not grammar_point:
                    return Response(
                        {"error": "grammar_point is required for grammar exercises"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                exercise_data = generator.generate_grammar_exercise(language, level, grammar_point)
            else:
                return Response(
                    {"error": "Invalid exercise type"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = self.get_serializer(data=exercise_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def check_answers(self, request, pk=None):
        exercise = self.get_object()
        user_answers = request.data.get('answers', {})
        
        if not user_answers:
            return Response(
                {"error": "No answers provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(exercise)
        results = serializer.check_answers(user_answers)
        
        return Response(results)