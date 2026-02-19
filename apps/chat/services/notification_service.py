from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class NotificationService:
    @staticmethod
    def broadcast_message_update(message):
        """
        إرسال تحديث للواجهة الأمامية (ممرض ولاجئ)
        Send update to frontend (Nurse and Refugee)
        """
        if not message.session_id:
            return

        channel_layer = get_channel_layer()
        
        payload = {
            'type': 'chat_message',
            'id': str(message.id),
            'sender_id': message.sender.id,
            'text_original': message.text_original,
            'text_translated': message.text_translated,
            'ai_analysis': message.ai_analysis,
            'is_urgent': message.is_urgent,
            'timestamp': message.timestamp.isoformat(),
        }

        if message.image:
            payload['image_url'] = message.image.url

        async_to_sync(channel_layer.group_send)(
            f'chat_{message.session_id}',
            payload
        )