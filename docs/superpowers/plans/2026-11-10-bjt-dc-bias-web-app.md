# BJT DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง Flask Web Application ที่รับค่า VCC, R1, R2, RC, RE, β, VBE แล้วคำนวณ DC Operating Point ของวงจร BJT Common-Emitter Voltage-Divider Bias ด้วย Python Backend พร้อม validation, region warning และ automated tests

**Architecture:** แยกชั้น HTTP (`app.py` + Jinja template) ออกจากชั้นวิศวกรรม (`dc_bias.py` ที่ไม่ import Flask) — `app.py` แปลงหน่วย/ตรวจสอบ input แล้วเรียก `calculate_dc_bias()` ซึ่งคืน dataclass ผลลัพธ์ที่ template นำไปแสดง

**Tech Stack:** Python 3.15.2, Flask, `unittest`, HTML + CSS (ไม่มี JavaScript)

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-dc-bias-web-app-design.md`

## Global Constraints

- Python 3.15.2 ที่ `%LOCALAPPDATA%\Programs\Python\Python315\python.exe` — ใช้ venv `.venv` ในโปรเจกต์
- Dependency เดียวที่อนุญาต: `Flask` (ห้ามเพิ่ม pytest/requests ฯลฯ) — test ใช้ `unittest`
- `dc_bias.py` **ห้าม import Flask** และห้ามมี HTML
- เว็บรันที่ `http://127.0.0.1:5000/` — ต้องเปิดผ่าน server ไม่ใช่ `file://`
- UI ภาษาไทย ศัพท์เทคนิคคงเป็นอังกฤษ; ไม่มี JavaScript
- หน่วยที่แสดง: แรงดันเป็น V (3 ตำแหน่ง), `IC`/`IE` เป็น mA (3 ตำแหน่ง), `IB` เป็น µA (3 ตำแหน่ง)
- Region constants: `"ACTIVE"`, `"CUTOFF"`, `"SATURATION"`; เกณฑ์ saturation warning คือ `VCE < 0.3 V`
- นอก Active Region: รายงานค่าดิบตามสมการ + warning (ห้าม clamp)
- Repo: Public, branch `main`, โฟลเดอร์ `C:\Users\b6806200\Documents\GitHub\BJT DC Bias Web App`
- Commit ทำด้วย `git` CLI ระหว่างพัฒนา (agent คลิก GUI ไม่ได้); **Publish + Push ทำใน GitHub Desktop**
- `.gitignore` ต้องมี `.venv/`, `__pycache__/`, `*.pyc`, `.env`, `.pytest_cache/`

## Review Focus

จุดที่ spec กล่าวถึงแต่ไม่มี test ของ task ใดครอบไว้ — เพิ่ม test ใน task ที่เป็นเจ้าของโค้ดแล้ว:

1. `R1` หรือ `R2` เป็น `0` → ต้องเป็น validation error ไม่ใช่ `ZeroDivisionError`/HTTP 500 (Task 3)
2. ช่องว่างหัวท้าย และตัวพิมพ์ใหญ่ `100K` / `2.2M` → ต้อง parse ได้ (Task 3)
3. ค่าติดลบ เช่น `-100k` → validation error ไม่ใช่คำนวณเงียบ ๆ (Task 3)
4. `VBE >= VCC` → validation error (Task 3)
5. กด Submit โดยฟอร์มว่างทั้งหมด → แสดง error ครบทุกช่อง ไม่ 500 (Task 3, Task 4)

---

### Task 1: Engineering core — คำนวณ DC Operating Point

**Files:**
- Create: `dc_bias.py`
- Create: `tests/test_dc_bias.py`
- Create: `requirements.txt`
- Create: `.gitignore`

**Interfaces:**
- Consumes: ไม่มี (task แรก)
- Produces:
  - `@dataclass BiasInput`: `vcc: float, r1: float, r2: float, rc: float, re: float, beta: float, vbe: float` (SI ทั้งหมด)
  - `@dataclass BiasResult`: `vth, rth, ib, ic, ie, vb, ve, vc, vce: float` + `region: str` + `warnings: list[str]`
  - `REGION_ACTIVE = "ACTIVE"`, `REGION_CUTOFF = "CUTOFF"`, `REGION_SATURATION = "SATURATION"`
  - `calculate_dc_bias(inp: BiasInput) -> BiasResult`
  - `VCE_SAT_WARN = 0.3`

