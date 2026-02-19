def get_client_ip(request):
    """
    دالة مخصصة لجلب IP المستخدم الحقيقي خلف Docker/Proxy.
    نستخدمها بدلاً من الاعتماد على إعدادات Axes المتغيرة.
    Custom function to get real user IP behind Docker/Proxy.
    Used instead of relying on variable Axes settings.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # في حال وجود عدة بروكسيات، العنوان الحقيقي هو الأول
        # In case of multiple proxies, the real address is the first one
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        # إذا كان اتصالاً مباشراً
        # If direct connection
        ip = request.META.get('REMOTE_ADDR')
    return ip