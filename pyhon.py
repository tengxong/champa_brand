from dataclasses import dataclass, field
from typing import Dict, Optional, List
import hashlib
import uuid
import time
import re
import os
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor


# ==========================
#  Models (ข้อมูลหลัก)
# ==========================


@dataclass
class User:
    id: int  # ใช้ตัวเลข (integer)
    username: str
    phone: Optional[str]
    password_hash: str
    role: str  # "admin" หรือ "customer"
    created_at: float = field(default_factory=time.time)


@dataclass
class Product:
    id: int  # ใช้ตัวเลข (integer)
    name: str
    price: float
    stock: Optional[int] = None
    image: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price_type: Optional[str] = None  # ประเภทแพ็กเกจ เช่น '1-10', '11-20', 'custom'
    created_at: float = field(default_factory=time.time)


@dataclass
class ProductReview:
    id: int
    product_id: int
    customer_name: str
    rating: int  # 1-5 stars
    customer_phone: Optional[str] = None
    customer_facebook: Optional[str] = None
    customer_instagram: Optional[str] = None
    comment: Optional[str] = None
    images: Optional[str] = None  # JSON array of image paths
    created_at: float = field(default_factory=time.time)


# ==========================
#  Database Config (PostgreSQL: champa)
# ==========================

# อ่านจาก environment (สำหรับ deploy) หรือใช้ค่าตั้งต้น
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "12345")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DATABASE_URL = os.environ.get("DATABASE_URL")  # Render/Railway ใช้ตัวนี้


def get_connection():
    """คืนค่า connection ไปยังฐานข้อมูล champa"""
    if DATABASE_URL:
        # บาง host ใช้ postgres:// ต้องเปลี่ยนเป็น postgresql:// สำหรับ psycopg2
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = "postgresql://" + url[9:]
        return psycopg2.connect(url)
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )


def init_db() -> None:
    """สร้างตารางพื้นฐาน (users, products) ถ้ายังไม่มี"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    profile_image TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            # ถ้าตารางมีอยู่แล้ว แต่อาจยังไม่มีคอลัมน์ phone และ profile_image
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT;")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image TEXT;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    price NUMERIC(12, 2) NOT NULL,
                    stock INTEGER,
                    image TEXT,
                    description TEXT,
                    category TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS image TEXT;")
            cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS description TEXT;")
            cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS category TEXT;")
            cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS price_type TEXT;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS product_reviews (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                    customer_name TEXT NOT NULL,
                    customer_phone TEXT,
                    customer_facebook TEXT,
                    customer_instagram TEXT,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    comment TEXT,
                    images TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )


# ==========================
#  Session (ยังเก็บในหน่วยความจำ)
# ==========================

SESSIONS: Dict[str, int] = {}  # token -> user_id (int)


# ==========================
#  Helper Functions
# ==========================


def _hash_password(password: str) -> str:
    """แฮชรหัสผ่านอย่างง่าย (ห้ามใช้แบบนี้ใน production จริง ๆ ควรใช้ bcrypt / argon2 ฯลฯ)"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def normalize_lao_phone(phone: Optional[str]) -> Optional[str]:
    """
    Normalize เบอร์ลาว (เฉพาะมือถือ 020) ให้เป็นรูปแบบ +85620XXXXXXXX
    รับได้หลายแบบ เช่น:
    - 020xxxxxxxx
    - 20xxxxxxxx
    - 85620xxxxxxxx
    - +85620xxxxxxxx
    """
    if not phone:
        return None

    p = phone.strip()
    if not p:
        return None

    # ตัดช่องว่าง/ขีด/วงเล็บ
    p = re.sub(r"[^\d+]", "", p)

    # ให้เหลือ + หรือ ตัวเลข
    if p.startswith("+"):
        p_digits = "+" + re.sub(r"\D", "", p[1:])
    else:
        p_digits = re.sub(r"\D", "", p)

    # แปลง prefix เป็น +856...
    if p_digits.startswith("+856"):
        e164 = p_digits
    elif p_digits.startswith("856"):
        e164 = "+856" + p_digits[3:]
    elif p_digits.startswith("0"):
        # เช่น 020xxxxxxx หรือ 021xxxxxx
        e164 = "+856" + p_digits[1:]
    else:
        # เช่น 20xxxxxxx หรือ 21xxxxxx
        e164 = "+856" + p_digits

    # รับเฉพาะมือถือ prefix 20 และความยาวโดยทั่วไปคือ 020 + 8 หลัก (รวมเป็น 10 หลักหลัง 0)
    # แต่เผื่อบางเบอร์มี 7-9 หลักหลัง 20 (จึงยอมรับ 7-9)
    if not re.fullmatch(r"\+85620\d{7,9}", e164):
        raise ValueError("รับเฉพาะเบอร์ลาวมือถือขึ้นต้น 020 (ตัวอย่าง: 020xxxxxxxx หรือ +85620xxxxxxxx)")

    return e164

