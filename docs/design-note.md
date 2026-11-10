# Design Note — BJT DC Bias Web App

## สถาปัตยกรรม

```
Browser
  │  GET /            → ฟอร์มพร้อมค่าเริ่มต้น
  │  POST /calculate  → ฟอร์ม + ผลลัพธ์
  ▼
app.py (Flask)
  ├─ parse_resistance / parse_float   แปลงหน่วยและตัวเลข
  ├─ collect_inputs                   validation → BiasInput
  └─ calculate_dc_bias(BiasInput) ───┐
                                     ▼
                              dc_bias.py
                              สมการ DC bias ล้วน
                              คืน BiasResult (+ region, warnings)
                                     │
  templates/index.html ◄─────────────┘
  static/style.css
```

### เส้นทางข้อมูล

1. `GET /` → `index()` render `index.html` ด้วย `DEFAULTS`
2. `POST /calculate` → `collect_inputs(request.form)`
   - ถ้ามี error → render หน้าเดิม + `<ul class="errors">` (HTTP 200)
   - ถ้าผ่าน → `calculate_dc_bias()` → render ผลลัพธ์ + badge region + warnings

## เหตุผลที่แยกชั้น

- `dc_bias.py` test ได้โดยไม่ต้องมี Flask และไม่มีทางรู้จัก HTML
- เปลี่ยน UI ภายหลัง (เช่นเพิ่มกราฟ AC ใน W3+) ไม่ต้องแตะสมการ
- Validation และ parsing อยู่ในชั้น app เพราะเป็นเรื่องของ input ผู้ใช้
  ไม่ใช่ฟิสิกส์ของวงจร
- Template ไม่มีสมการ — ตัวเลขทุกตัวมาจาก `BiasResult`

## ทางเลือกที่ตัดทิ้ง

| ทางเลือก | เหตุผลที่ไม่เลือก |
|---|---|
| JSON API + `fetch` | ต้องเขียน JavaScript และจัดการ error สองชั้น เสี่ยงพังเงียบ เกินเวลาคาบ |
| SPA (React ฯลฯ) | เกินขอบเขต Lab 02 มาก และไม่ได้คะแนนเพิ่ม |
| Clamp `VCE` ที่ `VCE(sat)` | ผิดสมมติฐาน Forward-Active และต้องเพิ่มสมการ/test โดยไม่จำเป็น |
| Dropdown หน่วย Ω/kΩ ต่อช่อง | ฟอร์มยาวขึ้น 4 dropdown ผู้ใช้กดมากขึ้น |
| รับค่าเป็น Ω ล้วน | ไม่ตอบข้อกำหนดเรื่องการแปลง `kΩ` → `Ω` |

## การตัดสินใจเรื่องหน่วย

- เก็บทุกอย่างใน `dc_bias.py` เป็น SI (V, A, Ω)
- แปลงเฉพาะตอนแสดงผล:
  - แรงดัน → V, 3 ตำแหน่ง
  - `IC`, `IE` → mA, 3 ตำแหน่ง
  - `IB` → **µA**, 3 ตำแหน่ง (ถ้าเป็น mA จะเหลือ 0.012 mA = 2 นัยสำคัญ)
- `parse_resistance` รับ `100000`, `100k`, `100K`, `2.2k`, `1M`
  โดย mega ใช้ `M` ตัวใหญ่เท่านั้น เพื่อไม่ให้ชนกับ milli ในอนาคต

## พฤติกรรมนอก Forward-Active

- `VTH <= VBE` → CUTOFF: `IB = IC = IE = 0`, `VE = 0`, `VB = VTH`, `VC = VCE = VCC`
- `VCE < 0.3 V` → SATURATION (near): รายงานค่าดิบตามสมการ + warning
- ไม่ clamp ค่าใด ๆ — ผู้ใช้เลือก Approach A เพื่อความโปร่งใสและตรงกับ handout

## ข้อจำกัดที่รู้ตัว

- `β` และ `VBE` คงที่ ไม่มี temperature model
- เกณฑ์ saturation เป็น heuristic `0.3 V` ไม่ใช่ `VCE(sat)` จาก datasheet
- หน้าเว็บกะพริบตอน submit เพราะเป็น full-page POST (แลกมากับความเรียบง่าย)
