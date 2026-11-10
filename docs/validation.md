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
