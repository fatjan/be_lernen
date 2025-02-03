from rest_framework import viewsets, authentication, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Word, Language
from .serializers import WordSerializer, UserRegistrationSerializer, LanguageSerializer
from django.contrib.auth.models import User

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

class WordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing words.
    Requires token authentication.
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Word.objects.all()
    serializer_class = WordSerializer

    def perform_create(self, serializer):
        """
        Ensure the word is associated with the authenticated user.
        """
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """
        Ensure users only see their own words.
        """
        return Word.objects.filter(user=self.request.user)

class UserRegisterView(APIView):
    """
    API endpoint for user registration.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User registered successfully!",
                "user": {
                    "username": user.username,
                    "email": user.email
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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