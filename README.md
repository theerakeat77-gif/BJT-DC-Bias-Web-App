# BJT DC Bias Web App — ENG29 2121 Lab 02

Flask web application สำหรับคำนวณ **DC Operating Point** ของวงจร
BJT NPN Common-Emitter แบบ **Voltage-Divider Bias**
ผู้ใช้กรอก `VCC, R1, R2, RC, RE, β, VBE` แล้ว Python Backend จะคำนวณ
`VB, VE, VC, VCE, IC, IE, IB` พร้อมหน่วยและแจ้งเตือนเมื่อวงจรอยู่นอก Forward-Active Region

> ต้องเปิดผ่าน Flask server ที่ `http://127.0.0.1:5000/` — เปิดไฟล์ `templates/index.html`
> ตรง ๆ ด้วย `file://` จะไม่ได้ผลลัพธ์ เพราะไม่มีการคำนวณฝั่ง Python

## สิ่งที่ต้องมี

- Python 3.15+ (พัฒนาด้วย 3.15.2)
- Windows / PowerShell (คำสั่งด้านล่างเป็น PowerShell)

## ติดตั้ง

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## รันเว็บ

```powershell
.\.venv\Scripts\python.exe -m flask --app app run
```

เปิดเบราว์เซอร์ที่ <http://127.0.0.1:5000/>

## รัน test

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## โครงสร้างโปรเจกต์

```
app.py                  Flask routes + parsing/validation ของฟอร์ม
dc_bias.py              สมการ DC bias ล้วน ๆ (ไม่ import Flask)
templates/index.html    หน้าเดียว: ฟอร์ม + ผลลัพธ์
static/style.css        Layout และสี
tests/test_dc_bias.py   Engineering tests
tests/test_web.py       Parser/validation + Flask test client
docs/                   Design note, validation record, reflection skeleton
```

## สมการที่ใช้ (Forward-Active, β และ VBE คงที่)

| ปริมาณ | สมการ |
|---|---|
| VTH | `VCC * R2 / (R1 + R2)` |
| RTH | `R1 * R2 / (R1 + R2)` |
| IB | `(VTH - VBE) / (RTH + (β + 1) * RE)` |
| IC | `β * IB` |
| IE | `(β + 1) * IB` |
| VE | `IE * RE` |
| VB | `VE + VBE` |
| VC | `VCC - IC * RC` |
| VCE | `VC - VE` |

## ค่าตัวอย่างและผลอ้างอิง

`VCC = 12 V, R1 = 100 kΩ, R2 = 22 kΩ, RC = 2.2 kΩ, RE = 1 kΩ, β = 100, VBE = 0.70 V`

| ปริมาณ | ค่า |
|---|---|
| VTH | 2.163934 V |
| RTH | 18 032.787 Ω |
| IB | 12.2986 µA |
| IC | 1.22986 mA |
| IE | 1.24216 mA |
| VE | 1.24216 V |
| VB | 1.94216 V |
| VC | 9.29431 V |
| VCE | 8.05215 V |
| Region | ACTIVE |

ค่าชุดนี้คำนวณแยกจากสมการโดยตรง (ไม่ใช่ค่าที่อ่านจากภาพใน handout)
และถูกใช้เป็น oracle ของ automated tests

## สมมติฐานและข้อจำกัด

- ใช้แบบจำลอง Forward-Active: `VBE` คงที่ตามที่กรอก และ `β` คงที่
- **ไม่ใช่ SPICE solver** — ไม่มี AC, transient, Bode plot หรือ parasitic
- ถ้า `VTH <= VBE` → **CUTOFF**: รายงาน `IB = IC = IE = 0`, `VE = 0`, `VB = VTH`,
  `VC = VCE = VCC` พร้อม warning
- ถ้า `VCE < 0.3 V` → **SATURATION (near)**: รายงานค่าดิบตามสมการพร้อม warning
  ว่า approximation ใช้ไม่ได้ — **ไม่ clamp** ค่า
- ค่าความต้านทานรับได้ทั้ง `100000`, `100k`, `100K`, `2.2k`, `1M`
  (mega ใช้ `M` ตัวใหญ่เท่านั้น)
- Validation ฝั่ง app ตรวจครบ 7 ช่อง, ค่าต้องเป็นตัวเลข, `VCC/R1/R2/RC/RE/β > 0`,
  `0 <= VBE < VCC` — กรอกผิดจะแสดง error โดยไม่ทำให้หน้าเว็บล้ม
