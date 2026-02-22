/* static/js/chat.js */

function initChat(config) {

    const sessionId = config.sessionId;
    const currentUserId = config.userId;
    const csrfToken = config.csrfToken;
    const uploadUrl = config.uploadUrl;
    
    const STORAGE_KEY = `offline_queue_${sessionId}`;

    let chatSocket = null;
    let reconnectInterval = null;

    // --- Voice Recording Variables ---
    let mediaRecorder = null;
    let audioChunks = [];
    const micBtn = document.getElementById('mic-btn');

    function connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const host = window.location.host;
        const socketUrl = `${protocol}${host}/ws/chat/${sessionId}/`;
        
        console.log("Connecting to:", socketUrl);
        chatSocket = new WebSocket(socketUrl);

        chatSocket.onopen = function() {
            console.log("Connected!");
            const statusDot = document.querySelector('.status-dot');
            if(statusDot) {
                statusDot.style.color = '#28a745';
                statusDot.innerText = '● connected';
            }

            if (reconnectInterval){
                clearInterval(reconnectInterval);
                reconnectInterval = null;
            }

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
            if(statusDot) {
                statusDot.style.color = 'red';
                statusDot.innerText = '● offline';
            }

            if (!reconnectInterval){
                reconnectInterval = setInterval(connect, 5000);
            }
        };

        chatSocket.onerror = function(err) {
            console.error("Socket error:", err);
            chatSocket.close();
        };
    }

    function processOfflineQueue() {
        const queue = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
        if (queue.length > 0 && chatSocket.readyState === WebSocket.OPEN) {
            console.log(`Sending ${queue.length} offline messages...`);
            queue.forEach(msgText => {
                chatSocket.send(JSON.stringify({message: msgText}));
            });
            localStorage.removeItem(STORAGE_KEY);
            document.querySelectorAll('.message.pending').forEach(el => el.remove());
        }
    }

    function saveToQueueAndShow(msgText) {
        const queue = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
        queue.push(msgText);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));

        const tempId = `temp-${Date.now()}`;
        handleMessage({
            id: tempId,
            sender_id: currentUserId,
            text_original: msgText,
            timestamp: new Date().toISOString(),
            is_pending: true
        });
    }

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
            if (!span.closest('.pending')) {
                span.innerHTML = '<span style="color: #69f0ae;">✔✔</span>';
            }
        });
    }

    function formatTime(isoString){
        if(!isoString) return "";
        
        const d = new Date(isoString);
        if (isNaN(d.getTime())) {
            if(isoString.includes(':') && isoString.length === 5) {
                const today = new Date();
                return `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')} / ${isoString}`;
            }
            return ""; 
        }

        const Y = d.getFullYear();
        const M = String(d.getMonth()+1).padStart(2,'0');
        const D = String(d.getDate()).padStart(2,'0');
        const h = String(d.getHours()).padStart(2,'0');
        const m = String(d.getMinutes()).padStart(2,'0');
        return `${Y}-${M}-${D} / ${h}:${m}`;
    }

    function handleMessage(data){
        const msgId = data.is_pending ? data.id : `msg-${data.id}`;
        
        // 🛑 إذا كانت الرسالة موجودة (مثلاً حالة Processing)، نحدثها بدلاً من تجاهلها
        let div = document.getElementById(msgId);
        if (div) {
            // تحديث المحتوى (مثلاً تحول النص من Processing إلى النص الحقيقي)
            const bodyDiv = div.querySelector('.msg-body');
            if(bodyDiv) {
                 let newBody = "";
                 if(data.image_url) {
                      // ... images ...
                 } else {
                     let text = "";
                     if(String(data.sender_id) === currentUserId){
                         text = data.text_original || "";
                     } else {
                         text = data.text_translated || data.text_original || "";
                     }
                     text = text.replace(/</g,"&lt;").replace(/>/g,"&gt;");
                     newBody = text;
                 }
                 // فقط إذا تغير النص نقوم بالتحديث
                 if(bodyDiv.innerHTML !== newBody) bodyDiv.innerHTML = newBody;
            }
            return;
        }

        div = document.createElement('div');
        div.id = msgId;

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

        // نضع الجسم في div منفصل لسهولة التحديث لاحقاً
        const bodyHtml = `<div class="msg-body">${body}</div>`;

        const timeHtml = `<span class="time">${formatTime(data.timestamp)}</span>`;
        
        let tickHtml = '';
        if (String(data.sender_id) === currentUserId) {
            if (data.is_pending) {
                tickHtml = '<span class="tick-container tick-pending" style="color: #fd7e14; margin-left:5px; font-size:0.8em;">🕒</span>';
            } else {
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
        div.innerHTML = senderLabel + bodyHtml + metaHtml;
        document.querySelector('#chat-log').appendChild(div);
        scrollToBottom();
    }

    // --- Image Upload ---
    const imageBtn = document.getElementById('image-btn');
    const imageInput = document.getElementById('image-input');

    if(imageBtn) {
        imageBtn.onclick = () => imageInput.click();
    }

    if(imageInput) {
        imageInput.onchange = function(){
            const file = imageInput.files[0];
            if(file) uploadFile(file, 'image');
        };
    }

    // --- Voice Recording Logic 🎙️ ---
    if(micBtn) {
        // ضغط مستمر للبدء
        micBtn.onmousedown = startRecording;
        micBtn.ontouchstart = startRecording; // للموبايل

        // رفع الإصبع للإيقاف والإرسال
        micBtn.onmouseup = stopRecording;
        micBtn.ontouchend = stopRecording; // للموبايل
    }

    function startRecording(e) {
        if(e) e.preventDefault(); // منع تحديد النص
        
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            showError("Microphone not supported on this browser.");
            return;
        }

        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    // إرسال الملف فوراً
                    uploadFile(audioBlob, 'audio');
                };

                mediaRecorder.start();
                micBtn.classList.add('recording'); // تغيير اللون للأحمر (CSS)
                micBtn.innerHTML = "🛑"; // تغيير الأيقونة
            })
            .catch(err => {
                console.error("Mic Error:", err);
                showError("Microphone access denied.");
            });
    }

    function stopRecording(e) {
        if(e) e.preventDefault();
        
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
            micBtn.classList.remove('recording');
            micBtn.innerHTML = "🎤";
        }
    }

    // دالة رفع موحدة (صورة أو صوت)
    function uploadFile(file, type){
        const fd = new FormData();
        // Django يتوقع 'image' أو 'audio'
        fd.append(type, file, type === 'audio' ? 'voice_note.webm' : file.name); 
        fd.append('session_id', sessionId);

        // تعطيل الأزرار أثناء الرفع
        if(type === 'image' && imageBtn) {
            imageBtn.innerHTML="⏳";
            imageBtn.disabled=true;
        } else if (type === 'audio' && micBtn) {
            micBtn.innerHTML="⏳";
            micBtn.disabled=true;
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
            resetBtns();
        })
        .catch(err => {
            console.error(err);
            // في حالة الصوت، الرسالة "Processing..." ستظهر من السيرفر، فلا داعي للخطأ
            // showError("Processing..."); 
            resetBtns();
        });
    }

    function resetBtns() {
        if(imageBtn) {
            imageBtn.innerHTML="📎";
            imageBtn.disabled=false;
            imageInput.value="";
        }
        if(micBtn) {
            micBtn.innerHTML="🎤";
            micBtn.disabled=false;
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

    // --- Text Sending ---
    const submitBtn = document.querySelector('#chat-message-submit');
    const textInput = document.querySelector('#chat-message-input');

    if(submitBtn) {
        submitBtn.onclick = function(){
            const msg = textInput.value;
            if(msg.trim() !== ""){
                if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
                    chatSocket.send(JSON.stringify({message: msg}));
                } else {
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

    loadInitialPending();
    connect();
    scrollToBottom();
}