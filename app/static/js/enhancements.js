/**
 * UI Enhancements - Life Admin System
 * Toast notifications, loading states, keyboard shortcuts, and UX improvements
 */

// Toast notification system
const Toast = {
  container: null,

  init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }
  },

  show(title, message, type = 'info', duration = 4000) {
    this.init();

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
      success: '✓',
      error: '✕',
      info: 'ℹ',
      warning: '⚠'
    };

    toast.innerHTML = `
      <div class="toast-icon">${icons[type] || icons.info}</div>
      <div class="toast-content">
        ${title ? `<div class="toast-title">${title}</div>` : ''}
        <div class="toast-message">${message}</div>
      </div>
    `;

    this.container.appendChild(toast);

    // Auto-remove after duration
    setTimeout(() => {
      toast.classList.add('removing');
      setTimeout(() => {
        toast.remove();
      }, 300);
    }, duration);

    // Click to dismiss
    toast.addEventListener('click', () => {
      toast.classList.add('removing');
      setTimeout(() => toast.remove(), 300);
    });

    return toast;
  },

  success(title, message, duration) {
    return this.show(title, message, 'success', duration);
  },

  error(title, message, duration) {
    return this.show(title, message, 'error', duration);
  },

  info(title, message, duration) {
    return this.show(title, message, 'info', duration);
  },

  warning(title, message, duration) {
    return this.show(title, message, 'warning', duration);
  }
};

// Loading state helper
function setButtonLoading(button, isLoading) {
  if (isLoading) {
    button.dataset.originalText = button.textContent;
    button.classList.add('btn-loading');
    button.disabled = true;
  } else {
    button.classList.remove('btn-loading');
    button.disabled = false;
    if (button.dataset.originalText) {
      button.textContent = button.dataset.originalText;
    }
  }
}

// Improved delete function with toast
async function deleteItem(itemId, itemTitle) {
  if (!confirm(`Delete "${itemTitle}"?\n\nThis will mark the item as deleted but preserve it in storage.`)) {
    return;
  }

  try {
    const response = await fetch(`/items/${itemId}`, {
      method: 'DELETE',
    });

    const result = await response.json();

    if (result.ok) {
      Toast.success('Deleted', `"${itemTitle}" has been deleted`);
      setTimeout(() => window.location.reload(), 1000);
    } else {
      Toast.error('Delete Failed', result.message || 'Unknown error');
    }
  } catch (error) {
    Toast.error('Delete Failed', error.message);
  }
}

// Improved generate summary with loading state
async function generateSummaryInline(itemId) {
  const button = event.target;
  setButtonLoading(button, true);

  try {
    const response = await fetch(`/items/${itemId}/summary`, {
      method: 'POST',
    });

    const result = await response.json();

    if (result.ok) {
      Toast.success('Summary Generated', 'AI summary has been created');
      setTimeout(() => window.location.reload(), 1000);
    } else {
      Toast.error('Generation Failed', result.message || 'Unknown error');
      setButtonLoading(button, false);
    }
  } catch (error) {
    Toast.error('Generation Failed', error.message);
    setButtonLoading(button, false);
  }
}

// Improved regenerate summary with loading state
async function regenerateSummary(itemId) {
  if (!confirm('Regenerate AI summary?\n\nThis will replace the existing summary with a new one.')) {
    return;
  }

  const button = event.target;
  setButtonLoading(button, true);

  try {
    const response = await fetch(`/items/${itemId}/summary`, {
      method: 'POST',
    });

    const result = await response.json();

    if (result.ok) {
      Toast.success('Summary Regenerated', 'AI summary has been updated');
      setTimeout(() => window.location.reload(), 1000);
    } else {
      Toast.error('Regeneration Failed', result.message || 'Unknown error');
      setButtonLoading(button, false);
    }
  } catch (error) {
    Toast.error('Regeneration Failed', error.message);
    setButtonLoading(button, false);
  }
}

