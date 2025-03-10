from . import (
    APIView,
    AllowAny,
    UserRegistrationSerializer,
    UserLoginSerializer,
    Token,
    authentication,
    IsAdminUser,
    ObtainAuthToken,
    TokenAuthentication,
    IsAuthenticated,
    generics,
    UserProfileUpdateSerializer,
    UserProfileDetailSerializer,
    Response,
    ValidationError,
    status,
    UserProfile,  # Add this import
)

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
        profile = user.userprofile
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "message": "User registered successfully!",
            "user": {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile": {
                    "onboarded": profile.onboarded,
                    "preferred_language": profile.preferred_language.code if profile.preferred_language else None,
                    "subscription": profile.subscription.code if profile.subscription else None,
                    "words_count": profile.words_count
                }
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

# for login 
class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            
            user_data = serializer.data
            user_data['is_admin'] = user.is_staff
            
            return Response({
                'token': token.key,
                'user': user_data
            })
        except ValidationError as e:
            return Response({
                'error': 'Invalid credentials',
                'message': 'Unable to log in with provided credentials.'
            }, status=status.HTTP_400_BAD_REQUEST)

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