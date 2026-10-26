import os
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from xml.sax.saxutils import escape

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

st.set_page_config(page_title="FoodShare | หารค่าอาหาร", page_icon="🍽️", layout="centered")
st.markdown("""
<style>
:root {color-scheme:light;}
.stApp {background:#fff7fa; color:#36303a;}
.block-container {max-width:900px; padding-top:2rem; padding-bottom:4rem;}
h1,h2,h3 {color:#a43169;}
div.stButton > button[kind="primary"], div.stDownloadButton > button[kind="primary"] {
 background:#d84f88; border-color:#d84f88; color:white;
}
div[data-testid="stMetric"] {background:white; padding:14px; border:1px solid #f4d5e2; border-radius:14px;}
</style>
""", unsafe_allow_html=True)

CENT = Decimal("0.01")

def money(value):
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)

def to_cents(value):
    return int((money(value) * 100).to_integral_value(rounding=ROUND_HALF_UP))

def baht(cents):
    return f"{cents / 100:,.2f}"

def allocate(total_cents, weights):
    """แบ่งจำนวนสตางค์ให้ตรงยอดจริง แม้มีเศษสตางค์"""
    weights = [max(0, int(w)) for w in weights]
    if not weights or sum(weights) == 0:
        return [0] * len(weights)
    sign = 1 if total_cents >= 0 else -1
    amount = abs(total_cents)
    denominator = sum(weights)
    base = [(amount * w) // denominator for w in weights]
    left = amount - sum(base)
    ranking = sorted(range(len(weights)), key=lambda i: (-(amount * weights[i] % denominator), i))
    for i in ranking[:left]:
        base[i] += 1
    return [sign * n for n in base]

def receipt_pdf(rows, people, shares, subtotal, discount, service, vat, tip, total, method):
    font_path = os.path.join("fonts", "Sarabun-Regular.ttf")
    if not os.path.isfile(font_path):
        raise FileNotFoundError("กรุณาเพิ่ม fonts/Sarabun-Regular.ttf ใน GitHub ก่อนดาวน์โหลด PDF")
    if "Sarabun" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("Sarabun", font_path))
    normal = ParagraphStyle("FSNormal", fontName="Sarabun", fontSize=10, leading=15, textColor=colors.HexColor("#36303a"))
    center = ParagraphStyle("FSCenter", parent=normal, alignment=TA_CENTER)
    heading = ParagraphStyle("FSHeading", parent=center, fontSize=20, leading=26, textColor=colors.HexColor("#a43169"))
    small = ParagraphStyle("FSSmall", parent=normal, fontSize=8, leading=12)
    right = ParagraphStyle("FSRight", parent=normal, alignment=TA_RIGHT)
    bold = ParagraphStyle("FSBold", parent=normal, textColor=colors.HexColor("#a43169"), fontSize=12)
    def p(text, style=normal):
        return Paragraph(escape(str(text)), style)
    def line(label, value, emphasize=False):
        return [p(label, bold if emphasize else normal), p(value, right)]

    content = [p("FoodShare", heading), p("ใบสรุปค่าใช้จ่าย", center),
               p(datetime.now().strftime("%d/%m/%Y %H:%M"), center),
               p("วิธีแบ่ง: " + method, center), Spacer(1, 6*mm),
               HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e8b9cc")),
               Spacer(1, 3*mm), p("รายการอาหาร", bold)]
    table_data = [[p("รายการ"), p("ราคา", right)]]
    for item in rows:
        desc = f"{item['name']}  x{item['qty']}"
        if method == "จ่ายตามรายการที่กิน":
            desc += "  (" + ", ".join(people[i] for i in item["eaters"]) + ")"
        table_data.append([p(desc, small), p(baht(item["cents"]) + " บาท", right)])
    t = Table(table_data, colWidths=[116*mm, 43*mm], hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([("VALIGN", (0,0),(-1,-1),"TOP"), ("BOTTOMPADDING",(0,0),(-1,-1),6),
                           ("LINEBELOW",(0,0),(-1,0),0.5,colors.HexColor("#e8b9cc"))]))
    content += [t, Spacer(1, 3*mm)]
    breakdown = [line("รวมค่าอาหาร", baht(subtotal)+" บาท"),
                 line("ส่วนลด", "-"+baht(discount)+" บาท"),
                 line("ค่าบริการ", baht(service)+" บาท"),
                 line("VAT", baht(vat)+" บาท"),
                 line("ทิป", baht(tip)+" บาท"),
                 line("ยอดสุทธิ", baht(total)+" บาท", True)]
    tbl = Table(breakdown, colWidths=[90*mm,69*mm], hAlign="LEFT")
    tbl.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"), ("BOTTOMPADDING",(0,0),(-1,-1),5),
                             ("LINEABOVE",(0,-1),(-1,-1),0.8,colors.HexColor("#a43169"))]))
    content += [tbl, Spacer(1, 5*mm), p("ยอดที่แต่ละคนต้องจ่าย", bold)]
    person_table = Table([line(f"{i+1}. {name}", baht(shares[i])+" บาท") for i,name in enumerate(people)] +
                         [line("รวมยอดทุกคน", baht(sum(shares))+" บาท", True)],
                         colWidths=[90*mm,69*mm], hAlign="LEFT")
    person_table.setStyle(TableStyle([("BOTTOMPADDING",(0,0),(-1,-1),6),
                                      ("LINEABOVE",(0,-1),(-1,-1),0.8,colors.HexColor("#a43169"))]))
    content += [person_table, Spacer(1, 8*mm), p("ขอบคุณที่ใช้ FoodShare", center),
                p("เอกสารสรุปค่าใช้จ่าย ไม่ใช่ใบกำกับภาษี", center)]
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=(190*mm, 270*mm),
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=13*mm, bottomMargin=13*mm)
    doc.build(content)
    return output.getvalue()

