# Validation Record — BJT DC Bias Web App (Lab 02)

วันที่ตรวจ: 2026-11-10
สภาพแวดล้อม: Windows 11, PowerShell, Python 3.15.2, Flask 3.1.3
คำสั่ง test ที่ใช้ทั้งเอกสาร:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

ผลรวมล่าสุด: **Ran 28 tests — OK (0 failures, 0 errors)**
(5 engineering tests + 7 parser + 7 validation + 3 non-finite + 6 Flask route tests)

## ตารางตรวจรับ A1–A7

| เกณฑ์ | สิ่งที่ทดสอบ | คำสั่ง/วิธีที่รัน | ผลที่ได้จริง |
|---|---|---|---|
| **A1** `GET /` | หน้าแรก HTTP 200 และมี input ครบ 7 ช่อง (`vcc, r1, r2, rc, re, beta, vbe`) | `TestRoutes.test_get_index_returns_form` และเปิด `http://127.0.0.1:5000/` | ผ่าน — 200, ฟอร์มมีค่าเริ่มต้นจาก handout ครบ |
| **A2** `POST /calculate` | ส่งค่าตัวอย่างแล้วได้ผลคำนวณจาก Python (ไม่ใช่ค่าคงที่ใน HTML) และแสดงค่า Ω ที่ตีความได้ข้างช่องกรอก | `TestRoutes.test_post_calculate_returns_engineering_result`, `test_get_index_shows_interpreted_resistance`, `test_post_shows_interpreted_resistance` และกด Calculate ในเบราว์เซอร์ | ผ่าน — 200, แสดง `VCE 8.052 V`, `IC 1.230 mA`, badge `ACTIVE`; ช่อง `100k` แสดง `= 100,000 Ω` |
| **A3** Engineering reference | เทียบค่าที่คำนวณกับ independent calculation (spec §8) | `TestReferenceOperatingPoint.test_reference_operating_point` + `test_kvl_consistency` | ผ่าน — ค่าตรงทุกตัว (ตารางด้านล่าง) และ KVL ปิด |
| **A4** Validation | ฟอร์มว่าง, ค่าที่ไม่ใช่ตัวเลข, ค่า 0/ติดลบ, `nan`/`inf`, `VBE >= VCC` ต้องได้ error ไม่ 500 | `TestCollectInputs` (7 tests), `TestNonFiniteInput` (3 tests) + `TestRoutes.test_post_invalid_input_shows_error_without_crash` + `test_post_empty_form_shows_errors` | ผ่าน — 200 ทุกกรณี, ฟอร์มว่างรายงาน 7 ช่อง, `nan`/`inf` ถูกปฏิเสธ |
| **A5** Outside Active Region | CUTOFF และ SATURATION ต้องมี warning และไม่ clamp | `TestRegionDetection` (3 tests) + ตรวจในเบราว์เซอร์ 2 กรณี | ผ่าน — CUTOFF: กระแส 0, `VC = VCE = 12 V`; SATURATION: รายงาน `VCE = -1.541 V` ดิบ + warning |
| **A6** Automated tests | ≥3 engineering tests + ≥1 Flask test client test | `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` | ผ่าน — **28 tests OK** (engineering 5, Flask route 6) |
| **A7** GitHub | `.gitignore` กันไฟล์ต้องห้าม, มี `README.md`, commit ครบ, repo Public | ตรวจ `git status` / GitHub Desktop → Publish repository | commit ครบ 5 รอบในเครื่อง; **Publish + Push ทำใน GitHub Desktop โดยผู้ใช้** (ต้องเอา *Keep this code private* ออก) |

## ค่าที่เว็บแสดง vs Independent Calculation

อินพุต: `VCC=12 V, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.70 V`

| ปริมาณ | Independent (spec §8) | เว็บแสดง | ตรงกัน |
|---|---|---|---|
| VTH | 2.163934 V | (คำนวณภายใน ไม่แสดง) | — |
| RTH | 18 032.787 Ω | (คำนวณภายใน ไม่แสดง) | — |
| VB | 1.94216 V | 1.942 V | ✅ |
| VE | 1.24216 V | 1.242 V | ✅ |
| VC | 9.29431 V | 9.294 V | ✅ |
| VCE | 8.05215 V | 8.052 V | ✅ |
| IC | 1.22986 mA | 1.230 mA | ✅ |
| IE | 1.24216 mA | 1.242 mA | ✅ |
| IB | 12.2986 µA | 12.299 µA | ✅ |
| Region | ACTIVE | ACTIVE | ✅ |

## 4 กรณีตรวจในเบราว์เซอร์ (`http://127.0.0.1:5000/`)

| # | อินพุตที่เปลี่ยน | ผลที่ได้จริง |
|---|---|---|
| 1 | ค่าเริ่มต้นทั้งหมด | badge **ACTIVE** — VB 1.942 V, VE 1.242 V, VC 9.294 V, VCE 8.052 V, IC 1.230 mA, IE 1.242 mA, IB 12.299 µA |
| 2 | `R1 = 0` | HTTP 200 — error **"R1 ต้องมากกว่า 0"** ไม่มี traceback |
| 3 | `R2 = 1k` | badge **CUTOFF** — VB 0.119 V, VE 0.000 V, VC 12.000 V, VCE 12.000 V, IC/IE/IB 0 — warning เรื่อง Cutoff |
| 4 | `RC = 10k` | badge **SATURATION** — VC −0.299 V, VCE −1.541 V, IC 1.230 mA (ค่าดิบ ไม่ clamp) — warning เรื่อง VCE < 0.3 V |

## หลักฐานเพิ่มเติม

- `TestReferenceOperatingPoint.test_kvl_consistency` ตรวจ `IC·RC + VCE + IE·RE = VCC`
  ด้วย tolerance `1e-9` — กันการคำนวณเพี้ยนแบบเงียบ
- `test_zero_resistance_reports_error_not_division_by_zero` ยืนยันว่า `R1`/`R2` เป็น 0
  ไม่ทำให้เกิด `ZeroDivisionError` หรือ HTTP 500
- `test_empty_form_reports_all_seven_fields` ยืนยันว่ารายงาน error ครบทั้ง 7 ช่องในครั้งเดียว

---

# Lab 04 — BJT Amplifier Simulator v1

วันที่ตรวจ: 2026-11-24

## สภาพแวดล้อมที่ใช้จริง

- Windows 11, PowerShell, Python **3.14.2**, Flask 3.1.3
- **ngspice-47** (build 2026-08-11) ติดตั้ง portable ที่
  `%LOCALAPPDATA%\ngspice-47\Spice64\bin\ngspice_con.exe`
  ตั้งผ่าน `NGSPICE_EXECUTABLE` (ไม่แก้ PATH ของเครื่อง)
- BJT model: **`t2n2222`** จาก `ngspice-47/examples/noise/bipolar-noise.cir`
  (T. Tuma & A. Burmen) — **ไม่ใช่ Starter Kit ของผู้สอน** เพราะยังไม่ได้รับไฟล์นั้น
- เครื่องมือตรวจหน้าเว็บ: **OpenCode Browser tool** (evaluate/screenshot/console) + **headless Chrome CDP** สำหรับ viewport 390×844
  **ไม่ใช่ Playwright MCP**; ไม่มี `node`/`npx` จึงติดตั้ง **Impeccable 4.10.0 แบบ manual copy** แล้วใช้ launcher `.cmd` ที่ส่งมากับ skill
- คำสั่ง test: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
  ผล **Ran 54 tests — OK** (28 Lab 03 + 20 SPICE/route + 6 unified dropdown) ตรวจซ้ำหลังปรับ UI แล้วยัง OK

## ตารางตรวจรับ B1–B8

