# Impeccable — manual install และหลักฐานการใช้ (Lab 04)

สภาพแวดล้อมนี้ไม่มี `node`/`npx` จึงไม่ใช้ `npx impeccable install` แต่ติดตั้งแบบ
manual copy ตามที่ Impeccable รองรับสำหรับ OpenCode:

- Source: <https://github.com/pbakaus/impeccable> (main, skill version **4.10.0**)
- ตำแหน่งใน repo: `.opencode/skills/impeccable/` และ `.opencode/commands/impeccable.md`
- Launcher ที่ใช้จริง: `.opencode\skills\impeccable\scripts\impeccable.cmd` (binary ส่งมากับ skill ไม่ต้องลง Node)
- ผล `impeccable context`: `NO_PRODUCT_MD` / `MANUAL_DETECTOR_REQUIRED` เพราะ repo นี้ยังไม่มี
  `PRODUCT.md`; งานนี้เป็น scoped refinement ของ UI เดิมจึงไม่บังคับ new-work flow

## คำสั่งที่ใช้

```powershell
.opencode\skills\impeccable\scripts\impeccable.cmd context
.opencode\skills\impeccable\scripts\impeccable.cmd detect --json templates/index.html
.opencode\skills\impeccable\scripts\impeccable.cmd detect --json http://127.0.0.1:5000/ --viewport 1440x900
.opencode\skills\impeccable\scripts\impeccable.cmd detect --json http://127.0.0.1:5000/ --viewport 390x844
.opencode\skills\impeccable\scripts\impeccable.cmd shot http://127.0.0.1:5000/ --viewport 1440x900,390x844 --out docs\captures\impeccable-review-after
```

## Critique แบบ isolated A/B (รันจริงก่อนปรับ UI)

ส่ง assessment แยกกันให้ subagent สองตัวเพื่อไม่ให้ผลของตัวหนึ่งไปล็อกอีกตัว:

- **Assessment A (design review)**: Nielsen heuristic เฉลี่ยได้ 22/40 (acceptable band),
  cognitive load 7/8 fail; findings สำคัญคือโชว์พารามิเตอร์ 13 ช่องในทุกโหมด,
  ปุ่ม `Calculate / Run` อยู่ที่ `y=961` ต่ำกว่า viewport 905 px, ไม่มี pending state,
  `fL 1.412537544622754 Hz` ไม่ได้ format, และมี CSS ตายจากฟอร์มเก่า (`.simulator`, `.analysis-choice`)
- **Assessment B (detector + browser)**: `detect --json templates/index.html` exit 2,
  2 findings (`flat-type-hierarchy`, `em-dash-overuse` advisory) พร้อม stderr ว่า detector
  อ่าน stylesheet ไม่ได้เพราะเป็น Jinja `{{ url_for(...) }}`; live overlay ผ่าน CDP พบ
  `nested-cards` ที่ `fieldset.param-group`; console error จริงมีเพียง `favicon.ico` 404
- ข้อจำกัดที่บันทึกตรง ๆ: subagent ไม่ได้รับสิทธิ์ browser tool และโมเดล subagent ไม่รับ image input
  จึงใช้ headless Chrome + CDP แทนและยืนยัน DOM/console แทนการอ่านพิกเซล; ไม่ได้อ้างว่าเป็น Playwright

## Polish ที่ใช้จริง (ไม่แตะค่าคำนวณ/สมการ/ngspice)

- ยุบ `.param-group` ให้เป็น divider แทน card-z้อน-card → live detector หายไป
- CSS-only progressive disclosure ด้วย `:has(#mode option:checked)` ตามโหมด; ยังเป็นฟอร์มเดียว
  dropdown เดียว ปุ่มเดียว และ input ที่ซ่อนยังส่งค่าเดิมผ่าน POST (ตรวจ 6 โหมดแล้ว)
- ย้ายปุ่มเข้า `.form-actions` แบบ sticky → desktop `top` จาก 961 เหลือ 656 px
- ปรับ hierarchy (`h1` 1.5rem → 2rem), spacing, focus/hover/active/disabled, `select` เต็มความกว้าง
- เพิ่ม favicon แบบ data URI → console error หมด (`[]`)
- format `fL/fH`: ตัวเลขเป็น 4 sig figs (`1.413 Hz`), ข้อความ `not determined in sweep range`
  ไม่เติมหน่วย `Hz` ต่อท้าย
- เพิ่ม `role="status" aria-live="polite"` ให้ status banner, ปรับ `inputmode="decimal"` ให้ทุกช่องตัวเลข

## ผลหลัง polish

- `impeccable detect` แบบ live Desktop 1440×900 และ Mobile 390×844: `[]`, **exit 0** ทั้งสองครั้ง
  (CLI แบบอ่าน source ยังฟ้อง `flat-type-hierarchy`/`em-dash-overuse` เพราะอ่าน Jinja stylesheet ไม่ได้)
- `docs/captures/impeccable-before.png` vs `docs/captures/impeccable-after.png`
- `docs/captures/impeccable-review-after/390x844.png` — viewport จริงจาก `impeccable shot`
- รัน `54 tests` ซ้ำหลังปรับ UI → **OK**; B2–B7 ให้ค่าเดิมทุกตัว (ดู `docs/validation.md`)
- desktop `innerWidth=1000`, `scrollWidth=985`, 1 select/6 options/1 button, console `[]`
- mobile CDP 390×844: `scrollWidth=clientWidth=390`, select/button กว้าง 320 px,
  result มี 2 SVG chart กว้าง 302 px อยู่ใน viewport (ดู JSON ใน `docs/validation.md`)
