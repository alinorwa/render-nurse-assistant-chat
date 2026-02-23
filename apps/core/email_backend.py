# apps/core/email_backend.py
import socket
from django.core.mail.backends.smtp import EmailBackend

class IPv4EmailBackend(EmailBackend):
    def open(self):
        # نحفظ الدالة الأصلية للشبكة
        old_getaddrinfo = socket.getaddrinfo
        
        # ننشئ دالة جديدة تجبر النظام على اختيار IPv4 فقط (AF_INET)
        def new_getaddrinfo(*args, **kwargs):
            responses = old_getaddrinfo(*args, **kwargs)
            return [response for response in responses if response[0] == socket.AF_INET]
        
        # نطبق الدالة الجديدة مؤقتاً
        socket.getaddrinfo = new_getaddrinfo
        
        try:
            return super().open()
        finally:
            # نعيد الدالة الأصلية كما كانت بعد الانتهاء
            socket.getaddrinfo = old_getaddrinfo