// Product management page
const ProductPage = {
  allProducts: [],
  filteredProducts: [],
  searchTerm: '',
  filterCategory: 'all',
  filterCollar: 'all',
  filterStatus: 'all',
  currentPage: 1,
  itemsPerPage: 10,

  async load() {
    try {
      const list = await API.get('/api/admin/products');
      this.allProducts = list.map(p => ({
        ...p,
        category: p.category != null && p.category !== '' ? p.category : this.getCategory(p.id),
        sales: Math.floor(Math.random() * 500) + 100
      }));
      this.applyFilters();
      this.render();
      this.updateStats();
      this.updatePagination();
    } catch (error) {
      document.getElementById('product-tbody').innerHTML = 
        `<tr><td colspan="5" class="px-6 py-4 text-center text-red-500">${error.message}</td></tr>`;
    }
  },

  getCategory(id) {
    const categories = ['Electronics', 'Sports', 'Home'];
    return categories[id % categories.length];
  },

  getPackageTypeLabel(type) {
    const labels = {
      'company': 'ເສື້ອບານເຕະ',
      'football': 'ເສື້ອບານເຕະ',
      'agency': 'ເສື້ອຕີບານ',
      'event': 'ເສື້ອແລ່ນ',
      'sport': 'ເສື້ອ E-Sport',
      'jersey': 'ເສື້ອ ທີມງານ'
    };
    return labels[type] || type || '-';
  },

  getStatus(stock) {
    // Stock ไม่บังคับแล้ว ไม่ต้องแสดง status
    return { text: '-', class: 'bg-gray-100 text-gray-800' };
  },

  applyFilters() {
    this.filteredProducts = this.allProducts.filter(product => {
      const search = (this.searchTerm || '').trim().toLowerCase();
      const matchesSearch = !search ||
        (product.name && product.name.toLowerCase().includes(search)) ||
        (product.description && product.description.toLowerCase().includes(search));
      const cat = (product.category || '').toString().toLowerCase();
      const matchesCategory = this.filterCategory === 'all' ||
        cat === (this.filterCategory || '').toLowerCase();
      const collar = (product.price_type || '').trim();
      const matchesCollar = this.filterCollar === 'all' ||
        collar === this.filterCollar;
      return matchesSearch && matchesCategory && matchesCollar;
    });
  },

  getPaginatedProducts() {
    const start = (this.currentPage - 1) * this.itemsPerPage;
    const end = start + this.itemsPerPage;
    return this.filteredProducts.slice(start, end);
  },

  render() {
    const tbody = document.getElementById('product-tbody');
    const products = this.getPaginatedProducts();
    
    if (products.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="px-6 py-4 text-center text-gray-500">ไม่มีข้อมูล</td></tr>';
      return;
    }

    const truncate = (str, len) => {
      if (!str) return '-';
      return str.length <= len ? str : str.slice(0, len) + '…';
    };

    const productImageUrl = (path) => {
      if (!path) return null;
      return path.startsWith('/') ? path : '/static/' + path;
    };
    tbody.innerHTML = products.map(product => {
      const status = this.getStatus(product.stock);
      const productImage = productImageUrl(product.image);
      const imageDisplay = productImage 
        ? `<img src="${productImage}" alt="${product.name}" class="w-10 h-10 rounded-lg object-cover mr-3 border border-gray-200">`
        : `<div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center mr-3">
            <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
            </svg>
          </div>`;
      const descShort = truncate(product.description || '', 40);
      const categoryLabel = this.getPackageTypeLabel(product.category || '');
      const collarLabel = (product.price_type || '').trim() || '-';
      return `
        <tr class="hover:bg-gray-50">
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="flex items-center">
              ${imageDisplay}
              <div class="text-sm font-medium text-gray-900">${product.name}</div>
            </div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">${categoryLabel}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">${collarLabel}</td>
          <td class="px-6 py-4 text-sm text-gray-600 max-w-xs" title="${(product.description || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;')}">${descShort}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm">
            <div class="flex items-center space-x-2">
              <button onclick="ProductPage.view(${product.id})" class="text-blue-600 hover:text-blue-900" title="View">👁️</button>
              <button onclick="ProductPage.edit(${product.id})" class="text-indigo-600 hover:text-indigo-900" title="Edit">✏️</button>
              <button onclick="ProductPage.delete(${product.id})" class="text-red-600 hover:text-red-900" title="Delete">🗑️</button>
              <button class="text-gray-600 hover:text-gray-900" title="More">⋮</button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  },

  updateStats() {
    const total = this.allProducts.length;

    document.getElementById('stat-total-products').textContent = total;
    // ไม่แสดง stock stats แล้ว
    if (document.getElementById('stat-low-stock')) document.getElementById('stat-low-stock').textContent = '-';
    if (document.getElementById('stat-out-of-stock')) document.getElementById('stat-out-of-stock').textContent = '-';
  },

  updatePagination() {
    const total = this.filteredProducts.length;
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
      this.updatePagination();
    }
  },

  nextPage() {
    const totalPages = Math.ceil(this.filteredProducts.length / this.itemsPerPage);
    if (this.currentPage < totalPages) {
      this.currentPage++;
      this.render();
      this.updatePagination();
    }
  },

  view(id) {
    const product = this.allProducts.find(p => p.id === id);
    if (!product) {
      Notification.error('ไม่พบสินค้า');
      return;
    }
    const modal = document.getElementById('view-modal');
    if (!modal) return;
    document.getElementById('view-product-name').textContent = product.name;
    // ไม่แสดงราคาใน modal การดู
    const stockEl = document.getElementById('view-product-stock');
    if (stockEl) {
      stockEl.parentElement.style.display = 'none';
    }
    document.getElementById('view-product-description').textContent = product.description || '- ไม่มีคำอธิบาย -';
    const imgEl = document.getElementById('view-product-image');
    if (product.image) {
      const imgUrl = product.image.startsWith('/static/') ? product.image : '/static/' + product.image;
      imgEl.style.backgroundImage = `url(${imgUrl})`;
      imgEl.classList.remove('bg-gray-100');
    } else {
      imgEl.style.backgroundImage = '';
      imgEl.classList.add('bg-gray-100');
    }
    modal.classList.remove('hidden');
  },

  closeView() {
    const modal = document.getElementById('view-modal');
    if (modal) modal.classList.add('hidden');
  },

  async add() {
    const name = document.getElementById('add-name').value.trim();
    const description = document.getElementById('add-description').value.trim() || null;
    const category = document.getElementById('add-category').value;
    const addPriceTypeEl = document.getElementById('add-price-type');
    const priceType = addPriceTypeEl ? (addPriceTypeEl.value || null) : null;
    const imageFile = document.getElementById('add-product-image-input').files[0];

    if (!name) {
      Notification.warning('กรุณากรอกชื่อสินค้า');
      return;
    }

    try {
      const product = await API.post('/api/admin/products', { name, price: 0, stock: null, description, category: category || null, price_type: priceType });
      
      // ถ้ามีรูปให้อัปโหลด
      if (imageFile) {
        await this.uploadProductImage(product.id, imageFile);
      }
      
      this.closeAddModal();
      Notification.success('เพิ่มสินค้าสำเร็จ!');
      this.load();
    } catch (error) {
      Notification.error(error.message);
    }
  },

  previewAddImage(event) {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = function(e) {
        const preview = document.getElementById('add-product-image-preview');
        const placeholder = document.getElementById('add-product-image-placeholder');
        preview.src = e.target.result;
        preview.classList.remove('hidden');
        placeholder.classList.add('hidden');
      };
      reader.readAsDataURL(file);
    }
  },

  previewEditImage(event) {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = function(e) {
        const preview = document.getElementById('edit-product-image-preview');
        const placeholder = document.getElementById('edit-product-image-placeholder');
        preview.src = e.target.result;
        preview.classList.remove('hidden');
        placeholder.classList.add('hidden');
      };
      reader.readAsDataURL(file);
    }
  },

  async uploadProductImage(productId, file) {
    if (!file) {
      Notification.warning('กรุณาเลือกไฟล์รูปภาพ');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      Notification.error('ไฟล์ใหญ่เกินไป (สูงสุด 5MB)');
      return;
    }

    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      Notification.error('ไฟล์ไม่รองรับ (รองรับเฉพาะ: PNG, JPG, JPEG, GIF, WEBP)');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      Notification.info('กำลังอัปโหลดรูป...');
      const token = API.getToken();
      const response = await fetch(`/api/admin/products/${productId}/upload-image`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'อัปโหลดไม่สำเร็จ');
      }

      Notification.success('อัปโหลดรูปสำเร็จ!');
      return data.image;
    } catch (error) {
      Notification.error(error.message);
      throw error;
    }
  },

  showAddModal() {
    document.getElementById('add-modal').classList.remove('hidden');
  },

  closeAddModal() {
    document.getElementById('add-modal').classList.add('hidden');
    document.getElementById('add-name').value = '';
    document.getElementById('add-category').value = '';
    const addPriceType = document.getElementById('add-price-type');
    if (addPriceType) addPriceType.value = '';
    document.getElementById('add-product-image-input').value = '';
    document.getElementById('add-product-image-preview').src = '';
    document.getElementById('add-product-image-preview').classList.add('hidden');
    document.getElementById('add-product-image-placeholder').classList.remove('hidden');
    document.getElementById('add-description').value = '';
  },

  edit(id) {
    const product = this.allProducts.find(p => p.id === id);
    if (!product) {
      Notification.error('ไม่พบสินค้า');
      return;
    }

    document.getElementById('edit-product-id').value = id;
    document.getElementById('edit-product-name').value = product.name;
    document.getElementById('edit-product-description').value = product.description || '';
    const editCategoryEl = document.getElementById('edit-product-category');
    if (editCategoryEl) editCategoryEl.value = product.category || '';
    const editPriceType = document.getElementById('edit-product-price-type');
    const editPrice = document.getElementById('edit-product-price');
    if (editPriceType) editPriceType.value = product.price_type || 'custom';
    if (editPrice) editPrice.value = product.price;

    // แสดงรูปสินค้าใน edit modal
    const editImagePreview = document.getElementById('edit-product-image-preview');
    const editImagePlaceholder = document.getElementById('edit-product-image-placeholder');
    if (product.image) {
      const imgUrl = product.image.startsWith('/') ? product.image : '/static/' + product.image;
      editImagePreview.src = imgUrl;
      editImagePreview.classList.remove('hidden');
      editImagePlaceholder.classList.add('hidden');
    } else {
      editImagePreview.classList.add('hidden');
      editImagePlaceholder.classList.remove('hidden');
    }
    
    // Reset file input
    document.getElementById('edit-product-image-input').value = '';
    
    document.getElementById('edit-modal').classList.remove('hidden');
  },

  closeEdit() {
    document.getElementById('edit-modal').classList.add('hidden');
    document.getElementById('edit-product-image-input').value = '';
  },

  async uploadProductImageFromEdit() {
    const productId = parseInt(document.getElementById('edit-product-id').value);
    const fileInput = document.getElementById('edit-product-image-input');
    const file = fileInput.files[0];
    
    if (!file) {
      Notification.warning('กรุณาเลือกไฟล์รูปภาพ');
      return;
    }

    try {
      const result = await this.uploadProductImage(productId, file);
      // อัปเดตรูปใน modal
      const editImagePreview = document.getElementById('edit-product-image-preview');
      const editImagePlaceholder = document.getElementById('edit-product-image-placeholder');
      if (result) {
        const imgUrl = result.startsWith('/') ? result : '/static/' + result;
        editImagePreview.src = imgUrl;
        editImagePreview.classList.remove('hidden');
        editImagePlaceholder.classList.add('hidden');
      }
      // อัปเดต product ใน allProducts
      const product = this.allProducts.find(p => p.id === productId);
      if (product && result) {
        product.image = result;
      }
      this.load(); // Reload เพื่อแสดงรูปใหม่ในตาราง
    } catch (error) {
      // Error already shown in uploadProductImage
    }
  },

  async saveEdit() {
    const id = parseInt(document.getElementById('edit-product-id').value);
    const product = this.allProducts.find(p => p.id === id);
    const name = document.getElementById('edit-product-name').value.trim();
    const description = document.getElementById('edit-product-description').value.trim() || null;
    const editCategoryEl = document.getElementById('edit-product-category');
    const category = editCategoryEl ? (editCategoryEl.value || null) : (product ? product.category : null);
    const editPriceEl = document.getElementById('edit-product-price');
    const editPriceTypeEl = document.getElementById('edit-product-price-type');
    const price = editPriceEl ? parseFloat(editPriceEl.value) : (product ? product.price : 0);
    const priceType = editPriceTypeEl ? (editPriceTypeEl.value || null) : (product ? product.price_type : null);

    if (!name) {
      Notification.warning('กรุณากรอกชื่อสินค้า');
      return;
    }
    if (editPriceEl && (isNaN(price) || price < 0)) {
      Notification.warning('กรุณากรอกราคาให้ถูกต้อง');
      return;
    }

    try {
      await API.put(`/api/admin/products/${id}`, { name, price, stock: null, description, category, price_type: priceType });
      this.closeEdit();
      Notification.success('แก้ไขสินค้าสำเร็จ!');
      this.load();
    } catch (error) {
      Notification.error(error.message);
    }
  },

  async delete(id) {
    const confirmed = await Confirm.show('ยืนยันลบสินค้านี้?');
    if (!confirmed) return;

    try {
      await API.delete(`/api/admin/products/${id}`);
      Notification.success('ลบสินค้าสำเร็จ!');
      this.load();
    } catch (error) {
      Notification.error(error.message);
    }
  }
};

document.addEventListener('DOMContentLoaded', async () => {
  if (!API.getToken()) {
    window.location.href = '/login?next=' + encodeURIComponent('/product');
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
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        ProductPage.searchTerm = e.target.value;
        ProductPage.currentPage = 1;
        ProductPage.applyFilters();
        ProductPage.render();
        ProductPage.updatePagination();
      });
    }

    // Filter handlers
    const filterCategory = document.getElementById('filter-category');
    if (filterCategory) {
      filterCategory.addEventListener('change', (e) => {
        ProductPage.filterCategory = e.target.value;
        ProductPage.currentPage = 1;
        ProductPage.applyFilters();
        ProductPage.render();
        ProductPage.updatePagination();
      });
    }

    const filterCollar = document.getElementById('filter-collar');
    if (filterCollar) {
      filterCollar.addEventListener('change', (e) => {
        ProductPage.filterCollar = e.target.value;
        ProductPage.currentPage = 1;
        ProductPage.applyFilters();
        ProductPage.render();
        ProductPage.updatePagination();
      });
    }

    const filterStatus = document.getElementById('filter-status');
    if (filterStatus) {
      filterStatus.addEventListener('change', (e) => {
        ProductPage.filterStatus = e.target.value;
        ProductPage.currentPage = 1;
        ProductPage.applyFilters();
        ProductPage.render();
        ProductPage.updatePagination();
      });
    }

    ProductPage.load();
  } catch (error) {
    Notification.error(error.message);
    setTimeout(() => {
      window.location.href = '/login?next=' + encodeURIComponent('/product');
    }, 2000);
  }
});
