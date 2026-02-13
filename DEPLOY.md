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
  - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
  - **Instance Type**: Free

### 4. Environment Variables
ใน Web Service → **Environment** → Add:

| Key | Value |
|-----|--------|
| `DATABASE_URL` | วาง Internal Database URL จากขั้นตอนที่ 2 |
| `PYTHON_VERSION` | `3.11` หรือ `3.12` (สำคัญ: อย่าใช้ 3.14 เพราะ psycopg2-binary ยังไม่รองรับ) |

**หมายเหตุ:** ไฟล์ `runtime.txt` ในโปรเจกต์กำหนด Python 3.11 แล้ว แต่ถ้า Render ยังใช้ 3.14 ให้ตั้ง `PYTHON_VERSION` ใน Environment Variables ด้วย

(ถ้าใช้ External Database URL ให้ใช้ตัวนั้นแทน)

### 5. Deploy
- กด **Create Web Service**
- Render จะ build และ deploy ให้
- เมื่อเสร็จจะได้ URL เช่น `https://champa-brand.onrender.com`

---

## วิธี Deploy ใหม่ (Redeploy)

### วิธีที่ 1: Auto Deploy (เมื่อแก้โค้ด)
1. แก้ไขโค้ดในโปรเจกต์
2. Commit และ Push ขึ้น GitHub:
   ```bash
   git add .
   git commit -m "Update: คำอธิบายการเปลี่ยนแปลง"
   git push origin main
   ```
3. Render จะ detect การเปลี่ยนแปลงและ **auto-deploy** ให้อัตโนมัติ
4. ดู progress ที่ **Logs** tab

### วิธีที่ 2: Manual Deploy (เมื่อแก้ Environment Variables หรือต้องการ deploy ใหม่ทันที)
1. ไปที่ Web Service บน Render Dashboard
2. คลิกที่ **Manual Deploy** (มุมขวาบน)
3. เลือก **Deploy latest commit**
4. Render จะ build และ deploy ใหม่

### วิธีที่ 3: Deploy Commit เฉพาะ
1. ไปที่ Web Service → **Manual Deploy**
2. เลือก **Deploy specific commit**
3. เลือก commit ที่ต้องการ
4. กด Deploy

### วิธีที่ 4: Clear Build Cache และ Deploy ใหม่
ถ้า build มีปัญหา:
1. ไปที่ Web Service → **Settings**
2. เลื่อนลงไปหา **Clear build cache**
3. กด **Clear build cache**
4. จากนั้น **Manual Deploy** → **Deploy latest commit**

---

## ตรวจสอบสถานะ Deploy

- **Logs tab**: ดู build logs และ runtime logs
- **Events tab**: ดู history ของ deployments
- **Metrics tab**: ดู CPU, Memory, Request count

### 5.1 Troubleshooting: ถ้า gunicorn crash (Exited with status 1)

**ตรวจสอบ Logs:**
- ไปที่ Web Service → **Logs** tab
- ดู error message ที่แท้จริง

**ปัญหาที่พบบ่อย:**

1. **DATABASE_URL ไม่ได้ตั้งค่า**
   - Error: `could not connect to server` หรือ `init_db failed`
   - แก้: ไปที่ **Environment** → เพิ่ม `DATABASE_URL` = Internal Database URL จาก PostgreSQL

2. **Python version ไม่รองรับ (Python 3.14)**
   - Error: `undefined symbol: _PyInterpreterState_Get` จาก psycopg2-binary
   - สาเหตุ: Python 3.14 ยังใหม่เกินไป psycopg2-binary 2.9.9 ยังไม่รองรับ
   - แก้: เพิ่ม Environment Variable `PYTHON_VERSION` = `3.11` หรือ `3.12` (สำคัญมาก!)

3. **gunicorn ไม่พบ app**
   - Error: `Failed to find application object 'app'`
   - แก้: ตรวจสอบว่า Start Command = `gunicorn app:app` (ไม่ใช่ `python app.py`)

4. **Import error จาก pyhon.py**
   - Error: `ModuleNotFoundError` หรือ `ImportError`
   - แก้: ตรวจสอบว่า `requirements.txt` มี dependencies ครบ และ build สำเร็จ

**ทดสอบ local ก่อน deploy:**
```bash
# ติดตั้ง dependencies
pip install -r requirements.txt

# ทดสอบว่า app import ได้
python test_app.py

# ทดสอบรันด้วย gunicorn
gunicorn app:app --bind 0.0.0.0:5000
```

**ถ้ายังไม่ได้ ให้ตรวจสอบ:**

1. **ดู Logs บน Render:**
   - ไปที่ Web Service → **Logs** tab
   - Copy error message ทั้งหมดมา
   - มักจะบอกว่า import error ที่ไหน หรือ connection error

2. **ตรวจสอบ Environment Variables:**
   - ไปที่ **Environment** tab
   - ต้องมี `DATABASE_URL` (ถ้ายังไม่มี PostgreSQL ให้สร้างก่อน)
   - อาจเพิ่ม `PYTHON_VERSION` = `3.11`

3. **ตรวจสอบ Start Command:**
   - ต้องเป็น: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - ไม่ใช่: `python app.py` หรือ `flask run`

4. **ถ้า error เกี่ยวกับ DATABASE_URL:**
   - ไปสร้าง PostgreSQL ก่อน (ขั้นตอนที่ 2)
   - Copy **Internal Database URL**
   - ใส่ใน Environment Variables → `DATABASE_URL`
   - Deploy ใหม่

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
