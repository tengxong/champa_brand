# วิธี Deploy CHAMPA BRAND ขึ้น Server

โปรเจกต์พร้อม deploy บน **Render** หรือ **Railway** (มี free tier)

---

## ตัวเลือก 1: Render.com (แนะนำ)

> **สำคัญ:** โปรเจกต์นี้เป็น **Flask (Backend + หน้าเว็บ)** ต้องสร้างเป็น **Web Service** เท่านั้น  
> **อย่าเลือก Static Site** — ถ้าเห็นช่อง "Publish Directory" (Required) แปลว่าคุณอยู่ที่ Static Site ให้ยกเลิกแล้วไปสร้าง **New + → Web Service** แทน

### 1. สร้างบัญชีและเชื่อม GitHub
- ไปที่ https://render.com → Sign up (ใช้ GitHub)
- เชื่อม repo: **tengxong/champa_brand**

### 2. สร้าง PostgreSQL
- Dashboard → **New +** → **PostgreSQL**
- ตั้งชื่อ เช่น `champa-db`
- Region เลือกใกล้คุณ → **Create Database**
- หลังสร้างเสร็จ ให้ copy **Internal Database URL** (หรือ External ถ้า deploy ที่อื่น)

### 3. Deploy Web Service (ไม่ใช่ Static Site)
- **New +** → เลือก **Web Service** (ไม่ใช่ Static Site)
- เลือก repo **champa_brand**
- ตั้งค่า:
  - **Name**: `champa-brand`
  - **Runtime**: Python 3
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `gunicorn app:app`
  - **Instance Type**: Free

### 4. Environment Variables
ใน Web Service → **Environment** → Add:

| Key | Value |
|-----|--------|
| `DATABASE_URL` | วาง Internal Database URL จากขั้นตอนที่ 2 |
| `PYTHON_VERSION` | `3.11` |

(ถ้าใช้ External Database URL ให้ใช้ตัวนั้นแทน)

### 5. Deploy
- กด **Create Web Service**
- Render จะ build และ deploy ให้
- เมื่อเสร็จจะได้ URL เช่น `https://champa-brand.onrender.com`

### 6. สร้าง Admin คนแรก
หลัง deploy เสร็จ เรียก API สร้าง admin:

```bash
curl -X POST https://YOUR-APP-URL.onrender.com/api/setup/first-admin \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"admin\", \"password\": \"รหัสผ่านที่ต้องการ\", \"phone\": \"020xxxxxxxx\"}"
```

หรือใช้ Postman / Apidog ส่ง POST ไปที่ `/api/setup/first-admin` พร้อม body ด้านบน

### 7. เปิดใช้งานฐานข้อมูล (init tables)
ถ้ายังไม่มีตาราง ให้เรียกให้ Flask สร้างตาราง (รันคำสั่งบนเครื่องคุณที่เชื่อม DB เดียวกัน หรือเพิ่ม endpoint ชั่วคราว):

- วิธีง่าย: สร้างไฟล์ `init_db.py` ในโปรเจกต์ มีเนื้อหา:
```python
from pyhon import init_db
init_db()
print("DB initialized.")
```
- จากนั้นบน Render ไปที่ **Shell** (ถ้ามี) รัน `python init_db.py`
- หรือรัน local โดยตั้ง `DATABASE_URL` เป็น External URL ของ Render แล้วรัน `python init_db.py`

---

## ตัวเลือก 2: Railway

### 1. สร้างโปรเจกต์
- ไปที่ https://railway.app → Login with GitHub
- **New Project** → **Deploy from GitHub repo** → เลือก **champa_brand**

### 2. เพิ่ม PostgreSQL
- ในโปรเจกต์ กด **+ New** → **Database** → **PostgreSQL**
- Railway จะสร้างและตั้งค่า `DATABASE_URL` ให้อัตโนมัติ

### 3. ตั้งค่า Service
- คลิกที่ Web Service → **Settings**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Root Directory**: ว่างไว้

### 4. Variables
- Railway ใส่ `DATABASE_URL` ให้แล้วจาก PostgreSQL
- ไม่ต้องใส่อะไรเพิ่ม ถ้าใช้ default

### 5. Deploy
- กด **Deploy** (หรือ push code ขึ้น GitHub จะ deploy อัตโนมัติ)
- ได้ URL จาก **Settings** → **Generate Domain**

---

## สิ่งที่โปรเจกต์รองรับแล้ว

- อ่าน **PORT** จาก environment (Render/Railway ส่งให้อัตโนมัติ)
- อ่าน **DATABASE_URL** จาก environment (ไม่ต้องตั้ง DB_HOST, DB_NAME แยก)
- ใช้ **gunicorn** เป็น production server
- รันที่ **host 0.0.0.0** ให้บริการจากภายนอกได้

---

## หมายเหตุ

- **Free tier** อาจ sleep หลังไม่มีการใช้งาน ถ้าเป็น Render
- ไฟล์อัปโหลด (รูปสินค้า/รีวิว) บน free tier อาจหายเมื่อ restart ใช้ persistent disk ถ้ามี
- ควรเปลี่ยนรหัสผ่าน admin หลังสร้างครั้งแรก
