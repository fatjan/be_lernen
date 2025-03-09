from . import (
    api_view,
    permission_classes,
    AllowAny,
    GoogleAuthSerializer,
    settings,
    Response,
    status,
    requests,
    User, UserProfile, Token
)

@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    serializer = GoogleAuthSerializer(data=request.data)
    try:
        serializer.is_valid(raise_exception=True)
        token_data = serializer.validated_data['credential']
        
        headers = {
            'Authorization': f"{token_data.get('token_type', 'Bearer')} {token_data.get('access_token')}"
        }

        google_oauth2_uri = settings.GOOGLE_OAUTH2_URI
        
        response = requests.get(
            google_oauth2_uri,
            headers=headers
        )
        if response.status_code != 200:
            raise ValueError('Failed to get user info from Google')
            
        user_info = response.json()
        
        # Extract user info
        email = user_info['email']
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create new user
            username = email.split('@')[0]
            base_username = username
            counter = 1
            
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
        
        # Update last login
        serializer.update_last_login(user)
        
        # Ensure UserProfile exists
        UserProfile.objects.get_or_create(user=user)
        
        # Create/get auth token
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_admin': user.is_staff,
                'onboarded': hasattr(user, 'userprofile') and user.userprofile.onboarded,
                'preferred_language': hasattr(user, 'userprofile') and user.userprofile.preferred_language
            }
        })
            
    except ValueError as e:
        return Response({
            'error': 'Invalid token',
            'message': 'Token validation failed'
        }, status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': 'Server error',
            'message': str(e)
        }, status.HTTP_500_INTERNAL_SERVER_ERROR)