| Case | Method | Input | Expected / Reference | Observed (จริง) | Evidence | Status |
|---|---|---|---|---|---|---|
| **B1** Regression | Browser tool: เลือก `divider` ใน dropdown เดียว → Calculate / Run | `VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.70` divider | `VB 1.942, VE 1.242, VC 9.294, VCE 8.052, IC 1.230 mA, IB 12.299 µA, ACTIVE` | ตรงทุกค่า, badge `ACTIVE`; `fixed`/`emitter` ก็ตรง (RB=1M) | หน้า `/` → `/run` snapshot; `tests/test_web.py`, `test_web_unified.py` | **PASS** |
| **B2** DC SPICE | Browser tool: เลือก `ce-dc` ใน dropdown เดียว → Calculate / Run | Baseline เดิม + `.op` | มี VB/VE/VC/VCE/IC, engine status, ชื่อ model/version | `Status: Success`, `ngspice-47`, `t2n2222`; VB 1.9791 V, VE 1.3314 V, VC 9.0936 V, VCE 7.7622 V, IC 1.3211 mA (IC จากแรงดันตกที่ RC, IE จาก RE, IB = IE−IC) | หน้า `/run`; `<details>` แสดง netlist + run.log จริง | **PASS** |
| **B3** Change RE | Browser tool: เปลี่ยน RE ค่าเดียวแล้วรัน DC ซ้ำ | RE = `2k`, แล้ว `470` แยกจาก baseline 1k | ทิศทาง: RE เพิ่ม → IC ลด/VCE เพิ่ม; RE ลด → IC เพิ่ม/VCE ลด | 2 kΩ: IC 0.7097 mA, VCE 9.0077 V · 470 Ω: IC 2.4433 mA, VCE 5.4675 V · (baseline 1.3211 mA / 7.7622 V) | snapshot ก่อน/หลัง 3 ครั้ง | **PASS** |
| **B4** AC | Browser tool: เลือก `ce-ac` ใน dropdown เดียว → Calculate / Run | `.ac dec 20 1 10MEG`, Vin=หลัง Cin, Vout=หลัง Cout | แกน Frequency(Hz), Gain(dB), Phase(°) มีหน่วย; ข้อมูลจาก run จริง | gain สูงสุด 4.87 dB @ 5012 Hz, phase 180.0°, fL 1.413 Hz, fH `not determined in sweep range`; SVG มี 141 จุด/เส้นที่ parse จาก run.raw | `docs/captures/lab04-ac-desktop.png`; 2 polyline ในหน้า + `<details>` netlist/log | **PASS** |
| **B5** Transient | Browser tool: เลือก `ce-tran` ใน dropdown เดียว → Calculate / Run | 10 mV peak, 1 kHz, `.tran` 5 cycles | Vin/Vout ตามเวลา, มีแกน Time(s)/Voltage(V), กลับเฟส ~180° | Vin peak 0.0100 V, Vout peak 0.0175 V, gain 1.75×, phase −179.9°, period 0.001 s; waveform 504 จุด/เส้น | `docs/captures/lab04-transient-desktop.png` + สรุปเฟสจากหน้า | **PASS** |
| **B6** Change Source | Browser tool: เปลี่ยน Amplitude/Frequency แล้วรันซ้ำ | 20 mV peak, 10 kHz (เทียบ 10 mV/1 kHz) | waveform/peak/period เปลี่ยนตาม input ไม่ใช่ hard-code | Vin peak 0.0200 V (2×), Vout peak 0.0350 V (2×), period 0.0001 s (1/10), gain คง 1.75×, phase 179.9° | snapshot ก่อน/หลัง; netlist มี `SIN(0 20m 10k)` | **PASS** |
| **B7** Invalid / Fail | Browser tool: เลือก `ce-dc` ใส่ RE = `0` แล้ว Run; อีกกรณีเปิด server ชั่วคราว port 5001 โดยตั้ง `NGSPICE_EXECUTABLE` ให้ชี้ path ที่ไม่มีจริงแล้วรัน `ce-dc` | `re=0`; `executable=C:\definitely-missing-ngspice\ngspice_con.exe` | error ชัดเจน, ไม่ค้าง, ไม่มี Success ปลอม | ทั้ง 2 กรณีได้ `status error`: (1) `RE ต้องเป็นตัวเลขบวกและมีหน่วยถูกต้อง` (2) `ngspice ไม่พบใน PATH — กรุณาตั้ง NGSPICE_EXECUTABLE หรือติดตั้ง ngspice`; ทั้งคู่ไม่มี `.sim-results` และไม่มี `.status.success` | `docs/captures/lab04-error-re0-desktop.png`; browser snapshot port 5000/5001; `tests/test_spice_engine.py`, `tests/test_web_simulate.py` | **PASS** |
| **B8a** UI desktop | Browser tool: หน้า `/` และ `/run` (`selects=1`, `name="mode"`, 6 options, 1 button) | dropdown เดียว + เปลี่ยนโหมด | ปุ่ม/กราฟ/หน่วยอ่านได้ ไม่ถูกตัด | `scrollWidth 985 <= innerWidth 1000`, ปุ่ม Calculate / Run `top=656` (ก่อนปรับ `top=961`) อยู่ใน viewport, console error `[]`; ตรวจ CSS-only progressive disclosure 6 โหมดแล้ว field ที่ไม่เกี่ยวข้องถูกซ่อนแต่ค่ายังส่งผ่านฟอร์ม | `docs/captures/lab04-unified-dropdown-desktop.png`, `docs/captures/impeccable-before.png`, `docs/captures/impeccable-after.png`, `docs/captures/b8-desktop-check.png` | **PASS** |
| **B8b** UI mobile / Impeccable | headless Chrome CDP `Emulation.setDeviceMetricsOverride(390×844, mobile=true)` + `impeccable shot --viewport 390x844` + `impeccable detect` ที่ viewport 390×844 | viewport 390×844, เปิด `/` แล้ว submit `ce-ac` | กราฟ/ปุ่ม/select ไม่ถูกตัด, detector ไม่พบ anti-pattern, มี before/after จริง | หน้า `/`: `innerWidth=390`, `scrollWidth=clientWidth=390`, `matchMedia(max-width:640px)=true`, select/Putton กว้าง 320 px (left 35/right 355), card กว้าง 358 px, grid 1 column; หน้า `/run`: 2 SVG chart กว้าง 302 px (left 44/right 346) `scrollWidth=390`, status Success; `impeccable detect` desktop 1440×900 และ mobile 390×844 ได้ `[]` exit 0 | `docs/captures/impeccable-review-after/390x844.png`, `docs/impeccable-install.md`, CDP JSON ในบันทึกด้านล่าง | **PASS** |

