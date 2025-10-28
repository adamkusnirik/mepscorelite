/**
 * Frontend Synchronization Manager
 * Ensures frontend data stays synchronized with backend changes
 */

class SyncManager {
    constructor() {
        this.syncApiUrl = `${window.location.protocol}//${window.location.host}:5002/api/sync`;
        this.checkInterval = 30000; // Check every 30 seconds
        this.intervalId = null;
        this.isChecking = false;
        this.apiAvailable = false;
        this.callbacks = {
            onSyncNeeded: [],
            onSyncComplete: [],
            onError: []
        };
        
        // Check API availability before starting monitoring
        this.checkApiAvailability().then(() => {
            if (this.apiAvailable) {
                this.startMonitoring();
            } else {
                // Don't show notification in standalone mode - it's normal
            }
        });
    }
    
    /**
     * Check if sync API is available
     */
    async checkApiAvailability() {
        try {
            const response = await fetch(`${this.syncApiUrl}/status`, {
                method: 'GET',
                signal: AbortSignal.timeout(3000) // 3 second timeout
            });
            this.apiAvailable = response.ok;
            return this.apiAvailable;
        } catch (error) {
            this.apiAvailable = false;
            return false;
        }
    }

    /**
     * Add callback for sync events
     */
    on(event, callback) {
        if (this.callbacks[event]) {
            this.callbacks[event].push(callback);
        }
    }
    