def _generate_token() -> str:
    return str(uuid.uuid4())


def _row_to_user(row) -> User:
    return User(
        id=int(row["id"]),
        username=row["username"],
        phone=row.get("phone"),
        password_hash=row["password_hash"],
        role=row["role"],
        created_at=float(row["created_at"]),
    )


def _row_to_product(row) -> Product:
    stock_val = row.get("stock")
    return Product(
        id=int(row["id"]),
        name=row["name"],
        price=float(row["price"]),
        stock=int(stock_val) if stock_val is not None else None,
        image=row.get("image"),
        description=row.get("description"),
        category=row.get("category"),
        price_type=row.get("price_type"),
        created_at=float(row["created_at"]),
    )


def _get_user_by_username(username: str) -> Optional[User]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id,
                    username,
                    phone,
                    password_hash,
                    role,
                    EXTRACT(EPOCH FROM created_at) AS created_at
                FROM users
                WHERE username = %s
                """,
                (username,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return _row_to_user(row)


def _get_user_by_id(user_id: int) -> Optional[User]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id,
                    username,
                    phone,
                    password_hash,
                    role,
                    EXTRACT(EPOCH FROM created_at) AS created_at
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return _row_to_user(row)


def _get_user_by_phone(phone_normalized: str) -> Optional[User]:
    """ดึง user จากเบอร์มือถือ (ต้องเป็นรูปแบบ +85620... ที่ normalize แล้ว)"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id,
                    username,
                    phone,
                    password_hash,
                    role,
                    EXTRACT(EPOCH FROM created_at) AS created_at
                FROM users
                WHERE phone = %s
                """,
                (phone_normalized,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return _row_to_user(row)


def _require_admin(user: User):
    if user.role != "admin":
        raise PermissionError("ต้องเป็น admin เท่านั้น")


# ==========================
#  Auth: Login / Register
# ==========================


def register(username: str, password: str, role: str = "customer", phone: Optional[str] = None) -> User:
    """
    สมัครสมาชิกใหม่
    - username ต้องไม่ซ้ำ
    - role: "admin" หรือ "customer"
    """
    if _get_user_by_username(username):
        raise ValueError("username นี้ถูกใช้งานแล้ว")

    if role not in ("admin", "customer"):
        raise ValueError("role ไม่ถูกต้อง (ต้องเป็น 'admin' หรือ 'customer')")

    password_hash = _hash_password(password)
    created_at = time.time()
    phone_clean = normalize_lao_phone(phone)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (username, phone, password_hash, role, created_at)
                VALUES (%s, %s, %s, %s, TO_TIMESTAMP(%s))
                RETURNING id
                """,
                (username, phone_clean, password_hash, role, created_at),
            )
            user_id = cur.fetchone()[0]

    return User(
        id=user_id,
        username=username,
        phone=phone_clean,
        password_hash=password_hash,
        role=role,
        created_at=created_at,
    )


def login(login_id: str, password: str) -> str:
    """
    ล็อกอิน ด้วย username หรือ เบอร์มือถือที่สมัครไว้
    - login_id: username หรือ เบอร์ลาว (020xxxxxxxx / +85620xxxxxxxx)
    - ถ้าสำเร็จ: คืนค่า token (session token)
    """
    login_stripped = (login_id or "").strip()
    if not login_stripped:
        raise ValueError("กรุณากรอก username หรือ เบอร์มือถือ")

    user = _get_user_by_username(login_stripped)
    if not user:
        try:
            phone_norm = normalize_lao_phone(login_stripped)
            if phone_norm:
                user = _get_user_by_phone(phone_norm)
        except ValueError:
            pass
    if not user:
        raise ValueError("username/เบอร์มือถือ หรือ password ไม่ถูกต้อง")

    if user.password_hash != _hash_password(password):
        raise ValueError("username/เบอร์มือถือ หรือ password ไม่ถูกต้อง")

    token = _generate_token()
    SESSIONS[token] = user.id
    return token


