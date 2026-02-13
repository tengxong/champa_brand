# เพิ่ม Admin ผ่าน ApiDog

Base URL: `http://127.0.0.1:5000` (รัน `python app.py` ก่อน)

---

## วิธีที่ 1: สร้างแอดมิน (ไม่จำกัด - ไม่ต้องส่ง token)

**ใช้ได้ตลอด ไม่จำกัดจำนวนครั้ง** - ไม่ต้องส่ง token

| ค่า | ใส่ |
|-----|-----|
| **Method** | `POST` |
| **URL** | `http://127.0.0.1:5000/api/setup/first-admin` |
| **Headers** | `Content-Type: application/json` |
| **Body** (raw JSON) | `{"username": "admin", "password": "รหัสผ่าน", "phone": "020xxxxxxxx" (optional)}` |

ตัวอย่าง Body:
```json
{
  "username": "admin",
  "password": "123456",
  "phone": "02029149695"
}
```

**หมายเหตุ:** `phone` เป็น optional (ไม่บังคับ) แต่ถ้าส่งต้องเป็นเบอร์ลาวขึ้นต้น 020

ถ้าสำเร็จ: ได้ `201` และ `{"id": 1, "username": "admin", "role": "admin"}`  
**หมายเหตุ:** ถ้า username ซ้ำจะได้ error `"username นี้ถูกใช้งานแล้ว"`

---

## วิธีที่ 2: สร้างแอดมินเพิ่ม (เมื่อมี Admin อยู่แล้ว)

ต้องล็อกอินเป็น Admin ก่อนเพื่อเอา **token** มาใช้

### ขั้นที่ 1 – ล็อกอินเอา token

| ค่า | ใส่ |
|-----|-----|
| **Method** | `POST` |
| **URL** | `http://127.0.0.1:5000/api/login` |
| **Headers** | `Content-Type: application/json` |
| **Body** (raw JSON) | `{"username": "admin", "password": "รหัสผ่านของ admin"}` |

ตัวอย่าง Body:
```json
{
  "username": "admin",
  "password": "123456"
}
```

ตอบกลับจะมี `"token": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"` ให้ copy ไว้

### ขั้นที่ 2 – สร้างแอดมินใหม่

| ค่า | ใส่ |
|-----|-----|
| **Method** | `POST` |
| **URL** | `http://127.0.0.1:5000/api/admin/admins` |
| **Headers** | `Content-Type: application/json`<br>`Authorization: Bearer <token ที่ได้จากขั้นที่ 1>` |
| **Body** (raw JSON) | `{"username": "admin2", "password": "รหัสผ่าน", "phone": "020xxxxxxxx" (optional)}` |

ตัวอย่าง Headers ใน ApiDog:
- Key: `Content-Type` → Value: `application/json`
- Key: `Authorization` → Value: `Bearer 30e78651-c703-43ed-b563-45ba31b2002e` (ใส่ token จริง)

ตัวอย่าง Body:
```json
{
  "username": "admin2",
  "password": "abcdef",
  "phone": "02012345678"
}
```

**หมายเหตุ:** `phone` เป็น optional (ไม่บังคับ) แต่ถ้าส่งต้องเป็นเบอร์ลาวขึ้นต้น 020

ถ้าสำเร็จ: ได้ `201` และ `{"id": 2, "username": "admin2", "role": "admin"}`
