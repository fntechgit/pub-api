from celery import shared_task


@shared_task
def create_model_snapshot(summit_id):
    return f"Saving model for summit {summit_id}..."
