// ==================== THEME TOGGLE ====================
function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    const html = document.documentElement;
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    html.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
    
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
            
            // Add animation
            themeToggle.style.transform = 'rotate(360deg)';
            setTimeout(() => {
                themeToggle.style.transform = 'rotate(0deg)';
            }, 300);
        });
    }
}

function updateThemeIcon(theme) {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        const icon = themeToggle.querySelector('i');
        if (icon) {
            icon.className = theme === 'light' ? 'bi bi-moon-stars-fill' : 'bi bi-sun-fill';
        }
    }
}

// ==================== TOAST NOTIFICATIONS ====================
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="d-flex align-items-center gap-3">
            <i class="bi bi-${getToastIcon(type)} fs-4"></i>
            <div class="flex-grow-1">${message}</div>
            <button class="btn-close btn-close-sm" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

function getToastIcon(type) {
    const icons = {
        success: 'check-circle-fill',
        error: 'x-circle-fill',
        warning: 'exclamation-triangle-fill',
        info: 'info-circle-fill'
    };
    return icons[type] || icons.info;
}

// ==================== AJAX COMMENT SUBMISSION ====================
function initCommentForm() {
    const commentForm = document.getElementById('comment-form');
    if (!commentForm) return;
    
    commentForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(commentForm);
        const url = commentForm.action;
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Add comment to list
                addCommentToList(data.comment);
                
                // Clear form
                commentForm.reset();
                
                // Show success message
                showToast('Коментар додано!', 'success');
            }
        } catch (error) {
            console.error('Error:', error);
            showToast('Помилка при додаванні коментаря', 'error');
        }
    });
}

function addCommentToList(comment) {
    const commentsList = document.getElementById('comments-list');
    if (!commentsList) return;
    
    const commentHtml = `
        <div class="card mb-3 fade-in">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <strong>${comment.author}</strong>
                    <small class="text-muted">${comment.created_at}</small>
                </div>
                <p class="mb-0">${comment.content}</p>
            </div>
        </div>
    `;
    
    commentsList.insertAdjacentHTML('afterbegin', commentHtml);
}

// ==================== NOTIFICATION MANAGEMENT ====================
async function markNotificationAsRead(notificationId) {
    try {
        const response = await fetch(`/notifications/${notificationId}/read/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update UI
            const notificationElement = document.querySelector(`[data-notification-id="${notificationId}"]`);
            if (notificationElement) {
                notificationElement.classList.remove('unread');
            }
            
            // Update badge count
            updateNotificationBadge();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function markAllNotificationsAsRead() {
    try {
        const response = await fetch('/notifications/read-all/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update UI
            document.querySelectorAll('.notification-item.unread').forEach(item => {
                item.classList.remove('unread');
            });
            
            // Update badge count
            updateNotificationBadge();
            
            showToast('Всі нотифікації позначено як прочитані', 'success');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function updateNotificationBadge() {
    const badge = document.getElementById('notification-badge');
    if (badge) {
        const unreadCount = document.querySelectorAll('.notification-item.unread').length;
        if (unreadCount > 0) {
            badge.textContent = unreadCount;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    }
}

// ==================== ACTIVITY LOG ====================
async function loadTaskActivity(taskId) {
    try {
        const response = await fetch(`/tasks/${taskId}/activity/`);
        const data = await response.json();
        
        const activityList = document.getElementById('activity-list');
        if (!activityList) return;
        
        activityList.innerHTML = '';
        
        data.activities.forEach(activity => {
            const activityHtml = `
                <div class="activity-item mb-3 fade-in">
                    <div class="d-flex gap-3">
                        <div class="activity-icon">
                            <i class="bi bi-circle-fill"></i>
                        </div>
                        <div class="flex-grow-1">
                            <div class="d-flex justify-content-between">
                                <strong>${activity.user}</strong>
                                <small class="text-muted">${activity.created_at}</small>
                            </div>
                            <p class="mb-0 text-muted">${activity.description}</p>
                        </div>
                    </div>
                </div>
            `;
            activityList.insertAdjacentHTML('beforeend', activityHtml);
        });
    } catch (error) {
        console.error('Error:', error);
    }
}

// ==================== SEARCH FUNCTIONALITY ====================
function initSearch() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        
        searchTimeout = setTimeout(() => {
            const query = e.target.value.toLowerCase();
            filterItems(query);
        }, 300);
    });
}

function filterItems(query) {
    const items = document.querySelectorAll('.filterable-item');
    
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(query)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

// ==================== KEYBOARD SHORTCUTS ====================
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('search-input');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Ctrl/Cmd + N for new task
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            window.location.href = '/tasks/create/';
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });
}

// ==================== SMOOTH SCROLLING ====================
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// ==================== UTILITY FUNCTIONS ====================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ==================== MOBILE MENU ====================
function initMobileMenu() {
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
        
        // Close sidebar when clicking outside
        document.addEventListener('click', (e) => {
            if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        });
    }
}

// ==================== AUTO-REFRESH NOTIFICATIONS ====================
function startNotificationPolling() {
    // Refresh notifications every 30 seconds
    setInterval(async () => {
        try {
            const response = await fetch('/notifications/?filter=unread');
            // Update notification badge if needed
            updateNotificationBadge();
        } catch (error) {
            console.error('Error polling notifications:', error);
        }
    }, 30000);
}

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initCommentForm();
    initSearch();
    initKeyboardShortcuts();
    initSmoothScrolling();
    initMobileMenu();
    startNotificationPolling();
    
    // Add fade-in animation to all cards
    document.querySelectorAll('.card').forEach((card, index) => {
        card.style.animationDelay = `${index * 50}ms`;
        card.classList.add('fade-in');
    });
});

// Make functions globally available
window.showToast = showToast;
window.markNotificationAsRead = markNotificationAsRead;
window.markAllNotificationsAsRead = markAllNotificationsAsRead;
window.loadTaskActivity = loadTaskActivity;
