# คำแนะนำการอัปโหลดโปรเจกต์ขึ้น GitHub

## ขั้นตอนที่ 1: ติดตั้ง Git (ถ้ายังไม่มี)

1. ดาวน์โหลด Git จาก: https://git-scm.com/download/win
2. ติดตั้งตามขั้นตอน
3. เปิด PowerShell หรือ Command Prompt

## ขั้นตอนที่ 2: ตั้งค่า Git (ครั้งแรกเท่านั้น)

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## ขั้นตอนที่ 3: สร้าง Repository บน GitHub

1. ไปที่ https://github.com
2. คลิก **"New"** หรือ **"+"** → **"New repository"**
3. ตั้งชื่อ repository เช่น `champa-brand-website`
4. เลือก **Public** หรือ **Private**
5. **อย่า** check "Initialize with README" (เพราะเรามีไฟล์อยู่แล้ว)
6. คลิก **"Create repository"**

## ขั้นตอนที่ 4: Initialize Git และ Push

เปิด PowerShell ในโฟลเดอร์โปรเจกต์ (`d:\teng\website champa`) แล้วรันคำสั่ง:

```bash
# 1. Initialize git repository
git init

# 2. เพิ่มไฟล์ทั้งหมด
git add .

# 3. Commit ครั้งแรก
git commit -m "Initial commit: CHAMPA BRAND website"

# 4. เพิ่ม remote repository (แทน YOUR_USERNAME และ YOUR_REPO_NAME ด้วยค่าจริง)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 5. Push ขึ้น GitHub
git branch -M main
git push -u origin main
```

## ตัวอย่างคำสั่ง (แก้ไขตาม repository ของคุณ)

```bash
cd "d:\teng\website champa"
git init
git add .
git commit -m "Initial commit: CHAMPA BRAND website"
git remote add origin https://github.com/yourusername/champa-brand-website.git
git branch -M main
git push -u origin main
```

## ถ้าเจอปัญหา Authentication

ถ้า GitHub ต้องการ Personal Access Token:

1. ไปที่ GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. คลิก "Generate new token"
3. เลือก scope: `repo` (full control)
4. Copy token ที่ได้
5. เมื่อ push ให้ใช้ token แทน password

## คำสั่งสำหรับอัปเดตในอนาคต

```bash
git add .
git commit -m "Update: คำอธิบายการเปลี่ยนแปลง"
git push
```

## หมายเหตุ

- ไฟล์ `.gitignore` จะป้องกันไม่ให้ไฟล์ที่ไม่จำเป็น (เช่น `__pycache__`, `.db`) ถูกอัปโหลด
- อย่าลืมแก้ไข connection string ใน `pyhon.py` ก่อน push (หรือใช้ environment variables)
