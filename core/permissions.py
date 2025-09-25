from rest_framework import permissions
from rest_framework.throttling import UserRateThrottle
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta


class EnhancedGlobalPermission(permissions.BasePermission):
    """Enhanced global permission class with improved security"""

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user account is active
        if not request.user.is_active:
            return False

        # Check API quota
        if hasattr(request.user, 'profile'):
            if not request.user.profile.can_make_api_call():
                self.message = "API quota exceeded. Please upgrade your plan or wait for quota reset."
                return False

        # Get model permission
        model_permission = self._get_model_permission_codename(request.method, view)
        if not model_permission:
            return True  # No specific permission required

        # Check if user has the permission
        has_permission = request.user.has_perm(model_permission)
        if not has_permission:
            self.message = f"You don't have permission to {request.method.lower()} this resource."

        return has_permission

    def has_object_permission(self, request, view, obj):
        """Object-level permissions"""

        # Superusers have all permissions
        if request.user.is_superuser:
            return True

        # Check if object has an owner and user is the owner
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True

        if hasattr(obj, 'creator') and obj.creator == request.user:
            return True

        if hasattr(obj, 'user') and obj.user == request.user:
            return True

        # Check if object is public for read operations
        if request.method in permissions.SAFE_METHODS:
            if hasattr(obj, 'is_public') and obj.is_public:
                return True

        # Check campaign access for content pieces
        if hasattr(obj, 'campaign') and obj.campaign:
            if obj.campaign.owner == request.user:
                return True

        return False

    def _get_model_permission_codename(self, method, view):
        """Get the Django permission codename for the model and action"""
        try:
            model_name = view.queryset.model._meta.model_name
            app_label = view.queryset.model._meta.app_label
            action = self._get_action_suffix(method)
            return f'{app_label}.{action}_{model_name}'
        except AttributeError:
            return None

    def _get_action_suffix(self, method):
        """Map HTTP methods to Django permission actions"""
        method_actions = {
            'GET': 'view',
            'POST': 'add',
            'PUT': 'change',
            'PATCH': 'change',
            'DELETE': 'delete',
            'OPTIONS': 'view',
            'HEAD': 'view',
        }
        return method_actions.get(method, 'view')


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission to only allow owners of an object to edit it"""

    def has_object_permission(self, request, view, obj):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only to the owner
        return (
            hasattr(obj, 'owner') and obj.owner == request.user or
            hasattr(obj, 'creator') and obj.creator == request.user or
            hasattr(obj, 'user') and obj.user == request.user
        )


class IsPremiumUser(permissions.BasePermission):
    """Permission for premium features"""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'profile'):
            return request.user.profile.is_premium

        return False

    message = "This feature requires a premium account."


class IsOwnerOrPublic(permissions.BasePermission):
    """Permission to view public content or owned content"""

    def has_object_permission(self, request, view, obj):
        # Owner always has access
        if (hasattr(obj, 'owner') and obj.owner == request.user or
            hasattr(obj, 'creator') and obj.creator == request.user):
            return True

        # Public content is readable by authenticated users
        if (request.method in permissions.SAFE_METHODS and
            hasattr(obj, 'is_public') and obj.is_public):
            return True

        return False


class CanAccessCampaign(permissions.BasePermission):
    """Permission to access campaign and its related objects"""

    def has_object_permission(self, request, view, obj):
        # Direct campaign access
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        # Access through campaign relationship
        if hasattr(obj, 'campaign') and obj.campaign:
            return obj.campaign.owner == request.user

        return False


class APIQuotaPermission(permissions.BasePermission):
    """Check API quota before allowing access"""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return True  # Let other permissions handle auth

        if hasattr(request.user, 'profile'):
            profile = request.user.profile

            # Check if quota reset is needed
            now = timezone.now()
            if now >= profile.quota_reset_date:
                # Reset quota for new month
                profile.api_usage_current_month = 0
                profile.quota_reset_date = now + timedelta(days=30)
                profile.save(update_fields=['api_usage_current_month', 'quota_reset_date'])

            # Check quota
            if not profile.can_make_api_call():
                self.message = f"API quota exceeded ({profile.api_usage_current_month}/{profile.api_quota}). Upgrade your plan for higher limits."
                return False

        return True


class SecureResourceAccess(permissions.BasePermission):
    """Enhanced security for resource access"""

    def has_permission(self, request, view):
        # Block access from suspicious IPs
        ip = self._get_client_ip(request)
        blocked_ips_key = f"blocked_ip_{ip}"

        if cache.get(blocked_ips_key):
            self.message = "Access blocked due to suspicious activity."
            return False

        return True

    def has_object_permission(self, request, view, obj):
        # Check for resource-specific access patterns
        user_id = request.user.id if request.user.is_authenticated else None

        # Track resource access patterns
        if user_id:
            access_key = f"resource_access_{user_id}_{obj.__class__.__name__}_{obj.pk}"
            access_count = cache.get(access_key, 0)

            # Suspicious if accessing same resource too many times
            if access_count > 100:  # 100 accesses to same resource per hour
                self.message = "Too many accesses to this resource."
                return False

            cache.set(access_key, access_count + 1, 3600)  # 1 hour

        return True

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip