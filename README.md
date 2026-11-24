# BJT Amplifier Simulator v1 — ENG29 2121 Lab 04

Repository: <https://github.com/theerakeat77-gif/BJT-DC-Bias-Web-App.git>
(ใส่ **Lab 4 commit SHA** ในใบส่งหลัง commit/push แล้ว)

ต่อยอดจาก Lab 03 (BJT DC Bias Web App) ให้เป็นโปรแกรมจำลอง Common-Emitter
amplifier ที่รัน **ngspice จริง** สำหรับวงจร Voltage Divider อ้างอิงหนึ่งวงจร:

- **หน้าเดียว Dropdown เดียว**: เลือก `divider / fixed / emitter / ce-dc / ce-ac / ce-tran` จาก `<select name="mode">` เพียงตัวเดียว แล้วกด **Calculate / Run**
- Lab 03 ใช้ `dc_bias.py` แบบ Analytical; Lab 04 ใช้ `spice_engine.py` รัน ngspice จริง (`.op`, `.ac`, `.tran`)
- `/calculate` และ `/simulate` ยังเก็บไว้เป็น route ย้อนหลังสำหรับ test/handout เดิม
- ผล SPICE แยกจากผล Analytical อย่างชัดเจน พร้อม engine version, ชื่อ model, หน่วย, netlist และ log ที่ใช้รันจริง

> เปิดผ่าน Flask server ที่ <http://127.0.0.1:5000/> — เปิด `templates/index.html` ตรง ๆ จะไม่ได้ผลลัพธ์

## สิ่งที่ต้องมี

- Python 3.14+ (พัฒนาและทดสอบด้วย 3.14.2)
- Flask (pin ไว้ใน `requirements.txt`)
- **ngspice 47** (โปรแกรมภายนอก ไม่ใช่แพ็กเกจ pip) — ทดสอบกับ ngspice-47 build 2026-08-11
- Windows / PowerShell (คำสั่งด้านล่างเป็น PowerShell)

### ติดตั้ง ngspice แบบ portable (ไม่แก้ PATH ทั้งระบบ)

```powershell
$zip = "$env:TEMP\ngspice-47_64.7z"
$dest = "$env:LOCALAPPDATA\ngspice-47"
curl.exe -L --fail -o $zip `
  'https://downloads.sourceforge.net/project/ngspice/ng-spice-rework/47/ngspice-47_64.7z'
& 'C:\Program Files\7-Zip\7z.exe' x -y "-o$dest" $zip
$env:NGSPICE_EXECUTABLE = "$dest\Spice64\bin\ngspice_con.exe"
& $env:NGSPICE_EXECUTABLE --version
```

ถ้า `ngspice` อยู่ใน PATH อยู่แล้วไม่ต้องตั้ง `NGSPICE_EXECUTABLE` แอปจะหาเอง
หาก solver ไม่พบ หน้าเว็บจะแสดง **Status: Error** และไม่แสดงกราฟ/ค่าสำเร็จปลอม

## ติดตั้งและรัน

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:NGSPICE_EXECUTABLE = "$env:LOCALAPPDATA\ngspice-47\Spice64\bin\ngspice_con.exe"
.\.venv\Scripts\python.exe -m flask --app app run --port 5000
```

เปิด <http://127.0.0.1:5000/> → เลือกโหมดจาก Dropdown เดียวแล้วกด **Calculate / Run**
(ไม่มีฟอร์มที่สองและไม่มี radio/select สำหรับ analysis อีกต่อไป)

## รัน test

