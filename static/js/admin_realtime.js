

document.addEventListener('DOMContentLoaded', function() {
    
    // =========================================================
    // 1. منطق التنبيهات (Notification Logic)
    // =========================================================
    const pathParts = window.location.pathname.split('/');
    const sessionId = pathParts.find(part => part.length > 20 && part.includes('-')); // بحث أذكى عن UUID

    if (sessionId) {
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const socketUrl = protocol + window.location.host + '/ws/chat/' + sessionId + '/';
        
        console.log("Admin Connecting to:", socketUrl);
        
        try {
            const chatSocket = new WebSocket(socketUrl);
            // ... (كود التنبيهات كما هو، اختصرته هنا للتركيز على المشكلة) ...
        } catch (e) {
            console.log("WebSocket connection failed", e);
        }
    }

     // =========================================================
    // 2. منطق الردود الجاهزة (Canned Responses) - مخصص لـ Unfold
    // =========================================================
   const dataScript = document.getElementById('canned-responses-data');
    
    if (!dataScript) return;

    let cannedResponses = [];
    try {
        cannedResponses = JSON.parse(dataScript.textContent);
    } catch (e) {
        console.error(e);
        return;
    }
    function injectQuickReplyButton() {
        // 1. البحث عن كل مناطق الكتابة
        const allTextAreas = document.querySelectorAll('textarea[name*="text_original"]');
        
        if (allTextAreas.length === 0) return;

        // 2. التصفية: استبعاد القالب المخفي (__prefix__)
        const visibleTextAreas = Array.from(allTextAreas).filter(area => {
            return !area.name.includes('__prefix__') && !area.id.includes('__prefix__');
        });

        if (visibleTextAreas.length === 0) return;

        // 3. نأخذ الأخير (السطر الفارغ الجديد)
        const targetTextArea = visibleTextAreas[visibleTextAreas.length - 1];
        
        // نتأكد أننا لم نضف الزر له مسبقاً
        if (targetTextArea.dataset.hasQuickReply) return;
        
        console.log("✅ Found REAL target textarea:", targetTextArea.name);

        // 4. 🛑 التعديل الجذري هنا: نستخدم الأب المباشر فقط لتجنب الخطأ
        const parent = targetTextArea.parentNode;
        
        // إنشاء الحاوية والأزرار
        const toolsContainer = document.createElement('div');
        toolsContainer.style.cssText = "margin-top: 8px; margin-bottom: 8px; display: flex; align-items: center;";

        const quickReplyBtn = document.createElement('button');
        quickReplyBtn.type = "button";
        quickReplyBtn.innerHTML = `<span style="margin-right:5px;">⚡</span> Choose an answer`;
        quickReplyBtn.className = "bg-primary-600 text-white hover:bg-primary-700"; // Unfold classes if available
        
        // ستايل احتياطي لضمان المظهر
        quickReplyBtn.style.cssText = `
            background-color: #ebf5ff; 
            color: #1d4ed8; 
            border: 1px solid #bfdbfe;
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
        `;
        
        // إنشاء القائمة (Dropdown)
        const dropdown = document.createElement('div');
        dropdown.style.cssText = `
            position: absolute;
            background-color: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            padding: 5px;
            z-index: 99999;
            display: none;
            min-width: 280px;
            max-height: 250px;
            overflow-y: auto;
        `;

        if (cannedResponses.length > 0) {
            cannedResponses.forEach(resp => {
                const item = document.createElement('div');
                item.innerHTML = `
                     <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-size:1.2em;">📝</span>
                        <span style="font-weight:500; color:#374151; font-size:0.9rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:240px;">
                            ${resp.text}
                        </span>
                    </div>
                `;
                item.style.cssText = "padding: 8px; cursor: pointer; border-bottom: 1px solid #f3f4f6;";
                
                item.addEventListener('click', (e) => {
                    e.stopPropagation();
                    targetTextArea.value = resp.text;
                    // تفعيل الأحداث ليعرف جانغو أن النص تغير
                    targetTextArea.dispatchEvent(new Event('input', { bubbles: true }));
                    targetTextArea.dispatchEvent(new Event('change', { bubbles: true }));
                    
                    targetTextArea.focus();
                    dropdown.style.display = "none";
                    
                    targetTextArea.style.backgroundColor = "#dcfce7";
                    setTimeout(() => targetTextArea.style.backgroundColor = "", 500);
                });
                
                item.onmouseover = () => item.style.backgroundColor = "#f9fafb";
                item.onmouseout = () => item.style.backgroundColor = "white";
                
                dropdown.appendChild(item);
            });
        } else {
            dropdown.innerHTML = "<div style='padding:10px; color:#999; font-size:0.8em;'>No responses found.</div>";
        }

        // تشغيل القائمة (حساب الموقع بدقة)
        quickReplyBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            // نغلق أي قوائم أخرى
            document.querySelectorAll('div[id^="canned-dropdown"]').forEach(d => d.style.display = 'none');

            const rect = quickReplyBtn.getBoundingClientRect();
            dropdown.style.top = (window.scrollY + rect.bottom + 5) + "px";
            dropdown.style.left = (window.scrollX + rect.left) + "px";
            dropdown.style.display = dropdown.style.display === "none" ? "block" : "none";
        });

        document.addEventListener('click', () => dropdown.style.display = "none");

        // 5. الإضافة إلى DOM (بأمان تام)
        // نستخدم parentNode الذي جلبناه في الخطوة 4
        if (parent) {
            // نضع الحاوية قبل الـ textarea
            parent.insertBefore(toolsContainer, targetTextArea);
            toolsContainer.appendChild(quickReplyBtn);
            document.body.appendChild(dropdown); // القائمة تتبع body لتظهر فوق كل شيء
            
            targetTextArea.dataset.hasQuickReply = "true";
        } else {
            console.error("❌ Parent node not found for textarea");
        }
    }
    // التشغيل الأولي
    setTimeout(injectQuickReplyButton, 500); // تأخير بسيط لضمان تحميل Unfold

    // مراقبة التغييرات (لأن Unfold قد يحمل العناصر ببطء)
    const observer = new MutationObserver(() => {
        injectQuickReplyButton();
    });
    
    const adminContent = document.querySelector('#content-main') || document.body;
    observer.observe(adminContent, { childList: true, subtree: true });
});

// إضافة Animation للتنبيه العلوي
const style = document.createElement('style');
style.innerHTML = `
    @keyframes slideDown {
        from { top: -50px; opacity: 0; }
        to { top: 10px; opacity: 1; }
    }
`;
document.head.appendChild(style);