- [ ] **Step 1: สร้าง venv และติดตั้ง Flask**

Run (PowerShell, workdir = repo root):
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
.\.venv\Scripts\python.exe -m pip install "Flask>=3.0,<4"
```
Expected: ไม่มี error; `pip show flask` แสดง version

- [ ] **Step 2: เขียน `.gitignore` และ `requirements.txt`**

`.gitignore`:
```
.venv/
__pycache__/
*.pyc
.env
.pytest_cache/
```

`requirements.txt` (ชั่วคราว — Task 5 จะ pin เวอร์ชันจริงด้วย `pip freeze`):
```
Flask>=3.0,<4
```

- [ ] **Step 3: เขียน failing test**

`tests/test_dc_bias.py`:
```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dc_bias import BiasInput, calculate_dc_bias, REGION_ACTIVE


class TestReferenceOperatingPoint(unittest.TestCase):
    def setUp(self):
        # ค่าตัวอย่างจาก handout Lab 02
        self.inp = BiasInput(vcc=12.0, r1=100_000.0, r2=22_000.0,
                             rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70)

    def test_reference_operating_point(self):
        r = calculate_dc_bias(self.inp)
        self.assertAlmostEqual(r.vth, 2.163934, places=6)
        self.assertAlmostEqual(r.rth, 18_032.786885, places=4)
        self.assertAlmostEqual(r.ib, 12.298581e-6, places=12)
        self.assertAlmostEqual(r.ic, 1.2298581e-3, places=9)
        self.assertAlmostEqual(r.ie, 1.2421567e-3, places=9)
        self.assertAlmostEqual(r.ve, 1.2421567, places=6)
        self.assertAlmostEqual(r.vb, 1.9421567, places=6)
        self.assertAlmostEqual(r.vc, 9.2943122, places=6)
        self.assertAlmostEqual(r.vce, 8.0521555, places=6)
        self.assertEqual(r.region, REGION_ACTIVE)

    def test_kvl_consistency(self):
        r = calculate_dc_bias(self.inp)
        self.assertAlmostEqual(r.ic * self.inp.rc + r.vce + r.ie * self.inp.re,
                               self.inp.vcc, places=9)
```

- [ ] **Step 4: รัน test ให้เห็นว่า fail**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dc_bias'`

- [ ] **Step 5: เขียน `dc_bias.py`**

สร้าง dataclass ตาม Interfaces, ฟังก์ชัน `calculate_dc_bias` คำนวณตามสมการ:
```
vth = vcc * r2 / (r1 + r2)
rth = r1 * r2 / (r1 + r2)
ib  = (vth - vbe) / (rth + (beta + 1) * re)
ic  = beta * ib
ie  = (beta + 1) * ib
ve  = ie * re
vb  = ve + vbe
vc  = vcc - ic * rc
vce = vc - ve
```
`region` = `REGION_ACTIVE`, `warnings` = `[]` ใน task นี้ (Task 2 เติม logic)
ถ้า `r1 <= 0 or r2 <= 0 or rc <= 0 or re <= 0 or beta <= 0` → `raise ValueError(...)`

- [ ] **Step 6: รัน test ให้ผ่าน**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: `Ran 2 tests ... OK`

- [ ] **Step 7: Commit**

```bash
git add .gitignore requirements.txt dc_bias.py tests/test_dc_bias.py
git commit -m "feat: add DC bias engineering core with reference tests"
```

---

### Task 2: Region detection และ warning นอก Forward-Active

**Files:**
- Modify: `dc_bias.py` (ฟังก์ชัน `calculate_dc_bias`)
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `BiasInput`, `BiasResult`, `calculate_dc_bias` จาก Task 1
- Produces: `REGION_CUTOFF`, `REGION_SATURATION`, `VCE_SAT_WARN = 0.3`, และ `warnings: list[str]` ที่มีข้อความภาษาไทย

- [ ] **Step 1: เขียน failing tests**

