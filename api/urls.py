from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WordViewSet, ListUsers, UserRegisterView, LanguageViewSet, health_check, GetUserDataView, CustomAuthToken, UpdateUserView

router = DefaultRouter()
router.register(r'words', WordViewSet, basename='word')
router.register(r'languages', LanguageViewSet, basename='language')

urlpatterns = [
    path('api/', include(router.urls)),  
    path('api/login/', CustomAuthToken.as_view(), name='api_login'), 
    path('api/register/', UserRegisterView.as_view(), name='api_register'), 
    path('api/list-users/', ListUsers.as_view(), name='list_users'),
    path('health/', health_check, name='health_check'),
    path('api/profile/', GetUserDataView.as_view(), name='get-user-data'),
    path('api/user/update/', UpdateUserView.as_view(), name='update-user'),
]