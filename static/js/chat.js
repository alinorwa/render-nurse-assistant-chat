/* static/js/chat.js */

function initChat(config) {

    const sessionId = config.sessionId;
    const currentUserId = config.userId;
    const csrfToken = config.csrfToken;
    const uploadUrl = config.uploadUrl;
    
    // مفتاح التخزين المحلي (فريد لكل جلسة)
    const STORAGE_KEY = `offline_queue_${sessionId}`;

    let chatSocket = null;
    let reconnectInterval = null;

    function connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const host = window.location.host;
        const socketUrl = `${protocol}${host}/ws/chat/${sessionId}/`;
        
        console.log("Connecting to:", socketUrl);
        chatSocket = new WebSocket(socketUrl);

        chatSocket.onopen = function() {
            console.log("Connected!");
            const statusDot = document.querySelector('.status-dot');
            statusDot.style.color = '#28a745';
            statusDot.innerText = '● connected'; // تحديث النص

            if (reconnectInterval){
                clearInterval(reconnectInterval);
                reconnectInterval = null;
            }

            // 🛑 فور الاتصال: تحقق هل توجد رسائل معلقة وأرسلها
            processOfflineQueue();
        };

        chatSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            
            if (data.type === 'read_receipt') {
                markAllAsRead();
            } else if (data.type === 'error_alert') {
                showError(data.error);
            } else if (data.type === 'chat_message') {
                if (String(data.sender_id) !== currentUserId) {
                    chatSocket.send(JSON.stringify({'type': 'mark_read'}));
                }
                handleMessage(data);
            }
        };

        chatSocket.onclose = function() {
            console.log("Socket closed, reconnecting...");
            const statusDot = document.querySelector('.status-dot');
            statusDot.style.color = 'red';
            statusDot.innerText = '● offline'; // تحديث النص ليعرف المستخدم

            if (!reconnectInterval){
                reconnectInterval = setInterval(connect, 5000);
            }
        };

        chatSocket.onerror = function(err) {
            console.error("Socket error:", err);
            chatSocket.close();
        };
    }

    // 🛑 دالة لمعالجة الطابور عند عودة الإنترنت
    function processOfflineQueue() {
        const queue = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
        
        if (queue.length > 0 && chatSocket.readyState === WebSocket.OPEN) {
            console.log(`Sending ${queue.length} offline messages...`);
            
            // نرسل الرسائل بالترتيب
            queue.forEach(msgText => {
                chatSocket.send(JSON.stringify({message: msgText}));
            });

            // تفريغ الطابور بعد الإرسال
            localStorage.removeItem(STORAGE_KEY);
            
            // إزالة الرسائل المؤقتة (Pending) من الشاشة لأن السيرفر سيرسل النسخ الحقيقية الآن
            document.querySelectorAll('.message.pending').forEach(el => el.remove());
        }
    }

    // 🛑 دالة لإضافة رسالة للطابور وعرضها مؤقتاً
    function saveToQueueAndShow(msgText) {
        // 1. الحفظ في LocalStorage
        const queue = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
        queue.push(msgText);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));

        // 2. العرض في الشاشة (شكل مؤقت)
        const tempId = `temp-${Date.now()}`;
        
        handleMessage({
            id: tempId,
            sender_id: currentUserId,
            text_original: msgText,
            timestamp: new Date().toISOString(),
            is_pending: true // علامة لتمييزها
        });
    }

    // 🛑 تحميل الرسائل المعلقة عند تحديث الصفحة (إذا كان لا يزال أوفلاين)
    function loadInitialPending() {
        const queue = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
        queue.forEach(msgText => {
            handleMessage({
                id: `temp-${Math.random().toString(36).substr(2, 9)}`,
                sender_id: currentUserId,
                text_original: msgText,
                timestamp: new Date().toISOString(),
                is_pending: true
            });
        });
    }

    function markAllAsRead() {
        const ticks = document.querySelectorAll('.tick-status');
        ticks.forEach(span => {
            // لا نعدل الرسائل المعلقة (Pending)
            if (!span.closest('.pending')) {
                span.innerHTML = '<span style="color: #69f0ae;">✔✔</span>';
            }
        });
    }

    function formatTime(isoString){
        if(!isoString) return "";
        const d = new Date(isoString);
        const Y = d.getFullYear();
        const M = String(d.getMonth()+1).padStart(2,'0');
        const D = String(d.getDate()).padStart(2,'0');
        const h = String(d.getHours()).padStart(2,'0');
        const m = String(d.getMinutes()).padStart(2,'0');
        return `${Y}-${M}-${D} / ${h}:${m}`;
    }

    function handleMessage(data){
        // إذا كانت رسالة مؤقتة نستخدم ID خاص بها، وإلا ID السيرفر
        const msgId = data.is_pending ? data.id : `msg-${data.id}`;
        
        // منع التكرار (إذا وصلت الرسالة الحقيقية وكان هناك واحدة قديمة بنفس الID)
        if (document.getElementById(msgId)) return;

        let div = document.createElement('div');
        div.id = msgId;

        // تحديد الكلاس (مرسل/مستقبل) + (pending إذا كانت معلقة)
        let msgClass = (String(data.sender_id) === currentUserId) ? "sent" : "received";
        if (data.is_pending) msgClass += " pending";

        let senderLabel = "";
        if(String(data.sender_id) !== currentUserId){
            senderLabel = '<span class="sender-label">Nurse 👩‍⚕️</span>';
        }

        let body = "";
        if(data.image_url){
            const url = data.image_url.includes('?') 
                ? data.image_url 
                : data.image_url + '?v=' + new Date().getTime();

            body = `
                <a href="${data.image_url}" target="_blank">
                    <img src="${url}" class="chat-image">
                </a>
            `;
        } else {
            let text = "";
            if(String(data.sender_id) === currentUserId){
                text = data.text_original || "";
            } else {
                text = data.text_translated || data.text_original || "";
            }
            text = text.replace(/</g,"&lt;").replace(/>/g,"&gt;");
            body = text;
        }

        const timeHtml = `<span class="time">${formatTime(data.timestamp)}</span>`;
        
        // 🛑 منطق الأيقونات (صح / ساعة)
        let tickHtml = '';
        if (String(data.sender_id) === currentUserId) {
            if (data.is_pending) {
                // 🕒 ساعة للرسائل المعلقة
                tickHtml = '<span class="tick-container tick-pending" style="color: #fd7e14; margin-left:5px; font-size:0.8em;">🕒</span>';
            } else {
                // ✔ للرسائل المرسلة
                if (data.is_read) {
                    tickHtml = '<span class="tick-container tick-status"><span style="color: #69f0ae;">✔✔</span></span>';
                } else {
                    tickHtml = '<span class="tick-container tick-status"><span style="color: #ccc;">✔</span></span>';
                }
            }
        }

        const metaHtml = `
            <div class="meta-info">
                ${timeHtml}
                ${tickHtml}
            </div>
        `;

        div.className = `message ${msgClass}`;
        div.innerHTML = senderLabel + body + metaHtml;
        document.querySelector('#chat-log').appendChild(div);
        scrollToBottom();
    }

    const imageBtn = document.getElementById('image-btn');
    const imageInput = document.getElementById('image-input');

    if(imageBtn) {
        imageBtn.onclick = () => imageInput.click();
    }

    if(imageInput) {
        imageInput.onchange = function(){
            const file = imageInput.files[0];
            if(file) uploadImage(file);
        };
    }

    function uploadImage(file){
        const fd = new FormData();
        fd.append('image', file);
        fd.append('session_id', sessionId);

        if(imageBtn) {
            imageBtn.innerHTML="⏳";
            imageBtn.disabled=true;
        }

        fetch(uploadUrl,{
            method:'POST',
            headers:{'X-CSRFToken':csrfToken},
            body:fd
        })
        .then(r => {
            if(!r.ok) throw new Error("Upload Failed");
            return r.json();
        })
        .then(data => {
            if(data.error) showError(data.error);
            resetBtn();
        })
        .catch(err => {
            console.error(err);
            showError("Upload Failed");
            resetBtn();
        });
    }

    function resetBtn() {
        if(imageBtn) {
            imageBtn.innerHTML="📎";
            imageBtn.disabled=false;
            imageInput.value="";
        }
    }

    function showError(msg){
        const b = document.getElementById('error-banner');
        if(b) {
            b.innerText="⚠️ "+msg;
            b.style.display='block';
            setTimeout(()=>b.style.display='none',5000);
        }
    }

    const submitBtn = document.querySelector('#chat-message-submit');
    const textInput = document.querySelector('#chat-message-input');

    if(submitBtn) {
        submitBtn.onclick = function(){
            const msg = textInput.value;
            if(msg.trim() !== ""){
                
                // 🛑 التعديل الجوهري: فحص الاتصال
                if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
                    // متصل: أرسل فوراً
                    chatSocket.send(JSON.stringify({message: msg}));
                } else {
                    // غير متصل: احفظ في الطابور واعرضها
                    console.log("Offline! Queuing message...");
                    saveToQueueAndShow(msg);
                }
                
                textInput.value = '';
                scrollToBottom();
            }
        };
    }

    if(textInput) {
        textInput.onkeyup = function(e){
            if(e.key === "Enter") submitBtn.click();
        };
    }

    function scrollToBottom(){
        const log = document.querySelector('#chat-log');
        if(log) log.scrollTop = log.scrollHeight;
    }

    // البدء
    loadInitialPending(); // استرجاع المعلقات القديمة
    connect();
    scrollToBottom();
}