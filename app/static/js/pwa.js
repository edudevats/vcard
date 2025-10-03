// PWA functionality for VCard Digital
class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.swRegistration = null;
        
        this.init();
    }
    
    async init() {
        // Register service worker
        if ('serviceWorker' in navigator) {
            try {
                this.swRegistration = await navigator.serviceWorker.register('/static/sw.js');
                console.log('Service Worker registered:', this.swRegistration);
                
                // Handle updates
                this.swRegistration.addEventListener('updatefound', () => {
                    const newWorker = this.swRegistration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateAvailable();
                        }
                    });
                });
                
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
        
        // Handle install prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallButton();
        });
        
        // Check if already installed
        window.addEventListener('appinstalled', () => {
            this.isInstalled = true;
            this.hideInstallButton();
            this.showInstalledMessage();
        });
        
        // Handle online/offline status
        this.setupOfflineHandling();
        
        // Setup push notifications
        this.setupPushNotifications();
    }
    
    showInstallButton() {
        const installButton = document.getElementById('pwa-install-button');
        if (installButton) {
            installButton.style.display = 'block';
            installButton.addEventListener('click', () => this.installApp());
        } else {
            // Create install banner
            this.createInstallBanner();
        }
    }
    
    hideInstallButton() {
        const installButton = document.getElementById('pwa-install-button');
        if (installButton) {
            installButton.style.display = 'none';
        }
        
        const banner = document.getElementById('pwa-install-banner');
        if (banner) {
            banner.remove();
        }
    }
    
    createInstallBanner() {
        const banner = document.createElement('div');
        banner.id = 'pwa-install-banner';
        banner.className = 'alert alert-info alert-dismissible fade show position-fixed';
        banner.style.cssText = 'top: 10px; right: 10px; z-index: 1050; max-width: 350px;';
        
        banner.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="me-3">
                    <i class="fas fa-mobile-alt fa-2x text-primary"></i>
                </div>
                <div class="flex-grow-1">
                    <h6 class="alert-heading mb-1">¡Instala VCard Digital!</h6>
                    <small>Accede más rápido desde tu dispositivo</small>
                </div>
            </div>
            <div class="mt-2">
                <button class="btn btn-primary btn-sm me-2" onclick="pwaManager.installApp()">
                    <i class="fas fa-download me-1"></i>Instalar
                </button>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.appendChild(banner);
    }
    
    async installApp() {
        if (!this.deferredPrompt) {
            return;
        }
        
        this.deferredPrompt.prompt();
        const choiceResult = await this.deferredPrompt.userChoice;
        
        if (choiceResult.outcome === 'accepted') {
            console.log('User accepted the install prompt');
            this.hideInstallButton();
        } else {
            console.log('User dismissed the install prompt');
        }
        
        this.deferredPrompt = null;
    }
    
    showInstalledMessage() {
        this.showToast('¡App instalada exitosamente! 🎉', 'success');
    }
    
    showUpdateAvailable() {
        const updateBanner = document.createElement('div');
        updateBanner.className = 'alert alert-warning alert-dismissible fade show position-fixed';
        updateBanner.style.cssText = 'top: 10px; left: 50%; transform: translateX(-50%); z-index: 1051;';
        
        updateBanner.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-sync-alt me-2"></i>
                <span class="me-3">Nueva versión disponible</span>
                <button class="btn btn-warning btn-sm me-2" onclick="pwaManager.updateApp()">
                    Actualizar
                </button>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.appendChild(updateBanner);
    }
    
    updateApp() {
        if (this.swRegistration && this.swRegistration.waiting) {
            this.swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
            window.location.reload();
        }
    }
    
    setupOfflineHandling() {
        // Show offline indicator
        window.addEventListener('online', () => {
            this.showToast('Conexión restablecida', 'success');
            this.hideOfflineIndicator();
        });
        
        window.addEventListener('offline', () => {
            this.showToast('Sin conexión - Modo offline activado', 'warning');
            this.showOfflineIndicator();
        });
        
        // Initial check
        if (!navigator.onLine) {
            this.showOfflineIndicator();
        }
    }
    
    showOfflineIndicator() {
        let indicator = document.getElementById('offline-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'offline-indicator';
            indicator.className = 'alert alert-warning mb-0 text-center';
            indicator.innerHTML = `
                <i class="fas fa-wifi me-2"></i>
                Trabajando sin conexión
            `;
            document.body.insertBefore(indicator, document.body.firstChild);
        }
    }
    
    hideOfflineIndicator() {
        const indicator = document.getElementById('offline-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    async setupPushNotifications() {
        if (!('Notification' in window) || !this.swRegistration) {
            return;
        }
        
        // Check current permission
        if (Notification.permission === 'granted') {
            this.subscribeToNotifications();
        } else if (Notification.permission === 'default') {
            this.showNotificationPrompt();
        }
    }
    
    showNotificationPrompt() {
        // You might want to show this only in certain contexts
        const showPrompt = localStorage.getItem('notification-prompt-dismissed');
        if (showPrompt === 'true') {
            return;
        }
        
        const prompt = document.createElement('div');
        prompt.className = 'alert alert-info alert-dismissible fade show position-fixed';
        prompt.style.cssText = 'bottom: 10px; right: 10px; z-index: 1050; max-width: 350px;';
        
        prompt.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="me-3">
                    <i class="fas fa-bell fa-2x text-info"></i>
                </div>
                <div class="flex-grow-1">
                    <h6 class="alert-heading mb-1">Notificaciones</h6>
                    <small>Recibe avisos sobre nuevas visitas a tus tarjetas</small>
                </div>
            </div>
            <div class="mt-2">
                <button class="btn btn-info btn-sm me-2" onclick="pwaManager.requestNotificationPermission()">
                    Activar
                </button>
                <button type="button" class="btn-close" onclick="pwaManager.dismissNotificationPrompt()"></button>
            </div>
        `;
        
        document.body.appendChild(prompt);
    }
    
    async requestNotificationPermission() {
        const permission = await Notification.requestPermission();
        
        if (permission === 'granted') {
            this.subscribeToNotifications();
            this.showToast('Notificaciones activadas', 'success');
        }
        
        this.dismissNotificationPrompt();
    }
    
    dismissNotificationPrompt() {
        const prompt = document.querySelector('.alert:has(.fas.fa-bell)');
        if (prompt) {
            prompt.remove();
        }
        localStorage.setItem('notification-prompt-dismissed', 'true');
    }
    
    async subscribeToNotifications() {
        try {
            // Get VAPID public key from server
            const response = await fetch('/api/vapid-public-key');
            const data = await response.json();

            if (!response.ok || !data.publicKey) {
                console.error('Failed to get VAPID public key:', data);
                return;
            }

            const subscription = await this.swRegistration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlB64ToUint8Array(data.publicKey)
            });
            
            // Send subscription to server
            await fetch('/api/push-subscription', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(subscription)
            });
            
            console.log('Push notification subscription successful');
            
        } catch (error) {
            console.error('Failed to subscribe to push notifications:', error);
        }
    }
    
    urlB64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }
    
    // Utility methods
    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        // Create toast container if it doesn't exist
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1055';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        
        // Initialize and show toast
        const bsToast = new bootstrap.Toast(toast, { autohide: true, delay: duration });
        bsToast.show();
        
        // Clean up after toast is hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
    
    // Share functionality
    async shareCard(cardData) {
        if (navigator.share) {
            try {
                await navigator.share({
                    title: cardData.title,
                    text: cardData.description,
                    url: cardData.url
                });
                console.log('Card shared successfully');
            } catch (error) {
                if (error.name !== 'AbortError') {
                    console.error('Error sharing:', error);
                    this.fallbackShare(cardData);
                }
            }
        } else {
            this.fallbackShare(cardData);
        }
    }
    
    fallbackShare(cardData) {
        // Fallback sharing options
        if (navigator.clipboard) {
            navigator.clipboard.writeText(cardData.url);
            this.showToast('Enlace copiado al portapapeles', 'success');
        } else {
            // Show sharing modal with options
            this.showShareModal(cardData);
        }
    }
    
    showShareModal(cardData) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Compartir Tarjeta</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">Enlace de la tarjeta:</label>
                            <div class="input-group">
                                <input type="text" class="form-control" value="${cardData.url}" readonly>
                                <button class="btn btn-outline-secondary" onclick="navigator.clipboard.writeText('${cardData.url}'); this.textContent='¡Copiado!';">
                                    Copiar
                                </button>
                            </div>
                        </div>
                        <div class="d-grid gap-2">
                            <a href="whatsapp://send?text=${encodeURIComponent(cardData.url)}" class="btn btn-success">
                                <i class="fab fa-whatsapp me-2"></i>WhatsApp
                            </a>
                            <a href="mailto:?subject=${encodeURIComponent(cardData.title)}&body=${encodeURIComponent(cardData.url)}" class="btn btn-primary">
                                <i class="fas fa-envelope me-2"></i>Email
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }
    
    // Analytics for PWA usage
    trackPWAUsage(event, data = {}) {
        // Send PWA usage analytics
        if (navigator.sendBeacon) {
            navigator.sendBeacon('/api/pwa-analytics', JSON.stringify({
                event,
                data,
                timestamp: Date.now(),
                userAgent: navigator.userAgent,
                standalone: window.matchMedia('(display-mode: standalone)').matches
            }));
        }
    }
}

// Initialize PWA Manager
let pwaManager;
document.addEventListener('DOMContentLoaded', () => {
    pwaManager = new PWAManager();
});

// Add to global scope for easy access
window.pwaManager = pwaManager;