    /**
     * Trigger callbacks for an event
     */
    trigger(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => callback(data));
        }
    }
    
    /**
     * Start monitoring for sync needs
     */
    startMonitoring() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        
        // Initial check
        this.checkSyncStatus();
        
        // Periodic checks
        this.intervalId = setInterval(() => {
            this.checkSyncStatus();
        }, this.checkInterval);
        
    }
    
    /**
     * Stop monitoring
     */
    stopMonitoring() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
    
    /**
     * Check if synchronization is needed
     */
    async checkSyncStatus() {
        if (this.isChecking || !this.apiAvailable) return;
        
        this.isChecking = true;
        
        try {
            const response = await fetch(`${this.syncApiUrl}/status`, {
                signal: AbortSignal.timeout(5000) // 5 second timeout
            });
            const data = await response.json();
            
            if (data.success && data.sync_needed) {
                console.warn('SyncManager: Backend changes detected - synchronization needed');
                this.trigger('onSyncNeeded', data);
                
                // Optionally auto-sync (can be configured)
                if (this.shouldAutoSync()) {
                    await this.performSync();
                }
            }
            
        } catch (error) {
            // Only log if this is an unexpected error (not a simple network failure)
            if (error.name !== 'AbortError' && error.name !== 'TypeError') {
                console.error('SyncManager: Failed to check sync status:', error);
            }
            
            // Check if API became unavailable
            const apiStillAvailable = await this.checkApiAvailability();
            if (!apiStillAvailable && this.apiAvailable) {
                this.stopMonitoring();
            }
        } finally {
            this.isChecking = false;
        }
    }
    
    /**
     * Determine if auto-sync should be performed
     */
    shouldAutoSync() {
        // Auto-sync if explicitly enabled or if no user is actively using the interface
        return localStorage.getItem('autoSync') === 'true' || document.hidden;
    }
    
    /**
     * Perform full synchronization
     */
    async performSync() {
        if (!this.apiAvailable) {
            this.showSyncNotification(
                'Sync API offline. Please refresh the page manually to get latest data.',
                'warning'
            );
            return false;
        }

        
        try {
            const response = await fetch(`${this.syncApiUrl}/perform`, {
                method: 'POST',
                signal: AbortSignal.timeout(30000) // 30 second timeout for sync operations
            });
            const data = await response.json();
            
            if (data.success) {
                this.trigger('onSyncComplete', data);
                
                // Reload current page data if needed
                if (typeof window.loadCurrentPageData === 'function') {
                    await window.loadCurrentPageData();
                }
                
                return true;
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('SyncManager: Synchronization failed:', error);
            this.trigger('onError', { type: 'sync_failed', error });
            return false;
        }
    }
    
    /**
     * Validate consistency of a specific term
     */
    async validateTerm(term) {
        try {
            const response = await fetch(`${this.syncApiUrl}/validate/${term}`);
            const data = await response.json();
            
            if (data.success) {
                return data;
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error(`SyncManager: Failed to validate term ${term}:`, error);
            return { consistent: false, error: error.message };
        }
    }
    
    /**
     * Regenerate dataset for a specific term
     */
    async regenerateTerm(term) {
        try {
            const response = await fetch(`${this.syncApiUrl}/regenerate/${term}`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                return true;
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error(`SyncManager: Failed to regenerate term ${term}:`, error);
            return false;
        }
    }
    
    /**
     * Show sync notification to user
     */
    showSyncNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `sync-notification sync-${type}`;
        notification.innerHTML = `
            <div class="sync-notification-content">
                <i class="fas fa-sync-alt ${type === 'warning' ? 'fa-spin' : ''}"></i>
                <span>${message}</span>
                ${type === 'warning' ? `
                    <button class="sync-btn" onclick="window.syncManager.performSync()">
                        Sync Now
                    </button>
                ` : ''}
                <button class="sync-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Add styles if not already present
        if (!document.querySelector('#sync-notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'sync-notification-styles';
            styles.textContent = `
                .sync-notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 9999;
                    min-width: 300px;
                    max-width: 500px;
                    padding: 15px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    transition: all 0.3s ease;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                }
                .sync-notification.sync-info {
                    background: #e1f5fe;
                    border-left: 4px solid #03a9f4;
                    color: #01579b;
                }
                .sync-notification.sync-warning {
                    background: #fff3e0;
                    border-left: 4px solid #ff9800;
                    color: #e65100;
                }
                .sync-notification.sync-success {
                    background: #e8f5e8;
                    border-left: 4px solid #4caf50;
                    color: #2e7d32;
                }
                .sync-notification-content {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                .sync-btn {
                    background: #ff9800;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                }
                .sync-btn:hover {
                    background: #f57c00;
                }
                .sync-close {
                    background: none;
                    border: none;
                    cursor: pointer;
                    color: inherit;
                    opacity: 0.7;
                    margin-left: auto;
                }
                .sync-close:hover {
                    opacity: 1;
                }
            `;
            document.head.appendChild(styles);
        }
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 10 seconds for info/success messages
        if (type !== 'warning') {
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 10000);
        }
    }
}

// Initialize sync manager when page loads
let syncManager;

document.addEventListener('DOMContentLoaded', () => {
    // Disable sync manager for now - running in simple static mode
    // This prevents CORS errors when sync service is not available
    window.syncManager = null;
    
    // TODO: Re-enable sync manager when sync service is needed
    // Uncomment the code below and remove the above lines to enable sync functionality
    /*
    // Check if we're running with a sync-enabled server
    fetch('/api/sync/status', { 
        method: 'GET',
        signal: AbortSignal.timeout(1000) // Quick check
    }).then(() => {
        // Sync API is available, initialize sync manager
        syncManager = new SyncManager();
        window.syncManager = syncManager; // Make globally available
        setupSyncEventHandlers();
    }).catch(() => {
        // No sync API available, skip sync manager entirely
        window.syncManager = null;
    });
    */
});

function setupSyncEventHandlers() {
    if (!syncManager) return;
    
    // Set up event handlers
    syncManager.on('onSyncNeeded', (data) => {
        syncManager.showSyncNotification(
            'Backend data has changed. Click to synchronize with latest updates.',
            'warning'
        );
    });
    
    syncManager.on('onSyncComplete', (data) => {
        syncManager.showSyncNotification(
            'Data synchronized successfully! Page will refresh to show latest updates.',
            'success'
        );
        
        // Refresh page after 2 seconds
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    });
    
    syncManager.on('onError', (data) => {
        console.error('Sync error:', data);
        // Don't show notifications for network errors when API is unavailable
        if (syncManager.apiAvailable || data.type !== 'check_failed') {
            syncManager.showSyncNotification(
                `Synchronization error: ${data.error.message || data.error}`,
                'warning'
            );
        }
    });
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SyncManager;
}