if "people_count" not in st.session_state:
    st.session_state["people_count"] = 2
if "item_count" not in st.session_state:
    st.session_state["item_count"] = 2

st.title("🍽️ FoodShare")
st.caption("คำนวณค่าอาหารง่าย ๆ หารกับเพื่อนอย่างเป็นธรรม พร้อมดาวน์โหลดบิล PDF")

st.header("👥 1. สมาชิก")
people_count = st.number_input("จำนวนคน", min_value=1, max_value=30, step=1, key="people_count")
people = []
for i in range(people_count):
    name = st.text_input(f"ชื่อสมาชิกคนที่ {i+1}", value=f"คนที่ {i+1}", key=f"person_{i}").strip()
    people.append(name or f"คนที่ {i+1}")
if len(set(people)) != len(people):
    st.warning("ชื่อสมาชิกซ้ำกัน แนะนำให้ตั้งชื่อไม่ซ้ำเพื่อให้อ่านบิลได้ง่าย")

st.header("🍛 2. รายการอาหาร")
method = st.radio("วิธีแบ่งค่าอาหาร", ["หารเท่ากัน", "จ่ายตามรายการที่กิน"], horizontal=True)
item_count = st.number_input("จำนวนรายการอาหาร", min_value=1, max_value=100, step=1, key="item_count")
items = []
for i in range(item_count):
    with st.expander(f"รายการที่ {i+1}", expanded=(i < 2)):
        name = st.text_input("ชื่ออาหาร", value=f"อาหาร {i+1}", key=f"food_{i}").strip() or f"อาหาร {i+1}"
        col1, col2 = st.columns(2)
        with col1:
            unit_price = st.number_input("ราคาต่อหน่วย (บาท)", min_value=0.0, max_value=1000000.0,
                                         value=0.0, step=1.0, format="%.2f", key=f"price_{i}")
        with col2:
            qty = st.number_input("จำนวน", min_value=1, max_value=1000, value=1, step=1, key=f"qty_{i}")
        if method == "จ่ายตามรายการที่กิน":
            eaters = st.multiselect("ใครรับประทานรายการนี้ (เลือกได้หลายคน)",
                                    options=list(range(people_count)),
                                    default=list(range(people_count)),
                                    format_func=lambda j: f"{j+1}. {people[j]}", key=f"eaters_{i}")
        else:
            eaters = list(range(people_count))
        cents = to_cents(money(unit_price) * qty)
        items.append({"name":name, "qty":qty, "cents":cents, "eaters":eaters})