def get_current_user(token: str) -> User:
    """ดึงข้อมูล user จาก token"""
    user_id = SESSIONS.get(token)
    if not user_id:
        raise PermissionError("token ไม่ถูกต้อง หรือหมดอายุ")
    user = _get_user_by_id(user_id)
    if not user:
        raise PermissionError("ไม่พบผู้ใช้สำหรับ token นี้")
    return user


# ==========================
#  Dashboard Management
# ==========================


def get_dashboard_overview(current_user: User) -> Dict:
    """
    ข้อมูลภาพรวมสำหรับ dashboard
    - จำนวนผู้ใช้ทั้งหมด
    - จำนวน admin
    - จำนวน customer
    - จำนวนสินค้า
    - Revenue (คำนวณจากราคารวมของสินค้าทั้งหมด)
    - Orders (ประมาณการจากจำนวนสินค้า x 10)
    - Revenue by month (6 เดือนล่าสุด)
    - Orders by week (7 วันล่าสุด)
    """
    _require_admin(current_user)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            total_users = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            total_admin = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM users WHERE role = 'customer'")
            total_customer = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM products")
            total_products = cur.fetchone()[0]

            # คำนวณ Revenue จากราคารวมของสินค้าทั้งหมด (ราคา x stock)
            cur.execute("SELECT COALESCE(SUM(price * stock), 0) FROM products")
            total_revenue = float(cur.fetchone()[0] or 0)

            # คำนวณ Orders (ประมาณการจากจำนวนสินค้า x 10 หรือจำนวน customer x 5)
            total_orders = max(total_products * 10, total_customer * 5)

            # Revenue by month (6 เดือนล่าสุด) - ใช้ข้อมูลจาก products ที่สร้างในแต่ละเดือน
            cur.execute("""
                SELECT 
                    DATE_TRUNC('month', created_at) as month,
                    COALESCE(SUM(price * stock), 0) as revenue
                FROM products
                WHERE created_at >= NOW() - INTERVAL '6 months'
                GROUP BY DATE_TRUNC('month', created_at)
                ORDER BY month
            """)
            revenue_by_month = cur.fetchall()
            
            # สร้าง array สำหรับ 6 เดือนล่าสุด
            revenue_data = [0.0] * 6
            month_labels = []
            for i in range(6):
                month_date = datetime.now() - timedelta(days=30 * (5 - i))
                month_labels.append(month_date.strftime('%b'))
            
            # Map ข้อมูลจาก database
            for row in revenue_by_month:
                month_date = row[0]
                revenue = float(row[1] or 0)
                # หา index ของเดือนใน array
                for i, label in enumerate(month_labels):
                    check_date = datetime.now() - timedelta(days=30 * (5 - i))
                    if month_date.month == check_date.month and month_date.year == check_date.year:
                        revenue_data[i] = revenue
                        break

            # Orders by week (7 วันล่าสุด) - ใช้ข้อมูลจาก users ที่สร้างในแต่ละวัน
            cur.execute("""
                SELECT 
                    DATE_TRUNC('day', created_at) as day,
                    COUNT(*) * 2 as orders
                FROM users
                WHERE role = 'customer' AND created_at >= NOW() - INTERVAL '7 days'
                GROUP BY DATE_TRUNC('day', created_at)
                ORDER BY day
            """)
            orders_by_day = cur.fetchall()
            
            # สร้าง array สำหรับ 7 วันล่าสุด (วันนี้คือวันสุดท้าย)
            orders_data = [0] * 7
            day_labels = []
            today = datetime.now()
            # สร้าง labels สำหรับ 7 วันล่าสุด (เริ่มจาก 6 วันก่อน ถึงวันนี้)
            for i in range(6, -1, -1):
                check_date = today - timedelta(days=i)
                day_labels.append(check_date.strftime('%a'))
            
            # Map ข้อมูลจาก database
            for row in orders_by_day:
                day_date = row[0]
                orders = int(row[1] or 0)
                # หาวันนี้อยู่ที่ index ไหน (6 = วันนี้, 0 = 6 วันก่อน)
                days_ago = (today.date() - day_date.date()).days
                if 0 <= days_ago <= 6:
                    orders_data[6 - days_ago] = orders

            # Recent Activity - ดึงข้อมูล user ล่าสุดที่สร้าง account หรือ product ล่าสุดที่เพิ่ม
            cur.execute("""
                SELECT username, role, created_at
                FROM users
                WHERE created_at >= NOW() - INTERVAL '7 days'
                ORDER BY created_at DESC
                LIMIT 5
            """)
            recent_users = cur.fetchall()
            
            cur.execute("""
                SELECT name, created_at
                FROM products
                WHERE created_at >= NOW() - INTERVAL '7 days'
                ORDER BY created_at DESC
                LIMIT 5
            """)
            recent_products = cur.fetchall()
            
            # รวมและเรียงตามเวลา
            recent_activities = []
            for row in recent_users:
                created_at = row[2]
                if hasattr(created_at, 'isoformat'):
                    created_at_str = created_at.isoformat()
                else:
                    created_at_str = str(created_at)
                recent_activities.append({
                    'name': row[0],
                    'action': 'Created an account' if row[1] == 'customer' else 'Admin joined',
                    'created_at': created_at_str,
                    'type': 'user'
                })
            for row in recent_products:
                created_at = row[1]
                if hasattr(created_at, 'isoformat'):
                    created_at_str = created_at.isoformat()
                else:
                    created_at_str = str(created_at)
                recent_activities.append({
                    'name': row[0],
                    'action': 'Product added',
                    'created_at': created_at_str,
                    'type': 'product'
                })
            
            # เรียงตามเวลาและเลือก 3 รายการล่าสุด
            recent_activities.sort(key=lambda x: x['created_at'], reverse=True)
            recent_activities = recent_activities[:3]

    return {
        "total_users": total_users,
        "total_admin": total_admin,
        "total_customer": total_customer,
        "total_products": total_products,
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "revenue_by_month": revenue_data,
        "revenue_month_labels": month_labels,
        "orders_by_week": orders_data,
        "orders_day_labels": day_labels,
        "recent_activities": recent_activities,
    }


