from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import WordViewSet, ListUsers, UserRegisterView, LanguageViewSet, health_check

router = DefaultRouter()
router.register(r'words', WordViewSet, basename='word')
router.register(r'languages', LanguageViewSet, basename='language')

urlpatterns = [
    path('api/', include(router.urls)),  
    path('api/login/', obtain_auth_token, name='api_login'), 
    path('api/register/', UserRegisterView.as_view(), name='api_register'), 
    path('api/list-users/', ListUsers.as_view(), name='list_users'),
    path('health/', health_check, name='health_check'),
]