## หมายเหตุความถูกต้อง

- ผล Lab 03 ยังอยู่ครบ 28 tests เดิม + 20 tests SPICE/route + 6 tests unified = 54 tests OK
- UI รวมเป็นฟอร์มเดียว: มี `<select name="mode">` เพียงตัวเดียว (6 options) และปุ่ม
  `Calculate / Run` ปุ่มเดียว ไม่มี radio `analysis` หรือฟอร์ม Lab 04 แยกอีกต่อไป;
  `/calculate` และ `/simulate` คือ compat route สำหรับ test เดิม
- ตรวจใน browser จริงแล้ว: `divider/fixed/emitter` ได้ผล Analytical ตรงตาราง,
  `ce-dc/ce-ac/ce-tran` ได้ผล ngspice จริงจาก dropdown เดียวกัน
- ตรวจซ้ำ B2–B8 หลังรวม dropdown: B2 status/model/version + netlist/log จริง;
  B3 IC/VCE เปลี่ยนตาม RE (1.3211/7.7622 → 0.7097/9.0077 → 2.4433/5.4675);
  B4 141 จุด/เส้น gain+phase; B5 504 จุด/เส้น phase −179.9°;
  B6 20 mV/10 kHz ได้ 0.0200 V/0.0350 V/0.0001 s และบรรทัด
  `VIN src 0 DC 0 AC 20m SIN(0 20m 10k)`; B7 ทั้ง input ผิดและ solver หาย
  ขึ้น Status: Error ไม่มี Success ปลอม; B8a desktop PASS, B8b mobile PASS ด้วย viewport จริง 390×844
- ผล SPICE ไม่ได้ถูกแก้ให้ตรง Analytical: model `t2n2222` ให้ IC 1.3211 mA
  เทียบ Analytical 1.2299 mA ที่ β/VBE คงที่ — ต่างกันตามสมมติฐานของแบบจำลอง
- ทุกกราฟสร้าง SVG จาก array ที่ parse ได้จาก `run.raw` เท่านั้น
  ไม่มีค่า gain/fL/fH/waveform ถูก hard-code ใน template หรือ `plots.py`
- fH ใน sweep 1 Hz–10 MHz ไม่มีจุดตัด −3 dB ด้านความถี่สูง จึงรายงาน
  `not determined in sweep range` ตามใบงาน ไม่ได้แต่งตัวเลขขึ้นมา
- ไฟล์ `run.raw`/`run.log` ถูกสร้างใน `TemporaryDirectory` ต่อรอบและลบหลัง parse
  หลักฐานที่เก็บคือข้อความ netlist/log ท้ายไฟล์ในหน้าเว็บ + screenshot จาก browser จริง
- `git` ไม่ได้อยู่ใน PATH ของ PowerShell แต่ใช้ embedded git จาก GitHub Desktop
  (`...\GitHubDesktop\app-3.7.0\resources\app\git\cmd\git.exe`) สำหรับ status/commit/push
- หลัง Impeccable polish ตรวจซ้ำ 54 tests OK และ B2–B7 ยังให้ค่าเดิมทุกตัว (ดูตารางข้างบน)
  มีการปรับเฉพาะ layout/typography/spacing/focus/format ของ fL/badge/aria-live ไม่แตะ netlist หรือสมการ

## หลักฐาน mobile 390×844 (headless Chrome CDP — รันจริง 2026-11-24)

คำสั่งตั้ง viewport: `Emulation.setDeviceMetricsOverride {width:390, height:844, deviceScaleFactor:1, mobile:true}`
แล้ว `Page.navigate` ไป `http://127.0.0.1:5000/`, อ่าน `Runtime.evaluate` ก่อนและหลัง submit `ce-ac`:

