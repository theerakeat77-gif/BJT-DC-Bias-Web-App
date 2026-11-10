# Design — BJT Common-Emitter DC Bias Web App (ENG29 2121 · Lab 02)

วันที่: 2026-11-10
สถานะ: **อนุมัติแล้ว** (2026-11-10) — ผ่าน builder check + ผู้ใช้อนุมัติ

## 1. Intent และเหตุผล

สร้าง **Flask Web Application หลายไฟล์** สำหรับคำนวณ DC Operating Point ของวงจร
BJT NPN Common-Emitter แบบ **Voltage-Divider Bias** โดยให้ Python Backend เป็นผู้คำนวณจริง
ไม่ใช่ค่าที่เขียนค้างไว้ใน HTML

เหตุผล: เป็นงาน Lab 02 ของรายวิชา ENG29 2121 (2/2569) นักศึกษาต้องส่ง Repository URL +
Commit SHA ผ่าน Moodle ภายในคาบ 3 ชั่วโมง และต้องผ่านเกณฑ์ตรวจรับ A1–A7 (rubric 10 คะแนน)
ชิ้นงานนี้ยังเป็นฐานของ W3–W11 ที่จะเพิ่ม Bias Type อื่น, ngspice, AC, Transient และ Interactive Schematic

ผู้ใช้: นักศึกษาเจ้าของเครื่อง (คนเดียว) เปิดผ่าน `http://127.0.0.1:5000/` บนเครื่องตนเอง
ผู้อ่านผล: ตัวนักศึกษาเองและอาจารย์ผู้ตรวจ

## 2. Goals

- G1 เปิดเว็บผ่าน localhost ได้ และเห็น Input Form (HTTP 200)
- G2 กรอก `VCC, R1, R2, RC, RE, β, VBE` แล้วได้ `VB, VE, VC, VCE, IC` (+ `IB, IE`) พร้อมหน่วย
- G3 ผลตรงกับ independent engineering calculation ภายใต้แบบจำลอง Forward-Active เดียวกัน
- G4 Validation ที่อ่านรู้เรื่อง ไม่ทำให้หน้าเว็บล้ม
- G5 Warning เมื่ออยู่นอก Active Region
- G6 Automated tests: ≥3 engineering tests + ≥1 Flask test client test
- G7 Commit/Push ขึ้น GitHub ผ่าน GitHub Desktop พร้อม README ที่ reproduce ได้

## 3. Non-goals (คาบนี้ไม่ทำ)

- AC small-signal, Gain, Bode Plot
- Transient, Signal Generator, Amplitude/Frequency control
- Interactive schematic / Overlay animation
- SPICE / ngspice solver
- Bias Type อื่น (Fixed, Emitter) — W3
- FET
- ระบบ login / ฐานข้อมูล / deploy สาธารณะ
- Dark mode, หลายภาษา, animation ตกแต่ง

## 4. Anti-goals (ทำงานได้แต่ถือว่าล้มเหลว)

- ตัวเลข DC Bias ถูก hardcode ใน HTML หรือ JavaScript
- เปิดด้วย `file://` แล้วได้ผล (แปลว่าไม่มี Backend จริง)
- Test ผ่านเพราะ assert ค่าที่ตัวเองใส่กลับไป (tautology) หรือไม่เคยรันจริง
- แสดงผลนอก Active Region โดยไม่มี warning และอ้างว่าแม่นยำ
- Commit `.venv/`, `__pycache__/`, `.env` หรือ credentials
- หน้าจอพัง (traceback 500) เมื่อผู้ใช้กรอกค่าผิด

## 5. Constraints

- Python 3.15.2 (ติดตั้งอยู่), Flask, ไลบรารีมาตรฐาน `unittest`
- Windows 11, PowerShell, เปิดเว็บที่ `127.0.0.1:5000`
- เวลาทำงานจริง ~75 นาทีสำหรับ build + 25 นาทีตรวจ
- Commit ผ่าน **GitHub Desktop** (GUI) ไม่ใช้ git CLI เป็นหลัก
- โฟลเดอร์โปรเจกต์: `C:\Users\b6806200\Documents\GitHub\BJT DC Bias Web App`
  (มี `.git` แล้ว, branch `main`, ยังไม่มี remote → ต้อง Publish repository)

## 6. Approaches ที่พิจารณา

### 6.1 สถาปัตยกรรมเว็บ

| ทาง | ลักษณะ | ข้อดี | ข้อเสีย |
|---|---|---|---|
| **A. Server-rendered Jinja + POST** ✅ | ฟอร์ม POST ไป `/calculate` แล้ว Flask render HTML กลับมาทั้งหน้า | ง่ายที่สุด, ตรงกับ A2, ไม่ต้องเขียน JS, test ผ่าน Flask test client ตรง ๆ | หน้าจอกะพริบตอน submit |
| B. JSON API + fetch | Flask คืน JSON, JS อัปเดต DOM | รู้สึกลื่นกว่า, ต่อยอด AC plot ได้ | ต้องเขียน JS + จัดการ error 2 ชั้น, เสี่ยงพังเงียบ |
| C. SPA (React ฯลฯ) | Frontend แยก build | ยืดหยุ่นสูงสุด | เกินขอบเขตคาบนี้มาก |

