// Admin management page
const AdminPage = {
  allAdmins: [],
  filteredAdmins: [],
  searchTerm: '',
  filterStatus: 'all',

  async load() {
    try {
      const list = await API.get('/api/admin/admins');
      this.allAdmins = list;
      this.applyFilters();
      this.render();
      this.updateStats();
    } catch (error) {
      document.getElementById('admin-tbody').innerHTML = 
        `<tr><td colspan="6" class="px-6 py-4 text-center text-red-500">${error.message}</td></tr>`;
    }
  },

  applyFilters() {
    this.filteredAdmins = this.allAdmins.filter(admin => {
      const matchesSearch = !this.searchTerm || 
        admin.username.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        (admin.phone && admin.phone.includes(this.searchTerm));
      const matchesFilter = this.filterStatus === 'all' || 
        (this.filterStatus === 'active' && admin.role === 'admin') ||
        (this.filterStatus === 'inactive' && admin.role !== 'admin');
      return matchesSearch && matchesFilter;
    });
  },

  render() {
    const tbody = document.getElementById('admin-tbody');
    
    if (this.filteredAdmins.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-4 text-center text-gray-500">ไม่มีข้อมูล</td></tr>';
      return;
    }

    tbody.innerHTML = this.filteredAdmins.map(admin => {
      const firstLetter = admin.username.charAt(0).toUpperCase();
      const colors = ['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-pink-500'];
      const colorIndex = admin.id % colors.length;
      const avatarColor = colors[colorIndex];
      const role = admin.role === 'admin' ? 'Super Admin' : admin.role;
      const roleColor = role === 'Super Admin' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800';
      const status = 'Active';
      const statusClass = 'bg-green-100 text-green-800';
      const lastLogin = this.getLastLogin(admin.id);
      const permissions = role === 'Super Admin' ? 'Full Access' : 'User Management, Product Management';

      return `
        <tr class="hover:bg-gray-50">
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="flex items-center">
              <div class="w-10 h-10 rounded-full ${avatarColor} flex items-center justify-center text-white font-semibold mr-3">
                ${firstLetter}
              </div>
              <div>
                <div class="text-sm font-medium text-gray-900">${admin.username}</div>
                <div class="text-sm text-gray-500">${admin.username}@champa.com</div>
              </div>
            </div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <span class="px-2 py-1 text-xs font-semibold rounded-full ${roleColor}">${role}</span>
          </td>
          <td class="px-6 py-4">
            <div class="flex flex-wrap gap-1">
              ${permissions.split(', ').map(p => `<span class="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">${p}</span>`).join('')}
            </div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <span class="px-2 py-1 text-xs font-semibold rounded-full ${statusClass}">${status}</span>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${lastLogin}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm">
            <div class="flex items-center space-x-2">
              <button onclick="AdminPage.edit(${admin.id})" class="text-blue-600 hover:text-blue-900" title="Edit">✏️</button>
              <button onclick="AdminPage.message(${admin.id})" class="text-green-600 hover:text-green-900" title="Message">✉️</button>
              <button onclick="AdminPage.delete(${admin.id})" class="text-red-600 hover:text-red-900" title="Delete">🗑️</button>
              <button class="text-gray-600 hover:text-gray-900" title="More">⋮</button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  },

  getLastLogin(id) {
    const times = ['2 hours ago', '5 hours ago', '1 day ago', '3 days ago'];
    return times[id % times.length];
  },

  updateStats() {
    const total = this.filteredAdmins.length;
    const active = this.filteredAdmins.filter(a => a.role === 'admin').length;
    document.getElementById('stat-total-admins').textContent = total;
    document.getElementById('stat-active-now').textContent = active;
  },

  edit(id) {
    Notification.info(`Edit admin #${id}`);
  },

  message(id) {
    Notification.info(`Message admin #${id}`);
  },

  async delete(id) {
    const confirmed = await Confirm.show('ยืนยันลบ Admin นี้?');
    if (!confirmed) return;

    try {
      await API.delete(`/api/admin/admins/${id}`);
      Notification.success('ลบ Admin สำเร็จ!');
      this.load();
    } catch (error) {
      Notification.error(error.message);
    }
  },

  showAddModal() {
    document.getElementById('add-modal').classList.remove('hidden');
  },

  closeAddModal() {
    document.getElementById('add-modal').classList.add('hidden');
    document.getElementById('add-username').value = '';
    document.getElementById('add-phone').value = '';
    document.getElementById('add-password').value = '';
  },

  async add() {
    const username = document.getElementById('add-username').value.trim();
    const phone = document.getElementById('add-phone').value.trim() || null;
    const password = document.getElementById('add-password').value;
    
    if (!username || !password) {
      Notification.warning('กรุณากรอก username และ password');
      return;
    }

    try {
      await API.post('/api/admin/admins', { username, password, phone });
      this.closeAddModal();
      Notification.success('เพิ่ม Admin สำเร็จ!');
      this.load();
    } catch (error) {
      Notification.error(error.message);
    }
  }
};

document.addEventListener('DOMContentLoaded', async () => {
  if (!API.getToken()) {
    window.location.href = '/login?next=' + encodeURIComponent('/admin');
    return;
  }

  // Set active nav item
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('active');
    if (item.getAttribute('href') === currentPath) {
      item.classList.add('active');
    }
  });

  try {
    await API.get('/api/admin/me');
    
    // Search handler
    document.getElementById('search-input').addEventListener('input', (e) => {
      AdminPage.searchTerm = e.target.value;
      AdminPage.applyFilters();
      AdminPage.render();
      AdminPage.updateStats();
    });

    // Filter handler
    document.getElementById('filter-select').addEventListener('change', (e) => {
      AdminPage.filterStatus = e.target.value;
      AdminPage.applyFilters();
      AdminPage.render();
      AdminPage.updateStats();
    });

    AdminPage.load();
  } catch (error) {
    Notification.error(error.message);
    setTimeout(() => {
      window.location.href = '/login?next=' + encodeURIComponent('/admin');
    }, 2000);
  }
});
