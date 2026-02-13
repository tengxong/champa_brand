// Beautiful Toast Notification System
const Notification = {
  container: null,

  init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'notification-container';
      this.container.className = 'fixed top-4 right-4 z-50 space-y-2';
      document.body.appendChild(this.container);
    }
  },

  show(message, type = 'info', duration = 3000) {
    this.init();
    
    const id = 'toast-' + Date.now();
    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    };
    
    const colors = {
      success: 'bg-green-50 border-green-200 text-green-800',
      error: 'bg-red-50 border-red-200 text-red-800',
      warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      info: 'bg-blue-50 border-blue-200 text-blue-800'
    };

    const toast = document.createElement('div');
    toast.id = id;
    toast.className = `${colors[type]} border rounded-lg shadow-lg p-4 flex items-center space-x-3 min-w-[300px] max-w-[400px] transform transition-all duration-300 translate-x-full opacity-0`;
    
    toast.innerHTML = `
      <span class="text-xl">${icons[type] || icons.info}</span>
      <div class="flex-1">
        <p class="font-medium">${message}</p>
      </div>
      <button onclick="Notification.close('${id}')" class="text-gray-400 hover:text-gray-600">
        ✕
      </button>
    `;

    this.container.appendChild(toast);

    // Animate in
    setTimeout(() => {
      toast.classList.remove('translate-x-full', 'opacity-0');
      toast.classList.add('translate-x-0', 'opacity-100');
    }, 10);

    // Auto close
    if (duration > 0) {
      setTimeout(() => {
        this.close(id);
      }, duration);
    }

    return id;
  },

  close(id) {
    const toast = document.getElementById(id);
    if (toast) {
      toast.classList.add('translate-x-full', 'opacity-0');
      setTimeout(() => {
        toast.remove();
      }, 300);
    }
  },

  success(message, duration = 3000) {
    return this.show(message, 'success', duration);
  },

  error(message, duration = 4000) {
    return this.show(message, 'error', duration);
  },

  warning(message, duration = 3000) {
    return this.show(message, 'warning', duration);
  },

  info(message, duration = 3000) {
    return this.show(message, 'info', duration);
  }
};

// Confirm dialog (แทน confirm())
const Confirm = {
  async show(message) {
    return new Promise((resolve) => {
      const overlay = document.createElement('div');
      overlay.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
      
      const dialog = document.createElement('div');
      dialog.className = 'bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4 transform transition-all';
      
      dialog.innerHTML = `
        <div class="mb-4">
          <h3 class="text-lg font-semibold text-gray-900 mb-2">ยืนยัน</h3>
          <p class="text-gray-600">${message}</p>
        </div>
        <div class="flex justify-end space-x-3">
          <button id="confirm-cancel" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
            ยกเลิก
          </button>
          <button id="confirm-ok" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
            ยืนยัน
          </button>
        </div>
      `;
      
      overlay.appendChild(dialog);
      document.body.appendChild(overlay);
      
      const close = (result) => {
        overlay.classList.add('opacity-0');
        setTimeout(() => {
          overlay.remove();
        }, 200);
        resolve(result);
      };
      
      document.getElementById('confirm-cancel').addEventListener('click', () => close(false));
      document.getElementById('confirm-ok').addEventListener('click', () => close(true));
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) close(false);
      });
    });
  }
};