**เลือก A** — เหตุผล: rubric ให้คะแนนที่ "Backend คำนวณจริง" ไม่ได้ให้คะแนนความลื่นของ UI
และ B/C เพิ่มจุดล้มเหลวที่ตรวจสอบยากภายในเวลาที่มี

### 6.2 พฤติกรรมเมื่ออยู่นอก Forward-Active

| ทาง | ลักษณะ | ข้อดี | ข้อเสีย |
|---|---|---|---|
| **A. ค่าดิบ + Warning** ✅ | คำนวณตามสมการตรง ๆ แล้วติด warning | โปร่งใส, ตรงกับ handout ที่ห้ามอ้างว่า approximation ใช้ได้, test ง่าย | ตัวเลขอาจดู "แปลก" เช่น VCE ติดลบ |
| B. Clamp ที่ VCE(sat) | บังคับ VCE = 0.2 V แล้วคำนวณ IC(sat) ใหม่ | ใกล้ความจริงทางไฟฟ้า | ผิดสมมติฐาน forward-active, ต้องเพิ่มสมการและ test, เกิน W2 |
| C. แสดงทั้งสอง | โชว์ค่าดิบ + ค่า clamp | ครบที่สุด | งานเพิ่มเกือบเท่าตัว, ผู้ใช้สับสนว่าค่าไหนคือคำตอบ |

**เลือก A** (ผู้ใช้เป็นผู้เลือก)

### 6.3 การรับค่าความต้านทานและหน่วย

| ทาง | ลักษณะ | ข้อดี | ข้อเสีย |
|---|---|---|---|
| **A. ตัวเลข + suffix** ✅ | รับ `100000`, `100k`, `2.2k`, `1M` แล้วแปลงเป็น Ω | ตรงกับข้อกำหนด "แปลง kΩ เป็น Ω", demo ได้จริง, test ได้ | ต้องเขียน parser + test เพิ่ม |
| B. Dropdown หน่วยต่อช่อง | ช่องตัวเลข + เลือก Ω/kΩ | ชัดเจน ไม่กำกวม | ฟอร์มยาวขึ้น 4 dropdown, กดมากขึ้น |
| C. กรอกเป็น Ω ล้วน | hint อย่างเดียว | โค้ดน้อยสุด | ไม่ตอบข้อกำหนดเรื่องการแปลงหน่วย |

**เลือก A** — parser อยู่ในชั้น app (ไม่ใช่ `dc_bias.py`) และแสดงค่าที่แปลงแล้วกลับให้ผู้ใช้เห็น

## 7. การตัดสินใจที่確定แล้ว (พร้อมเหตุผล)

1. **โครงไฟล์** แยก `app.py` (HTTP) / `dc_bias.py` (วิศวกรรมล้วน) / `templates/` / `static/` / `tests/`
   — ตามโครงใน handout, ทำให้ `dc_bias.py` test ได้โดยไม่ต้องมี Flask
2. **`dc_bias.py` ห้าม import Flask** และห้ามรู้จัก HTML — รับ/คืน dataclass
3. **หน้าเดียว** `templates/index.html` มีทั้งฟอร์มและผลลัพธ์ (แสดงผลเมื่อมีข้อมูล)
4. **ค่าเริ่มต้นในฟอร์ม** = ค่าตัวอย่างใน handout (VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.70)
5. **เส้นทาง**: `GET /` แสดงฟอร์ม, `POST /calculate` คำนวณและ render ผล (ใช้ template เดียวกัน)
6. **Region logic** (ค่าคงที่ใน `dc_bias.py`):
   - `VTH <= VBE` → **CUTOFF**: ไม่มีกระแสไหล → `IB = IC = IE = 0`,
     `VE = IE * RE = 0`, `VC = VCC - IC * RC = VCC`, `VB = VTH` (divider ไม่มีโหลด),
     `VCE = VC - VE = VCC` + warning
   - `VCE < 0.3 V` → **SATURATION (near)**: รายงานค่าดิบ + warning ว่า approximation ใช้ไม่ได้
   - อื่น ๆ → **ACTIVE**
7. **Validation** (ฝั่ง app ก่อนเรียก `dc_bias`): ต้องมีครบ 7 ค่า, เป็นตัวเลขได้, `VCC > 0`,
   `R1, R2, RC, RE > 0`, `β > 0`, `0 <= VBE < VCC`; ผิดข้อใดให้แสดง error รวมทุกข้อในหน้าเดียว
   **ห้าม raise จนหน้า 500**
