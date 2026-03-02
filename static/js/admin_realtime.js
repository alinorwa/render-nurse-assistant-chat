/* static/js/admin_realtime.js */

document.addEventListener('DOMContentLoaded', function() {
    
    // =========================================================
    // 1. منطق الردود الجاهزة (Canned Responses) - فقط
    // =========================================================
    // تم إزالة منطق التنبيهات (WebSockets Notification Bar) بناءً على الطلب
    
    const dataScript = document.getElementById('canned-responses-data');
    
    if (!dataScript) return;

    let cannedResponses = [];
    try {
        cannedResponses = JSON.parse(dataScript.textContent);
    } catch (e) {
        console.error("Error parsing JSON:", e);
        return;
    }

    function injectQuickReplyButton() {
        // البحث عن حقول النص
        const allTextAreas = document.querySelectorAll('textarea[name*="text_original"]');
        if (allTextAreas.length === 0) return;

        // استبعاد القوالب المخفية
        const visibleTextAreas = Array.from(allTextAreas).filter(area => {
            return !area.name.includes('__prefix__') && !area.id.includes('__prefix__');
        });

        if (visibleTextAreas.length === 0) return;

        // الحقل المستهدف (الأخير)
        const targetTextArea = visibleTextAreas[visibleTextAreas.length - 1];
        if (targetTextArea.dataset.hasQuickReply) return; // تم الحقن مسبقاً

        // الحاوية الأم
        const parent = targetTextArea.parentNode;
        
        // إنشاء حاوية الزر
        const toolsContainer = document.createElement('div');
        toolsContainer.style.cssText = "margin-top: 8px; margin-bottom: 8px; display: flex; align-items: center;";

        // زر فتح القائمة
        const quickReplyBtn = document.createElement('button');
        quickReplyBtn.type = "button";
        quickReplyBtn.innerHTML = `<span style="margin-right:5px;">⚡</span> Choose an answer`;
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
            transition: background-color 0.2s;
        `;
        
        // القائمة المنسدلة
        const dropdown = document.createElement('div');
        dropdown.id = "canned-responses-dropdown";
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
                    targetTextArea.dispatchEvent(new Event('input', { bubbles: true }));
                    targetTextArea.dispatchEvent(new Event('change', { bubbles: true }));
                    targetTextArea.focus();
                    dropdown.style.display = "none";
                    targetTextArea.style.transition = "background-color 0.3s";
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

        // تشغيل القائمة
        quickReplyBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            document.querySelectorAll('div[id^="canned-responses-dropdown"]').forEach(d => d.style.display = 'none');
            const rect = quickReplyBtn.getBoundingClientRect();
            dropdown.style.top = (window.scrollY + rect.bottom + 5) + "px";
            dropdown.style.left = (window.scrollX + rect.left) + "px";
            dropdown.style.display = dropdown.style.display === "none" ? "block" : "none";
        });

        document.addEventListener('click', () => dropdown.style.display = "none");

        // إضافة للـ DOM
        if (parent) {
            parent.insertBefore(toolsContainer, targetTextArea);
            toolsContainer.appendChild(quickReplyBtn);
            document.body.appendChild(dropdown);
            targetTextArea.dataset.hasQuickReply = "true";
        }
    }

    // التشغيل والمراقبة
    setTimeout(injectQuickReplyButton, 500); 
    const observer = new MutationObserver(() => { injectQuickReplyButton(); });
    const adminContent = document.querySelector('#content-main') || document.body;
    if (adminContent) { observer.observe(adminContent, { childList: true, subtree: true }); }
});