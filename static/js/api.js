// Shared API functions
const API = {
  token: null,

  setToken(token) {
    this.token = token;
    localStorage.setItem('token', token);
  },

  getToken() {
    // ตรวจจาก URL query parameter ก่อน (สำหรับ redirect)
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('token');
    if (urlToken) {
      this.token = urlToken;
      localStorage.setItem('token', urlToken);
      // ลบ token จาก URL
      params.delete('token');
      const newUrl = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
      window.history.replaceState({}, '', newUrl);
      return this.token;
    }
    
    // ถ้าไม่มี token ใน URL ให้อ่านจาก localStorage
    if (!this.token) {
      this.token = localStorage.getItem('token');
    }
    
    // ถ้ายังไม่มี token ให้ return null
    return this.token || null;
  },

  headers() {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.getToken()}`
    };
  },

  async request(path, options = {}) {
    const baseUrl = window.location.origin;
    const url = `${baseUrl}${path}`;
    const token = this.getToken();
    if (!token) {
      throw new Error('กรุณาเข้าสู่ระบบ');
    }
    const config = {
      ...options,
      headers: {
        ...this.headers(),
        ...(options.headers || {})
      }
    };
    const response = await fetch(url, config);
    const data = await response.json();
    if (!response.ok) {
      // ถ้า token หมดอายุหรือไม่ถูกต้อง ให้ลบ token และ redirect
      if (response.status === 401) {
        this.token = null;
        localStorage.removeItem('token');
      }
      throw new Error(data.error || 'เกิดข้อผิดพลาด');
    }
    return data;
  },

  async get(path) {
    return this.request(path, { method: 'GET' });
  },

  async post(path, body) {
    return this.request(path, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  },

  async put(path, body) {
    return this.request(path, {
      method: 'PUT',
      body: JSON.stringify(body)
    });
  },

  async delete(path) {
    return this.request(path, { method: 'DELETE' });
  }
};
