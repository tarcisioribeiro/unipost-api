# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({'detail': 'Logout efetuado com sucesso.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_permissions(request):
    user = request.user

    # Bloqueia superusuários de usar a interface Streamlit
    if user.is_superuser:
        return Response(
            {'error': 'Administradores não podem acessar esta interface'},
            status=status.HTTP_403_FORBIDDEN
        )

    perms = user.get_all_permissions()
    return Response({
        "username": user.username,
        "permissions": list(perms),
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
    })
