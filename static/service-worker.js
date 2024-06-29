self.addEventListener('install', event => {
    event.waitUntil(
        caches.open('attendance-app-cache').then(cache => {
            return cache.addAll([
                '/',
                '/static/manifest.json',
                '/static/style.css',
                '/static/script.js',
                '/static/kredpool.png'
            ]);
        })
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});
