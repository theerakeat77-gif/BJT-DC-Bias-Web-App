# ชุดข้อมูลเตรียมทำ Lab 04 — BJT CE Amplifier Simulator

จัดทำ 2026-11-24 · อ้างอิงจาก `Lab04_BJT_Amplifier_Simulator_2-2569.html` (ใบงาน Lab 4)
และข้อมูลเดิมของ repo นี้ (`README.md`, `docs/validation.md`, `docs/lab03-handout.html`, `dc_bias.py`)

> ไฟล์ที่ใช้ได้จริงกับโปรแกรม: **`docs/lab04-fixture.json`** (ข้อมูลแบบ machine-readable)
> เอกสารนี้เป็นคำอธิบายและตารางอ่านง่ายเท่านั้น

---

## 1. สิ่งที่เปิดและตรวจแล้วตอนนี้

- รัน Flask จาก repo แลป 3 ด้วย `.venv` ที่สร้างใหม่: `28 tests OK`
- เปิดหน้าแอปที่ **<http://127.0.0.1:5000/>** และกด Calculate ด้วยชุดค่าเดิมแล้ว
  ผลที่หน้าแสดง: `ACTIVE`, VB 1.942 V, VE 1.242 V, VC 9.294 V, VCE 8.052 V,
  IC 1.230 mA, IE 1.242 mA, IB 12.299 µA — ตรง `docs/validation.md`
- `ngspice` **ยังไม่พบใน PATH**, และยังไม่พบ Starter Kit/ไฟล์ BJT model
  (`.cir/.mod/.lib`) ในเครื่องหรือ repo นี้ → ยังรัน `.op/.ac/.tran` ไม่ได้
- `git` ไม่ได้อยู่ใน PATH ของ PowerShell ที่ใช้ตรวจ → ต้องเพิ่ม PATH หรือใช้ GitHub Desktop
  ตอนจะ commit/push

## 2. สรุปสิ่งที่ใบงาน Lab 4 ต้องการ (ศึกษา HTML แล้ว)

| เรื่อง | สิ่งที่ต้องทำ | หมายเหตุ |
|---|---|---|
| คงของเดิม | DC Bias 3 โหมด (Divider / Fixed / Emitter) + 28 tests | ห้ามทำเสีย |
| เพิ่มใหม่ | `spice_engine.py` เรียก `ngspice` ผ่าน `subprocess` สำหรับ **CE Voltage Divider หนึ่งวงจรอ้างอิง** | `.op`, `.ac`, `.tran` |
| ผลที่ต้องเห็น | ตัวเลข + กราฟจริง, engine status, ชื่อ model, หน่วย, แยกผล Analytical กับ SPICE | ห้าม mock/hard-code |
| UI | ฟอร์มมีหน่วย, เลือก analysis mode, error state, แก้ด้วย Impeccable, ตรวจ desktop/mobile | กราฟต้องอ่านได้ |
| ตรวจรับ | B1–B8 ใน `docs/validation.md` พร้อมหลักฐาน | ไม่รันจริงต้องเขียน NOT RUN |
| ส่งงาน | Repo URL + commit SHA, README, validation record, screenshot, บันทึก AI ทำอะไร/นักศึกษาตรวจอะไร | ใบงาน §10 |

ข้อควรระวังจากใบงาน: ภาพ wireframe และกราฟใน HTML เป็น **ตัวอย่างหน้าจอ ไม่ใช่ผล ngspice**;
ห้ามนำตัวเลข Gain / fL / fH / waveform จากภาพมาใช้เป็นผลจำลอง

## 3. Input Fixture — วงจร CE อ้างอิง

ที่มา: ใบงาน Lab 4 §06 (Baseline Reference)

| Parameter | ค่า | หน่วย / รูปแบบในฟอร์ม |
|---|---|---|
| VCC | 12 | V (`12`) |
| R1 | 100 kΩ | `100k` = 100000 Ω |
| R2 | 22 kΩ | `22k` = 22000 Ω |
| RC | 2.2 kΩ | `2.2k` = 2200 Ω |
| RE | 1 kΩ | `1k` = 1000 Ω (**ไม่มี CE bypass**) |
| RL | 10 kΩ | 10000 Ω |
| Cin / Cout | 10 µF / 10 µF | coupling capacitor |
| Source | 10 mV peak, 1 kHz | `SIN(...)`, ใช้กับ `.tran` |
| β / VBE | 100 / 0.70 V | ค่าอ้างอิงเชิงวิเคราะห์จาก Lab 3 |
| BJT model | **ยังไม่กำหนด** | ต้องได้ชื่อ + parameter จาก Instructor Starter Kit |

จุดวัดที่ต้องระบุให้ชัดใน netlist: `Vin` = หลัง Cin ฝั่ง base,
`Vout` = ฝั่ง collector ผ่าน Cout ที่ RL

## 4. ค่าอ้างอิงเชิงวิเคราะห์ (ใช้เทียบ ไม่ใช่ผล SPICE)

คำนวณด้วย `dc_bias.py` ของ repo นี้โดยตรง (แบบจำลอง β/VBE คงที่) — สามารถใช้เป็น oracle
ตรวจ regression B1 และเป็นจุดเทียบทิศทางกับผล SPICEได้