st.header("🧮 3. ส่วนลดและค่าใช้จ่ายเพิ่มเติม")
col1,col2 = st.columns(2)
with col1:
    discount_pct = st.number_input("ส่วนลด (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
    service_pct = st.number_input("ค่าบริการ (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
with col2:
    vat_pct = st.number_input("VAT (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
    tip_baht = st.number_input("ทิป (บาท)", min_value=0.0, max_value=1000000.0, value=0.0, step=1.0, format="%.2f")

subtotal = sum(item["cents"] for item in items)
discount = to_cents(Decimal(subtotal)/100 * Decimal(str(discount_pct))/100)
after_discount = subtotal - discount
service = to_cents(Decimal(after_discount)/100 * Decimal(str(service_pct))/100)
vat = to_cents(Decimal(after_discount + service)/100 * Decimal(str(vat_pct))/100)
tip = to_cents(tip_baht)
total = after_discount + service + vat + tip

# คำนวณน้ำหนักค่าอาหารรายบุคคลเป็นหน่วยสตางค์
base = [0] * people_count
invalid = []
for idx,item in enumerate(items):
    if not item["eaters"]:
        invalid.append(idx+1)
        continue
    allocations = allocate(item["cents"], [1 if i in item["eaters"] else 0 for i in range(people_count)])
    base = [a+b for a,b in zip(base,allocations)]

# แบ่งยอดสุทธิตามสัดส่วนค่าอาหารของแต่ละคน (หรือหารเท่ากัน)
weights = base if method == "จ่ายตามรายการที่กิน" else [1]*people_count
if sum(weights) == 0:
    weights = [1]*people_count
shares = allocate(total, weights)

st.header("🧾 4. สรุปค่าใช้จ่าย")
if invalid:
    st.error("กรุณาเลือกผู้รับผิดชอบในรายการอาหารหมายเลข: " + ", ".join(map(str,invalid)))
else:
    a,b,c = st.columns(3)
    a.metric("ค่าอาหาร", f"{baht(subtotal)} ฿")
    b.metric("ส่วนลด", f"{baht(discount)} ฿")
    c.metric("ยอดสุทธิ", f"{baht(total)} ฿")
    with st.expander("ดูรายละเอียดการคำนวณ", expanded=True):
        st.write(f"ยอดหลังส่วนลด: **{baht(after_discount)} บาท**")
        st.write(f"ค่าบริการ: **{baht(service)} บาท**")
        st.write(f"VAT: **{baht(vat)} บาท**")
        st.write(f"ทิป: **{baht(tip)} บาท**")
        st.caption("ค่าบริการคิดจากยอดหลังส่วนลด และ VAT คิดจากยอดหลังส่วนลดรวมค่าบริการ")
    st.subheader("ยอดที่แต่ละคนต้องจ่าย")
    for i,name in enumerate(people):
        st.write(f"**{i+1}. {name}** — {baht(shares[i])} บาท")
    st.success(f"รวมยอดของสมาชิกทุกคน {baht(sum(shares))} บาท")

    with st.expander("💵 ตรวจสอบเงินทอนของแต่ละคน"):
        for i,name in enumerate(people):
            paid = st.number_input(f"{name} ชำระแล้ว (บาท)", min_value=0.0, max_value=10000000.0,
                                   value=0.0, step=1.0, format="%.2f", key=f"paid_{i}")
            diff = to_cents(paid) - shares[i]
            if diff > 0:
                st.info(f"{name}: เงินทอน {baht(diff)} บาท")
            elif diff < 0:
                st.warning(f"{name}: ยังขาด {baht(-diff)} บาท")
            else:
                st.success(f"{name}: ชำระพอดี")

    st.subheader("📄 ดาวน์โหลดใบเสร็จ PDF")
    if not os.path.isfile(os.path.join("fonts","Sarabun-Regular.ttf")):
        st.warning("ยังไม่มีฟอนต์ไทย: อัปโหลดไฟล์ fonts/Sarabun-Regular.ttf ไปยัง GitHub ก่อน จึงจะสร้าง PDF ภาษาไทยได้")
    else:
        try:
            pdf_bytes = receipt_pdf(items,people,shares,subtotal,discount,service,vat,tip,total,method)
            st.download_button("🧾 ดาวน์โหลดใบเสร็จ PDF", data=pdf_bytes,
                               file_name=f"FoodShare_Receipt_{datetime.now():%Y%m%d_%H%M}.pdf",
                               mime="application/pdf", type="primary", use_container_width=True)
        except Exception as exc:
            st.error(f"สร้าง PDF ไม่สำเร็จ: {exc}")

st.divider()
st.caption("FoodShare • โปรแกรมช่วยแบ่งค่าอาหาร • เอกสาร PDF เป็นใบสรุปค่าใช้จ่าย ไม่ใช่ใบกำกับภาษี")
