from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView, TokenVerifyView
)
from .views import (
    LogoutView,
    get_user_permissions,
)


urlpatterns = [
    path(
        'authentication/token/',
        TokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),
    path(
        'authentication/token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),
    path(
        'authentication/token/verify/',
        TokenVerifyView.as_view(),
        name='token_verify'
    ),
    path(
        'authentication/logout/',
        LogoutView.as_view(),
        name='logout'
    ),
    path(
        "user/permissions/",
        get_user_permissions,
        name="user-permissions"
    ),
]
