from django.urls import path
from . import views


urlpatterns = [
    path(
        'texts/',
        views.TextCreateListView.as_view(),
        name="text-create-list"
    ),
    path(
        'texts/<int:pk>/',
        views.TextRetrieveUpdateDestroyView.as_view(),
        name='text-detail-view',
    ),
    path(
        'webhook/approval/',
        views.webhook_update_approval,
        name='webhook-approval',
    )
]
