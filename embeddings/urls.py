from django.urls import path
from . import views


urlpatterns = [
    path(
        'embeddings/',
        views.EmbeddingCreateListView.as_view(),
        name="embedding-create-list"
    ),
    path(
        'embeddings/<uuid:pk>/',
        views.EmbeddingRetrieveUpdateDestroyView.as_view(),
        name='embedding-detail-view',
    ),
]