# ==========================
#  Admin Management (จัดการ admin)
# ==========================


def count_admins() -> int:
    """จำนวน admin ในระบบ (ไม่ต้องล็อกอิน) ใช้สำหรับ setup แอดมินคนแรก"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            return cur.fetchone()[0]


def create_admin(current_user: User, username: str, password: str) -> User:
    """สร้าง admin ใหม่ (ต้องเป็น admin เท่านั้นที่สร้างได้)"""
    _require_admin(current_user)
    return register(username=username, password=password, role="admin")


def list_admins(current_user: User) -> List[User]:
    """รายการ admin ทั้งหมด"""
    _require_admin(current_user)

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id,
                    username,
                    phone,
                    password_hash,
                    role,
                    EXTRACT(EPOCH FROM created_at) AS created_at
                FROM users
                WHERE role = 'admin'
                ORDER BY created_at DESC
                """
            )
            rows = cur.fetchall()
            return [_row_to_user(r) for r in rows]


def delete_admin(current_user: User, admin_id: str) -> None:
    """ลบ admin (ห้ามลบตัวเอง)"""
    _require_admin(current_user)
    aid = int(admin_id) if isinstance(admin_id, str) and admin_id.isdigit() else admin_id
    if current_user.id == aid:
        raise ValueError("ไม่สามารถลบ admin ที่กำลังใช้งานอยู่ได้")

    with get_connection() as conn:
        with conn.cursor() as cur:
            # ตรวจสอบว่าเป็น admin จริง
            cur.execute(
                "SELECT role FROM users WHERE id = %s",
                (admin_id,),
            )
            row = cur.fetchone()
            if not row or row[0] != "admin":
                raise ValueError("ไม่พบ admin ที่ต้องการลบ")

            cur.execute("DELETE FROM users WHERE id = %s", (admin_id,))


# ==========================
#  Customer Management (จัดการ customer)
# ==========================


