from django.urls import path
from . import views

urlpatterns = [
    # Dashboard Analytics
    path(
        'dashboard/analytics/',
        views.DashboardAnalyticsView.as_view(),
        name='dashboard-analytics'
    ),

    # Admin System Health
    path(
        'admin/system/health/',
        views.AdminSystemHealthView.as_view(),
        name='admin-system-health'
    ),

    # Admin Audit Logs
    path(
        'admin/audit/logs/',
        views.AdminAuditLogsView.as_view(),
        name='admin-audit-logs'
    ),
]