from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
from .push_notifications import send_push_notification


@receiver(post_save, sender=Notification)
def send_push_notification_on_create(sender, instance, created, **kwargs):
    """
    Automatically send push notification when a Notification is created.
    """
    if created:  # Only send when notification is first created, not on updates
        try:
            # Check if user has FCM token
            if instance.user.fcm_token:
                send_push_notification(
                    fcm_token=instance.user.fcm_token,
                    title=instance.title,
                    body=instance.message,
                    data={
                        'type': instance.notification_type,
                        'notification_id': instance.id,
                        'related_id': instance.related_id or '',
                    }
                )
                print(f"📱 Push notification sent for notification {instance.id} to user {instance.user.username}")
            else:
                print(f"⚠️ User {instance.user.username} has no FCM token. Skipping push notification.")
        except Exception as e:
            # Log error but don't fail notification creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send push notification for notification {instance.id}: {str(e)}")
            print(f"❌ Error sending push notification for notification {instance.id}: {str(e)}")

