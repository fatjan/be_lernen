from . import serializers
from ..models import Exercise, ExerciseQuestion, UserExerciseProgress
from api.models import ExerciseResult

class ExerciseResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseResult
        fields = ['id', 'exercise_type', 'created_at', 'completed_at', 
                 'correct_answers', 'incorrect_answers', 'score', 'language']
        read_only_fields = ['id', 'created_at', 'completed_at', 'score']

class ExerciseQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseQuestion
        fields = [
            'id',
            'question_text',
            'options',
            'correct_answer',
            'explanation',
            'order'
        ]

    def validate_options(self, value):
        if not isinstance(value, list) or len(value) < 2:
            raise serializers.ValidationError("At least 2 options are required")
        return value

class UserExerciseProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserExerciseProgress
        fields = ['id', 'completed', 'score', 'answers', 'completed_at']

class ExerciseSerializer(serializers.ModelSerializer):
    questions = ExerciseQuestionSerializer(many=True, read_only=True)
    user_progress = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = [
            'id',
            'title',
            'language',
            'exercise_type',
            'difficulty_level',
            'content',
            'instructions',
            'questions',
            'user_progress',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            progress = UserExerciseProgress.objects.filter(
                user=request.user,
                exercise=obj
            ).first()
            if progress:
                return UserExerciseProgressSerializer(progress).data
        return None

    def validate(self, data):
        if data['exercise_type'] == 'reading' and len(data['content']) < 100:
            raise serializers.ValidationError("Reading exercises must have content of at least 100 characters")
        return data

    def create(self, validated_data):
        questions_data = self.context.get('questions', [])
        exercise = Exercise.objects.create(**validated_data)
        
        for idx, question_data in enumerate(questions_data):
            question_data['order'] = idx + 1
            ExerciseQuestion.objects.create(exercise=exercise, **question_data)
            
        return exercise

    def check_answers(self, user_answers):
        exercise = self.instance
        correct_count = 0
        total_questions = exercise.questions.count()
        results = []

        for question in exercise.questions.all():
            user_answer = user_answers.get(str(question.id))
            is_correct = user_answer == question.correct_answer
            if is_correct:
                correct_count += 1
            
            results.append({
                'question_id': question.id,
                'correct': is_correct,
                'explanation': question.explanation if is_correct else None
            })

        score = int((correct_count / total_questions) * 100) if total_questions > 0 else 0

        return {
            'score': score,
            'correct_count': correct_count,
            'total_questions': total_questions,
            'results': results
        }