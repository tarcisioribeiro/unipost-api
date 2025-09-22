from django.urls import path
from . import views

app_name = 'unipost_image_generator'

urlpatterns = [
    path('generate/', views.GenerateImageView.as_view(), name='generate-image'),
    path('status/<uuid:image_id>/', views.ImageStatusView.as_view(), name='image-status'),
    path('list/', views.ListGeneratedImagesView.as_view(), name='list-images'),
]
