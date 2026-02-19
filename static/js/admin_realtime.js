/* static/js/admin_realtime.js */

document.addEventListener('DOMContentLoaded', function() {
    // 1. استخراج Session ID من الرابط
    // رابط الأدمن: /admin/chat/chatsession/<uuid>/change/
    const pathParts = window.location.pathname.split('/');
    // الـ UUID عادة يكون قبل آخر جزء (change)
    const sessionId = pathParts[pathParts.length - 3]; // تأكد من الترتيب حسب الرابط لديك

    // التأكد أننا داخل صفحة جلسة
    if (!sessionId || sessionId.length < 20) return; 

    // 2. الاتصال بالويب سوكيت
    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const socketUrl = protocol + window.location.host + '/ws/chat/' + sessionId + '/';
    
    console.log("Admin Connecting to:", socketUrl);
    const chatSocket = new WebSocket(socketUrl);

    // 3. إنشاء شريط التنبيه (مخفي حالياً)
    const notifyBar = document.createElement('div');
    notifyBar.style.cssText = `
        display: none;
        position: fixed;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        background-color: #10b981; /* أخضر */
        color: white;
        padding: 15px 30px;
        border-radius: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 99999;
        cursor: pointer;
        font-weight: bold;
        font-size: 16px;
        animation: slideDown 0.5s ease;
    `;
    notifyBar.innerHTML = "🔔 Nye data tilgjengelig (analyse bilden eller melding)... Trykk for å oppdatere";
    
    // عند الضغط على الشريط، نحدث الصفحة
    notifyBar.onclick = function() {
        window.location.reload();
    };
    
    document.body.appendChild(notifyBar);

    // 4. الاستماع للرسائل
    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        console.log("Admin received update:", data);

        // إذا وصلنا تحليل AI أو رسالة جديدة، نظهر التنبيه
        if (data.ai_analysis || data.text_translated) {
            notifyBar.style.display = 'block';
            
            // تشغيل صوت تنبيه خفيف (اختياري)
            // const audio = new Audio('/static/sounds/ping.mp3');
            // audio.play().catch(e => console.log(e));
        }
    };

    chatSocket.onclose = function(e) {
        console.log('Admin socket closed');
    };
});

// إضافة Animation بسيط
const style = document.createElement('style');
style.innerHTML = `
    @keyframes slideDown {
        from { top: -50px; opacity: 0; }
        to { top: 10px; opacity: 1; }
    }
`;
document.head.appendChild(style);