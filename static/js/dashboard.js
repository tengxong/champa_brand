// Dashboard page logic
let revenueChart, ordersChart;

document.addEventListener('DOMContentLoaded', async () => {
  // รอให้ api.js โหลดเสร็จก่อน
  if (typeof API === 'undefined') {
    console.error('API is not defined');
    setTimeout(() => {
      window.location.href = '/login?next=' + encodeURIComponent('/dashboard');
    }, 100);
    return;
  }
  
  // รอสักครู่เพื่อให้แน่ใจว่า token ถูกบันทึกลง localStorage แล้ว
  await new Promise(resolve => setTimeout(resolve, 50));
  
  const token = API.getToken();
  if (!token) {
    console.error('No token found in localStorage or URL');
    setTimeout(() => {
      window.location.href = '/login?next=' + encodeURIComponent('/dashboard');
    }, 100);
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
    // Load user info
    const user = await API.get('/api/admin/me');
    const userInfoEl = document.getElementById('user-info');
    if (userInfoEl) {
      userInfoEl.textContent = `${user.username} (${user.role})`;
    }

    // Load dashboard stats
    const stats = await API.get('/api/admin/dashboard');
    const totalUsers = stats.total_users || 0;
    const totalProducts = stats.total_products || 0;
    const totalOrders = stats.total_orders || 0;
    const totalRevenue = stats.total_revenue || 0;
    
    document.getElementById('stat-users').textContent = totalUsers.toLocaleString();
    document.getElementById('stat-orders').textContent = totalOrders.toLocaleString();
    document.getElementById('stat-revenue').textContent = `$${totalRevenue.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;

    // Load charts with real data
    initCharts(stats);
    
    // Load recent activities
    loadRecentActivities(stats.recent_activities || []);
  } catch (error) {
    console.error('Dashboard error:', error);
    if (typeof Notification !== 'undefined') {
      Notification.error(error.message);
    }
    setTimeout(() => {
      window.location.href = '/login?next=' + encodeURIComponent('/dashboard');
    }, 2000);
  }
});

function initCharts(stats) {
  // Revenue Overview Chart
  const revenueCtx = document.getElementById('revenue-chart');
  if (revenueCtx) {
    const revenueData = stats.revenue_by_month || [0, 0, 0, 0, 0, 0];
    const revenueLabels = stats.revenue_month_labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    const maxRevenue = Math.max(...revenueData, 1000); // Ensure minimum scale
    
    revenueChart = new Chart(revenueCtx, {
      type: 'line',
      data: {
        labels: revenueLabels,
        datasets: [{
          label: 'Revenue',
          data: revenueData,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
          padding: {
            top: 10,
            bottom: 10,
            left: 10,
            right: 10
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            enabled: true,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 10
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            }
          },
          y: {
            beginAtZero: true,
            max: Math.ceil(maxRevenue * 1.2 / 1000) * 1000 || 6000,
            ticks: {
              stepSize: Math.ceil(maxRevenue * 1.2 / 4 / 1000) * 1000 || 1500
            },
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            }
          }
        }
      }
    });
  }

  // Weekly Orders Chart
  const ordersCtx = document.getElementById('orders-chart');
  if (ordersCtx) {
    const ordersData = stats.orders_by_week || [0, 0, 0, 0, 0, 0, 0];
    const ordersLabels = stats.orders_day_labels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const maxOrders = Math.max(...ordersData, 50); // Ensure minimum scale
    
    ordersChart = new Chart(ordersCtx, {
      type: 'bar',
      data: {
        labels: ordersLabels,
        datasets: [{
          label: 'Orders',
          data: ordersData,
          backgroundColor: '#8b5cf6',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
          padding: {
            top: 10,
            bottom: 10,
            left: 10,
            right: 10
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            enabled: true,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 10
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            }
          },
          y: {
            beginAtZero: true,
            max: Math.ceil(maxOrders * 1.2 / 50) * 50 || 200,
            ticks: {
              stepSize: Math.ceil(maxOrders * 1.2 / 4 / 50) * 50 || 50
            },
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            }
          }
        }
      }
    });
  }
}

function loadRecentActivities(activities) {
  const container = document.getElementById('recent-activity');
  if (!container) return;
  
  if (activities.length === 0) {
    container.innerHTML = `
      <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
        <div class="w-10 h-10 rounded-full bg-gray-400 flex items-center justify-center text-white font-semibold">-</div>
        <div class="flex-1">
          <p class="text-sm font-medium text-gray-900">No recent activity</p>
          <p class="text-xs text-gray-500">Activity will appear here</p>
        </div>
      </div>
    `;
    return;
  }
  
  const colors = ['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-pink-500', 'bg-yellow-500'];
  const formatTimeAgo = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  };
  
  container.innerHTML = activities.map((activity, idx) => {
    const firstLetter = activity.name.charAt(0).toUpperCase();
    const colorIndex = idx % colors.length;
    const avatarColor = colors[colorIndex];
    const timeAgo = formatTimeAgo(activity.created_at);
    
    return `
      <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
        <div class="w-10 h-10 rounded-full ${avatarColor} flex items-center justify-center text-white font-semibold">${firstLetter}</div>
        <div class="flex-1">
          <p class="text-sm font-medium text-gray-900">${activity.name} - ${activity.action}</p>
          <p class="text-xs text-gray-500">${timeAgo}</p>
        </div>
      </div>
    `;
  }).join('');
}
