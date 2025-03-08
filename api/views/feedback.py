from . import (
    APIView,
    AllowAny,
    FeedbackSerializer,
    status,
    Response,
    Feedback,
)

class FeedbackView(APIView):
    """
    API endpoint for user feedback.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id
        
        serializer = FeedbackSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Thank you for your feedback!",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        if not request.user.is_staff:
            return Response(
                {"error": "Not authorized to view feedback"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        feedbacks = Feedback.objects.all().order_by('-created_at')
        serializer = FeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data)