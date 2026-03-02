from flask import Flask, request, jsonify, render_template_string, render_template, send_from_directory, redirect
import os
import sys
from werkzeug.utils import secure_filename

# Logging สำหรับ debug
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from pyhon import (
    init_db,
    register,
    list_reviews,
    create_review,
    create_review_by_customer,
    get_review,
    update_review,
    update_review_rating_by_customer,
    delete_review,
    login,
    logout as logout_session,
    get_current_user,
    get_dashboard_overview,
    list_products,
    create_product,
    get_product,
    update_product,
    delete_product,
    list_customers,
    create_admin,
    list_admins,
    delete_customer,
    delete_admin,
    count_admins,
    User,
)

app = Flask(__name__)
# ใช้ absolute path เพื่อให้รูปโหลดได้ไม่ว่า CWD จะอยู่ที่ไหน (รวมตอน deploy)
_base = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER_PROFILE'] = os.path.join(_base, 'static', 'uploads', 'profile')
app.config['UPLOAD_FOLDER_PRODUCT'] = os.path.join(_base, 'static', 'uploads', 'product')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def _normalize_image_path(path):
    """ให้ path รูปใช้ forward slash เสมอ เพื่อให้ URL ใช้ได้ทุกที่"""
    if not path or not isinstance(path, str):
        return path
    return path.replace("\\", "/")

