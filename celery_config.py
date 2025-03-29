from celery import Celery
import os

broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("tasks", broker=broker_url)
celery_app.conf.update(
    result_backend=broker_url,
    timezone="Asia/Tashkent",
    enable_utc=False,
)
