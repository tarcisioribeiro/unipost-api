from django.urls import path
from . import views


urlpatterns = [
    path(
        'sites/',
        views.SiteCreateListView.as_view(),
        name="site-create-list"
    ),
    path(
        'sites/<int:pk>/',
        views.SiteRetrieveUpdateDestroyView.as_view(),
        name='site-detail-view',
    ),
]