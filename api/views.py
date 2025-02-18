from rest_framework import viewsets, authentication, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import JsonResponse
from .models import Word, Language, UserProfile
from .serializers import WordSerializer, UserRegistrationSerializer, LanguageSerializer, UserLoginSerializer, UserProfileDetailSerializer, UserProfileUpdateSerializer
from .exceptions import ConflictError
from django_filters.rest_framework import DjangoFilterBackend
from .filters import WordFilter
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework import generics, filters

def health_check():
    return JsonResponse({"status": "ok"})

class LanguageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing languages.
    Requires token authentication.
    * Only admin users are able to access this view.
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAdminUser]

    queryset = Language.objects.all()
    serializer_class = LanguageSerializer

    def get_queryset(self):
        return Language.objects.all()

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

        language_id = self.request.query_params.get("language")
        if language_id:
            filters["language"] = language_id

        return Word.objects.select_related('language', 'user').filter(**filters)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
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
        featured_words = self.get_queryset().filter(category='daily')
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

class UserRegisterView(APIView):
    """
    API endpoint for user registration.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        
        if not serializer.is_valid():
            unique_fields = ["username", "email"]
            for field in unique_fields:
                if field in serializer.errors and any(
                    err.code == "unique" for err in serializer.errors[field]
                ):
                    return Response(
                        {"error": f"{field.capitalize()} already taken."},
                        status=status.HTTP_409_CONFLICT
                    )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "message": "User registered successfully!",
            "user": {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "token": token.key,
        }, status=status.HTTP_201_CREATED)

class ListUsers(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request, format=None):
        """
        Return a list of all users.
        """
        usernames = [user.username for user in User.objects.all()]
        return Response(usernames)

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        # Use UserSerializer for consistent data representation
        user_data = UserLoginSerializer(user).data
        
        return Response({
            'token': token.key,
            'user': user_data
        })

class GetUserDataView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileDetailSerializer(request.user)
        return Response(serializer.data)

class UpdateUserView(generics.UpdateAPIView):
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)