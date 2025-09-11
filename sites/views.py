from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from sites.models import Site
from sites.serializers import SiteSerializer
from app.permissions import GlobalDefaultPermission


class SiteCreateListView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    queryset = Site.objects.all()
    serializer_class = SiteSerializer


class SiteRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