def list_customers(current_user: User) -> List[User]:
    """รายการ customer ทั้งหมด (เฉพาะ admin)"""
    _require_admin(current_user)

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id,
                    username,
                    phone,
                    password_hash,
                    role,
                    EXTRACT(EPOCH FROM created_at) AS created_at
                FROM users
                WHERE role = 'customer'
                ORDER BY created_at DESC
                """
            )
            rows = cur.fetchall()
            return [_row_to_user(r) for r in rows]


def update_customer_role_to_admin(current_user: User, customer_id: str) -> User:
    """อัปเกรด customer ให้เป็น admin"""
    _require_admin(current_user)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT role FROM users WHERE id = %s",
                (customer_id,),
            )
            row = cur.fetchone()
            if not row or row[0] != "customer":
                raise ValueError("ไม่พบ customer ที่ต้องการอัปเกรด")

            cur.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (customer_id,),
            )

    # ดึงข้อมูล user หลังอัปเดต
    user = _get_user_by_id(customer_id)
    if not user:
        raise ValueError("เกิดข้อผิดพลาดหลังอัปเดต role")
    return user


def delete_customer(current_user: User, customer_id: str) -> None:
    """ลบ customer"""
    _require_admin(current_user)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT role FROM users WHERE id = %s",
                (customer_id,),
            )
            row = cur.fetchone()
            if not row or row[0] != "customer":
                raise ValueError("ไม่พบ customer ที่ต้องการลบ")

            cur.execute("DELETE FROM users WHERE id = %s", (customer_id,))


# ==========================
#  Product Management (จัดการ product)
# ==========================


def create_product(
    current_user: User,
    name: str,
    price: float,
    stock: Optional[int] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    price_type: Optional[str] = None,
) -> Product:
    """สร้างสินค้าใหม่ (เฉพาะ admin)"""
    _require_admin(current_user)
    if price < 0:
        raise ValueError("price ต้องมากกว่าหรือเท่ากับ 0")
    if stock is not None and stock < 0:
        raise ValueError("stock ต้องมากกว่าหรือเท่ากับ 0")

    created_at = time.time()
    desc = (description or "").strip() or None

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO products (name, price, stock, image, description, category, price_type, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, TO_TIMESTAMP(%s))
                RETURNING id
                """,
                (name, price, stock if stock is not None else None, None, desc, category, price_type, created_at),
            )
            product_id = cur.fetchone()[0]

    return Product(
        id=product_id,
        name=name,
        price=price,
        stock=stock,
        image=None,
        description=desc,
        category=category,
        price_type=price_type,
        created_at=created_at,
    )


