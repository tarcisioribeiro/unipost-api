from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from texts.models import Text
from texts.serializers import TextSerializer
from app.permissions import GlobalDefaultPermission


class TextCreateListView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    queryset = Text.objects.all()
    serializer_class = TextSerializer


class TextRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = Text.objects.all()
    serializer_class = TextSerializer


@api_view(['POST'])
def webhook_update_approval(request):
    text_id = request.data.get('id')
    approval_status = request.data.get('status')

    if text_id is None:
        return Response(
            {'error': 'ID do texto é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if approval_status is None:
        return Response(
            {'error': 'Status é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not isinstance(approval_status, bool):
        return Response(
            {'error': 'Status deve ser um valor booleano (true/false)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        text = get_object_or_404(Text, id=text_id)
        text.is_approved = approval_status
        text.save()

        return Response(
            {
                'message': 'Status de aprovação atualizado com sucesso',
                'id': text.id,  # type: ignore
                'is_approved': text.is_approved
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'error': f'Erro interno: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