เพิ่มใน `tests/test_dc_bias.py`:
```python
from dc_bias import REGION_CUTOFF, REGION_SATURATION


class TestRegionDetection(unittest.TestCase):
    def test_cutoff_when_vth_below_vbe(self):
        # VTH = 12*1000/101000 = 0.1188 V < 0.7 V
        inp = BiasInput(vcc=12.0, r1=100_000.0, r2=1_000.0,
                        rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70)
        r = calculate_dc_bias(inp)
        self.assertEqual(r.region, REGION_CUTOFF)
        self.assertEqual(r.ib, 0.0)
        self.assertEqual(r.ic, 0.0)
        self.assertEqual(r.ie, 0.0)
        self.assertAlmostEqual(r.ve, 0.0, places=9)
        self.assertAlmostEqual(r.vb, 0.1188119, places=6)
        self.assertAlmostEqual(r.vc, 12.0, places=9)
        self.assertAlmostEqual(r.vce, 12.0, places=9)
        self.assertTrue(r.warnings)

    def test_saturation_warning_when_vce_low(self):
        # RC = 10k => VC = 12 - 12.2986 = -0.2986 V, VCE = -1.54 V
        inp = BiasInput(vcc=12.0, r1=100_000.0, r2=22_000.0,
                        rc=10_000.0, re=1_000.0, beta=100.0, vbe=0.70)
        r = calculate_dc_bias(inp)
        self.assertEqual(r.region, REGION_SATURATION)
        self.assertLess(r.vce, 0.3)
        self.assertTrue(r.warnings)
        # ยังรายงานค่าดิบตามสมการ ไม่ clamp
        self.assertAlmostEqual(r.ic, 1.2298581e-3, places=9)

    def test_active_has_no_warning(self):
        inp = BiasInput(vcc=12.0, r1=100_000.0, r2=22_000.0,
                        rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70)
        self.assertEqual(calculate_dc_bias(inp).warnings, [])
```

- [ ] **Step 2: รัน test ให้เห็นว่า fail**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: FAIL — `ImportError: cannot import name 'REGION_CUTOFF'`

- [ ] **Step 3: เติม logic ใน `calculate_dc_bias`**

หลังคำนวณ `vth` แล้ว ถ้า `vth <= vbe` → คืนผลแบบ cutoff:
`ib=ic=ie=0`, `ve=0`, `vb=vth`, `vc=vcc`, `vce=vcc`, `region=REGION_CUTOFF`,
`warnings=["วงจรอยู่ในช่วง Cutoff (VTH <= VBE): ทรานซิสเตอร์ไม่นำกระแส ค่าที่แสดงไม่ใช่จุดทำงานแบบ Forward-Active"]`

ถ้าไม่ใช่ cutoff: ถ้า `vce < VCE_SAT_WARN` → `region=REGION_SATURATION` และเพิ่ม warning
`"VCE ต่ำกว่า 0.3 V: วงจรใกล้ Saturation สมการ Forward-Active ใช้ไม่ได้ ค่าที่แสดงเป็นค่าตามสมการ ไม่ใช่ค่าจริงของวงจร"`
มิฉะนั้น `region=REGION_ACTIVE`

- [ ] **Step 4: รัน test ให้ผ่าน**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: `Ran 5 tests ... OK`

- [ ] **Step 5: Commit**

```bash
git add dc_bias.py tests/test_dc_bias.py
git commit -m "feat: detect cutoff and saturation regions with warnings"
```

---

### Task 3: แปลงหน่วยและตรวจสอบ input (`app.py` ชั้น app)

**Files:**
- Create: `app.py` (เฉพาะส่วน parsing/validation — routes อยู่ใน Task 4)
- Create: `tests/test_web.py`

**Interfaces:**
- Consumes: `BiasInput` จาก Task 1
- Produces:
  - `parse_float(text: str) -> float` — ตัดช่องว่าง, raise `ValueError` ถ้าไม่ใช่ตัวเลข
  - `parse_resistance(text: str) -> float` — รับ `100000`, `100k`, `100K`, `2.2k`, `1M`; คืนค่าเป็น Ω
  - `collect_inputs(form: Mapping[str, str]) -> tuple[BiasInput | None, list[str]]` — คืน `(None, errors)` เมื่อมีข้อผิดพลาด
  - `FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")`
  - `DEFAULTS: dict[str, str]` = ค่าตัวอย่างของ handout (`12`, `100k`, `22k`, `2.2k`, `1k`, `100`, `0.70`)
  - `app: Flask` (สร้าง instance แต่ยังไม่มี route)

