from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from texts.models import Text
from texts.serializers import TextSerializer
from app.permissions import GlobalDefaultPermission


class TextCreateListView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    queryset = Text.objects.all()
    serializer_class = TextSerializer


class TextRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = Text.objects.select_related('account').all()
    serializer_class = TextSerializer