def list_products(current_user: User) -> List[Product]:
    """รายการสินค้าทั้งหมด (admin หรือ customer ก็เรียกดูได้)"""
    # ถ้าต้องการเฉพาะคนที่ล็อกอิน ให้เช็กสิทธิ์ที่ layer ด้านนอก
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id,
                    name,
                    price,
                    stock,
                    image,
                    description,
                    category,
                    price_type,
                    EXTRACT(EPOCH FROM created_at) AS created_at
                FROM products
                ORDER BY created_at DESC
                """
            )
            rows = cur.fetchall()
            return [_row_to_product(r) for r in rows]


def get_product(current_user: User, product_id: str) -> Product:
    """ดูรายละเอียดสินค้า"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id,
                    name,
                    price,
                    stock,
                    image,
                    description,
                    category,
                    price_type,
                    EXTRACT(EPOCH FROM created_at) AS created_at
                FROM products
                WHERE id = %s
                """,
                (product_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("ไม่พบสินค้า")
            return _row_to_product(row)


def update_product(
    current_user: User,
    product_id: str,
    name: Optional[str] = None,
    price: Optional[float] = None,
    stock: Optional[int] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    price_type: Optional[str] = None,
) -> Product:
    """แก้ไขข้อมูลสินค้า (เฉพาะ admin)"""
    _require_admin(current_user)

    fields = []
    values = []

    if name is not None:
        fields.append("name = %s")
        values.append(name)

    if description is not None:
        fields.append("description = %s")
        values.append((description or "").strip() or None)

    if price is not None:
        if price < 0:
            raise ValueError("price ต้องมากกว่าหรือเท่ากับ 0")
        fields.append("price = %s")
        values.append(price)

    if stock is not None:
        if stock < 0:
            raise ValueError("stock ต้องมากกว่าหรือเท่ากับ 0")
        fields.append("stock = %s")
        values.append(stock)
    elif stock is None and "stock" in [f.split()[0] for f in fields]:
        # ถ้าต้องการ set stock เป็น NULL
        fields.append("stock = NULL")

    if category is not None:
        fields.append("category = %s")
        values.append(category)

    if price_type is not None:
        fields.append("price_type = %s")
        values.append(price_type)

    if not fields:
        # ไม่มีอะไรเปลี่ยน แค่คืนค่าปัจจุบัน
        return get_product(current_user, product_id)

    values.append(product_id)
    set_clause = ", ".join(fields)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE products SET {set_clause} WHERE id = %s",
                tuple(values),
            )

    return get_product(current_user, product_id)


def delete_product(current_user: User, product_id: str) -> None:
    """ลบสินค้า (เฉพาะ admin)"""
    _require_admin(current_user)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM products WHERE id = %s",
                (product_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("ไม่พบสินค้าที่ต้องการลบ")

            cur.execute("DELETE FROM products WHERE id = %s", (product_id,))


# ==========================
#  Product Review Functions
# ==========================


def _row_to_review(row) -> ProductReview:
    import json
    images = None
    if row.get("images"):
        try:
            images = json.loads(row["images"]) if isinstance(row["images"], str) else row["images"]
        except:
            images = None
    return ProductReview(
        id=int(row["id"]),
        product_id=int(row["product_id"]),
        customer_name=row["customer_name"],
        customer_phone=row.get("customer_phone"),
        customer_facebook=row.get("customer_facebook"),
        customer_instagram=row.get("customer_instagram"),
        rating=int(row["rating"]),
        comment=row.get("comment"),
        images=images,
        created_at=float(row["created_at"]),
    )


def list_reviews(current_user: User, product_id: Optional[int] = None) -> List[ProductReview]:
    """รายการรีวิวสินค้า (admin หรือ customer ก็เรียกดูได้)"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if product_id:
                cur.execute(
                    """
                    SELECT
                        id,
                        product_id,
                        customer_name,
                        customer_phone,
                        customer_facebook,
                        customer_instagram,
                        rating,
                        comment,
                        images,
                        EXTRACT(EPOCH FROM created_at) AS created_at
                    FROM product_reviews
                    WHERE product_id = %s
                    ORDER BY created_at DESC
                    """,
                    (product_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT
                        id,
                        product_id,
                        customer_name,
                        customer_phone,
                        customer_facebook,
                        customer_instagram,
                        rating,
                        comment,
                        images,
                        EXTRACT(EPOCH FROM created_at) AS created_at
                    FROM product_reviews
                    ORDER BY created_at DESC
                    """
                )
            rows = cur.fetchall()
            return [_row_to_review(r) for r in rows]


def create_review(
    current_user: User,
    product_id: int,
    customer_name: str,
    rating: int,
    customer_phone: Optional[str] = None,
    customer_facebook: Optional[str] = None,
    customer_instagram: Optional[str] = None,
    comment: Optional[str] = None,
    images: Optional[List[str]] = None,
) -> ProductReview:
    """สร้างรีวิวสินค้าใหม่ (admin เท่านั้น)"""
    _require_admin(current_user)
    if rating < 1 or rating > 5:
        raise ValueError("rating ต้องอยู่ระหว่าง 1-5")
    
    # ตรวจสอบว่า product_id มีอยู่จริง
    product = get_product(current_user, str(product_id))
    if not product:
        raise ValueError("ไม่พบสินค้า")
    
    import json
    images_json = json.dumps(images) if images else None
    
    created_at = time.time()
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO product_reviews (product_id, customer_name, customer_phone, customer_facebook, customer_instagram, rating, comment, images, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TO_TIMESTAMP(%s))
                RETURNING id
                """,
                (product_id, customer_name, customer_phone, customer_facebook, customer_instagram, rating, comment, images_json, created_at),
            )
            review_id = cur.fetchone()[0]
    
    return ProductReview(
        id=review_id,
        product_id=product_id,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_facebook=customer_facebook,
        customer_instagram=customer_instagram,
        rating=rating,
        comment=comment,
        images=images,
        created_at=created_at,
    )


def create_review_by_customer(
    product_id: int,
    customer_name: str,
    rating: int,
    customer_phone: Optional[str] = None,
    customer_facebook: Optional[str] = None,
    customer_instagram: Optional[str] = None,
    comment: Optional[str] = None,
    images: Optional[List[str]] = None,
) -> ProductReview:
    """ลูกค้าส่งรีวิวและคะแนนดาว ม system บันทึกแล้ว admin ดูได้"""
    if rating < 1 or rating > 5:
        raise ValueError("rating ต้องอยู่ระหว่าง 1-5")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM products WHERE id = %s", (product_id,))
            if not cur.fetchone():
                raise ValueError("ไม่พบสินค้า")
    import json
    images_json = json.dumps(images) if images else None
    created_at = time.time()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO product_reviews (product_id, customer_name, customer_phone, customer_facebook, customer_instagram, rating, comment, images, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TO_TIMESTAMP(%s))
                RETURNING id
                """,
                (product_id, customer_name.strip(), customer_phone, customer_facebook, customer_instagram, rating, comment, images_json, created_at),
            )
            review_id = cur.fetchone()[0]
    return ProductReview(
        id=review_id,
        product_id=product_id,
        customer_name=customer_name.strip(),
        customer_phone=customer_phone,
        customer_facebook=customer_facebook,
        customer_instagram=customer_instagram,
        rating=rating,
        comment=comment,
        images=images,
        created_at=created_at,
    )


def get_review(current_user: User, review_id: str) -> ProductReview:
    """ดูรายละเอียดรีวิว"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id,
                    product_id,
                    customer_name,
                    customer_phone,
                    customer_facebook,
                    customer_instagram,
                    rating,
                    comment,
                    images,
                    EXTRACT(EPOCH FROM created_at) AS created_at
                FROM product_reviews
                WHERE id = %s
                """,
                (review_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("ไม่พบรีวิว")
            return _row_to_review(row)


def update_review(
    current_user: User,
    review_id: str,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    customer_facebook: Optional[str] = None,
    customer_instagram: Optional[str] = None,
    rating: Optional[int] = None,
    comment: Optional[str] = None,
    images: Optional[List[str]] = None,
) -> ProductReview:
    """แก้ไขข้อมูลรีวิว (เฉพาะ admin)"""
    _require_admin(current_user)
    
    fields = []
    values = []
    
    if customer_name is not None:
        fields.append("customer_name = %s")
        values.append(customer_name)
    
    if customer_phone is not None:
        fields.append("customer_phone = %s")
        values.append(customer_phone)
    
    if customer_facebook is not None:
        fields.append("customer_facebook = %s")
        values.append(customer_facebook)
    
    if customer_instagram is not None:
        fields.append("customer_instagram = %s")
        values.append(customer_instagram)
    
    if rating is not None:
        if rating < 1 or rating > 5:
            raise ValueError("rating ต้องอยู่ระหว่าง 1-5")
        fields.append("rating = %s")
        values.append(rating)
    
    if comment is not None:
        fields.append("comment = %s")
        values.append((comment or "").strip() or None)
    
    if images is not None:
        import json
        images_json = json.dumps(images) if images else None
        fields.append("images = %s")
        values.append(images_json)
    
    if not fields:
        return get_review(current_user, review_id)
    
    values.append(review_id)
    set_clause = ", ".join(fields)
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE product_reviews SET {set_clause} WHERE id = %s",
                values,
            )
    
    return get_review(current_user, review_id)


def update_review_rating_by_customer(review_id: str, customer_name: str, rating: int) -> ProductReview:
    """ลูกค้าแก้ไขเฉพาะคะแนนดาวของตัวเองได้ ถ้าชื่อตรงกับรีวิวนั้น"""
    if rating < 1 or rating > 5:
        raise ValueError("rating ต้องอยู่ระหว่าง 1-5")
    review = get_review(User(id=0, username="guest", phone=None, password_hash="", role="customer"), review_id)
    name_given = (customer_name or "").strip()
    name_in_db = (review.customer_name or "").strip()
    if name_given.lower() != name_in_db.lower():
        raise ValueError("ຊື່ບໍ່ຕົງກັນ ບໍ່ສາມາດແກ້ໄຂຄະແນນໄດ້")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE product_reviews SET rating = %s WHERE id = %s", (rating, review_id))
    return get_review(User(id=0, username="guest", phone=None, password_hash="", role="customer"), review_id)


def delete_review(current_user: User, review_id: str) -> None:
    """ลบรีวิว (เฉพาะ admin)"""
    _require_admin(current_user)
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM product_reviews WHERE id = %s", (review_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError("ไม่พบรีวิวที่ต้องการลบ")
            
            cur.execute("DELETE FROM product_reviews WHERE id = %s", (review_id,))

