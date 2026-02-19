const CACHE_NAME = "nurse-app-v1";
const ASSETS_TO_CACHE = [
  "/",
  "/static/css/main.css",
  "/static/images/img-icon.png",
  "/offline/" 
];

// 1. التثبيت: حفظ الملفات الأساسية
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

// 2. تفعيل الكاش وتنظيف القديم
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
});

// 3. استراتيجية الشبكة (Network First)
// نحاول جلب الصفحة من النت، إذا فشل (انقطع النت) نجلبها من الكاش
self.addEventListener("fetch", (event) => {
  event.respondWith(
    fetch(event.request)
      .catch(() => {
        return caches.match(event.request).then((response) => {
          if (response) {
            return response;
          }
          // إذا لم تكن الصفحة في الكاش والنت مقطوع، اعرض صفحة الأوفلاين
          return caches.match("/offline/");
        });
      })
  );
});