from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from embeddings.models import Embedding
from embeddings.serializers import EmbeddingSerializer
from app.permissions import GlobalDefaultPermission


class EmbeddingCreateListView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission)
    queryset = Embedding.objects.all()
    serializer_class = EmbeddingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['origin']
    search_fields = ['title', 'content']

    def get_queryset(self):
        queryset = Embedding.objects.all()

        # Filtro por metadata - busca em campos específicos do JSON metadata
        search_query = self.request.query_params.get('q', None)
        if search_query:
            # Busca em múltiplos campos do metadata usando Q objects
            from django.db.models import Q
            queryset = queryset.filter(
                Q(metadata__elasticsearch_index__icontains=search_query
                  ) |
                Q(metadata__elasticsearch_id__icontains=search_query) |
                Q(metadata__original_source__icontains=search_query) |
                Q(metadata__source_fields__icontains=search_query)
            )

        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """
        Retorna duas listas: metadados e vetores de similaridade
        para análise no frontend
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Extrair metadados e vetores separadamente
        metadados = []
        vetores = []

        for embedding in queryset:
            metadados.append({
                'id': str(embedding.id),
                'origin': embedding.origin,
                'title': embedding.title,
                'content': embedding.content,
                'metadata': embedding.metadata,
                'created_at': embedding.created_at,
                'updated_at': embedding.updated_at
            })
            vetores.append(embedding.embedding_vector)

        return Response({
            'metadados': metadados,
            'vetores': vetores,
            'total': len(metadados)
        })


class EmbeddingRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = Embedding.objects.all()
    serializer_class = EmbeddingSerializer