# สร้างโฟลเดอร์สำหรับเก็บรูปภาพ
os.makedirs(app.config['UPLOAD_FOLDER_PROFILE'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_PRODUCT'], exist_ok=True)

# Flag เพื่อ init DB ครั้งเดียว
_db_initialized = False

def initialize_database():
    """สร้างตารางใน DB เมื่อ deploy (ปลอดภัย: CREATE TABLE IF NOT EXISTS)"""
    global _db_initialized
    if _db_initialized:
        return
    try:
        logger.info("Initializing database...")
        init_db()
        _db_initialized = True
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
        # ไม่ crash - จะ retry เมื่อมี request แรก

# เรียก init_db เมื่อ app start (lazy - จะเรียกเมื่อมี request แรก)
@app.before_request
def ensure_db_initialized():
    initialize_database()

# Log เมื่อ app start
logger.info("Flask app initialized")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _get_token_from_request():
    """ดึง token จาก Authorization: Bearer <token> หรือ query ?token= หรือ JSON body"""
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:].strip()
    if request.args.get("token"):
        return request.args.get("token").strip()
    data = request.get_json(silent=True) or {}
    return (data.get("token") or "").strip()


def _require_admin():
    """คืน current_user ถ้าเป็น admin ไม่ใช่คืน (None, json_error), ใช่คืน (user, None)"""
    token = _get_token_from_request()
    if not token:
        return None, (jsonify({"error": "กรุณาเข้าสู่ระบบ"}), 401)
    try:
        user = get_current_user(token)
        if user.role != "admin":
            return None, (jsonify({"error": "ต้องเป็น Admin เท่านั้น"}), 403)
        return user, None
    except Exception as e:
        return None, (jsonify({"error": str(e)}), 401)

# init_db() ถูกเรียกแบบ lazy ใน @app.before_request (ensure_db_initialized) เท่านั้น
# อย่าเรียก init_db() ตอน import เพราะบน Render ยังไม่มี DATABASE_URL หรือจะเชื่อม localhost

PAGE_HTML = r"""
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Champa - เข้าสู่ระบบ</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      min-height: 100vh;
      background: linear-gradient(135deg, #f9f3ff, #e0f7ff);
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .card-auth {
      max-width: 420px;
      width: 100%;
      box-shadow: 0 18px 45px rgba(15, 23, 42, 0.15);
      border-radius: 18px;
      overflow: hidden;
    }
    .brand {
      font-weight: 700;
      letter-spacing: .08em;
      font-size: 0.85rem;
      text-transform: uppercase;
      color: #6366f1;
    }
    .btn-primary {
      background: linear-gradient(135deg, #6366f1, #4f46e5);
      border: none;
    }
    .btn-primary:hover {
      background: linear-gradient(135deg, #4f46e5, #4338ca);
    }
    .status {
      font-size: 0.85rem;
    }
  </style>
</head>
<body>
  <div class="card card-auth">
    <div class="card-body p-4 p-md-5">
      <div class="mb-4 text-center">
        <div class="brand">CHAMPA</div>
        <h2 class="mt-2 mb-1">เข้าสู่ระบบ</h2>
        <p class="text-muted mb-0">กรุณาเข้าสู่ระบบเพื่อใช้งาน</p>
      </div>

      <!-- Login form -->
      <form id="form-login">
        <div class="mb-3">
          <label class="form-label">Username หรือ เบอร์มือถือ</label>
          <input type="text" class="form-control" id="login-username" placeholder="username หรือ 020xxxxxxxx" required />
        </div>
        <div class="mb-3">
          <label class="form-label">Password</label>
          <input type="password" class="form-control" id="login-password" required />
        </div>
        <button type="submit" class="btn btn-primary w-100">
          เข้าสู่ระบบ
        </button>
      </form>

    </div>
  </div>

  <script src="/static/js/notification.js"></script>
  <script>
    const formLogin = document.getElementById("form-login");

    formLogin.addEventListener("submit", async (e) => {
      e.preventDefault();
      const password = document.getElementById("login-password").value;
      const loginId = document.getElementById("login-username").value.trim();
      
      if (!loginId || !password) {
        Notification.warning("กรุณากรอก username/เบอร์มือถือ และ password");
        return;
      }

      try {
        Notification.info("กำลังเข้าสู่ระบบ...", 1000);
        const res = await fetch("/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: loginId, password }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "เกิดข้อผิดพลาด");
        
        // บันทึก token ลง localStorage ก่อน redirect
        if (data.token) {
          const isAdmin = data.user && data.user.role === "admin";
          if (isAdmin) {
            localStorage.setItem("token", data.token);  // Admin ใช้ key นี้
          } else {
            localStorage.setItem("champa_token", data.token);  // Customer ใช้ key นี้
          }
        }
        
        Notification.success("เข้าสู่ระบบสำเร็จ!");
        setTimeout(() => {
          const isAdmin = data.user && data.user.role === "admin";
          // ตรวจสอบ next parameter หรือ redirect ตาม role
          const urlParams = new URLSearchParams(window.location.search);
          const next = urlParams.get("next");
          
          if (next && next.startsWith("/")) {
            window.location.href = next + (next.indexOf("?") >= 0 ? "&" : "?") + "token=" + encodeURIComponent(data.token);
          } else if (isAdmin) {
            window.location.href = "/dashboard?token=" + encodeURIComponent(data.token);
          } else {
            window.location.href = "/brand/";
          }
        }, 500);
      } catch (err) {
        Notification.error(err.message);
      }
    });
  </script>
</body>
</html>
"""


# ========== ฝั่ง Client (Champa Brand - เว็บลูกค้า) ==========
CLIENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client")


@app.get("/")
def index():
    """หน้าแรก -> ไปที่ Champa brand"""
    return redirect("/brand/")


@app.get("/brand/")
def brand_index():
    """หน้าแรก Champa brand"""
    return send_from_directory(CLIENT_DIR, "index.html")


@app.get("/brand/<path:path>")
def brand_static(path):
    """ไฟล์ static ของ Champa brand (css, js, images, หน้าอื่น)"""
    return send_from_directory(CLIENT_DIR, path)


@app.get("/login")
def login_register_page():
    """หน้าเข้าสู่ระบบ / สมัครสมาชิก"""
    return render_template("login_register.html")


@app.get("/admin/loging")
@app.get("/admin/login")
def admin_login_redirect():
    """แก้ typo /admin/loging และ /admin/login ไปหน้า /login (ไม่แสดง Register)"""
    return redirect("/login?next=/dashboard")


@app.get("/ping")
@app.get("/health")
def health_check():
    """Keep-alive endpoint เพื่อป้องกัน Render free tier sleep (เรียกทุก 5-10 นาที)"""
    return jsonify({"status": "ok", "message": "Server is alive"}), 200


@app.get("/setup")
def setup_page():
    """หน้าสร้างแอดมินคนแรก — แสดงเฉพาะเมื่อยังไม่มีแอดมินในระบบ"""
    try:
        if count_admins() > 0:
            return redirect("/login?next=/admin")
    except Exception:
        pass  # DB ยังไม่พร้อมก็ให้แสดงฟอร์มได้ ลองสร้างได้
    return render_template("setup.html")


# ========== API สาธารณะ (สำหรับ Champa brand) ==========


@app.get("/api/products")
def api_products_public():
    """รายการสินค้าสำหรับแสดงบนเว็บ brand (ไม่ต้องล็อกอิน)"""
    try:
        guest = User(id=0, username="guest", phone=None, password_hash="", role="customer")
        products = list_products(guest)
        return jsonify([
            {"id": p.id, "name": p.name, "price": p.price, "stock": p.stock, "image": _normalize_image_path(p.image), "description": p.description, "category": p.category, "price_type": p.price_type}
            for p in products
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/register")
def api_register():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    phone = (data.get("phone") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"error": "กรุณากรอก username และ password"}), 400

    try:
        user = register(username=username, phone=phone, password=password, role="customer")
        return jsonify(
            {
                "id": user.id,
                "username": user.username,
                "phone": user.phone,
                "role": user.role,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/login")
def api_login():
    data = request.get_json(force=True)
    login_id = (data.get("username") or "").strip()  # รองรับ username หรือ เบอร์มือถือ
    password = (data.get("password") or "").strip()

    if not login_id or not password:
        return jsonify({"error": "กรุณากรอก username/เบอร์มือถือ และ password"}), 400

    try:
        token = login(login_id=login_id, password=password)
        user = get_current_user(token)
        return jsonify(
            {
                "token": token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role,
                },
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/logout")
def api_logout():
    """ออกจากระบบ — ลบ session เฉพาะเมื่อผู้ใช้กดปุ่มออกจากระบบ"""
    token = _get_token_from_request()
    if not token:
        return jsonify({"ok": True}), 200
    try:
        logout_session(token)
    except Exception:
        pass
    return jsonify({"ok": True}), 200


# ========== Setup: สร้างแอดมินคนแรก (ใช้กับ ApiDog / Postman ได้ ไม่ต้องส่ง token) ==========


@app.post("/api/setup/first-admin")
def api_setup_first_admin():
    """
    สร้างแอดมินได้โดยไม่จำกัด (ไม่ต้องส่ง token) - ใช้จาก ApiDog ได้เลย
    ใช้จาก ApiDog: POST body JSON { "username": "admin", "password": "รหัสผ่าน", "phone": "020xxxxxxxx" (optional) }
    """
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    phone = (data.get("phone") or "").strip() or None
    if not username or not password:
        return jsonify({"error": "กรุณาส่ง username และ password ใน body (JSON)"}), 400
    try:
        user = register(username=username, password=password, role="admin", phone=phone)
        return jsonify({"id": user.id, "username": user.username, "phone": user.phone, "role": user.role}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ========== Admin (ต้องส่ง token ใน header Authorization: Bearer <token> หรือ ?token=) ==========


@app.get("/api/admin/me")
def api_admin_me():
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    # ดึง profile image path จาก database
    profile_image = None
    try:
        from pyhon import get_connection
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT profile_image FROM users WHERE id = %s", (user.id,))
                result = cur.fetchone()
                if result and result[0]:
                    profile_image = result[0]
    except:
        pass
    return jsonify({
        "id": user.id, 
        "username": user.username, 
        "role": user.role, 
        "phone": user.phone,
        "profile_image": profile_image
    })


@app.get("/api/admin/dashboard")
def api_admin_dashboard():
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    try:
        data = get_dashboard_overview(user)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 403


@app.post("/api/admin/upload-profile")
def api_admin_upload_profile():
    """อัปโหลดรูป profile"""
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    
    if 'file' not in request.files:
        return jsonify({"error": "ไม่มีไฟล์"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "ไม่ได้เลือกไฟล์"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "ไฟล์ไม่รองรับ (รองรับเฉพาะ: png, jpg, jpeg, gif, webp)"}), 400
    
    try:
        # สร้างชื่อไฟล์ใหม่ (user_id_timestamp.extension)
        import time
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"{user.id}_{int(time.time())}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER_PROFILE'], new_filename)
        
        # บันทึกไฟล์
        file.save(filepath)
        
        # บันทึก path ลง database
        from pyhon import get_connection
        with get_connection() as conn:
            with conn.cursor() as cur:
                # ลบรูปเก่าถ้ามี
                cur.execute("SELECT profile_image FROM users WHERE id = %s", (user.id,))
                old_image = cur.fetchone()
                if old_image and old_image[0]:
                    old_path = os.path.join(_base, 'static', old_image[0])
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except:
                            pass
                
                # บันทึก path ใหม่ (เก็บเป็น relative path จาก static)
                relative_path = f"uploads/profile/{new_filename}"
                cur.execute("UPDATE users SET profile_image = %s WHERE id = %s", (relative_path, user.id))
                conn.commit()
        
        return jsonify({
            "success": True,
            "message": "อัปโหลดรูปสำเร็จ",
            "profile_image": relative_path
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/static/uploads/profile/<filename>")
def uploaded_profile_file(filename):
    """Serve uploaded profile images"""
    return send_from_directory(app.config['UPLOAD_FOLDER_PROFILE'], filename)


@app.post("/api/admin/products/<int:product_id>/upload-image")
def api_admin_products_upload_image(product_id):
    """อัปโหลดรูปสินค้า"""
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    
    if 'file' not in request.files:
        return jsonify({"error": "ไม่มีไฟล์"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "ไม่ได้เลือกไฟล์"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "ไฟล์ไม่รองรับ (รองรับเฉพาะ: png, jpg, jpeg, gif, webp)"}), 400
    
    try:
        # ตรวจสอบว่าสินค้ามีอยู่จริง
        from pyhon import get_product
        product = get_product(user, str(product_id))
        if not product:
            return jsonify({"error": "ไม่พบสินค้า"}), 404
        
        # สร้างชื่อไฟล์ใหม่
        import time
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"product_{product_id}_{int(time.time())}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER_PRODUCT'], new_filename)
        
        # บันทึกไฟล์
        file.save(filepath)
        
        # บันทึก path ลง database
        from pyhon import get_connection
        with get_connection() as conn:
            with conn.cursor() as cur:
                # ลบรูปเก่าถ้ามี
                cur.execute("SELECT image FROM products WHERE id = %s", (product_id,))
                old_image = cur.fetchone()
                if old_image and old_image[0]:
                    old_path = os.path.join(_base, 'static', old_image[0])
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except:
                            pass
                
                # บันทึก path ใหม่
                relative_path = f"uploads/product/{new_filename}"
                cur.execute("UPDATE products SET image = %s WHERE id = %s", (relative_path, product_id))
                conn.commit()
        
        return jsonify({
            "success": True,
            "message": "อัปโหลดรูปสำเร็จ",
            "image": relative_path
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/static/uploads/product/<filename>")
def uploaded_product_file(filename):
    """Serve uploaded product images"""
    return send_from_directory(app.config['UPLOAD_FOLDER_PRODUCT'], filename)


@app.get("/api/admin/products")
def api_admin_products_list():
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    try:
        products = list_products(user)
        return jsonify([{"id": p.id, "name": p.name, "price": p.price, "stock": p.stock, "image": _normalize_image_path(p.image), "description": p.description, "category": p.category, "price_type": p.price_type} for p in products])
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/admin/products")
def api_admin_products_create():
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip() or None
    category = (data.get("category") or "").strip() or None
    price_type = (data.get("price_type") or "").strip() or None
    try:
        price = float(data.get("price", 0))
        stock = data.get("stock")
        if stock is not None:
            stock = int(stock)
    except (TypeError, ValueError):
        return jsonify({"error": "price ต้องเป็นตัวเลข"}), 400
    if not name:
        return jsonify({"error": "กรุณากรอกชื่อสินค้า"}), 400
    try:
        p = create_product(user, name=name, price=price, stock=stock, description=description, category=category, price_type=price_type)
        return jsonify({"id": p.id, "name": p.name, "price": p.price, "stock": p.stock, "image": _normalize_image_path(p.image), "description": p.description, "category": p.category, "price_type": p.price_type}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.put("/api/admin/products/<int:product_id>")
def api_admin_products_update(product_id):
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip() if data.get("name") is not None else None
    description = (data.get("description") or "").strip() if data.get("description") is not None else None
    if data.get("description") is not None and description == "":
        description = None
    category = (data.get("category") or "").strip() if data.get("category") is not None else None
    if data.get("category") is not None and category == "":
        category = None
    price_type = (data.get("price_type") or "").strip() if data.get("price_type") is not None else None
    if data.get("price_type") is not None and price_type == "":
        price_type = None
    try:
        price = float(data["price"]) if data.get("price") is not None else None
    except (TypeError, ValueError):
        return jsonify({"error": "price ต้องเป็นตัวเลขที่ถูกต้อง"}), 400
    try:
        stock = int(data["stock"]) if data.get("stock") is not None else None
    except (TypeError, ValueError):
        return jsonify({"error": "stock ต้องเป็นจำนวนเต็มที่ถูกต้อง"}), 400
    try:
        p = update_product(user, str(product_id), name=name, price=price, stock=stock, description=description, category=category, price_type=price_type)
        return jsonify({"id": p.id, "name": p.name, "price": p.price, "stock": p.stock, "image": _normalize_image_path(p.image), "description": p.description, "category": p.category, "price_type": p.price_type})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.delete("/api/admin/products/<int:product_id>")
def api_admin_products_delete(product_id):
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    try:
        delete_product(user, str(product_id))
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ========== Product Reviews API ==========

@app.get("/api/reviews")
def api_reviews_public():
    """รายการรีวิวสินค้าสำหรับแสดงบนเว็บ brand (ไม่ต้องล็อกอิน)"""
    try:
        guest = User(id=0, username="guest", phone=None, password_hash="", role="customer")
        product_id = request.args.get("product_id", type=int)
        reviews = list_reviews(guest, product_id=product_id)
        return jsonify([
            {
                "id": r.id,
                "product_id": r.product_id,
                "customer_name": r.customer_name,
                "customer_phone": r.customer_phone,
                "customer_facebook": r.customer_facebook,
                "customer_instagram": r.customer_instagram,
                "rating": r.rating,
                "comment": r.comment,
                "images": r.images,
                "created_at": r.created_at
            }
            for r in reviews
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/reviews")
def api_reviews_create_by_customer():
    """ลูกค้าส่งรีวิวและคะแนนดาว (ไม่ต้องล็อกอิน) คะแนนที่ลูกค้าให้จะถูกบันทึกและ admin ดูได้"""
    data = request.get_json(force=True) if request.is_json else (request.form or {})
    product_id = data.get("product_id")
    if product_id is not None and not isinstance(product_id, int):
        try:
            product_id = int(product_id)
        except (TypeError, ValueError):
            product_id = None
    customer_name = (data.get("customer_name") or "").strip()
    rating = data.get("rating")
    if rating is not None and not isinstance(rating, int):
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            rating = None
    customer_phone = (data.get("customer_phone") or "").strip() or None
    customer_facebook = (data.get("customer_facebook") or "").strip() or None
    customer_instagram = (data.get("customer_instagram") or "").strip() or None
    comment = (data.get("comment") or "").strip() or None
    images = data.get("images")

    if not product_id:
        return jsonify({"error": "กรุณาระบุ product_id"}), 400
    if not customer_name:
        return jsonify({"error": "กรุณากรอกชื่อลูกค้า"}), 400
    if not rating or rating < 1 or rating > 5:
        return jsonify({"error": "คะแนนดาวต้องอยู่ระหว่าง 1-5"}), 400

    try:
        r = create_review_by_customer(
            product_id=product_id,
            customer_name=customer_name,
            rating=rating,
            customer_phone=customer_phone,
            customer_facebook=customer_facebook,
            customer_instagram=customer_instagram,
            comment=comment,
            images=images,
        )
        return jsonify({
            "id": r.id,
            "product_id": r.product_id,
            "customer_name": r.customer_name,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at,
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.put("/api/reviews/<int:review_id>")
def api_reviews_update_rating(review_id):
    """ลูกค้าแก้ไขคะแนนดาวของตัวเองได้ ถ้าชื่อตรงกับรีวิว (ส่ง customer_name + rating)"""
    data = request.get_json(force=True) if request.is_json else (request.form or {})
    customer_name = (data.get("customer_name") or "").strip()
    rating = data.get("rating")
    if rating is not None and not isinstance(rating, int):
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            rating = None
    if not customer_name:
        return jsonify({"error": "ກະລຸນາໃສ່ຊື່ລູກຄ້າ"}), 400
    if not rating or rating < 1 or rating > 5:
        return jsonify({"error": "ຄະແນນດາວຕ້ອງຢູ່ລະຫວ່າງ 1-5"}), 400
    try:
        r = update_review_rating_by_customer(str(review_id), customer_name, rating)
        return jsonify({"id": r.id, "rating": r.rating})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/admin/reviews")
def api_admin_reviews_list():
    """รายการรีวิวทั้งหมด (Admin)"""
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    try:
        product_id = request.args.get("product_id", type=int)
        reviews = list_reviews(user, product_id=product_id)
        return jsonify([
            {
                "id": r.id,
                "product_id": r.product_id,
                "customer_name": r.customer_name,
                "customer_phone": r.customer_phone,
                "customer_facebook": r.customer_facebook,
                "customer_instagram": r.customer_instagram,
                "rating": r.rating,
                "comment": r.comment,
                "images": r.images,
                "created_at": r.created_at
            }
            for r in reviews
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/admin/reviews")
def api_admin_reviews_create():
    """สร้างรีวิวใหม่ (Admin)"""
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    data = request.get_json(force=True)
    product_id = data.get("product_id")
    customer_name = (data.get("customer_name") or "").strip()
    rating = data.get("rating")
    customer_phone = (data.get("customer_phone") or "").strip() or None
    customer_facebook = (data.get("customer_facebook") or "").strip() or None
    customer_instagram = (data.get("customer_instagram") or "").strip() or None
    comment = (data.get("comment") or "").strip() or None
    images = data.get("images")  # List of image paths
    
    if not product_id:
        return jsonify({"error": "กรุณาระบุ product_id"}), 400
    if not customer_name:
        return jsonify({"error": "กรุณากรอกชื่อลูกค้า"}), 400
    if not rating or rating < 1 or rating > 5:
        return jsonify({"error": "rating ต้องอยู่ระหว่าง 1-5"}), 400
    
    try:
        r = create_review(
            user,
            product_id=product_id,
            customer_name=customer_name,
            rating=rating,
            customer_phone=customer_phone,
            customer_facebook=customer_facebook,
            customer_instagram=customer_instagram,
            comment=comment,
            images=images
        )
        return jsonify({
            "id": r.id,
            "product_id": r.product_id,
            "customer_name": r.customer_name,
            "customer_phone": r.customer_phone,
            "customer_facebook": r.customer_facebook,
            "customer_instagram": r.customer_instagram,
            "rating": r.rating,
            "comment": r.comment,
            "images": r.images,
            "created_at": r.created_at
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.put("/api/admin/reviews/<int:review_id>")
def api_admin_reviews_update(review_id):
    """แก้ไขรีวิว (Admin)"""
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    data = request.get_json(force=True)
    customer_name = (data.get("customer_name") or "").strip() if data.get("customer_name") is not None else None
    customer_phone = (data.get("customer_phone") or "").strip() if data.get("customer_phone") is not None else None
    customer_facebook = (data.get("customer_facebook") or "").strip() if data.get("customer_facebook") is not None else None
    customer_instagram = (data.get("customer_instagram") or "").strip() if data.get("customer_instagram") is not None else None
    rating = data.get("rating") if data.get("rating") is not None else None
    comment = (data.get("comment") or "").strip() if data.get("comment") is not None else None
    if data.get("comment") is not None and comment == "":
        comment = None
    images = data.get("images") if data.get("images") is not None else None
    
    try:
        r = update_review(
            user,
            str(review_id),
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_facebook=customer_facebook,
            customer_instagram=customer_instagram,
            rating=rating,
            comment=comment,
            images=images
        )
        return jsonify({
            "id": r.id,
            "product_id": r.product_id,
            "customer_name": r.customer_name,
            "customer_phone": r.customer_phone,
            "customer_facebook": r.customer_facebook,
            "customer_instagram": r.customer_instagram,
            "rating": r.rating,
            "comment": r.comment,
            "images": r.images,
            "created_at": r.created_at
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.delete("/api/admin/reviews/<int:review_id>")
def api_admin_reviews_delete(review_id):
    """ลบรีวิว (Admin)"""
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    try:
        delete_review(user, str(review_id))
        return jsonify({"message": "ลบรีวิวสำเร็จ"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.get("/api/admin/customers")
def api_admin_customers_list():
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    try:
        customers = list_customers(user)
        return jsonify([{"id": u.id, "username": u.username, "phone": u.phone, "role": u.role} for u in customers])
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.delete("/api/admin/customers/<int:customer_id>")
def api_admin_customers_delete(customer_id):
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    try:
        delete_customer(user, str(customer_id))
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/admin/admins")
def api_admin_admins_create():
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    phone = (data.get("phone") or "").strip() or None
    if not username or not password:
        return jsonify({"error": "กรุณากรอก username และ password"}), 400
    try:
        u = register(username=username, password=password, role="admin", phone=phone)
        return jsonify({"id": u.id, "username": u.username, "phone": u.phone, "role": u.role}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.get("/api/admin/admins")
def api_admin_admins_list():
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    try:
        admins = list_admins(user)
        return jsonify([{"id": u.id, "username": u.username, "role": u.role} for u in admins])
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.delete("/api/admin/admins/<int:admin_id>")
def api_admin_admins_delete(admin_id):
    user, err = _require_admin()
    if err:
        return err[0], err[1]
    try:
        delete_admin(user, str(admin_id))
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# หน้า Admin (ส่ง token ผ่าน query ?token=xxx)
ADMIN_PAGE_HTML = r"""
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Champa - Admin</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { font-family: system-ui, sans-serif; background: #f1f5f9; }
    .navbar-brand { font-weight: 700; color: #6366f1; }
    .card { border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
    .table th { background: #f8fafc; }
  </style>
</head>
<body>
  <nav class="navbar navbar-expand-lg navbar-light bg-white border-bottom">
    <div class="container-fluid">
      <a class="navbar-brand" href="/">CHAMPA</a>
      <span class="navbar-text me-3" id="admin-name"></span>
      <a class="btn btn-outline-secondary btn-sm" href="/">ออกจากระบบ / กลับหน้าแรก</a>
    </div>
  </nav>
  <div class="container py-4">
    <div id="admin-error" class="alert alert-danger d-none"></div>
    <div class="row mb-4">
      <div class="col-md-3"><div class="card p-3"><h6 class="text-muted">ผู้ใช้ทั้งหมด</h6><div id="stat-users" class="h4">-</div></div></div>
      <div class="col-md-3"><div class="card p-3"><h6 class="text-muted">ลูกค้า</h6><div id="stat-customers" class="h4">-</div></div></div>
      <div class="col-md-3"><div class="card p-3"><h6 class="text-muted">สินค้า</h6><div id="stat-products" class="h4">-</div></div></div>
    </div>
    <div class="card p-4 mb-4">
      <h5 class="mb-3">เพิ่มสินค้า</h5>
      <div class="row g-2">
        <div class="col-md-4"><input type="text" class="form-control" id="new-name" placeholder="ชื่อสินค้า" /></div>
        <div class="col-md-2"><input type="number" class="form-control" id="new-price" placeholder="ราคา" step="0.01" min="0" /></div>
        <div class="col-md-2"><input type="number" class="form-control" id="new-stock" placeholder="จำนวน" min="0" /></div>
        <div class="col-md-2"><button type="button" class="btn btn-primary w-100" id="btn-add-product">เพิ่ม</button></div>
      </div>
      <div id="add-status" class="text-danger small mt-1"></div>
    </div>
    <div class="card p-4">
      <h5 class="mb-3">รายการสินค้า</h5>
      <div class="table-responsive">
        <table class="table table-hover">
          <thead><tr><th>#</th><th>ชื่อ</th><th>ราคา</th><th>จำนวน</th><th>จัดการ</th></tr></thead>
          <tbody id="products-tbody"></tbody>
        </table>
      </div>
    </div>
  </div>
  <div class="modal fade" id="editModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header"><h5 class="modal-title">แก้ไขสินค้า</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
        <div class="modal-body">
          <input type="hidden" id="edit-id" />
          <div class="mb-2"><label class="form-label">ชื่อ</label><input type="text" class="form-control" id="edit-name" /></div>
          <div class="mb-2"><label class="form-label">ราคา</label><input type="number" class="form-control" id="edit-price" step="0.01" min="0" /></div>
          <div class="mb-2"><label class="form-label">จำนวน</label><input type="number" class="form-control" id="edit-stock" min="0" /></div>
        </div>
        <div class="modal-footer"><button type="button" class="btn btn-secondary" data-bs-dismiss="modal">ยกเลิก</button><button type="button" class="btn btn-primary" id="btn-save-edit">บันทึก</button></div>
      </div>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token") || "";
    function authHeader() { return { "Authorization": "Bearer " + token, "Content-Type": "application/json" }; }
    function api(path, opts) { return fetch(path, Object.assign({ headers: authHeader() }, opts)); }
    function showErr(msg) { const el = document.getElementById("admin-error"); el.textContent = msg; el.classList.remove("d-none"); }
    function hideErr() { document.getElementById("admin-error").classList.add("d-none"); }
    async function loadMe() {
      const r = await api("/api/admin/me");
      if (!r.ok) { showErr("กรุณาเข้าสู่ระบบเป็น Admin ก่อน (หรือ token หมดอายุ)"); return false; }
      const u = await r.json(); document.getElementById("admin-name").textContent = "Admin: " + u.username; return true;
    }
    async function loadDashboard() {
      const r = await api("/api/admin/dashboard");
      if (!r.ok) return;
      const d = await r.json();
      document.getElementById("stat-users").textContent = d.total_users || 0;
      document.getElementById("stat-customers").textContent = d.total_customer || 0;
      document.getElementById("stat-products").textContent = d.total_products || 0;
    }
    async function loadProducts() {
      const r = await api("/api/admin/products");
      if (!r.ok) return;
      const list = await r.json();
      const tbody = document.getElementById("products-tbody");
      tbody.innerHTML = list.map(function(p) {
        return "<tr><td>" + p.id + "</td><td>" + p.name + "</td><td>" + p.price + "</td><td>" + p.stock +
          "</td><td><button class=\"btn btn-sm btn-outline-primary me-1\" data-id=\"" + p.id + "\" data-name=\"" + p.name.replace(/"/g, "&quot;") + "\" data-price=\"" + p.price + "\" data-stock=\"" + p.stock + "\">แก้ไข</button>" +
          "<button class=\"btn btn-sm btn-outline-danger\" data-id=\"" + p.id + "\">ลบ</button></td></tr>";
      }).join("");
      tbody.querySelectorAll("button[data-id]").forEach(function(btn) {
        if (btn.textContent === "แก้ไข") {
          btn.addEventListener("click", function() {
            document.getElementById("edit-id").value = btn.dataset.id;
            document.getElementById("edit-name").value = btn.dataset.name;
            document.getElementById("edit-price").value = btn.dataset.price;
            document.getElementById("edit-stock").value = btn.dataset.stock;
            new bootstrap.Modal(document.getElementById("editModal")).show();
          });
        } else {
          btn.addEventListener("click", function() {
            if (!confirm("ยืนยันลบสินค้านี้?")) return;
            deleteProduct(btn.dataset.id);
          });
        }
      });
    }
    async function addProduct() {
      const name = document.getElementById("new-name").value.trim();
      const price = parseFloat(document.getElementById("new-price").value);
      const stock = parseInt(document.getElementById("new-stock").value, 10) || 0;
      document.getElementById("add-status").textContent = "";
      if (!name || isNaN(price) || price < 0) { document.getElementById("add-status").textContent = "กรุณากรอกชื่อและราคาที่ถูกต้อง"; return; }
      const r = await api("/api/admin/products", { method: "POST", body: JSON.stringify({ name: name, price: price, stock: stock }) });
      const data = await r.json();
      if (!r.ok) { document.getElementById("add-status").textContent = data.error || "เพิ่มไม่สำเร็จ"; return; }
      document.getElementById("new-name").value = ""; document.getElementById("new-price").value = ""; document.getElementById("new-stock").value = "";
      loadProducts(); loadDashboard();
    }
    async function saveEdit() {
      const id = document.getElementById("edit-id").value;
      const name = document.getElementById("edit-name").value.trim();
      const price = parseFloat(document.getElementById("edit-price").value);
      const stock = parseInt(document.getElementById("edit-stock").value, 10);
      if (!name || isNaN(price) || price < 0) { alert("กรุณากรอกข้อมูลให้ถูกต้อง"); return; }
      const r = await api("/api/admin/products/" + id, { method: "PUT", body: JSON.stringify({ name: name, price: price, stock: stock }) });
      const data = await r.json();
      if (!r.ok) { alert(data.error || "แก้ไขไม่สำเร็จ"); return; }
      bootstrap.Modal.getInstance(document.getElementById("editModal")).hide();
      loadProducts(); loadDashboard();
    }
    async function deleteProduct(id) {
      const r = await api("/api/admin/products/" + id, { method: "DELETE" });
      if (!r.ok) { const d = await r.json(); alert(d.error || "ลบไม่สำเร็จ"); return; }
      loadProducts(); loadDashboard();
    }
    document.getElementById("btn-add-product").addEventListener("click", addProduct);
    document.getElementById("btn-save-edit").addEventListener("click", saveEdit);
    (async function() {
      if (!token) { showErr("ไม่มี token กรุณาเข้าสู่ระบบแล้วไปที่ลิงก์ Admin"); return; }
      if (!(await loadMe())) return;
      hideErr();
      await loadDashboard();
      await loadProducts();
    })();
  </script>
</body>
</html>
"""


@app.get("/admin-old")
def admin_page_old():
    """หน้า admin เดิม (ยังเก็บไว้)"""
    return render_template_string(ADMIN_PAGE_HTML)


# ========== Dashboard Page (มี tabs: Admin, Customer, Product) ==========

DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Champa - Dashboard</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { font-family: system-ui, sans-serif; background: #f1f5f9; }
    .navbar-brand { font-weight: 700; color: #6366f1; }
    .nav-tabs .nav-link { color: #64748b; }
    .nav-tabs .nav-link.active { color: #6366f1; font-weight: 600; }
    .card { border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); margin-bottom: 20px; }
    .table th { background: #f8fafc; }
    .btn-sm { padding: 0.25rem 0.5rem; }
  </style>
</head>
<body>
  <nav class="navbar navbar-expand-lg navbar-light bg-white border-bottom">
    <div class="container-fluid">
      <a class="navbar-brand" href="/">CHAMPA</a>
      <span class="navbar-text me-3" id="user-info"></span>
      <a class="btn btn-outline-secondary btn-sm" href="/">ออกจากระบบ</a>
    </div>
  </nav>
  <div class="container py-4">
    <div id="error-alert" class="alert alert-danger d-none"></div>
    <ul class="nav nav-tabs mb-4">
      <li class="nav-item"><a class="nav-link active" data-tab="admin">จัดการ Admin</a></li>
      <li class="nav-item"><a class="nav-link" data-tab="customer">จัดการ Customer</a></li>
      <li class="nav-item"><a class="nav-link" data-tab="product">จัดการ Product</a></li>
    </ul>
    <div id="admin-tab" class="tab-content">
      <div id="admin-component"></div>
    </div>
    <div id="customer-tab" class="tab-content d-none">
      <div id="customer-component"></div>
    </div>
    <div id="product-tab" class="tab-content d-none">
      <div id="product-component"></div>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script type="module">
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token") || "";
    if (!token) { window.location.href = "/"; return; }
    function authHeader() { return { "Authorization": "Bearer " + token, "Content-Type": "application/json" }; }
    function api(path, opts) { return fetch(path, Object.assign({ headers: authHeader() }, opts)); }
    function showErr(msg) { const el = document.getElementById("error-alert"); el.textContent = msg; el.classList.remove("d-none"); }
    function hideErr() { document.getElementById("error-alert").classList.add("d-none"); }
    async function loadUser() {
      const r = await api("/api/admin/me");
      if (!r.ok) { window.location.href = "/"; return null; }
      const u = await r.json();
      document.getElementById("user-info").textContent = u.username + " (" + u.role + ")";
      return u;
    }
    // Tab switching
    document.querySelectorAll("[data-tab]").forEach(tab => {
      tab.addEventListener("click", function() {
        document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach(c => c.classList.add("d-none"));
        this.classList.add("active");
        document.getElementById(this.dataset.tab + "-tab").classList.remove("d-none");
        if (this.dataset.tab === "admin") AdminComponent.load();
        else if (this.dataset.tab === "customer") CustomerComponent.load();
        else if (this.dataset.tab === "product") ProductComponent.load();
      });
    });
    // Admin Component
    const AdminComponent = {
      async load() {
        const container = document.getElementById("admin-component");
        container.innerHTML = '<div class="card p-4"><h5>จัดการ Admin</h5><div class="mb-3"><input type="text" class="form-control d-inline-block w-auto me-2" id="new-admin-username" placeholder="Username" /><input type="password" class="form-control d-inline-block w-auto me-2" id="new-admin-password" placeholder="Password" /><button class="btn btn-primary" onclick="AdminComponent.add()">เพิ่ม Admin</button></div><div id="admin-status" class="text-danger small mb-2"></div><table class="table"><thead><tr><th>ID</th><th>Username</th><th>Role</th><th>จัดการ</th></tr></thead><tbody id="admin-tbody"></tbody></table></div>';
        const r = await api("/api/admin/admins");
        if (!r.ok) return;
        const list = await r.json();
        const tbody = document.getElementById("admin-tbody");
        tbody.innerHTML = list.map(u => '<tr><td>' + u.id + '</td><td>' + u.username + '</td><td>' + u.role + '</td><td><button class="btn btn-sm btn-danger" onclick="AdminComponent.delete(' + u.id + ')">ลบ</button></td></tr>').join("");
      },
      async add() {
        const username = document.getElementById("new-admin-username").value.trim();
        const password = document.getElementById("new-admin-password").value;
        document.getElementById("admin-status").textContent = "";
        if (!username || !password) { document.getElementById("admin-status").textContent = "กรุณากรอก username และ password"; return; }
        const r = await api("/api/admin/admins", { method: "POST", body: JSON.stringify({ username, password }) });
        const d = await r.json();
        if (!r.ok) { document.getElementById("admin-status").textContent = d.error || "เพิ่มไม่สำเร็จ"; return; }
        document.getElementById("new-admin-username").value = "";
        document.getElementById("new-admin-password").value = "";
        this.load();
      },
      async delete(id) {
        if (!confirm("ยืนยันลบ Admin นี้?")) return;
        const r = await api("/api/admin/admins/" + id, { method: "DELETE" });
        if (!r.ok) { const d = await r.json(); alert(d.error || "ลบไม่สำเร็จ"); return; }
        this.load();
      }
    };
    // Customer Component
    const CustomerComponent = {
      async load() {
        const container = document.getElementById("customer-component");
        container.innerHTML = '<div class="card p-4"><h5>จัดการ Customer</h5><table class="table"><thead><tr><th>ID</th><th>Username</th><th>Phone</th><th>Role</th><th>จัดการ</th></tr></thead><tbody id="customer-tbody"></tbody></table></div>';
        const r = await api("/api/admin/customers");
        if (!r.ok) return;
        const list = await r.json();
        const tbody = document.getElementById("customer-tbody");
        tbody.innerHTML = list.map(u => '<tr><td>' + u.id + '</td><td>' + u.username + '</td><td>' + (u.phone || '-') + '</td><td>' + u.role + '</td><td><button class="btn btn-sm btn-danger" onclick="CustomerComponent.delete(' + u.id + ')">ลบ</button></td></tr>').join("");
      },
      async delete(id) {
        if (!confirm("ยืนยันลบ Customer นี้?")) return;
        const r = await api("/api/admin/customers/" + id, { method: "DELETE" });
        if (!r.ok) { const d = await r.json(); alert(d.error || "ลบไม่สำเร็จ"); return; }
        this.load();
      }
    };
    // Product Component
    const ProductComponent = {
      async load() {
        const container = document.getElementById("product-component");
        container.innerHTML = '<div class="card p-4"><h5>จัดการ Product</h5><div class="mb-3 row g-2"><div class="col-md-3"><input type="text" class="form-control" id="new-product-name" placeholder="ชื่อสินค้า" /></div><div class="col-md-2"><input type="number" class="form-control" id="new-product-price" placeholder="ราคา" step="0.01" min="0" /></div><div class="col-md-2"><input type="number" class="form-control" id="new-product-stock" placeholder="จำนวน" min="0" /></div><div class="col-md-2"><button class="btn btn-primary" onclick="ProductComponent.add()">เพิ่มสินค้า</button></div></div><div id="product-status" class="text-danger small mb-2"></div><table class="table"><thead><tr><th>ID</th><th>ชื่อ</th><th>ราคา</th><th>จำนวน</th><th>จัดการ</th></tr></thead><tbody id="product-tbody"></tbody></table></div>';
        const r = await api("/api/admin/products");
        if (!r.ok) return;
        const list = await r.json();
        const tbody = document.getElementById("product-tbody");
        tbody.innerHTML = list.map(p => '<tr><td>' + p.id + '</td><td>' + p.name + '</td><td>' + p.price + '</td><td>' + p.stock + '</td><td><button class="btn btn-sm btn-outline-primary me-1" onclick="ProductComponent.edit(' + p.id + ',\'' + p.name.replace(/'/g, "\\'") + '\',' + p.price + ',' + p.stock + ')">แก้ไข</button><button class="btn btn-sm btn-danger" onclick="ProductComponent.delete(' + p.id + ')">ลบ</button></td></tr>').join("");
      },
      async add() {
        const name = document.getElementById("new-product-name").value.trim();
        const price = parseFloat(document.getElementById("new-product-price").value);
        const stock = parseInt(document.getElementById("new-product-stock").value, 10) || 0;
        document.getElementById("product-status").textContent = "";
        if (!name || isNaN(price) || price < 0) { document.getElementById("product-status").textContent = "กรุณากรอกชื่อและราคาที่ถูกต้อง"; return; }
        const r = await api("/api/admin/products", { method: "POST", body: JSON.stringify({ name, price, stock }) });
        const d = await r.json();
        if (!r.ok) { document.getElementById("product-status").textContent = d.error || "เพิ่มไม่สำเร็จ"; return; }
        document.getElementById("new-product-name").value = "";
        document.getElementById("new-product-price").value = "";
        document.getElementById("new-product-stock").value = "";
        this.load();
      },
      async edit(id, name, price, stock) {
        const n = prompt("ชื่อสินค้า:", name);
        const p = prompt("ราคา:", price);
        const s = prompt("จำนวน:", stock);
        if (n === null || p === null || s === null) return;
        const r = await api("/api/admin/products/" + id, { method: "PUT", body: JSON.stringify({ name: n, price: parseFloat(p), stock: parseInt(s, 10) }) });
        const d = await r.json();
        if (!r.ok) { alert(d.error || "แก้ไขไม่สำเร็จ"); return; }
        this.load();
      },
      async delete(id) {
        if (!confirm("ยืนยันลบสินค้านี้?")) return;
        const r = await api("/api/admin/products/" + id, { method: "DELETE" });
        if (!r.ok) { const d = await r.json(); alert(d.error || "ลบไม่สำเร็จ"); return; }
        this.load();
      }
    };
    // Make components global for onclick handlers
    window.AdminComponent = AdminComponent;
    window.CustomerComponent = CustomerComponent;
    window.ProductComponent = ProductComponent;
    // Initialize
    (async function() {
      const user = await loadUser();
      if (!user) return;
      hideErr();
      AdminComponent.load();
    })();
  </script>
</body>
</html>
"""


# ========== ฝั่ง Admin (templates - หลังล็อกอินแอดมิน) ==========
@app.get("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")


@app.get("/admin")
def admin_page_new():
    return render_template("admin.html")


@app.get("/customer")
def customer_page():
    return render_template("customer.html")


@app.get("/product")
def product_page():
    return render_template("product.html")


@app.errorhandler(405)
def method_not_allowed(e):
    """แสดงข้อความที่ชัดเจนเมื่อใช้ HTTP method ผิด"""
    return jsonify({
        "error": "Method Not Allowed",
        "message": "HTTP method ที่ใช้ไม่ถูกต้อง (เช่น ใช้ GET แทน POST หรือใช้ POST แทน GET)",
        "hint": "ตรวจสอบว่าใช้ method ที่ถูกต้อง: POST สำหรับสร้างข้อมูล, GET สำหรับดูข้อมูล, PUT สำหรับแก้ไข, DELETE สำหรับลบ"
    }), 405


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    app.run(host="0.0.0.0", port=port, debug=debug)

