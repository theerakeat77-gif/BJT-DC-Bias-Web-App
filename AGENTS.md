# AGENTS.md — กติกาสำหรับ AI agent ในโปรเจกต์นี้

## ขอบเขต

โปรเจกต์นี้เป็นงาน Lab 02 ของ ENG29 2121: Flask web app คำนวณ DC bias
ของ BJT Common-Emitter แบบ Voltage-Divider Bias เท่านั้น
**ห้ามเพิ่ม** AC, transient, Bode plot, SPICE solver, bias type อื่น หรือ FET
ในรอบนี้

## กติกาที่ห้ามละเมิด

1. **`dc_bias.py` ห้าม import Flask** และห้ามรู้จัก HTTP/HTML — เป็นชั้นวิศวกรรมล้วน
   รับ/คืน dataclass (`BiasInput` → `BiasResult`)
2. **ห้ามใส่สมการหรือค่าคำนวณใน `templates/`** — template ทำหน้าที่แสดงผลเท่านั้น
   ตัวเลขทุกตัวต้องมาจาก Python
3. **ต้องมี failing test ก่อนแก้ logic** (TDD) — แก้ `dc_bias.py` หรือ validation
   ต้องมี test ที่ fail ก่อน แล้วจึงเขียนโค้ดให้ผ่าน
4. **ห้าม commit** `.venv/`, `__pycache__/`, `*.pyc`, `.env` หรือ credentials
5. **UI เป็นภาษาไทย** (ศัพท์เทคนิคคงภาษาอังกฤษ) และ **ห้ามเพิ่ม JavaScript**
   ในรอบนี้ — ใช้ server-rendered form + POST
6. **ห้ามเพิ่ม dependency** นอกจาก Flask โดยไม่จำเป็น และต้อง pin เวอร์ชันใน
   `requirements.txt` ด้วย `pip freeze`
7. **ห้าม clamp** ค่านอก Active Region — ต้องรายงานค่าดิบตามสมการ + warning
   ตามการตัดสินใจของผู้ใช้ (Approach A)
8. **Validation ต้องไม่ทำให้หน้า 500** — กรอกผิดทุกกรณีต้องได้ HTTP 200
   พร้อม error message

## คำสั่งที่ใช้บ่อย

```powershell
# ติดตั้ง
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# test
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

# รันเว็บ
.\.venv\Scripts\python.exe -m flask --app app run
```

## นิยามของ "เสร็จ"

- test ทั้งหมดผ่าน (`OK`, 0 failures, 0 errors)
- เปิด `http://127.0.0.1:5000/` แล้วกรอกค่าตัวอย่างได้ผลตรงตารางใน `README.md`
- กรณี `R1 = 0` ได้ error, `R2 = 1k` ได้ CUTOFF + warning, `RC = 10k` ได้
  SATURATION + warning
- ไม่มีไฟล์ต้องห้ามถูก track ใน git
