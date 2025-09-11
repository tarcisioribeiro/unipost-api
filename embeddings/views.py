from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from embeddings.models import Embedding
from embeddings.serializers import EmbeddingSerializer
from app.permissions import GlobalDefaultPermission


class EmbeddingCreateListView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    serializer_class = EmbeddingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['origin']
    search_fields = ['title', 'content']
    
    def get_queryset(self):
        queryset = Embedding.objects.all()
        
        # Filtro simples por conteúdo - equivalente a SELECT * FROM embeddings_embedding WHERE content LIKE '%term%'
        search_query = self.request.query_params.get('q', None)
        if search_query:
            queryset = queryset.filter(content__icontains=search_query)
        
        return queryset.order_by('-created_at')
    


class EmbeddingRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = Embedding.objects.all()
    serializer_class = EmbeddingSerializer