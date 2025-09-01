// Service Worker for VCard Digital PWA
const CACHE_NAME = 'vcard-digital-v1.0.0';
const STATIC_CACHE = 'vcard-static-v1';
const DYNAMIC_CACHE = 'vcard-dynamic-v1';

// Files to cache for offline functionality
const STATIC_ASSETS = [
  '/',
  '/static/css/bootstrap.min.css',
  '/static/js/bootstrap.bundle.min.js',
  '/static/manifest.json',
  '/dashboard',
  '/auth/login',
  // Add other critical assets
];

// Dynamic content patterns that should be cached
const CACHE_PATTERNS = [
  /\/c\/[\w-]+$/,  // Card view pages
  /\/dashboard/,   // Dashboard pages
  /\/static\//,    // Static assets
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE).then(cache => {
        console.log('Caching static assets');
        return cache.addAll(STATIC_ASSETS.map(url => new Request(url, {
          credentials: 'same-origin'
        })));
      })
    ])
  );
  
  // Skip waiting to activate immediately
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      // Take control of all pages
      self.clients.claim()
    ])
  );
});

// Fetch event - serve from cache with network fallback
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip cross-origin requests (unless they're for APIs)
  if (url.origin !== location.origin && !url.pathname.startsWith('/api/')) {
    return;
  }
  
  // Handle different types of requests
  if (isStaticAsset(request.url)) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
  } else if (isCardPage(request.url)) {
    event.respondWith(staleWhileRevalidate(request, DYNAMIC_CACHE));
  } else if (isDashboardPage(request.url)) {
    event.respondWith(networkFirst(request, DYNAMIC_CACHE));
  } else if (isAPIRequest(request.url)) {
    event.respondWith(networkOnly(request));
  } else {
    event.respondWith(networkFirst(request, DYNAMIC_CACHE));
  }
});

// Cache strategies
async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  
  if (cached) {
    return cached;
  }
  
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.log('Cache first failed:', error);
    return new Response('Offline', { status: 503 });
  }
}

async function networkFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await cache.match(request);
    if (cached) {
      return cached;
    }
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/offline');
    }
    
    return new Response('Network error', { status: 503 });
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  
  // Always try to fetch in background
  const fetchPromise = fetch(request).then(response => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(() => {
    // If fetch fails, return cached version
    return cached;
  });
  
  // Return cached version immediately, or wait for network
  return cached || fetchPromise;
}

async function networkOnly(request) {
  return fetch(request);
}

// Helper functions
function isStaticAsset(url) {
  return url.includes('/static/') || 
         url.includes('.css') || 
         url.includes('.js') || 
         url.includes('.png') || 
         url.includes('.jpg') || 
         url.includes('.svg');
}

function isCardPage(url) {
  return /\/c\/[\w-]+$/.test(url);
}

function isDashboardPage(url) {
  return url.includes('/dashboard');
}

function isAPIRequest(url) {
  return url.includes('/api/') || url.includes('/ajax/');
}

// Background sync for offline actions
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

async function doBackgroundSync() {
  // Handle queued actions when back online
  console.log('Background sync triggered');
  
  // You could implement offline action queuing here
  // For example, saving draft cards, queuing analytics, etc.
}

// Push notifications
self.addEventListener('push', event => {
  if (!event.data) {
    return;
  }
  
  const data = event.data.json();
  
  const options = {
    body: data.body,
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    vibrate: [200, 100, 200],
    data: data.data || {},
    actions: [
      {
        action: 'view',
        title: 'Ver',
        icon: '/static/icons/action-view.png'
      },
      {
        action: 'dismiss',
        title: 'Descartar',
        icon: '/static/icons/action-dismiss.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'view') {
    const url = event.notification.data.url || '/dashboard';
    event.waitUntil(
      clients.openWindow(url)
    );
  }
});

// Handle notification close
self.addEventListener('notificationclose', event => {
  // Analytics: track notification dismissal
  console.log('Notification closed:', event.notification.data);
});

// Share target (for Web Share Target API)
self.addEventListener('fetch', event => {
  if (event.request.url.endsWith('/share-target') && 
      event.request.method === 'POST') {
    event.respondWith(handleShare(event.request));
  }
});

async function handleShare(request) {
  const formData = await request.formData();
  const title = formData.get('title') || '';
  const text = formData.get('text') || '';
  const url = formData.get('url') || '';
  
  // Handle shared content - perhaps create a new card or save to drafts
  console.log('Shared content:', { title, text, url });
  
  return Response.redirect('/dashboard?shared=true', 303);
}

// Periodic background sync
self.addEventListener('periodicsync', event => {
  if (event.tag === 'analytics-sync') {
    event.waitUntil(syncAnalytics());
  }
});

async function syncAnalytics() {
  // Sync analytics data in background
  console.log('Syncing analytics data...');
}

// Error handling
self.addEventListener('error', event => {
  console.error('Service Worker error:', event.error);
});

self.addEventListener('unhandledrejection', event => {
  console.error('Service Worker unhandled promise rejection:', event.reason);
});

// Utilities for cache management
async function cleanupCaches() {
  const cacheWhitelist = [STATIC_CACHE, DYNAMIC_CACHE];
  const cacheNames = await caches.keys();
  
  return Promise.all(
    cacheNames.map(cacheName => {
      if (!cacheWhitelist.includes(cacheName)) {
        return caches.delete(cacheName);
      }
    })
  );
}

// Message handling from main thread
self.addEventListener('message', event => {
  if (event.data && event.data.type) {
    switch (event.data.type) {
      case 'SKIP_WAITING':
        self.skipWaiting();
        break;
      case 'GET_VERSION':
        event.ports[0].postMessage({
          version: CACHE_NAME
        });
        break;
      case 'CLEAR_CACHE':
        cleanupCaches().then(() => {
          event.ports[0].postMessage({
            success: true
          });
        });
        break;
      default:
        console.log('Unknown message type:', event.data.type);
    }
  }
});