# apps/core/utils.py

def get_client_ip(request):
    """
    استخراج IP الحقيقي للمستخدم سواء كان محلياً أو خلف Render Load Balancer
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # في Render، العنوان الحقيقي هو الأول في القائمة
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        # محلياً
        ip = request.META.get('REMOTE_ADDR')
    return ip