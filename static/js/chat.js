/* static/js/chat.js */

function initChat(config) {

    const sessionId = config.sessionId;
    const currentUserId = config.userId;
    const csrfToken = config.csrfToken;
    const uploadUrl = config.uploadUrl;
    
    // إعدادات العداد والرسائل المترجمة
    let currentImageCount = config.initialImageCount || 0;
    const LIMIT_ERROR_MSG = config.limitErrorMsg || "Limit reached: You can only send up to 7 images.";
    const MAX_IMAGES = 7;
    const counterDisplay = document.getElementById('img-counter');

    const STORAGE_KEY = `offline_queue_${sessionId}`;

    let chatSocket = null;
    let reconnectInterval = null;

    // --- Voice Recording Variables ---
    let mediaRecorder = null;
    let audioChunks = [];
    const micBtn = document.getElementById('mic-btn');
    const recordingOverlay = document.getElementById('recording-overlay');

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
        if (isNaN(d.getTime())) return "";
        return d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    function handleMessage(data){
        const msgId = data.is_pending ? data.id : `msg-${data.id}`;
        let div = document.getElementById(msgId);

        // بناء المحتوى (Body)
        let bodyContent = "";
        
        if (data.audio_url) {
            // التحقق من حالة المعالجة
            const isProcessing = data.text_original && (data.text_original.includes("Processing") || data.text_original.includes("Behandler") || data.text_original.includes("🎤"));
            const displayText = isProcessing ? '<span style="color:#888; font-style:italic;">⏳ ...</span>' : data.text_original;

            bodyContent = `
                <audio controls class="chat-audio" style="max-width: 100%; margin-bottom: 5px;">
                    <source src="${data.audio_url}" type="audio/webm">
                    Your browser does not support audio.
                </audio>
                <div class="audio-text" style="font-size:0.9em; line-height:1.4; color:#333; white-space: pre-wrap;">${displayText}</div>
            `;
        } else if (data.image_url) {
            const url = data.image_url.includes('?') ? data.image_url : data.image_url + '?v=' + new Date().getTime();
            bodyContent = `
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
            bodyContent = `<div class="msg-text">${text}</div>`;
        }

        // تحديث إذا كانت الرسالة موجودة (مثل تحديث النص بعد التحليل)
        if (div) {
            const msgBody = div.querySelector('.msg-body');
            if (msgBody) {
                // نحدث فقط إذا تغير المحتوى (لتجنب وميض مشغل الصوت)
                if (msgBody.innerHTML !== bodyContent) {
                     msgBody.innerHTML = bodyContent;
                }
            }
            return;
        }

        // إنشاء جديد
        div = document.createElement('div');
        div.id = msgId;

        let msgClass = (String(data.sender_id) === currentUserId) ? "sent" : "received";
        if (data.is_pending) msgClass += " pending";

        let senderLabel = "";
        if(String(data.sender_id) !== currentUserId){
            senderLabel = '<span class="sender-label">Nurse 👩‍⚕️</span>';
        }

        const bodyHtml = `<div class="msg-body">${bodyContent}</div>`;
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
        imageBtn.onclick = () => {
            // التحقق من العدد
            if (currentImageCount >= MAX_IMAGES) {
                showError(LIMIT_ERROR_MSG);
                if(counterDisplay) {
                    counterDisplay.style.color = "red";
                    counterDisplay.style.fontWeight = "bold";
                    setTimeout(() => {
                        counterDisplay.style.color = "#666";
                        counterDisplay.style.fontWeight = "normal";
                    }, 2000);
                }
                return;
            }
            imageInput.click();
        };
    }

    if(imageInput) {
        imageInput.onchange = function(){
            const file = imageInput.files[0];
            if(file) uploadFile(file, 'image');
        };
    }

    // --- Voice Recording Logic (Unified & Fixed) ---
    if(micBtn) {
        // دعم اللمس والماوس
        micBtn.onmousedown = startRecording;
        micBtn.ontouchstart = startRecording; 
        
        window.onmouseup = stopRecording;
        window.ontouchend = stopRecording;
    }

    function startRecording(e) {
        if(e.type === 'touchstart') e.preventDefault();
        
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            showError("Microphone not supported.");
            return;
        }

        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                let options = { mimeType: 'audio/webm' };
                if (!MediaRecorder.isTypeSupported('audio/webm')) {
                    options = { mimeType: 'audio/mp4' }; 
                }

                mediaRecorder = new MediaRecorder(stream, options);
                audioChunks = [];

                mediaRecorder.ondataavailable = event => {
                    if (event.data.size > 0) audioChunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    if (audioChunks.length === 0) return;
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    // إرسال فقط إذا كان هناك صوت فعلي
                    if (audioBlob.size > 1000) {
                        uploadFile(audioBlob, 'audio');
                    }
                };

                mediaRecorder.start(200); // تجميع كل 200ms
                
                // إظهار الشاشة السوداء
                if(recordingOverlay) {
                    recordingOverlay.style.display = 'flex';
                }
                micBtn.classList.add('recording');
            })
            .catch(err => {
                console.error("Mic Error:", err);
                showError("Microphone access denied.");
            });
    }

    function stopRecording(e) {
        // إخفاء الشاشة السوداء
        if(recordingOverlay) {
            recordingOverlay.style.display = 'none';
        }
        micBtn.classList.remove('recording');

        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }

    function uploadFile(file, type){
        const fd = new FormData();
        fd.append(type, file, type === 'audio' ? 'voice_note.webm' : file.name); 
        fd.append('session_id', sessionId);

        // تعطيل الأزرار أثناء الرفع
        if(type === 'image' && imageBtn) {
            imageBtn.disabled=true;
            imageBtn.style.opacity = "0.5";
        }

        fetch(uploadUrl,{
            method:'POST',
            headers:{'X-CSRFToken':csrfToken},
            body:fd
        })
        .then(r => {
            if(!r.ok) return r.json().then(data => { throw new Error(data.error || "Upload Failed") });
            return r.json();
        })
        .then(data => {
            if(data.error) {
                showError(data.error);
            } else {
                if (type === 'image') {
                    currentImageCount++;
                    if(counterDisplay) counterDisplay.innerText = `${currentImageCount}/${MAX_IMAGES}`;
                }
            }
            resetBtns();
        })
        .catch(err => {
            if (err.message.includes("Limit reached")) {
                showError(err.message);
            } else {
               if(type !== 'audio') showError("Upload Failed"); 
            }
            resetBtns();
        });
    }

    function resetBtns() {
        if(imageBtn) {
            imageBtn.disabled=false;
            imageInput.value="";
            imageBtn.style.opacity = "1";
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