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
from .serializers import WordSerializer, UserRegistrationSerializer, LanguageSerializer, UserSerializer
from .exceptions import ConflictError
from django_filters.rest_framework import DjangoFilterBackend
from .filters import WordFilter
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework import generics

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

    queryset = Word.objects.all()
    serializer_class = WordSerializer
    pagination_class = WordPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = WordFilter 

    def perform_create(self, serializer):
        """
        Ensure the word is associated with the authenticated user.
        """
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise ConflictError("A word with this user and language already exists.")
        except Exception as e:
            raise ValidationError(f"An error occurred: {str(e)}")

    def get_queryset(self):
        """
        Admins see all words; users see only their own words.
        """
        filters = {} if self.request.user.is_staff else {"user": self.request.user}

        language_id = self.request.query_params.get("language")
        if language_id:
            filters["language"] = language_id

        words = Word.objects.filter(**filters)

        return words

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def featured(self, request):
        featured_words = Word.objects.filter(category='daily') 
        serializer = self.get_serializer(featured_words, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def batch(self, request):
        user = request.user 
        words_data = request.data
        
        for word in words_data:
            word['user'] = user.id
        
        serializer = WordSerializer(data=words_data, many=True)
        
        if serializer.is_valid():
            serializer.save()

            if hasattr(user, 'userprofile'):
                user.userprofile.onboarded = True
                user.userprofile.save()

            return Response({"message": "Words added successfully!", "data": serializer.data}, status=201)
        
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
        user_profile, _ = UserProfile.objects.get_or_create(user=user)

        return Response({
            "message": "User registered successfully!",
            "user": {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "token": token.key,
            "onboarded": user_profile.onboarded,
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

class GetUserDataView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user 
        serializer = UserSerializer(user)
        return Response(serializer.data)

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data["token"])
        user = token.user

        user_profile, _ = UserProfile.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "onboarded": user_profile.onboarded,
        })

class UpdateUserView(generics.UpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user  # Only allow users to update their own data

    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        user_serializer = self.get_serializer(user, data=request.data, partial=True)

        if user_serializer.is_valid():
            user_serializer.save()

            return Response(user_serializer.data)

        return Response(user_serializer.errors, status=400)