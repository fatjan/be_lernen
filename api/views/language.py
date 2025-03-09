from . import (
    viewsets,
    authentication,
    IsAuthenticated,
    Language,
    LanguageSerializer,
)

class LanguageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing languages.
    Requires token authentication.
    * Only admin users are able to access this view.
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Language.objects.all()
    serializer_class = LanguageSerializer

    def get_queryset(self):
        return Language.objects.all()