// Improved dismiss insight
async function dismissInsight(insightId) {
  try {
    const response = await fetch(`/insights/${insightId}/dismiss`, {
      method: 'POST',
    });

    const result = await response.json();

    if (result.ok) {
      Toast.success('Dismissed', 'Insight has been dismissed');
      setTimeout(() => window.location.reload(), 1000);
    } else {
      Toast.error('Dismiss Failed', result.message || 'Unknown error');
    }
  } catch (error) {
    Toast.error('Dismiss Failed', error.message);
  }
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  // Cmd/Ctrl + K: Focus search
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
      searchInput.focus();
      searchInput.select();
    }
  }

  // Cmd/Ctrl + U: Open upload modal
  if ((e.metaKey || e.ctrlKey) && e.key === 'u') {
    e.preventDefault();
    if (typeof showUploadModal === 'function') {
      showUploadModal();
    }
  }

  // Escape: Close modal
  if (e.key === 'Escape') {
    if (typeof hideUploadModal === 'function') {
      hideUploadModal();
    }
  }

  // Cmd/Ctrl + D: Go to dashboard
  if ((e.metaKey || e.ctrlKey) && e.key === 'd') {
    e.preventDefault();
    window.location.href = '/dashboard';
  }

  // Cmd/Ctrl + H: Go to home/vault
  if ((e.metaKey || e.ctrlKey) && e.key === 'h') {
    e.preventDefault();
    window.location.href = '/';
  }
});

// Mobile menu toggle
function initMobileMenu() {
  const sidebar = document.querySelector('.sidebar');
  const topBar = document.querySelector('.top-bar');

  if (!sidebar || !topBar) return;

  // Create mobile menu button
  const menuBtn = document.createElement('button');
  menuBtn.className = 'mobile-menu-btn';
  menuBtn.innerHTML = '☰';
  menuBtn.setAttribute('aria-label', 'Open menu');
  topBar.insertBefore(menuBtn, topBar.firstChild);

  // Create overlay
  const overlay = document.createElement('div');
  overlay.className = 'mobile-overlay';
  document.body.appendChild(overlay);

  // Toggle menu
  menuBtn.addEventListener('click', () => {
    sidebar.classList.toggle('mobile-open');
    overlay.classList.toggle('active');
  });

  // Close on overlay click
  overlay.addEventListener('click', () => {
    sidebar.classList.remove('mobile-open');
    overlay.classList.remove('active');
  });

  // Close on navigation
  sidebar.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      sidebar.classList.remove('mobile-open');
      overlay.classList.remove('active');
    });
  });
}

// Smooth scroll for row expansion
function toggleExpand(itemId) {
  const expandedRow = document.getElementById(`expanded-${itemId}`);
  const expandIcon = document.getElementById(`expand-icon-${itemId}`);

  if (!expandedRow || !expandIcon) return;

  const isExpanded = expandedRow.style.display !== 'none';

  if (isExpanded) {
    expandedRow.style.display = 'none';
    expandIcon.classList.remove('expanded');
  } else {
    expandedRow.style.display = 'table-row';
    expandIcon.classList.add('expanded');

    // Smooth scroll to make sure it's visible
    setTimeout(() => {
      expandedRow.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
      });
    }, 100);
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  initMobileMenu();

  // Show toast for any URL parameters
  const params = new URLSearchParams(window.location.search);
  if (params.get('uploaded')) {
    Toast.success('Upload Complete', 'Your document has been added to the vault');
  }
  if (params.get('deleted')) {
    Toast.success('Deleted', 'The document has been removed');
  }

  // Auto-open batch summaries modal if requested (from menu bar app)
  if (params.get('show_summaries') === 'true') {
    // Small delay to ensure page is loaded
    setTimeout(() => {
      if (typeof showBatchSummaryModal === 'function') {
        showBatchSummaryModal();
      }
    }, 500);
  }
});

// Progress bar for page loads
let progressBar = null;

function showProgress() {
  if (!progressBar) {
    progressBar = document.createElement('div');
    progressBar.className = 'progress-bar';
    document.body.appendChild(progressBar);
  }
  progressBar.classList.add('active');
}

function hideProgress() {
  if (progressBar) {
    progressBar.classList.remove('active');
  }
}

// Show progress on form submits and link clicks
document.addEventListener('submit', () => showProgress());
document.addEventListener('click', (e) => {
  if (e.target.tagName === 'A' && e.target.href && !e.target.target) {
    showProgress();
  }
});

// Hide progress when page loads
window.addEventListener('load', () => hideProgress());
