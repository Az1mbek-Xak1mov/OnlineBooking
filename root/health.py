from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
from redis import Redis
from django.conf import settings

def health_check(request):
    # Check database connection
    db_healthy = True
    try:
        connections['default'].cursor()
    except OperationalError:
        db_healthy = False

    # Check Redis connection
    redis_healthy = True
    try:
        redis = Redis.from_url(settings.REDIS_URL)
        redis.ping()
    except Exception:
        redis_healthy = False

    status = 200 if (db_healthy and redis_healthy) else 503
    health_status = {
        'status': 'healthy' if status == 200 else 'unhealthy',
        'database': 'up' if db_healthy else 'down',
        'redis': 'up' if redis_healthy else 'down',
    }

    return JsonResponse(health_status, status=status)