from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ping
from .views.word import WordViewSet, GenerateWordsView
from .views.language import LanguageViewSet
from .views.exercise import ExerciseViewSet
from .views.user import UserRegisterView, CustomAuthToken, ListUsers, GetUserDataView, UpdateUserView, UpdateUserPasswordView
from .views.feedback import FeedbackView
from .views.google_auth import google_auth
from .views.reading import ReadingContentViewSet


router = DefaultRouter()
router.register(r'words', WordViewSet, basename='word')
router.register(r'languages', LanguageViewSet, basename='language')
router.register(r'exercises', ExerciseViewSet, basename='exercise')
router.register(r'readings', ReadingContentViewSet, basename='reading')

urlpatterns = [
    path('api/', include(router.urls)),  
    path('api/ping/', ping, name='ping'),
    path('api/login/', CustomAuthToken.as_view(), name='api_login'), 
    path('api/register/', UserRegisterView.as_view(), name='api_register'), 
    path('api/list-users/', ListUsers.as_view(), name='list_users'),
    path('api/profile/', GetUserDataView.as_view(), name='get-user-data'),
    path('api/user/update/', UpdateUserView.as_view(), name='update-user'),
    path('api/feedback/', FeedbackView.as_view(), name='feedback'),
    path('api/auth/google/', google_auth, name='google-auth'),
    path('api/update-password/', UpdateUserPasswordView.as_view(), name='update-password'),
    path('api/generate-words/', GenerateWordsView.as_view(), name='generate-words')
]