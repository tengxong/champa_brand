# โครงสร้างโปรเจกต์ CHAMPA

## ฝั่ง Client (เว็บลูกค้า – Champa Brand)
- **โฟลเดอร์:** `client/` (เดิมชื่อ "Champa brand")
- **URL:** `/`, `/brand/`, `/brand/<path>`
- **หน้าที่:** หน้าแรก, สินค้า, รีวิว, ติดต่อ, ล็อกอิน/สมัครสมาชิก
- **ไฟล์หลัก:** `client/index.html`, `client/products.html`, `client/script.js`, `client/style.css`
- **API ที่ใช้:** `GET /api/products`, `POST /api/login`, `POST /api/register`

## ฝั่ง Admin (หลังล็อกอินแอดมิน)
- **โฟลเดอร์:** `templates/`
- **URL:** `/dashboard`, `/admin`, `/customer`, `/product`, `/login`
- **หน้าที่:** แดชบอร์ด, จัดการแอดมิน, จัดการลูกค้า, จัดการสินค้า, หน้าเข้าสู่ระบบ/สมัคร
- **ไฟล์หลัก:** `templates/dashboard.html`, `templates/admin.html`, `templates/customer.html`, `templates/product.html`, `templates/login_register.html`
- **Static JS:** `static/js/dashboard.js`, `admin.js`, `customer.js`, `product.js`, `api.js`, `notification.js`
- **API ที่ใช้:** `/api/admin/*` (ต้องส่ง token)

## สรุป
| ฝั่ง    | โฟลเดอร์   | ตัวอย่าง URL      |
|--------|-------------|--------------------|
| Client | `client/`   | `/brand/`, `/login` |
| Admin  | `templates/`| `/dashboard`, `/admin`, `/product` |
