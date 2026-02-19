import json
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from asgiref.sync import sync_to_async 
from .models import ChatSession, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.session_id = str(self.scope['url_route']['kwargs']['session_id'])
            self.room_group_name = f'chat_{self.session_id}'
            
            self.user = self.scope.get("user")

            if not self.user or self.user.is_anonymous:
                try:
                    session = await ChatSession.objects.aget(id=self.session_id)
                    self.user = await sync_to_async(lambda: session.refugee)()
                except ChatSession.DoesNotExist:
                    self.user = None

            if not self.user:
                print(f"❌ Unauthorized WebSocket attempt for session: {self.session_id}")
                await self.close()
                return

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            print(f"✅ WebSocket Connected (Async): User {self.user.id}")

            # 🛑 تعديل 1: عند الاتصال، قم بتحديث الرسائل غير المقروءة إلى مقروءة وإشعار الطرف الآخر
            # Mark unread messages as read when user connects
            await Message.objects.filter(session_id=self.session_id, is_read=False).exclude(sender=self.user).aupdate(is_read=True)
            
            # إرسال إشعار للطرف الآخر بأنني قرأت الرسائل
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt_event',
                    'reader_id': self.user.id
                }
            )
            
        except Exception as e:
            print("❌ Error during connect:", e)
            traceback.print_exc()
            await self.close()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        except:
            pass

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            
            # 🛑 تعديل 2: معالجة إشارة "تمت القراءة" القادمة من المتصفح
            if data.get('type') == 'mark_read':
                # تحديث الرسائل في قاعدة البيانات
                await Message.objects.filter(session_id=self.session_id, is_read=False).exclude(sender=self.user).aupdate(is_read=True)
                # إبلاغ الطرف الآخر لتحديث واجهته (✔✔)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'read_receipt_event',
                        'reader_id': self.user.id
                    }
                )
                return

            message_text = data.get('message', '').strip()
            user = self.user

            if not message_text:
                return

            if not user.is_staff:
                cache_key = f"throttle_user_{user.id}"
                LIMIT = 10000 
                PERIOD = 60 
                current_count = await sync_to_async(cache.get_or_set)(cache_key, 0, timeout=PERIOD)
                if current_count >= LIMIT:
                    await self.send(text_data=json.dumps({
                        'error': 'Please slow down. You are sending too fast.',
                        'type': 'error_alert'
                    }))
                    return
                await sync_to_async(cache.incr)(cache_key)

            session = await ChatSession.objects.aget(id=self.session_id)

            saved_message = await Message.objects.acreate(
                session=session,
                sender=user,
                text_original=message_text,
                is_read=False # الافتراضي، وسيتم تحديثه إذا كان الطرف الآخر متصلاً
            )

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'id': str(saved_message.id),
                    'sender_id': user.id,
                    'text_original': saved_message.text_original,
                    'text_translated': saved_message.text_translated,
                    'timestamp': str(saved_message.timestamp.strftime("%H:%M")),
                    'is_read': False # نرسل الحالة الأولية
                }
            )
        
        except Exception as e:
            print("❌ Error in receive:")
            traceback.print_exc()

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    # 🛑 تعديل 3: دالة جديدة لإرسال إشعار القراءة للفرونت إند
    async def read_receipt_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'reader_id': event['reader_id']
        }))