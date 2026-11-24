# คำตอบเตรียมตรวจรายบุคคล — Lab 04

อ้างอิงโค้ดจริงใน repo นี้ (ไม่ใช่คำตอบจำจากใบงาน). ตอบสั้น ๆ ด้วยคำของตัวเองตอน TA ถาม.

## 1. โปรแกรม Python ส่งอะไรให้ ngspice และรับผลกลับมาอย่างไร?

`spice_engine.build_netlist()` สร้าง **netlist ข้อความ** สำหรับวงจร CE voltage-divider
(แหล่งจ่าย, `CIN/COUT`, `R1/R2/RC/RE/RL`, `Q1`, model card `t2n2222`) แล้วเลือกบรรทัด
วิเคราะห์ `.op`, `.ac dec 20 1 10MEG` หรือ `.tran ...` ตาม dropdown จากนั้น
`run_simulation()` เขียน `circuit.cir` ลง `TemporaryDirectory` และเรียก
`subprocess.run([exe, "-b", "-o", "run.log", "-r", "run.raw", "circuit.cir"], cwd=..., timeout=30)`
**ไม่ใช้ `shell=True`** ผลกลับมาทางไฟล์ `run.raw` (ASCII) ที่ `parse_raw()` อ่านเป็น
plot/point แล้วคำนวณค่า DC/gain/phase/waveform; `run.log` ใช้ตรวจ error และเก็บหลักฐาน
เวอร์ชันอ่านจาก `ngspice --version` (`spice_engine.py:165-194, 366-413`).

## 2. เหตุใดกราฟ `.ac` และ `.tran` จึงไม่ใช่สิ่งเดียวกัน?

`.ac` เป็นการวิเคราะห์ small-signal ใน **โดเมนความถี่**: ngspice sweep 1 Hz–10 MHz
แล้วให้ `Vin/Vout` เป็นจำนวนเชิงซ้อนทั้งแ amplitude และ phase → เอามาพล็อต Bode
(Gain dB, Phase °) และหา fL/fH ที่ −3 dB (ถ้าไม่มีจุดตัดให้รายงาน
`not determined in sweep range`) ส่วน `.tran` เป็นการวิเคราะห์ **โดเมนเวลา** แบบ
large-signal จากแหล่ง `SIN(0 amplitude frequency)` → ได้ `v(t)` ของ Vin/Vout จริง
แล้ววัด peak, period, gain และ phase จาก 2–3 รอบสุดท้ายที่ค่าคงตัวแล้ว
(`spice_engine.py:186-190, 294-363`) คนละแกน คนละหน่วย และคนละคำถาม engineering.

## 3. ถ้าเปลี่ยน Amplitude แต่กราฟไม่เปลี่ยน คุณจะตรวจข้อมูลตรงไหนก่อน?

ลำดับตรวจ: (1) netlist ที่โชว์ใน `<details>` ว่าบรรทัด `VIN src 0 DC 0 AC ... SIN(0 ... ...)`
เปลี่ยนไหม (2) ช่องฟอร์ม `name="amplitude"` ถูกส่งมาและผ่าน `validate_spice_input()` ไหม
(3) ตาราง `Vin peak` ในผล Transient เปลี่ยนไหม (4) จำนวนจุด/ค่าใน `run.raw` ผ่าน
`parse_raw()` เปลี่ยนไหม (5) SVG `<polyline points="...">` ถูกสร้างจาก array นั้นจริงไหม
(`app.py:311-330`, `plots.py:19-109`) ถ้า netlist เปลี่ยนแต่กราฟไม่เปลี่ยน แปลว่ามีการ
hard-code/cache; ถ้า netlist ไม่เปลี่ยน แปลว่า browser ส่งค่เก่าหรือผู้ใช้แก้คนละช่อง.

## 4. Impeccable เปลี่ยนอะไรได้ และไม่ควรเปลี่ยนอะไร?

เปลี่ยนได้: โครงสร้าง/ hierarchy, spacing, typography, color token, contrast, focus ring,
label และ error copy, responsive layout, state ของปุ่ม/ตาราง/กราฟ — โดยยังเป็นหน้าเดียว
dropdown เดียวเหมือนเดิม ไม่ควรเปลี่ยน: ค่าที่คำนวณได้, netlist, model card, การเรียก
ngspice, ข้อมูลที่ parse จาก `run.raw`, สมการใน `dc_bias.py`, หน่วย, แหล่งที่มา
(netlist/log provenance) และสถานะ NOT RUN ของ mobile หลังตรวจแล้วต้องรัน test 54 ตัว
และเทียบ B2–B6 ซ้ำเพื่อยืนยันว่า UI ไม่กระทบผลคำนวณ.

## 5. คุณรู้ได้อย่างไรว่า Bode Plot เป็นผลจำลองจริง ไม่ใช่ Mock Data?

เพราะทุกจุดของ `<polyline>` ถูกสร้างโดย `plots.line_chart()` จาก array ที่
`parse_raw()` อ่าน `run.raw` ที่ ngspice เขียนในรันนั้น (`plots.py:34-38, 95-102`) ไม่มี
gain/frequency/phase ถูก hard-code ใน template; ในหน้าเว็บมี netlist จริงพร้อมบรรทัด
`.ac dec 20 1 10MEG` และท้าย `run.log` จากรันเดียวกัน; เปลี่ยน amplitude/frequency/RE
แล้ว peak/period/netlist เปลี่ยนตาม (B3, B6); ถ้า solver หายหน้าเว็บขึ้น `Status: Error`
และไม่แสดงกราฟหรือผล Success เลย (B7) — กราฟจึงตามข้อมูล ไม่ใช่ภาพตกแต่ง.