```json
{"url":"http://127.0.0.1:5000/","innerWidth":390,"media640":true,"scrollWidth":390,"clientWidth":390,"selects":1,"options":6,"buttons":1,"button":{"left":35,"right":355,"width":320,"top":800},"select":{"left":35,"right":355,"width":320},"grid":"320px","simGrid":"320px","card":{"left":16,"right":374,"width":358},"status":null}
{"url":"http://127.0.0.1:5000/run","innerWidth":390,"scrollWidth":390,"clientWidth":390,"media640":true,"charts":[{"left":44,"right":346,"width":302,"polylines":1},{"left":44,"right":346,"width":302,"polylines":1}],"status":"Status: Success\nEngine: ngspice-47\nBJT model: t2n2222\nAnalysis: AC","buttons":1,"selects":1}
```

ผล `impeccable detect --json http://127.0.0.1:5000/ --viewport 1440x900` และ `--viewport 390x844`: `[]`, exit 0 ทั้งสองครั้ง

---

## Rubric (10 คะแนน) — self-check 2026-11-24

| หัวข้อ | คะแนน | สถานะตอนนี้ | หลักฐาน / สิ่งที่ยังขาด |
|---|---:|---|---|
| ความต่อเนื่องจาก Lab 3 | 1 | **ครบ** | 28 tests เดิมยัง OK; `divider/fixed/emitter` ถูกตรวจผ่าน dropdown เดียวใน B1 |
| การเชื่อม ngspice | 3 | **ครบ** | `.op` สำเร็จ (B2), adapter ใช้ `subprocess.run([...])` ไม่ใช้ `shell=True`, มี error handling (B7), อ่าน `run.raw` จริงและโชว์ netlist/log (B2) |
| AC + Transient | 2 | **ครบ** | Bode/waveform มี 141/504 จุดจากรันจริง, แกน+หน่วยถูกต้อง, เปลี่ยน source แล้วผลเปลี่ยน (B4–B6) |
| UI และ Impeccable | 2 | **ครบ** | ติดตั้ง Impeccable 4.10.0 แบบ manual copy, รัน `context`/`detect` + isolated critique A/B จริง, ปรับ layout/typography/spacing/focus/format ตาม findings, เก็บ `impeccable-before.png`/`impeccable-after.png`, detector live desktop+mobile `[]` exit 0, 54 tests และ B2–B7 ไม่เปลี่ยน — ดู `docs/impeccable-install.md` |
| Browser Acceptance | 1 | **ครบ** | B1–B8 บันทึกวิธี/INPUT/Observed/Evidence/Status ตรงความจริง; ใช้ OpenCode Browser tool + headless Chrome CDP ที่ viewport 390×844 จริง ไม่ได้อ้าง Playwright |
| GitHub + Reproducibility | 1 | **ยังไม่ครบ** | README และ validation พร้อม แต่ยังไม่มี commit ของ Lab 4; ค่า SHA ใน `.git/refs/heads/main` คือ `7131057c4f4975c13e2f5049a202a98e066f8b0f` (clone เริ่มต้น) ยังไม่ใช่ Lab 4; ต้อง commit/push แล้วใส่ URL + SHA ใหม่ในใบส่ง |

**สรุป self-check: 9/10 คะแนนที่หลักฐานครบแล้ว / อีก 1 คะแนนยังเสี่ยง** (GitHub+Reproducibility 1) คะแนนจริงขึ้นกับ TA

### Submission checklist

- [x] **Impeccable/Unslop**: critique/polish จริง, before/after screenshot, 54 tests และ B2–B7 ไม่เปลี่ยน (`docs/impeccable-install.md`)
- [x] **Browser Acceptance**: B1–B8 ครบ รวม mobile viewport 390×844 จริง
- [x] **คำตอบตรวจรายบุคคล**: `docs/oral-check.md` มีคำตอบข้อเท็จจริง 5 ข้อ พร้อมแก้เป็นภาษาตัวเอง
- [ ] **Commit SHA สำหรับ Lab 4** หลัง commit/push (repo URL คือ `https://github.com/theerakeat77-gif/BJT-DC-Bias-Web-App.git`)
- [ ] **Reflect 3–5 บรรทัด**: `docs/reflection.md` เป็นร่างข้อเท็จจริงจากหลักฐาน — **ต้องเขียน/แก้ด้วยคำของนักศึกษาเอง** ก่อนส่ง (AI ไม่ควรแต่งความรู้สึกส่วนตัวแทน)
- [ ] ตอบคำถามสั้นของ TA ด้วยภาษาของตัวเองจาก `docs/oral-check.md` (ห้ามอ่านตามliteral)