- [ ] **Step 1: เขียน failing tests**

`tests/test_web.py`:
```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import collect_inputs, parse_float, parse_resistance


class TestParseResistance(unittest.TestCase):
    def test_plain_ohms(self):
        self.assertEqual(parse_resistance("100000"), 100_000.0)

    def test_kilo_lowercase(self):
        self.assertEqual(parse_resistance("100k"), 100_000.0)

    def test_kilo_uppercase_and_decimal(self):
        self.assertEqual(parse_resistance("2.2K"), 2_200.0)

    def test_mega(self):
        self.assertEqual(parse_resistance("1M"), 1_000_000.0)

    def test_whitespace_trimmed(self):
        self.assertEqual(parse_resistance("  100k  "), 100_000.0)

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            parse_resistance("abc")

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            parse_resistance("-100k")


class TestCollectInputs(unittest.TestCase):
    def valid_form(self):
        return {"vcc": "12", "r1": "100k", "r2": "22k", "rc": "2.2k",
                "re": "1k", "beta": "100", "vbe": "0.70"}

    def test_valid_form_returns_bias_input(self):
        inp, errors = collect_inputs(self.valid_form())
        self.assertEqual(errors, [])
        self.assertEqual(inp.r1, 100_000.0)
        self.assertEqual(inp.beta, 100.0)

    def test_missing_field_reports_error(self):
        form = self.valid_form()
        del form["vcc"]
        inp, errors = collect_inputs(form)
        self.assertIsNone(inp)
        self.assertTrue(any("VCC" in e for e in errors))

    def test_zero_resistance_reports_error_not_division_by_zero(self):
        form = self.valid_form()
        form["r2"] = "0"
        inp, errors = collect_inputs(form)
        self.assertIsNone(inp)
        self.assertTrue(any("R2" in e for e in errors))

    def test_non_numeric_reports_error(self):
        form = self.valid_form()
        form["rc"] = "abc"
        inp, errors = collect_inputs(form)
        self.assertIsNone(inp)
        self.assertTrue(any("RC" in e for e in errors))

    def test_negative_beta_reports_error(self):
        form = self.valid_form()
        form["beta"] = "-5"
        inp, errors = collect_inputs(form)
        self.assertIsNone(inp)
        self.assertTrue(any("β" in e or "beta" in e for e in errors))

    def test_vbe_not_below_vcc_reports_error(self):
        form = self.valid_form()
        form["vbe"] = "12"
        inp, errors = collect_inputs(form)
        self.assertIsNone(inp)
        self.assertTrue(any("VBE" in e for e in errors))

    def test_empty_form_reports_all_seven_fields(self):
        inp, errors = collect_inputs({})
        self.assertIsNone(inp)
        self.assertEqual(len(errors), 7)
```

- [ ] **Step 2: รัน test ให้เห็นว่า fail**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: เขียน `app.py` ส่วน parsing/validation**

- `parse_float`: `float(text.strip())` แล้ว raise `ValueError("...")` ถ้าแปลงไม่ได้
- `parse_resistance`: ตัดช่องว่าง → ถ้าลงท้ายด้วย `k`/`K` คูณ 1e3, `M` คูณ 1e6 แล้วตัด suffix ออก → `parse_float` ส่วนที่เหลือ → ถ้าผล `<= 0` raise `ValueError`
- `collect_inputs`: วนตาม `FIELDS`; ช่องว่าง/หาย → `"กรุณากรอก <NAME>"`; แปลงไม่ได้ → `"<NAME> ต้องเป็นตัวเลข"`;
  ค่า `<= 0` สำหรับ `vcc`, `r1`, `r2`, `rc`, `re`, `beta` → `"<NAME> ต้องมากกว่า 0"`;
  `vbe < 0` หรือ `vbe >= vcc` → `"VBE ต้องอยู่ระหว่าง 0 ถึง VCC"`
  (ตรวจ `vbe` เทียบ `vcc` เฉพาะเมื่อ `vcc` แปลงสำเร็จแล้ว) — ถ้ามี error ใด ๆ คืน `(None, errors)`

