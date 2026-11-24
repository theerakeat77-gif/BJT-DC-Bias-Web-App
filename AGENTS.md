# AGENTS.md — กติกาสำหรับ AI agent ในโปรเจกต์นี้

## ขอบเขต (ปรับสำหรับ Lab 04)

โปรเจกต์นี้คือ Flask Web App ของ ENG29 2121 ที่เริ่มจาก Lab 03 (DC Bias
สามโหมด) และต่อยอดเป็น **Lab 04 · BJT Amplifier Simulator v1**: เพิ่มการรัน
จริงด้วย ngspice สำหรับวงจร CE Voltage Divider อ้างอิงหนึ่งวงจร
(`.op`, `.ac`, `.tran`) โดย **ห้ามลบหรือทำให้ DC Bias เดิมทั้งสามโหมดเสีย**

กติกา Lab 02 เดิมที่ห้าม AC/transient/SPICE ถูกแทนที่ด้วยขอบเขต Lab 04 นี้
ส่วนข้อควรระวังด้าน separation of concerns, TDD และความปลอดภัยยังคงใช้

## กติกาที่ห้ามละเมิด

1. **`dc_bias.py` ห้าม import Flask** และห้ามรู้จัก HTTP/HTML — เป็นชั้นวิศวกรรมล้วน
   รับ/คืน dataclass (`BiasInput` → `BiasResult`) และยังเป็น Analytical Reference
   ของ Lab 04 เท่านั้น (ไม่ใช่แหล่งค่าผล SPICE)
2. **`spice_engine.py` ห้าม import Flask** — เป็น adapter เดียวที่สร้าง netlist,
   เรียก ngspice ด้วย `subprocess.run([list], timeout=..., cwd=...)`,
   **ห้ามใช้ `shell=True`**, และอ่านผลจาก log/raw ที่ solver เขียนจริง
3. **ห้ามใส่สมการหรือค่าคำนวณใน `templates/`** — template แสดงผลเท่านั้น
   ตัวเลข/กราฟ SVG ต้องมาจาก Python; SVG ใช้ server-rendered ไม่เพิ่ม JavaScript
4. **ต้องมี failing test ก่อนแก้ logic** (TDD) — รวมถึง adapter, parser และ route ใหม่
5. **ห้าม commit** `.venv/`, `__pycache__/`, `*.pyc`, `.env`, credentials,
   ไฟล์ run ชั่วคราว (`*.raw`, `run.log`) — เก็บเฉพาะ screenshot ตัวอย่างใน
   `docs/captures/` ที่สร้างจาก browser จริง
6. **UI เป็นภาษาไทย** (ศัพท์เทคนิคคงภาษาอังกฤษ); ฟอร์มต้องแสดงหน่วย,
   แยกป้าย SPICE กับ Analytical, แสดง engine status/model/version
7. **ห้าม clamp** ค่านอก Active Region ใน `dc_bias.py` — ต้องรายงานค่าดิบตามสมการ
   พร้อม warning; ผล SPICE ต้องไม่ถูกแก้เพื่อให้ตรง Analytical
8. **Validation ต้องไม่ทำให้หน้า 500** — กรอกผิดทุกกรณีต้องได้ HTTP 200
   พร้อม error message และ **ต้องไม่แสดงผลเก่าหรือสถานะ Success**
9. **ห้าม fabricate** Gain, fL, fH, waveform หรือ status; ถ้า sweep ไม่มีจุดตัด
   −3 dB ให้เขียน `not determined in sweep range`; solver ไม่พบ/run fail/timeout/
   output ว่างต้องเป็น Error เสมอ
10. ใช้ BJT model จาก Starter Kit ของผู้สอนถ้ามี; ถ้าไม่มี ให้ระบุชื่อ/ที่มา
    ของ model card ที่ใช้จริงใน netlist, README และ validation (ตอนนี้ใช้
    `t2n2222` จาก ngspice 47 example)
11. **UI ต้องมี Dropdown เดียวเท่านั้น**: `<select name="mode">` ตัวเดียวเลือกได้
    ทั้ง `divider/fixed/emitter` (Lab 03) และ `ce-dc/ce-ac/ce-tran` (Lab 04)
    ห้ามเพิ่มฟอร์มที่สอง radio `analysis` หรือ select อีกตัว; `/calculate` และ
    `/simulate` เป็นเพียง compat route สำหรับ test/handout เดิม ไม่ใช่ UI หลัก

## คำสั่งที่ใช้บ่อย

```powershell
# ติดตั้ง
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# test (ตั้ง path ngspice ก่อนถ้าไม่ได้อยู่ใน PATH)
$env:NGSPICE_EXECUTABLE = 'C:\path\to\ngspice_con.exe'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

# รันเว็บ
.\.venv\Scripts\python.exe -m flask --app app run --port 5000
```

## นิยามของ "เสร็จ"

- test ทั้งหมดผ่าน (`OK`, 0 failures, 0 errors) รวม test ของ SPICE adapter
- เปิด `http://127.0.0.1:5000/` แล้วเห็น `<select>` เพียงตัวเดียว; เลือกแต่ละโหมดแล้ว
  DC Bias ทั้งสามโหมดได้ผลตรง `README.md`
- เลือก `ce-dc/ce-ac/ce-tran` จาก dropdown เดียวแล้วเห็น status Success, engine version,
  ชื่อ model, หน่วย, กราฟที่อ่านได้ และ netlist/log ที่ใช้รันจริง
- กรณี `RE = 0` หรือ engine ไม่พร้อมได้ Error ไม่มีผล Success ปลอม
- `docs/validation.md` บันทึก B1–B8 ตามผลที่เกิดจริง (PASS/FAIL/NOT RUN)
- ไม่มีไฟล์ต้องห้ามถูก track ใน git
