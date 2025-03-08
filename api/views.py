from rest_framework import viewsets, authentication, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import JsonResponse
from .models import Word, Language, UserProfile, Feedback, Exercise
from .serializers import (
    FeedbackSerializer, GoogleAuthSerializer,
    ExerciseSerializer
)
# from .serializers.language import LanguageSerializer
# from .serializers.word import WordSerializer
# from .serializers.user import UserRegistrationSerializer, UserLoginSerializer
# from .serializers.user_profile import UserProfileDetailSerializer, UserProfileUpdateSerializer
from .exceptions import ConflictError
from django_filters.rest_framework import DjangoFilterBackend
from .filters import WordFilter
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework import generics, filters
from social_django.utils import load_strategy, load_backend
from social_core.exceptions import MissingBackend, AuthFailed
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from social_core.exceptions import AuthForbidden 
import requests 
import json
from django.conf import settings
from api.services.exercise_generator import ExerciseGenerator