- [ ] **Step 4: รัน test ให้ผ่าน**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: `Ran 17 tests ... OK`

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_web.py
git commit -m "feat: parse resistance units and validate form inputs"
```

---

### Task 4: Flask routes, template และ CSS

**Files:**
- Modify: `app.py` (เพิ่ม route)
- Create: `templates/index.html`
- Create: `static/style.css`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `collect_inputs`, `DEFAULTS`, `FIELDS` (Task 3); `calculate_dc_bias`, `BiasResult` (Task 1–2)
- Produces: `GET /` และ `POST /calculate` ที่คืน HTML 200 เสมอ (ไม่ 500 เมื่อ input ผิด)

- [ ] **Step 1: เขียน failing tests**

เพิ่มใน `tests/test_web.py`:
```python
from app import app


class TestRoutes(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_get_index_returns_form(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{field}"', body)

    def test_post_calculate_returns_engineering_result(self):
        resp = self.client.post("/calculate", data={
            "vcc": "12", "r1": "100k", "r2": "22k", "rc": "2.2k",
            "re": "1k", "beta": "100", "vbe": "0.70"})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn("8.052", body)   # VCE
        self.assertIn("1.230", body)   # IC (mA)
        self.assertIn("ACTIVE", body)

    def test_post_invalid_input_shows_error_without_crash(self):
        resp = self.client.post("/calculate", data={
            "vcc": "12", "r1": "0", "r2": "22k", "rc": "2.2k",
            "re": "1k", "beta": "100", "vbe": "0.70"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("R1", resp.get_data(as_text=True))

    def test_post_empty_form_shows_errors(self):
        resp = self.client.post("/calculate", data={})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("VCC", resp.get_data(as_text=True))
```

- [ ] **Step 2: รัน test ให้เห็นว่า fail**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: FAIL — `404 != 200` ใน `test_get_index_returns_form`

- [ ] **Step 3: เพิ่ม routes ใน `app.py`**

```python
@app.get("/")
def index():
    return render_template("index.html", form=DEFAULTS, result=None, errors=[])

@app.post("/calculate")
def calculate():
    form = {f: request.form.get(f, "") for f in FIELDS}
    bias_input, errors = collect_inputs(request.form)
    if errors:
        return render_template("index.html", form=form, result=None, errors=errors)
    return render_template("index.html", form=form,
                           result=calculate_dc_bias(bias_input), errors=[])
```
(import `render_template`, `request` จาก flask)

- [ ] **Step 4: เขียน `templates/index.html`**

หน้าเดียว มี 3 ส่วน:
1. `<form method="post" action="/calculate">` — input 7 ช่อง `name` ตรงตาม `FIELDS`,
   `value="{{ form.vcc }}"` ฯลฯ, ช่อง resistor มี hint "รับ 100000 / 100k / 2.2k / 1M"
2. ถ้า `errors` → `<ul class="errors">` แสดงทุกข้อ
3. ถ้า `result` → ตารางผลลัพธ์: VB, VE, VC, VCE (V, 3 ตำแหน่ง), IC, IE (mA, 3 ตำแหน่ง),
   IB (µA, 3 ตำแหน่ง) ใช้ `"{{ '%.3f'|format(result.vb) }}"`, badge แสดง `result.region`,
   และ `<ul class="warnings">` แสดง `result.warnings`
   — ใช้ `{% if result %}` ครอบทั้งบล็อก

- [ ] **Step 5: เขียน `static/style.css`**

Layout การ์ดกลางหน้า, ฟอร์มแบบ grid 2 คอลัมน์บนจอกว้าง / 1 คอลัมน์บนจอแคบ (`@media (max-width: 640px)`),
ตัวเลขผลลัพธ์ใช้ `font-family: Consolas, monospace`, badge ACTIVE สีเขียว / CUTOFF- SATURATION สีส้ม,
`.errors` พื้นแดงอ่อน, `.warnings` พื้นเหลืองอ่อน

- [ ] **Step 6: รัน test ให้ผ่าน**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: `Ran 21 tests ... OK`

- [ ] **Step 7: เปิดเว็บจริงและตรวจด้วยตา**

Run: `.\.venv\Scripts\python.exe -m flask --app app run`
Expected: เปิด `http://127.0.0.1:5000/` เห็นฟอร์มพร้อมค่าเริ่มต้น → กด Calculate → เห็นผลตรงกับ
`VB 1.942 V, VE 1.242 V, VC 9.294 V, VCE 8.052 V, IC 1.230 mA` และ badge ACTIVE

- [ ] **Step 8: Commit**

```bash
git add app.py templates/index.html static/style.css tests/test_web.py
git commit -m "feat: add Flask routes, results template and stylesheet"
```

---

### Task 5: เอกสาร, pin dependency และตรวจรับครบ A1–A7

**Files:**
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `docs/design-note.md`
- Create: `docs/validation.md`
- Create: `docs/reflection.md`
- Modify: `requirements.txt` (pin จาก `pip freeze`)

**Interfaces:**
- Consumes: ทั้งโปรเจกต์จาก Task 1–4
- Produces: ไม่มีโค้ดใหม่ — เอกสารและหลักฐานตรวจรับ

- [ ] **Step 1: Pin dependency**

Run: `.\.venv\Scripts\python.exe -m pip freeze > requirements.txt`
Expected: ไฟล์มี `Flask==...`, `Werkzeug==...`, `Jinja2==...` ฯลฯ

- [ ] **Step 2: เขียน `README.md`**

ต้องมี: ชื่อโปรเจกต์ + ภาพรวมสั้น, ต้องมีอะไรบ้าง (Python 3.15+), วิธีติดตั้ง (`python -m venv .venv`,
`.\.venv\Scripts\python.exe -m pip install -r requirements.txt`), วิธีรัน
(`.\.venv\Scripts\python.exe -m flask --app app run` → `http://127.0.0.1:5000/`),
วิธีรัน test (`.\.venv\Scripts\python.exe -m unittest discover -s tests -v`),
ตารางสมการที่ใช้, สมมติฐาน Forward-Active + ข้อจำกัด, และค่าตัวอย่างพร้อมผลอ้างอิง

- [ ] **Step 3: เขียน `AGENTS.md`**

กติกาสำหรับ AI: ห้ามใส่สมการใน `templates/`, `dc_bias.py` ห้าม import Flask, ต้องมี test ก่อนแก้ logic,
ห้าม commit `.venv/`/`.env`, UI ภาษาไทย ไม่เพิ่ม dependency โดยไม่จำเป็น

- [ ] **Step 4: เขียน `docs/design-note.md`**

สรุปสถาปัตยกรรม (Browser → Flask route → `dc_bias` → template), เหตุผลที่แยกชั้น,
ทางเลือกที่ตัดทิ้ง (JSON API, SPA, clamp ที่ VCE(sat)), และการตัดสินใจเรื่องหน่วย

- [ ] **Step 5: เขียน `docs/validation.md`**

ตารางตรวจรับ A1–A7: แต่ละข้อระบุ "สิ่งที่ทดสอบ / คำสั่งที่รัน / ผลที่ได้จริง"
และตารางเทียบค่าที่เว็บแสดงกับ independent calculation (ค่าจาก spec ข้อ 8)

- [ ] **Step 6: เขียน `docs/reflection.md` เป็นโครงให้เติม**

หัวข้อพร้อมคำถามนำ (ไม่ต้องมีคำตอบ):
1. เกิดอะไรขึ้นในคาบนี้ — อะไรทำได้ตามแผน อะไรไม่ได้
2. ติดปัญหาอะไร และแก้อย่างไร
3. จุดที่ AI ทำผิดหรือทำเกินขอบเขต และนักศึกษาจับได้อย่างไร
4. อธิบายด้วยคำของตัวเอง: ทำไมเปิด `templates/index.html` ตรง ๆ จึงไม่เท่ากับรัน Flask
5. ฟอร์มส่งข้อมูลไป Python อย่างไร
6. แก้สมการใน `dc_bias.py` ต้องแก้ HTML ด้วยหรือไม่ เพราะอะไร
7. ทำไมผลนอก Active Region ต้องมี Warning

- [ ] **Step 7: ตรวจรับครบวงจร**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: `Ran 21 tests ... OK` (0 failures, 0 errors)

Run: `.\.venv\Scripts\python.exe -m flask --app app run` แล้วตรวจในเบราว์เซอร์ 4 กรณี:
1. ค่าตัวอย่าง → ACTIVE + ตัวเลขตรงตาราง
2. `R1 = 0` → error "R1 ต้องมากกว่า 0"
3. `R2 = 1k` → CUTOFF + warning
4. `RC = 10k` → SATURATION + warning

- [ ] **Step 8: Commit**

```bash
git add README.md AGENTS.md docs/ requirements.txt
git commit -m "docs: add README, AGENTS, design note, validation and reflection skeleton"
```

- [ ] **Step 9: Publish และ Push ด้วย GitHub Desktop**

เปิด GitHub Desktop → เลือก repo นี้ → **Publish repository** (เอา *Keep this code private* **ออก** เพื่อให้เป็น Public)
→ ตรวจแท็บ History ว่ามี 5 commits → กด **Push origin** → คัดลอก URL และ SHA ล่าสุดส่ง Moodle

---

## Self-Review

**1. Spec coverage**

| Spec | Task |
|---|---|
| โครงไฟล์ multi-file (§7.1) | Task 1, 3, 4, 5 |
| `dc_bias.py` ไม่ import Flask (§7.2) | Task 1 (Global Constraints + AGENTS.md) |
| ค่าเริ่มต้นฟอร์ม (§7.4) | Task 3 (`DEFAULTS`), Task 4 (template) |
| `GET /`, `POST /calculate` (§7.5) | Task 4 |
| Region logic (§7.6) | Task 2 |
| Validation (§7.7) | Task 3 |
| หน่วย V/mA/µA (§7.8) | Task 4 Step 4 |
| UI ไทย ไม่มี JS (§7.9) | Task 4 |
| `unittest` (§7.10) | Task 1, 3, 4 |
| Flask เท่านั้น (§7.11) | Task 1 Step 2, Task 5 Step 1 |
| `.gitignore` (§7.12) | Task 1 Step 2 |
| เอกสาร (§7.13–7.15) | Task 5 |
| Public repo (§7.14) | Task 5 Step 9 |
| สมการ + reference (§8) | Task 1 Step 3, Task 5 Step 5 |
| A1–A7 (§9) | Task 4 (A1,A2,A6), Task 3 (A4), Task 2 (A5), Task 1 (A3), Task 5 (A7) |

ไม่มีช่องว่าง

**2. Step scan** — ทุก step มี action เดียวและผลตรวจได้; ไม่มี "handle edge cases" หรือ "TBD";
ไม่มี body ของฟังก์ชันที่ signature + test กำหนดไว้แล้ว (ยกเว้น `calculate_dc_bias` ที่มีสมการระบุชัดตาม spec)

**3. Type consistency** — `BiasInput`/`BiasResult` ใช้ชื่อ field เดียวกันตลอด (Task 1 → 2 → 4);
`collect_inputs` คืน tuple `(BiasInput | None, list[str])` ตรงกับที่ Task 4 ใช้;
`REGION_*` constants นิยาม Task 1 ใช้ Task 2 และ template

**4. Review Focus** — ทั้ง 5 ข้อมี test ใน Task 3 (`test_zero_resistance_reports_error_not_division_by_zero`,
`test_kilo_uppercase_and_decimal`, `test_mega`, `test_whitespace_trimmed`, `test_negative_raises`,
`test_vbe_not_below_vcc_reports_error`, `test_empty_form_reports_all_seven_fields`) และ Task 4
(`test_post_empty_form_shows_errors`, `test_post_invalid_input_shows_error_without_crash`)

**5. Proportion** — แผนยาวกว่า spec เล็กน้อยเพราะมี test code ครบ (จำเป็นต่อ TDD) แต่ไม่มี body
ของ implementation ที่ test กำหนดได้เอง
