    remainder = total_cents - sum(parts)
    order = sorted(range(len(raw)), key=lambda i: (raw[i] - parts[i], -i), reverse=True)
    for i in order[:remainder]:
        parts[i] += 1
    return parts


st.title("🍽️ FoodShare")
st.caption("แชร์ค่าอาหารกับเพื่อน ง่าย สวย และคำนวณได้ในหน้าเดียว 💗")

with st.container(border=True):
    st.subheader("👥 สมาชิก")
    people_count = st.number_input("จำนวนคน", min_value=1, max_value=30, value=2, step=1)
    names = []
    for i in range(int(people_count)):
        name = st.text_input(f"ชื่อคนที่ {i + 1}", value=f"คนที่ {i + 1}", key=f"member_{i}").strip()
        names.append(name or f"คนที่ {i + 1}")
    if len(set(names)) != len(names):
        st.error("ชื่อสมาชิกต้องไม่ซ้ำกัน กรุณาแก้ไขชื่อก่อนคำนวณ")

mode = st.radio("วิธีแบ่งค่าอาหาร", ["หารเท่ากัน", "จ่ายตามรายการที่กิน"], horizontal=True)

with st.container(border=True):
    st.subheader("🍜 รายการอาหาร")
    item_count = st.number_input("จำนวนรายการอาหาร", min_value=1, max_value=100, value=2, step=1)
    items = []
    for i in range(int(item_count)):
        st.markdown(f"**รายการที่ {i + 1}**")
        col1, col2 = st.columns([2, 1])
        with col1:
            item_name = st.text_input("ชื่ออาหาร", value="ข้าวผัด" if i == 0 else "น้ำดื่ม" if i == 1 else "", key=f"food_{i}")
        with col2:
            price = st.number_input("ราคา (บาท)", min_value=0.0, max_value=1000000.0, value=60.0 if i == 0 else 30.0 if i == 1 else 0.0, step=5.0, format="%.2f", key=f"price_{i}")
        if mode == "จ่ายตามรายการที่กิน":
            eaters = st.multiselect("ใครกินรายการนี้? (เลือกได้หลายคน)", options=list(range(len(names))), default=list(range(len(names))), format_func=lambda idx: names[idx], key=f"eaters_{i}")
        else:
            eaters = list(range(len(names)))
        items.append({"name": item_name.strip() or f"อาหารที่ {i + 1}", "price": Decimal(str(price)), "eaters": eaters})

with st.container(border=True):
    st.subheader("🏷️ ส่วนลดและค่าบริการ")
    discount_percent = st.number_input("ส่วนลด (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
    service_enabled = st.checkbox("คิด Service Charge 10%", value=False)
    vat_enabled = st.checkbox("คิด VAT 7%", value=False)
    tip = st.number_input("ทิปพนักงาน (บาท)", min_value=0.0, max_value=1000000.0, value=0.0, step=5.0)
    st.caption("คำนวณค่าบริการจากยอดหลังส่วนลด และ VAT จากยอดหลังส่วนลดรวมค่าบริการ")

if st.button("🧮 คำนวณค่าอาหาร", type="primary", use_container_width=True):
    if len(set(names)) != len(names):
        st.error("กรุณาแก้ชื่อสมาชิกที่ซ้ำกัน")
    elif mode == "จ่ายตามรายการที่กิน" and any(not item["eaters"] and item["price"] > 0 for item in items):
        st.error("รายการอาหารที่มีราคามากกว่า 0 บาท ต้องเลือกผู้รับผิดชอบอย่างน้อย 1 คน")
    else:
        food_total = sum((item["price"] for item in items), Decimal("0"))
        discount = food_total * Decimal(str(discount_percent)) / Decimal("100")
        discounted = food_total - discount
        service = discounted * Decimal("0.10") if service_enabled else Decimal("0")
        vat = (discounted + service) * Decimal("0.07") if vat_enabled else Decimal("0")
        total = discounted + service + vat + Decimal(str(tip))
        total_satang = cents(total)

        if mode == "หารเท่ากัน":
            weights = [Decimal("1")] * len(names)
        else:
            weights = [Decimal("0")] * len(names)
            for item in items:
                if item["eaters"]:
                    share = item["price"] / Decimal(len(item["eaters"]))
                    for person_index in item["eaters"]:
                        weights[person_index] += share
            # If no food was ordered, share any tip equally.
            if sum(weights) == 0:
                weights = [Decimal("1")] * len(names)

        shares_satang = allocate(total_satang, weights)
        st.session_state["receipt"] = {
            "names": names[:],
            "items": [(item["name"], baht(item["price"])) for item in items],
            "food": baht(food_total),
            "discount": baht(discount),
            "service": baht(service),
            "vat": baht(vat),
            "tip": baht(tip),
            "total": baht(Decimal(total_satang) / 100),
            "shares": shares_satang,
            "mode": mode,
        }

if "receipt" in st.session_state:
    receipt = st.session_state["receipt"]
    st.subheader("🧾 สรุปค่าอาหาร")
    for item_name, price in receipt["items"]:
        st.write(f"• {item_name} — {price} บาท")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("ค่าอาหาร", f'{receipt["food"]} ฿')
        st.metric("ส่วนลด", f'{receipt["discount"]} ฿')
        st.metric("Service Charge", f'{receipt["service"]} ฿')
    with col2:
        st.metric("VAT", f'{receipt["vat"]} ฿')
        st.metric("ทิป", f'{receipt["tip"]} ฿')
        st.metric("รวมทั้งหมด", f'{receipt["total"]} ฿')

    st.subheader("💸 แต่ละคนต้องจ่าย")
    for i, name in enumerate(receipt["names"]):
        st.success(f'{name}: {receipt["shares"][i] / 100:,.2f} บาท')

    st.subheader("💵 ตรวจสอบเงินทอน")
    for i, name in enumerate(receipt["names"]):
        paid = st.number_input(f"{name} จ่ายมา (บาท)", min_value=0.0, max_value=10000000.0, value=0.0, step=10.0, key=f"paid_{i}")
        change = cents(paid) - receipt["shares"][i]
        if change > 0:
            st.info(f"{name} ได้เงินทอน {change / 100:,.2f} บาท")
        elif change < 0:
            st.warning(f"{name} ยังขาด {-change / 100:,.2f} บาท")
        else:
            st.success(f"{name} จ่ายพอดีแล้ว")

    lines = ["FoodShare - สรุปค่าอาหาร", "=" * 32]
    lines += [f"{name}: {price} บาท" for name, price in receipt["items"]]
    lines += ["-" * 32, f'ค่าอาหาร: {receipt["food"]} บาท', f'ส่วนลด: {receipt["discount"]} บาท', f'Service Charge: {receipt["service"]} บาท', f'VAT: {receipt["vat"]} บาท', f'ทิป: {receipt["tip"]} บาท', f'ยอดรวม: {receipt["total"]} บาท', "", "ยอดที่ต้องจ่าย"]
    lines += [f"{name}: {satang / 100:,.2f} บาท" for name, satang in zip(receipt["names"], receipt["shares"])]
    st.download_button("📥 ดาวน์โหลดสรุปค่าอาหาร", data="\n".join(lines).encode("utf-8-sig"), file_name="foodshare_receipt.txt", mime="text/plain", use_container_width=True)
    st.caption("หากแก้ไขข้อมูลด้านบน ให้กดคำนวณค่าอาหารอีกครั้งเพื่ออัปเดตใบสรุป")

st.divider()
st.caption("Made with 💗 Python & Streamlit | FoodShare")