| กรณี | โหมด / การเปลี่ยน | IC | VCE | หมายเหตุ |
|---|---|---:|---:|---|
| A1 | Divider baseline | 1.229858 mA | 8.052155 V | ACTIVE |
| A2 | Fixed, RB = 1 MΩ | 1.130000 mA | 9.514000 V | ACTIVE |
| A3 | Emitter, RB = 1 MΩ, RE = 1 kΩ | 1.026340 mA | 8.705450 V | ACTIVE |
| A4 | Emitter, เฉพาะ RE → 2 kΩ | 0.940100 mA | 8.032779 V | IC ลดจาก A3 |
| B3a | Divider, เฉพาะ RE → 2 kΩ | 0.665326 mA | 9.192326 V | IC ลด, VCE เพิ่ม |
| B3b | Divider, เฉพาะ RE → 470 Ω | 2.234919 mA | 6.022261 V | IC เพิ่ม, VCE ลด |
| Reg | R2 → 1 kΩ | 0 | 12 V | CUTOFF |
| Reg | RC → 10 kΩ | 1.229858 mA | −1.540738 V | SATURATION (ค่าดิบ ไม่ clamp) |

ค่ารายละเอียดทั้งหมด (VB, VE, VC, IB, IE, VTH, RTH) อยู่ใน `docs/lab04-fixture.json`
ภายใต้ `analytical_reference.cases`

## 5. ข้อมูล SPICE ที่รันจริงแล้ว

`spice_capture_template` ยังคงเป็นโครงเปล่า (`null` / array ว่าง) เพื่อใช้เป็นแม่แบบ
กันการเอาค่าปลอมมาปนกับค่าจริง ส่วนผลที่รันได้จริงเก็บไว้ภายใต้
**`spice_observed_local_run`** ใน `lab04-fixture.json` แยกจากค่าอ้างอิงเชิงวิเคราะห์

| หมวด | สิ่งที่เก็บ | ผลย่อ |
|---|---|---|
| DC `.op` baseline | engine, model, VB/VE/VC/VCE/IC/IE/IB | ngspice-47, `t2n2222`, IC 1.3211 mA, VCE 7.7622 V |
| DC เปลี่ยน RE | 2 kΩ / 470 Ω | IC 0.7097 / 2.4433 mA; VCE 9.0077 / 5.4675 V |
| AC `.ac` | frequency/gain/gain_db/phase (sweep 1–10 MHz, ตัวอย่าง 81→81 จุด) | gain สูงสุด 4.87 dB @ 5012 Hz, fL 1.41 Hz, fH `not determined in sweep range` |
| Transient `.tran` | time/Vin/Vout ตัวอย่าง 220 จุด + peak/phase | 10 mV/1 kHz → Vin 10 mV, Vout 17.5 mV, phase −179.9° |
| เปลี่ยน source | 20 mV/10 kHz | Vin 20 mV, Vout 35 mV, period 0.1 ms |

Engine รันแบบ batch `ngspice -b -o run.log -r run.raw circuit.cir` ผ่าน
`subprocess.run([...], timeout=..., cwd=tempdir)` **ไม่ใช้ `shell=True`**
แล้ว parse `run.raw` ที่ solver เขียนจริง; ไม่มีตัวเลขไหนถูก hard-code ใน template

## 6. ผลตรวจรับ B1–B8 (ดูตารางฉบับเต็มใน `docs/validation.md`)

| Case | สถานะจริง | หลักฐานสั้น |
|---|---|---|
| B1 | PASS | เลือก `divider/fixed/emitter` ใน dropdown เดียวแล้วได้ผลตรงตารางข้อ 4 ทุกค่า |
| B2 | PASS | เลือก `ce-dc` ใน dropdown เดียว โชว์ status/model/version + netlist/log จริง |
| B3 | PASS | เปลี่ยน RE แล้ว IC/VCE เปลี่ยนตามทิศทาง |
| B4 | PASS | กราฟ gain/phase มี 141 จุดต่อเส้นจาก `run.raw` |
| B5 | PASS | waveform 504 จุด/เส้น, phase −179.9° ที่ 10 mV/1 kHz |
| B6 | PASS | peak และ period เปลี่ยนตาม source ที่กรอก |
| B7 | PASS | RE = 0 → `Status: Error`, ไม่มีผล Success |
| B8 | PASS | desktop 1000/1440 px + mobile 390×844 ด้วย headless Chrome CDP; `scrollWidth=390`, chart กว้าง 302 px, Impeccable manual install + detector `[]` |

## 7. สิ่งที่ยังต้องทำต่อ

1. รับ Instructor Starter Kit (netlist + BJT model) แล้วแทนที่
   `MODEL_CARD` ใน `spice_engine.py` และอัปเดต validation ให้ตรงชื่อจริง
2. รับ Starter Kit แล้วทดสอบซ้ำกับ model card ของผู้สอน (ถ้าต้องการเท่าตัวเลขใน handout)
3. push commit Lab 4 `83a479b41d98a1ea5835baaabbad1242a3eb648f` ขึ้น origin/main **สำเร็จ** (remote = `21fa55c...`, repo Public; SHA record อยู่ใน README/validation แล้ว)
4. แก้ `docs/reflection.md` ให้เป็นภาษาของตัวเองก่อนส่ง; AI ทำร่างข้อเท็จจริงให้แล้วแต่ไม่ควรแต่งความเห็นส่วนตัว

