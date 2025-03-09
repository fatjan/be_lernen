from rest_framework import viewsets, authentication, status, filters, generics
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db import IntegrityError
from ..exceptions import ConflictError
from api.models import (
    Word, Language, UserProfile, Feedback, Exercise
)
from api.serializers.language import LanguageSerializer
from api.serializers.word import WordSerializer
from api.serializers.google_auth import GoogleAuthSerializer
from api.serializers.user_profile import UserProfileDetailSerializer, UserProfileUpdateSerializer
from api.serializers.exercise import ExerciseSerializer
from api.serializers.feedback import FeedbackSerializer
from api.serializers.user import UserRegistrationSerializer, UserLoginSerializer
from api.serializers.language import LanguageSerializer
from api.serializers.word import WordSerializer
from api.serializers.reading import ReadingContentSerializer
from api.services.exercise_generator import ExerciseGenerator
from be_lernen import settings

@api_view(['GET'])
@permission_classes([AllowAny])
def ping(request):
    return Response({
        "status": "success",
        "message": "pong"
    })