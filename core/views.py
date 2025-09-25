"""
Enhanced views with security, performance, and standardized responses
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from datetime import timedelta

from .models import UserProfile, Campaign, SourceSite, APIAuditLog, SystemMetrics
from .serializers import (
    UserProfileSerializer, CampaignSerializer, SourceSiteSerializer,
    APIAuditLogSerializer, SystemMetricsSerializer
)
from .permissions import (
    EnhancedGlobalPermission, IsOwnerOrReadOnly, IsPremiumUser,
    APIQuotaPermission, SecureResourceAccess
)
from .responses import StandardizedResponse, EnhancedPageNumberPagination
from .middleware import APIAuditMiddleware


class BaseSecureView(generics.GenericAPIView):
    """Base view with enhanced security and standardized responses"""

    permission_classes = [
        EnhancedGlobalPermission,
        APIQuotaPermission,
        SecureResourceAccess
    ]
    pagination_class = EnhancedPageNumberPagination

    def handle_exception(self, exc):
        """Enhanced exception handling with standardized responses"""
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                return StandardizedResponse.validation_error(exc.detail)
            else:
                return StandardizedResponse.error(str(exc.detail))
        return StandardizedResponse.server_error()

    def get_queryset(self):
        """Base queryset with user filtering"""
        queryset = super().get_queryset()
        if hasattr(self.model, 'owner'):
            queryset = queryset.filter(owner=self.request.user)
        elif hasattr(self.model, 'creator'):
            queryset = queryset.filter(creator=self.request.user)
        return queryset


class UserProfileView(BaseSecureView):
    """Enhanced user profile management"""

    serializer_class = UserProfileSerializer

    def get_object(self):
        """Get current user's profile"""
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get(self, request):
        """Get current user's profile"""
        try:
            profile = self.get_object()
            serializer = self.get_serializer(profile)
            return StandardizedResponse.success(
                data=serializer.data,
                message="Profile retrieved successfully"
            )
        except Exception as e:
            return StandardizedResponse.server_error(str(e))

    def patch(self, request):
        """Update current user's profile"""
        try:
            profile = self.get_object()
            serializer = self.get_serializer(profile, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return StandardizedResponse.success(
                    data=serializer.data,
                    message="Profile updated successfully"
                )
            else:
                return StandardizedResponse.validation_error(serializer.errors)

        except Exception as e:
            return StandardizedResponse.server_error(str(e))


class CampaignListCreateView(BaseSecureView, generics.ListCreateAPIView):
    """Enhanced campaign list and creation"""

    serializer_class = CampaignSerializer
    model = Campaign

    def get_queryset(self):
        """Get campaigns for current user with optional filtering"""
        queryset = Campaign.objects.filter(owner=self.request.user)

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by active/inactive
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        return queryset.order_by('-created_at')

    def list(self, request):
        """List campaigns with standardized response"""
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return StandardizedResponse.success(
                data=serializer.data,
                message="Campaigns retrieved successfully"
            )

        except Exception as e:
            return StandardizedResponse.server_error(str(e))

    def create(self, request):
        """Create new campaign with standardized response"""
        try:
            serializer = self.get_serializer(data=request.data)

            if serializer.is_valid():
                with transaction.atomic():
                    campaign = serializer.save(owner=request.user)

                    # Update user profile stats
                    profile = request.user.profile
                    profile.save()

                return StandardizedResponse.success(
                    data=self.get_serializer(campaign).data,
                    message="Campaign created successfully",
                    status_code=status.HTTP_201_CREATED
                )
            else:
                return StandardizedResponse.validation_error(serializer.errors)

        except Exception as e:
            return StandardizedResponse.server_error(str(e))


class CampaignDetailView(BaseSecureView, generics.RetrieveUpdateDestroyAPIView):
    """Enhanced campaign detail view"""

    serializer_class = CampaignSerializer
    model = Campaign
    permission_classes = [EnhancedGlobalPermission, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Campaign.objects.filter(owner=self.request.user)

    def retrieve(self, request, pk=None):
        """Get campaign details"""
        try:
            campaign = self.get_object()
            serializer = self.get_serializer(campaign)

            # Add additional metrics
            data = serializer.data
            data['metrics'] = {
                'content_pieces_count': campaign.content_pieces.count(),
                'published_content_count': campaign.content_pieces.filter(is_published=True).count(),
                'scheduled_content_count': campaign.content_pieces.filter(status='scheduled').count(),
                'images_generated': campaign.image_requests.count(),
                'embeddings_count': campaign.embeddings.count(),
            }

            return StandardizedResponse.success(
                data=data,
                message="Campaign retrieved successfully"
            )

        except Campaign.DoesNotExist:
            return StandardizedResponse.not_found("Campaign", pk)
        except Exception as e:
            return StandardizedResponse.server_error(str(e))

    def update(self, request, pk=None, partial=True):
        """Update campaign"""
        try:
            campaign = self.get_object()
            serializer = self.get_serializer(campaign, data=request.data, partial=partial)

            if serializer.is_valid():
                serializer.save()
                return StandardizedResponse.success(
                    data=serializer.data,
                    message="Campaign updated successfully"
                )
            else:
                return StandardizedResponse.validation_error(serializer.errors)

        except Campaign.DoesNotExist:
            return StandardizedResponse.not_found("Campaign", pk)
        except Exception as e:
            return StandardizedResponse.server_error(str(e))

    def destroy(self, request, pk=None):
        """Delete campaign"""
        try:
            campaign = self.get_object()
            campaign.delete()

            return StandardizedResponse.success(
                message="Campaign deleted successfully"
            )

        except Campaign.DoesNotExist:
            return StandardizedResponse.not_found("Campaign", pk)
        except Exception as e:
            return StandardizedResponse.server_error(str(e))


class SourceSiteListCreateView(BaseSecureView, generics.ListCreateAPIView):
    """Enhanced source site management"""

    serializer_class = SourceSiteSerializer
    model = SourceSite

    def get_queryset(self):
        queryset = SourceSite.objects.filter(
            Q(owner=self.request.user) | Q(is_public=True)
        )

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filter by active/inactive
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.order_by('-created_at')

    def create(self, request):
        try:
            serializer = self.get_serializer(data=request.data)

            if serializer.is_valid():
                site = serializer.save(owner=request.user)
                return StandardizedResponse.success(
                    data=self.get_serializer(site).data,
                    message="Source site created successfully",
                    status_code=status.HTTP_201_CREATED
                )
            else:
                return StandardizedResponse.validation_error(serializer.errors)

        except Exception as e:
            return StandardizedResponse.server_error(str(e))


@api_view(['GET'])
@permission_classes([EnhancedGlobalPermission])
def dashboard_analytics(request):
    """Enhanced dashboard analytics with caching"""
    cache_key = f"dashboard_analytics_{request.user.id}"
    cached_data = cache.get(cache_key)

    if cached_data:
        return StandardizedResponse.success(
            data=cached_data,
            message="Dashboard analytics retrieved successfully (cached)"
        )

    try:
        # User metrics
        profile = request.user.profile
        user_metrics = {
            'api_usage_percentage': profile.get_api_usage_percentage(),
            'api_calls_remaining': profile.api_quota - profile.api_usage_current_month,
            'plan_type': profile.plan_type,
            'is_premium': profile.is_premium,
        }

        # Content metrics
        campaigns = Campaign.objects.filter(owner=request.user)
        content_metrics = {
            'total_campaigns': campaigns.count(),
            'active_campaigns': campaigns.filter(is_active=True).count(),
            'total_content_created': profile.total_content_created,
            'total_images_generated': profile.total_images_generated,
            'total_embeddings_created': profile.total_embeddings_created,
        }

        # Recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_campaigns = campaigns.filter(created_at__gte=week_ago).count()

        recent_activity = {
            'campaigns_this_week': recent_campaigns,
            'api_calls_this_week': APIAuditLog.objects.filter(
                user=request.user,
                timestamp__gte=week_ago
            ).count(),
        }

        analytics_data = {
            'user_metrics': user_metrics,
            'content_metrics': content_metrics,
            'recent_activity': recent_activity,
            'last_updated': timezone.now().isoformat()
        }

        # Cache for 15 minutes
        cache.set(cache_key, analytics_data, 900)

        return StandardizedResponse.success(
            data=analytics_data,
            message="Dashboard analytics retrieved successfully"
        )

    except Exception as e:
        return StandardizedResponse.server_error(str(e))


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def system_health(request):
    """System health check for administrators"""
    try:
        # Get latest system metrics
        latest_metrics = SystemMetrics.objects.order_by('-metrics_date').first()

        if not latest_metrics:
            return StandardizedResponse.error(
                error="No system metrics available",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        health_data = {
            'system_status': latest_metrics.system_status,
            'api_health': {
                'total_calls_today': latest_metrics.total_api_calls_today,
                'success_rate': round(
                    (latest_metrics.successful_api_calls_today / max(latest_metrics.total_api_calls_today, 1)) * 100, 2
                ),
                'avg_response_time': latest_metrics.avg_response_time_ms,
            },
            'user_metrics': {
                'active_users_today': latest_metrics.active_users_today,
                'new_users_today': latest_metrics.new_users_today,
                'premium_users': latest_metrics.premium_users,
            },
            'content_metrics': {
                'total_content': latest_metrics.total_content_pieces,
                'published_content': latest_metrics.total_published_content,
                'total_campaigns': latest_metrics.total_campaigns,
            },
            'ai_metrics': {
                'embeddings_created': latest_metrics.total_embeddings_created,
                'images_generated': latest_metrics.total_images_generated,
                'processing_cost_today': float(latest_metrics.ai_processing_cost_today),
            },
            'last_updated': latest_metrics.updated_at.isoformat()
        }

        return StandardizedResponse.success(
            data=health_data,
            message="System health retrieved successfully"
        )

    except Exception as e:
        return StandardizedResponse.server_error(str(e))


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def audit_logs(request):
    """Get audit logs for administrators"""
    try:
        logs = APIAuditLog.objects.all().order_by('-timestamp')

        # Apply filters
        user_id = request.query_params.get('user_id')
        if user_id:
            logs = logs.filter(user_id=user_id)

        suspicious_only = request.query_params.get('suspicious_only')
        if suspicious_only and suspicious_only.lower() == 'true':
            logs = logs.filter(is_suspicious=True)

        status_code = request.query_params.get('status_code')
        if status_code:
            logs = logs.filter(response_status=status_code)

        # Paginate results
        paginator = EnhancedPageNumberPagination()
        page = paginator.paginate_queryset(logs, request)

        if page is not None:
            serializer = APIAuditLogSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        serializer = APIAuditLogSerializer(logs[:100], many=True, context={'request': request})  # Limit to 100 if no pagination
        return StandardizedResponse.success(
            data=serializer.data,
            message="Audit logs retrieved successfully"
        )

    except Exception as e:
        return StandardizedResponse.server_error(str(e))


class DashboardAnalyticsView(generics.GenericAPIView):
    """Dashboard Analytics API View"""
    permission_classes = [EnhancedGlobalPermission]

    def get(self, request):
        return dashboard_analytics(request)


class AdminSystemHealthView(generics.GenericAPIView):
    """Admin System Health API View"""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return system_health(request)


class AdminAuditLogsView(generics.GenericAPIView):
    """Admin Audit Logs API View"""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return audit_logs(request)