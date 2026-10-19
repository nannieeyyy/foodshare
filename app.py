import streamlit as st
from decimal import Decimal, ROUND_HALF_UP

st.set_page_config(page_title='FoodShare 🍽️', page_icon='🍽️', layout='centered')
st.markdown('''<style>.stApp{background:#fff8fb}h1,h2,h3{color:#9d315d}.stButton>button[kind="primary"]{background:#db548d;border:0;border-radius:12px}.block-container{max-width:820px;padding-top:2rem}</style>''', unsafe_allow_html=True)
st.title('🍽️ FoodShare')
st.caption('หารค่าอาหารกับเพื่อน ง่าย ๆ ในหน้าเดียว 💗')

if 'people' not in st.session_state:
    st.session_state.people = ['นันนี่', 'เพื่อน']
if "people" not in st.session_state:
    st.session_state["people"] = ["นันนี่", "เพื่อน"]

if "items" not in st.session_state:
    st.session_state["items"] = [
        {
            "ชื่ออาหาร": "ข้าวผัด",
            "ราคา": 60.0,
            "ผู้รับผิดชอบ": "ทุกคน"
        },
        {
            "ชื่ออาหาร": "น้ำดื่ม",
            "ราคา": 30.0,
            "ผู้รับผิดชอบ": "ทุกคน"
        }
    ]

    st.session_state["items"] = [
        {"ชื่ออาหาร": "ข้าวผัด", "ราคา": 60.0, "ผู้รับผิดชอบ": "ทุกคน"},
        {"ชื่ออาหาร": "น้ำดื่ม", "ราคา": 30.0, "ผู้รับผิดชอบ": "ทุกคน"}
    ]

with st.container(border=True):
    st.subheader('👥 สมาชิก')
    n = st.number_input('จำนวนคน', min_value=1, max_value=30, value=len(st.session_state.people), step=1)
    names=[]
    for i in range(int(n)):
        default = st.session_state.people[i] if i < len(st.session_state.people) else f'คนที่ {i+1}'
        names.append(st.text_input(f'ชื่อคนที่ {i+1}',value=default,key=f'name_{i}').strip() or f'คนที่ {i+1}')
    st.session_state.people=names

mode = st.radio('วิธีแบ่งค่าอาหาร', ['หารเท่ากัน', 'จ่ายตามรายการที่กิน'], horizontal=True)
with st.container(border=True):
    st.subheader('🍜 รายการอาหาร')
    item_count = st.number_input(
    "จำนวนรายการอาหาร",
    min_value=1,
    max_value=100,
    value=1,
    step=1
)
   
    items = []

    for i in range(int(item_count)):
        if i < len(st.session_state["items"]):
            default = st.session_state["items"][i]
        else:
            default = {
                "ชื่ออาหาร": "",
                "ราคา": 0.0,
                "ผู้รับผิดชอบ": "ทุกคน"
            }

        c1, c2 = st.columns([2, 1])

        with c1:
            item_name = st.text_input(
                f"ชื่ออาหารรายการที่ {i+1}",
                value=str(default["ชื่ออาหาร"]),
                key=f"item_{i}"
            )

        with c2:
            price = st.number_input(
                f"ราคาอาหารรายการที่ {i+1}",
                min_value=0.0,
                value=float(default["ราคา"]),
                step=5.0,
                key=f"price_{i}"
            )

        owner = "ทุกคน"

        if mode == "จ่ายตามรายการที่กิน":
            opts = ["ทุกคน"] + names
            old = default.get("ผู้รับผิดชอบ", "ทุกคน")

            owner = st.selectbox(
                f"ใครเป็นคนกินรายการที่ {i+1}",
                opts,
                index=opts.index(old) if old in opts else 0,
                key=f"owner_{i}"
            )

        items.append({
            "ชื่ออาหาร": item_name,
            "ราคา": price,
            "ผู้รับผิดชอบ": owner
        })

    st.session_state["items"] = items

        c1,c2=st.columns([2,1])
        with c1: item_name=st.text_input('ชื่ออาหาร',value=default['ชื่ออาหาร'],key=f'item_{i}')
        with c2: price=st.number_input('ราคา (บาท)',min_value=0.0,value=float(default['ราคา']),step=5.0,key=f'price_{i}')
        owner='ทุกคน'
        if mode=='จ่ายตามรายการที่กิน':
            opts=['ทุกคน']+names
            old=default.get('ผู้รับผิดชอบ','ทุกคน')
            owner=st.selectbox('ใครเป็นคนกินรายการนี้?',opts,index=opts.index(old) if old in opts else 0,key=f'owner_{i}')
        items.append({'ชื่ออาหาร':item_name,'ราคา':price,'ผู้รับผิดชอบ':owner})
    st.session_state.items=items

