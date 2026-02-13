// Customer management page
const CustomerPage = {
  allCustomers: [],
  filteredCustomers: [],
  currentPage: 1,
  itemsPerPage: 10,
  searchTerm: '',
  filterStatus: 'all',

  async load() {
    try {
      const list = await API.get('/api/admin/customers');
      this.allCustomers = list;
      this.applyFilters();
      this.render();
      this.updateStats();
    } catch (error) {
      document.getElementById('customer-tbody').innerHTML = 
        `<tr><td colspan="7" class="px-6 py-4 text-center text-red-500">${error.message}</td></tr>`;
    }
  },

  applyFilters() {
    this.filteredCustomers = this.allCustomers.filter(customer => {
      const matchesSearch = !this.searchTerm || 
        customer.username.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        (customer.phone && customer.phone.includes(this.searchTerm));
      const matchesFilter = this.filterStatus === 'all' || 
        (this.filterStatus === 'active' && customer.role === 'customer') ||
        (this.filterStatus === 'inactive' && customer.role !== 'customer');
      return matchesSearch && matchesFilter;
    });
  },

  render() {
    const tbody = document.getElementById('customer-tbody');
    const start = (this.currentPage - 1) * this.itemsPerPage;
    const end = start + this.itemsPerPage;
    const pageData = this.filteredCustomers.slice(start, end);
    
    if (pageData.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center text-gray-500">ไม่มีข้อมูล</td></tr>';
      return;
    }

    tbody.innerHTML = pageData.map((customer, idx) => {
      const firstLetter = customer.username.charAt(0).toUpperCase();
      const colors = ['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-pink-500', 'bg-yellow-500', 'bg-red-500'];
      const colorIndex = customer.id % colors.length;
      const avatarColor = colors[colorIndex];
      const status = customer.role === 'customer' ? 'Active' : 'Inactive';
      const statusClass = status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800';
      
      // Mock data for demo (ถ้ามี API จริงให้ใช้ข้อมูลจริง)
      const locations = ['New York, USA', 'Los Angeles, USA', 'Chicago, USA', 'Houston, USA', 'Miami, USA', 'Seattle, USA'];
      const location = locations[idx % locations.length];
      const orders = Math.floor(Math.random() * 20) + 1;
      const totalSpent = (orders * Math.random() * 500).toFixed(2);
      const joinDate = new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      const email = `${customer.username}@champa.com`;
      const phoneDisplay = customer.phone || 'N/A';

      return `
        <tr class="hover:bg-gray-50">
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="flex items-center">
              <div class="w-10 h-10 rounded-full ${avatarColor} flex items-center justify-center text-white font-semibold mr-3">
                ${firstLetter}
              </div>
              <div>
                <div class="text-sm font-medium text-gray-900">${customer.username}</div>
                <div class="text-sm text-gray-500">${location}</div>
              </div>
            </div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="text-sm text-gray-900">${email}</div>
            <div class="text-sm text-gray-500">${phoneDisplay}</div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${orders}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">$${totalSpent}</td>
          <td class="px-6 py-4 whitespace-nowrap">
            <span class="px-2 py-1 text-xs font-semibold rounded-full ${statusClass}">${status}</span>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${joinDate}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm">
            <div class="flex items-center space-x-2">
              <button onclick="CustomerPage.view(${customer.id})" class="text-blue-600 hover:text-blue-900" title="View">👁️</button>
              <button onclick="CustomerPage.message(${customer.id})" class="text-green-600 hover:text-green-900" title="Message">✉️</button>
              <button onclick="CustomerPage.delete(${customer.id})" class="text-red-600 hover:text-red-900" title="Delete">🗑️</button>
              <button class="text-gray-600 hover:text-gray-900" title="More">⋮</button>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    this.updatePagination();
  },

  updateStats() {
    const total = this.filteredCustomers.length;
    const active = this.filteredCustomers.filter(c => c.role === 'customer').length;
    document.getElementById('stat-total-customers').textContent = total;
    document.getElementById('stat-active-customers').textContent = active;
    document.getElementById('stat-total-orders').textContent = total * 10; // Mock
    document.getElementById('stat-total-revenue').textContent = `$${(total * 2.2).toFixed(1)}K`; // Mock
  },

  updatePagination() {
    const total = this.filteredCustomers.length;
    const start = (this.currentPage - 1) * this.itemsPerPage + 1;
    const end = Math.min(this.currentPage * this.itemsPerPage, total);
    
    document.getElementById('showing-from').textContent = total > 0 ? start : 0;
    document.getElementById('showing-to').textContent = end;
    document.getElementById('showing-total').textContent = total;
    
    document.getElementById('prev-btn').disabled = this.currentPage === 1;
    document.getElementById('next-btn').disabled = end >= total;
  },

  prevPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.render();
    }
  },

  nextPage() {
    const totalPages = Math.ceil(this.filteredCustomers.length / this.itemsPerPage);
    if (this.currentPage < totalPages) {
      this.currentPage++;
      this.render();
    }
  },

  view(id) {
    Notification.info(`View customer #${id}`);
  },

  message(id) {
    Notification.info(`Message customer #${id}`);
  },

  async delete(id) {
    const confirmed = await Confirm.show('ยืนยันลบ Customer นี้?');
    if (!confirmed) return;
    try {
      await API.delete(`/api/admin/customers/${id}`);
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

  async addCustomer() {
    const username = document.getElementById('add-username').value.trim();
    const phone = document.getElementById('add-phone').value.trim() || null;
    const password = document.getElementById('add-password').value;
    
    if (!username || !password) {
      Notification.warning('กรุณากรอก username และ password');
      return;
    }

    try {
      await API.post('/api/register', { username, phone, password });
      this.closeAddModal();
      Notification.success('เพิ่ม Customer สำเร็จ!');
      this.load();
    } catch (error) {
      Notification.error(error.message);
    }
  }
};

document.addEventListener('DOMContentLoaded', async () => {
  if (!API.getToken()) {
    window.location.href = '/login?next=' + encodeURIComponent('/customer');
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
      CustomerPage.searchTerm = e.target.value;
      CustomerPage.currentPage = 1;
      CustomerPage.applyFilters();
      CustomerPage.render();
      CustomerPage.updateStats();
    });

    // Filter handler
    document.getElementById('filter-select').addEventListener('change', (e) => {
      CustomerPage.filterStatus = e.target.value;
      CustomerPage.currentPage = 1;
      CustomerPage.applyFilters();
      CustomerPage.render();
      CustomerPage.updateStats();
    });

    CustomerPage.load();
  } catch (error) {
    Notification.error(error.message);
    setTimeout(() => {
      window.location.href = '/login?next=' + encodeURIComponent('/customer');
    }, 2000);
  }
});
