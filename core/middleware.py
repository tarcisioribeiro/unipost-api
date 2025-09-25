import time
import json
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from .models import APIAuditLog
import uuid

# Loggers
audit_logger = logging.getLogger('core.audit')
security_logger = logging.getLogger('django.security')


class APIAuditMiddleware(MiddlewareMixin):
    """Comprehensive API audit logging middleware"""

    def process_request(self, request):
        # Start timing
        request._audit_start_time = time.time()
        request._audit_initial_queries = len(connection.queries)

        # Generate request ID
        request._audit_request_id = str(uuid.uuid4())

        return None

    def process_response(self, request, response):
        # Skip for certain endpoints
        skip_paths = ['/admin/', '/static/', '/media/', '/favicon.ico']
        if any(request.path.startswith(path) for path in skip_paths):
            return response

        try:
            # Calculate timing
            response_time = (time.time() - request._audit_start_time) * 1000
            db_queries = len(connection.queries) - request._audit_initial_queries

            # Calculate DB time
            db_time = sum(float(query['time']) for query in connection.queries[-db_queries:]) * 1000 if db_queries > 0 else 0

            # Get request data
            request_body = None
            if hasattr(request, 'body') and request.body:
                try:
                    if request.content_type == 'application/json':
                        request_body = json.loads(request.body.decode('utf-8'))
                    else:
                        request_body = {'content_type': request.content_type, 'size': len(request.body)}
                except:
                    request_body = {'error': 'Could not parse request body'}

            # Security risk assessment
            risk_score = self._calculate_risk_score(request, response)
            is_suspicious = risk_score > 70

            # Create audit log entry
            user = getattr(request, 'user', None)
            audit_data = {
                'user': user if user and not isinstance(user, AnonymousUser) else None,
                'session_id': request.session.session_key or '',
                'method': request.method,
                'endpoint': request.path,
                'full_url': request.build_absolute_uri(),
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                'referer': request.META.get('HTTP_REFERER'),
                'request_headers': self._get_safe_headers(request),
                'request_body': request_body,
                'response_status': response.status_code,
                'response_size': len(response.content) if hasattr(response, 'content') else 0,
                'response_time_ms': response_time,
                'db_queries_count': db_queries,
                'db_time_ms': db_time,
                'is_suspicious': is_suspicious,
                'risk_score': risk_score,
                'api_version': request.META.get('HTTP_X_API_VERSION', 'v1'),
                'additional_data': {
                    'request_id': request._audit_request_id,
                    'content_type': getattr(request, 'content_type', ''),
                }
            }

            # Log to database (async to avoid blocking)
            try:
                APIAuditLog.objects.create(**audit_data)
            except Exception as e:
                # Log to file if DB fails
                audit_logger.error(f"Failed to create audit log: {e}")

            # Log suspicious activity
            if is_suspicious:
                security_logger.warning(f"Suspicious activity detected: {request.method} {request.path} from {audit_data['ip_address']} (Risk Score: {risk_score})")

            # Add response headers
            response['X-Request-ID'] = request._audit_request_id
            response['X-Response-Time'] = f"{response_time:.2f}ms"
            response['X-API-Version'] = audit_data['api_version']

        except Exception as e:
            # Don't break the response if audit fails
            audit_logger.error(f"Audit middleware error: {e}")

        return response

    def _get_client_ip(self, request):
        """Get real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def _get_safe_headers(self, request):
        """Get safe headers (without sensitive information)"""
        safe_headers = {}
        sensitive_headers = ['authorization', 'cookie', 'x-api-key', 'x-auth-token']

        for key, value in request.META.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].lower().replace('_', '-')
                if header_name not in sensitive_headers:
                    safe_headers[header_name] = value[:200]  # Limit length
                else:
                    safe_headers[header_name] = '[REDACTED]'

        return safe_headers

    def _calculate_risk_score(self, request, response):
        """Calculate risk score based on various factors"""
        risk_score = 0

        # High status codes
        if response.status_code >= 400:
            risk_score += 20
        if response.status_code == 404:
            risk_score += 10
        if response.status_code == 403:
            risk_score += 30

        # Suspicious user agents
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        suspicious_agents = ['bot', 'crawler', 'spider', 'scan', 'curl', 'wget']
        if any(agent in user_agent for agent in suspicious_agents):
            risk_score += 25

        # Unusual paths
        path = request.path.lower()
        suspicious_paths = ['/admin', '/.env', '/config', '/wp-admin', '/phpmyadmin']
        if any(sus_path in path for sus_path in suspicious_paths):
            risk_score += 40

        # High request frequency from same IP
        ip = self._get_client_ip(request)
        cache_key = f"request_count_{ip}"
        request_count = cache.get(cache_key, 0)
        if request_count > 100:  # More than 100 requests per minute
            risk_score += 30

        cache.set(cache_key, request_count + 1, 60)  # 1 minute window

        # Anonymous user accessing sensitive endpoints
        user = getattr(request, 'user', None)
        if not user or isinstance(user, AnonymousUser):
            sensitive_endpoints = ['/api/', '/admin/']
            if any(endpoint in path for endpoint in sensitive_endpoints):
                risk_score += 15

        return min(risk_score, 100)  # Cap at 100


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add comprehensive security headers"""

    def process_response(self, request, response):
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        # Content Security Policy (adjust based on your needs)
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response['Content-Security-Policy'] = csp_policy

        # Cache control for sensitive endpoints
        if '/api/' in request.path:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting middleware with different limits per user type"""

    def process_request(self, request):
        # Skip for certain paths
        skip_paths = ['/admin/', '/static/', '/media/']
        if any(request.path.startswith(path) for path in skip_paths):
            return None

        ip = self._get_client_ip(request)

        # Check if user is available (after authentication middleware)
        user = getattr(request, 'user', None)

        # Determine rate limit
        if not user or isinstance(user, AnonymousUser):
            limit = 60  # 60 requests per minute for anonymous users
            window = 60
            prefix = f"rate_limit_anon_{ip}"
        else:
            # Different limits based on user type
            if hasattr(user, 'profile') and user.profile.is_premium:
                limit = 1000  # 1000 requests per minute for premium
            else:
                limit = 200   # 200 requests per minute for regular users
            window = 60
            prefix = f"rate_limit_user_{user.id}"

        # Check current count
        current_count = cache.get(prefix, 0)

        if current_count >= limit:
            # Rate limit exceeded
            username = user.username if user and not isinstance(user, AnonymousUser) else 'anonymous'
            security_logger.warning(f"Rate limit exceeded for {ip} (user: {username})")

            response = HttpResponse(
                json.dumps({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Limit: {limit} per minute.',
                    'retry_after': 60
                }),
                content_type='application/json',
                status=429
            )
            response['Retry-After'] = '60'
            response['X-RateLimit-Limit'] = str(limit)
            response['X-RateLimit-Remaining'] = '0'
            response['X-RateLimit-Reset'] = str(int(time.time()) + window)

            # Mark as rate limit hit in audit
            if hasattr(request, '_audit_start_time'):
                request._rate_limit_hit = True

            return response

        # Increment counter
        cache.set(prefix, current_count + 1, window)

        return None

    def process_response(self, request, response):
        # Add rate limit headers
        if '/api/' in request.path:
            user = getattr(request, 'user', None)

            if not user or isinstance(user, AnonymousUser):
                limit = 60
                prefix = f"rate_limit_anon_{self._get_client_ip(request)}"
            else:
                limit = 1000 if (hasattr(user, 'profile') and user.profile.is_premium) else 200
                prefix = f"rate_limit_user_{user.id}"

            current_count = cache.get(prefix, 0)
            remaining = max(0, limit - current_count)

            response['X-RateLimit-Limit'] = str(limit)
            response['X-RateLimit-Remaining'] = str(remaining)
            response['X-RateLimit-Reset'] = str(int(time.time()) + 60)

        return response

    def _get_client_ip(self, request):
        """Get real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


class UserActivityTrackingMiddleware(MiddlewareMixin):
    """Track user activity and update profiles"""

    def process_response(self, request, response):
        # Only track API calls for authenticated users
        user = getattr(request, 'user', None)
        if (not user or isinstance(user, AnonymousUser) or
            not request.path.startswith('/api/') or
            response.status_code >= 400):
            return response

        try:
            # Update user profile activity
            profile = user.profile

            # Increment API usage if successful
            if 200 <= response.status_code < 300:
                profile.increment_api_usage()

                # Update specific counters based on endpoint
                if 'content' in request.path:
                    profile.total_content_created += 1 if request.method == 'POST' else 0
                elif 'image' in request.path:
                    profile.total_images_generated += 1 if request.method == 'POST' else 0
                elif 'embedding' in request.path:
                    profile.total_embeddings_created += 1 if request.method == 'POST' else 0

                # Save if any counters were updated
                if request.method == 'POST':
                    profile.save(update_fields=[
                        'total_content_created',
                        'total_images_generated',
                        'total_embeddings_created'
                    ])

        except Exception as e:
            # Don't break the response if tracking fails
            logging.getLogger('core.audit').error(f"User activity tracking error: {e}")

        return response