with st.container(border=True):
    st.subheader('🧾 ส่วนลดและค่าบริการ')
    discount=st.number_input('ส่วนลด (%)',min_value=0.0,max_value=100.0,value=0.0,step=1.0)
    service_on=st.checkbox('คิด Service Charge 10%')
    vat_on=st.checkbox('คิด VAT 7%')
    tip=st.number_input('ทิปพนักงาน (บาท)',min_value=0.0,value=0.0,step=10.0)

D=lambda x: Decimal(str(x))
cent=lambda x: x.quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)
food=sum((D(it['ราคา']) for it in items),Decimal('0'))
discount_amount=cent(food*D(discount)/100)
base=food-discount_amount
service=cent(base*Decimal('0.10')) if service_on else Decimal('0')
vat=cent((base+service)*Decimal('0.07')) if vat_on else Decimal('0')
total=base+service+vat+cent(D(tip))

weights={name:Decimal('0') for name in names}
if mode=='หารเท่ากัน':
    for name in names: weights[name]=Decimal('1')
else:
    for it in items:
        price=D(it['ราคา'])
        if it['ผู้รับผิดชอบ']=='ทุกคน':
            for name in names: weights[name]+=price/len(names)
        else: weights[it['ผู้รับผิดชอบ']]+=price
    if sum(weights.values())==0:
        for name in names: weights[name]=Decimal('1')

# Allocate whole satang so the displayed amounts sum exactly to the bill.
unit_total=int(total*100)
weight_total=sum(weights.values())
raw=[Decimal(unit_total)*weights[name]/weight_total for name in names]
units=[int(x) for x in raw]
left=unit_total-sum(units)
order=sorted(range(len(names)),key=lambda i:(-(raw[i]-units[i]),i))
for i in order[:left]: units[i]+=1
payments={name:Decimal(units[i])/100 for i,name in enumerate(names)}

if st.button('✨ คำนวณค่าอาหาร',type='primary',use_container_width=True):
    st.session_state.show_results=True
if st.session_state.get('show_results',False):
    st.subheader('🎉 สรุปค่าอาหาร')
    a,b=st.columns(2)
    a.metric('ยอดรวมทั้งหมด',f'{total:,.2f} บาท')
    b.metric('จำนวนสมาชิก',f'{len(names)} คน')
    st.write(f'ค่าอาหาร: {food:,.2f} บาท')
    st.write(f'ส่วนลด: −{discount_amount:,.2f} บาท')
    st.write(f'Service Charge: {service:,.2f} บาท')
    st.write(f'VAT: {vat:,.2f} บาท')
    st.write(f'ทิป: {cent(D(tip)):,.2f} บาท')
    st.divider()
    st.subheader('💸 แต่ละคนจ่าย')
    for name,amount in payments.items():
        st.write(f'**{name}** — {amount:,.2f} บาท')
    st.subheader('💵 ตรวจสอบเงินทอน')
    payer=st.selectbox('เลือกผู้จ่าย',names)
    cash=st.number_input('จำนวนเงินที่จ่าย (บาท)',min_value=0.0,value=0.0,step=10.0)
    difference=cent(D(cash))-payments[payer]
    if difference>0: st.success(f'เงินทอน {difference:,.2f} บาท')
    elif difference<0: st.warning(f'เงินยังขาด {-difference:,.2f} บาท')
    else: st.success('จ่ายพอดี 🎉')
    summary='FoodShare 🍽️\n'+f'ยอดรวม {total:,.2f} บาท\n'+'\n'.join(f'{name}: {amount:,.2f} บาท' for name,amount in payments.items())
    st.code(summary,language=None)
    st.caption('คัดลอกข้อความด้านบนเพื่อส่งให้เพื่อนในกลุ่มได้เลย')
    st.caption('หมายเหตุ: ส่วนลดหักจากค่าอาหารก่อนคิดค่าบริการและ VAT; ค่าใช้จ่ายเพิ่มเติมแบ่งตามสัดส่วนรายการอาหาร')