```powershell
$env:NGSPICE_EXECUTABLE = "$env:LOCALAPPDATA\ngspice-47\Spice64\bin\ngspice_con.exe"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

ผลที่ตรวจแล้ว: **54 tests OK** (Lab 03 เดิม 28 + SPICE engine/route 20 + unified dropdown 6)
ชุด `TestRealEngine` จะ `skip` เองถ้าไม่พบ ngspice

## โครงสร้างโปรเจกต์

```
app.py                  /run (single dropdown) + legacy /calculate, /simulate
dc_bias.py              สมการ DC bias ล้วน ๆ — Analytical Reference (ไม่ import Flask)
spice_engine.py         สร้าง netlist, subprocess.run ngspice, อ่าน raw/log จริง
plots.py                สร้าง SVG กราฟจากข้อมูลที่ parse แล้ว (server-rendered, ไม่มี JS)
templates/index.html    ฟอร์มเดียว (dropdown เดียว) + ตารางผล + กราฟ + netlist/log
static/style.css        Layout  desktop/mobile
tests/                  test_dc_bias, test_web, test_spice_engine, test_web_simulate
docs/lab04-fixture.json Input fixture + analytical reference + ช่องผล SPICE
docs/lab04-dataset.md   สรุปชุดข้อมูลอ่านง่าย
docs/validation.md      ผลตรวจรับ B1–B8
docs/captures/          ภาพหน้าจอจาก browser จริง
```

## วงจรอ้างอิง Lab 04

| Parameter | ค่า |
|---|---|
| VCC / R1 / R2 | 12 V / 100 kΩ / 22 kΩ |
| RC / RE / RL | 2.2 kΩ / 1 kΩ / 10 kΩ (ไม่มี emitter bypass) |
| Cin / Cout | 10 µF / 10 µF |
| Source | 10 mV peak, 1 kHz (ปรับได้) |
| Nodes | `vin` หลัง Cin (base), `vout` หลัง Cout ที่ RL |

BJT model ที่ใช้: **`t2n2222`** — คัดลอกจาก model card ใน
`ngspice-47/Spice64/examples/noise/bipolar-noise.cir`
(T. Tuma & A. Burmen, *Circuit Simulation with SPICE OPUS*, 2009)
เพื่อให้รันซ้ำได้โดยไม่เดาค่าเอง **ยังไม่ใช่ Starter Kit ของผู้สอน**
ถ้าได้ Starter Kit ให้แทนที่ `MODEL_CARD` ใน `spice_engine.py` และอัปเดต validation

## ตัวอย่างผลที่รันจริงในเครื่องนี้ (ngspice-47, model t2n2222)

| Analysis | ผลที่เห็นใน browser |
|---|---|
| DC `.op` (baseline) | VB 1.9791 V, VE 1.3314 V, VC 9.0936 V, VCE 7.7622 V, IC 1.3211 mA |
| DC เปลี่ยน RE → 2 kΩ | IC 0.7097 mA, VCE 9.0077 V (IC ลด, VCE เพิ่ม) |
| DC เปลี่ยน RE → 470 Ω | IC 2.4433 mA, VCE 5.4675 V (IC เพิ่ม, VCE ลด) |
| AC `.ac` 1 Hz–10 MHz | Gain สูงสุด 4.87 dB @ 5.012 kHz, phase 180.0°, fL 1.41 Hz, fH `not determined in sweep range` |
| Transient 10 mV / 1 kHz | Vin peak 10.0 mV, Vout peak 17.5 mV, gain 1.75×, phase ≈ −180° (กลับเฟส) |
| Transient 20 mV / 10 kHz | Vin peak 20.0 mV, Vout peak 35.0 mV, period 0.1 ms — เปลี่ยนตาม input |

ค่าข้างต้นมาจาก ngspice จริง ไม่ใช่ค่าจากภาพใน handout และไม่บังคับให้เท่า
Analytical (β/VBE คงที่) ทุกหลัก เพราะแบบจำลองต่างกัน

## สมการ Analytical (Lab 03 — ใช้เทียบเท่านั้น)

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

Baseline: `VTH 2.163934 V, RTH 18032.787 Ω, IB 12.2986 µA, IC 1.22986 mA,
IE 1.24216 mA, VB 1.94216 V, VE 1.24216 V, VC 9.29431 V, VCE 8.05215 V, ACTIVE`
(ใช้เป็น oracle ของ test regression B1)

## สมมติฐานและข้อจำกัด

- `dc_bias.py` ไม่ clamp ค่านอก Active Region — รายงานค่าดิบพร้อม warning (CUTOFF/SATURATION)
- ngspice ถูกเรียกแบบ batch: `ngspice -b -o run.log -r run.raw circuit.cir`
  ผ่าน `subprocess.run([...], cwd=tempdir, timeout=30)` **ไม่ใช้ `shell=True`**
  และอ่านผลจาก `run.raw` ที่ solver เขียนจริง
- ถ้า run fail, timeout, raw ว่าง หรือ parser ไม่พบ plot ที่คาด → Error ไม่ใช่ Success
- fL/fH หาจากจุดตัด −3 dB เทียบ gain สูงสุดใน sweep; ถ้าไม่มีจุดตัดในช่วงให้เขียน
  `not determined in sweep range`
- ไม่มี `node`/`npx` จึงติดตั้ง **Impeccable 4.10.0 แบบ manual copy** (`.opencode/`) แล้วใช้ launcher `.cmd`
  ที่ส่งมากับ skill; ใช้ OpenCode Browser tool + headless Chrome CDP ตรวจ desktop/mobile
  รายละเอียด critique/polish อยู่ใน `docs/impeccable-install.md`

## หลักฐาน

- `docs/captures/lab04-unified-dropdown-desktop.png` — หน้าแรกที่มี `<select>` เดียว
- `docs/captures/lab04-ac-desktop.png` — หน้า AC พร้อมกราฟ gain/phase
- `docs/captures/lab04-transient-desktop.png` — หน้า Transient พร้อม waveform
- `docs/captures/lab04-error-re0-desktop.png` — กรณี RE = 0 แสดง Error ไม่มีผล Success
- `docs/captures/impeccable-before.png` / `impeccable-after.png` — ภาพก่อน/หลัง Impeccable polish
- `docs/captures/impeccable-review-after/390x844.png` — mobile viewport จริงหลัง polish
- `docs/oral-check.md` — คำตอบข้อเท็จจริง 5 ข้อสำหรับตรวจรายบุคคล
- `docs/reflection.md` — ร่าง 3–5 บรรทัดที่ต้องแก้เป็นภาษาของนักศึกษาก่อนส่ง
