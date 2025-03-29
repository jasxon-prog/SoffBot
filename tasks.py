from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task
def send_reminder(seller_id, buyer_id):
    print(f"Sending reminder to seller {seller_id} for buyer {buyer_id}")