8. **หน่วยที่แสดง**: แรงดันเป็น V (ทศนิยม 3 ตำแหน่ง), `IC` และ `IE` เป็น mA (3 ตำแหน่ง),
   `IB` เป็น **µA** (3 ตำแหน่ง) — ถ้าอัดเป็น mA จะเหลือ `0.012 mA` เพียง 2 นัยสำคัญ
   และแสดง Ω ที่ตีความได้ข้างช่องกรอก
9. **ภาษา UI**: ไทย (ศัพท์เทคนิคคงเป็นอังกฤษ) — ผู้ตรวจเป็นคนไทย
10. **Tests**: `unittest` (ไม่เพิ่ม dependency), `tests/test_dc_bias.py` + `tests/test_web.py`
11. **Dependencies**: `Flask` เท่านั้น (+ `requirements.txt` แบบ pin เวอร์ชัน)
12. **Git**: `.gitignore` ต้องมี `.venv/`, `__pycache__/`, `*.pyc`, `.env`, `.pytest_cache/`
13. **เอกสาร**: `README.md` (วิธีติดตั้ง/รัน/test), `AGENTS.md`, `docs/design-note.md`,
    `docs/validation.md`, `docs/reflection.md`
14. **Repo visibility**: **Public** — publish ผ่าน GitHub Desktop, อาจารย์เปิด URL ได้โดยไม่ต้องเพิ่มสิทธิ์
15. **`docs/reflection.md`**: ผมเขียนเป็น **โครง + คำถามนำ** (เกิดอะไรขึ้น / ติดอะไร / แก้อย่างไร /
    ได้เรียนอะไร) แล้วนักศึกษาเติมคำตอบเอง — ไม่ร่างเนื้อหาแทน เพราะเป็นงานสะท้อนความคิดส่วนบุคคล

## 8. สมการอ้างอิง (Forward-Active, β และ VBE คงที่)

```
VTH = VCC * R2 / (R1 + R2)
RTH = R1 * R2 / (R1 + R2)
IB  = (VTH - VBE) / (RTH + (beta + 1) * RE)
IC  = beta * IB
IE  = (beta + 1) * IB
VE  = IE * RE
VB  = VE + VBE
VC  = VCC - IC * RC
VCE = VC - VE
```

### Independent reference (ค่าตัวอย่างใน handout)

VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V

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

ค่าชุดนี้คำนวณด้วยมือ/สคริปต์แยก **ไม่ใช่** ค่าที่อ่านจากภาพใน handout
(ภาพใน handout ระบุชัดว่าเป็นค่าประกอบภาพ) — ใช้เป็น oracle ของ test

## 9. Mapping กับเกณฑ์ตรวจรับ

| เกณฑ์ | องค์ประกอบที่รองรับ |
|---|---|
| A1 GET / | `app.py: index()` + `templates/index.html` |
| A2 POST /calculate | `app.py: calculate()` เรียก `dc_bias.calculate_dc_bias()` |
| A3 Engineering reference | `tests/test_dc_bias.py` เทียบค่าตารางข้อ 8 |
| A4 Validation | `validate_inputs()` + error block ใน template |
| A5 Outside Active Region | `region` + `warnings` จาก `dc_bias.py` |
| A6 Tests | ≥5 engineering tests + ≥3 Flask tests |
| A7 GitHub | `.gitignore`, `README.md`, commit ผ่าน GitHub Desktop |

## 10. สิ่งที่เหลือให้ผู้สร้างตัดสินใจเอง (ไม่ต้องถามกลับ)

- ชื่อฟังก์ชัน/ตัวแปรภายใน, การจัดกลุ่ม CSS, การเลือกฟอนต์
- จำนวนทศนิยมของค่ากลาง (VTH, RTH) ที่แสดง
- จะแสดงตารางสมการในหน้าเว็บหรือไม่
- โครงสร้าง HTML ภายใน (semantic tags, fieldset)
- จะมี `docs/` เพิ่มเติมนอกจากที่ระบุหรือไม่

## 11. ความเสี่ยง

| ความเสี่ยง | การรับมือ |
|---|---|
| Python 3.15 ใหม่มาก, wheel บางตัวยังไม่มี | ใช้ Flask เท่านั้น (pure Python) — dry-run ผ่านแล้ว |
| PATH ของ process ที่รัน OpenCode ยังเก่า | เติม PATH ในคำสั่ง หรือ restart OpenCode |
| เวลาไม่พอถ้า UI ซับซ้อน | UI เป็น server-rendered หน้าเดียว, ไม่มี JS |
| สับสนค่าดิบ vs ค่าจริงตอน Saturation | Warning ต้องเด่นและอธิบายว่าตัวเลขคือ "ค่าตามสมการ ไม่ใช่ค่าจริง" |
