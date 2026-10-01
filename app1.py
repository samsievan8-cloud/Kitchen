import streamlit as st
import pandas as pd
import datetime
import os
import json
import random
import qrcode
from PIL import Image

# --- 1. ПАРАҚША КОНФИГУРАЦИЯСЫ ---
st.set_page_config(page_title="№144 Unity Kitchen", page_icon="🍱", layout="wide")

# Қажетті папкалар мен файлдар
if not os.path.exists("images"):
    os.makedirs("images")

MENU_FILE = "smart_menu_v7.json"
DATA_FILE = "kitchen_sales.csv"
PRIVILEGED_FILE = "Лист1.csv" # Тізім файлы

# Dynamic QR код генерациялау функциясы
def generate_qr(text):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=2,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    qr_path = os.path.join("images", "temp_qr.png")
    img.save(qr_path)
    return qr_path

# --- 2. ДЕРЕКТЕРМЕН ЖҰМЫС ФУНКЦИЯЛАРЫ ---

def clean_string(text):
    """Мәтінді бос орындардан тазарту және кіші әріпке айналдыру"""
    if text:
        return " ".join(str(text).split()).lower().strip()
    return ""

def load_privileged_list():
    if os.path.exists(PRIVILEGED_FILE):
        try:
            df = pd.read_csv(PRIVILEGED_FILE, skiprows=4, header=None, sep=None, engine='python', encoding="cp1251")
            if not df.empty:
                return [clean_string(name) for name in df.iloc[:, 0].dropna()]
        except Exception as e:
            st.error(f"Файлды оқу мүмкін емес: {e}")
            return []
    return []
            
def load_menu():
    if os.path.exists(MENU_FILE):
        try:
            with open(MENU_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_menu(new_menu):
    with open(MENU_FILE, "w", encoding="utf-8") as f:
        json.dump(new_menu, f, ensure_ascii=False, indent=4)

def save_data(name, location, items_str, total, order_id, status, pay_method):
    now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    new_data = pd.DataFrame([[
        order_id, name, location, items_str, total, pay_method, now, status
    ]], columns=["ID", "Аты-жөні", "Орны", "Тапсырыс", "Сомма", "Төлем түрі", "Уақыты", "Мәртебе"])
    
    if not os.path.exists(DATA_FILE):
        new_data.to_csv(DATA_FILE, index=False, sep=';', encoding="utf-8-sig")
    else:
        new_data.to_csv(DATA_FILE, mode='a', index=False, sep=';', header=False, encoding="utf-8-sig")

# --- 3. ДИЗАЙН (CSS) ---
st.markdown("""
    <style>
    .main-title { color: #1E3A8A; text-align: center; font-size: 36px; font-weight: bold; margin-bottom: 20px; }
    div[data-testid="stImage"] > img { height: 200px; width: 100%; object-fit: cover; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .receipt-box { border: 2px dashed #333; padding: 20px; background-color: #fff; color: #000; font-family: monospace; width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SESSION STATE ЖӘНЕ ДЕРЕКТЕР ---
if 'basket' not in st.session_state:
    st.session_state.basket = []
if 'user_info' not in st.session_state:
    st.session_state.user_info = {"name": "", "place": "", "role": "Оқушы"}

privileged_names = load_privileged_list()

# --- 5. SIDEBAR ---
st.sidebar.header("📂 Мәзір бөлімдері")
category_filter = st.sidebar.radio("Түрді таңдаңыз:", ["Барлығы", "1-тағамдар", "2-тағамдар", "Сусындар", "Тәттілер"])

st.sidebar.write("---")
st.sidebar.header("🛒 Себет")
if not st.session_state.basket:
    st.sidebar.info("Себет бос")
else:
    total_basket = 0
    for item in st.session_state.basket:
        st.sidebar.write(f"• {item['dish']} x {item['qty']} = {item['sum']} тг")
        total_basket += item['sum']
    st.sidebar.write(f"**Жалпы: {total_basket} тг**")
    if st.sidebar.button("🗑️ Тазалау"):
        st.session_state.basket = []
        st.rerun()

# --- 6. БАСТЫ ИНТЕРФЕЙС ---
st.markdown("<div class='main-title'>🏫 №144 SMART АСХАНА</div>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["🛍️ Тапсырыс беру", "👨‍🏫 Әкімшілік"])

with tab1:
    menu = load_menu()
    c1, c2, c3 = st.columns([2, 1, 1])
    u_name = c1.text_input("Аты-жөніңізді жазыңыз:", value=st.session_state.user_info["name"])
    u_place = c2.text_input("Сынып:", value=st.session_state.user_info["place"])
    u_role = c3.selectbox("Кімсіз?", ["Оқушы", "Мұғалім"])

    # Жеңілдікті тексеру логикасы
    is_privileged = False
    status_label = u_role

    if u_role == "Оқушы" and u_name:
        cleaned_input = clean_string(u_name)
        if len(privileged_names) > 0 and cleaned_input in privileged_names:
            is_privileged = True
            status_label = "АСП (Тегін)"
            st.success(f"✅ Расталды: {u_name}. Сізге 100% жеңілдік берілді!")

    display_menu = menu if category_filter == "Барлығы" else {k: v for k, v in menu.items() if v.get('category') == category_filter}

    if not display_menu:
        st.info("Тағам табылмады.")
    else:
        m_cols = st.columns(3)
        for i, (dish, info) in enumerate(display_menu.items()):
            with m_cols[i % 3]:
                if os.path.exists(info.get('image', '')):
                    st.image(info['image'], use_container_width=True)
                
                base_price = info['price']
                if is_privileged:
                    current_price = 0
                    price_display = f":green[**ТЕГІН**]"
                elif u_role == "Мұғалім":
                    current_price = int(base_price * 0.9)
                    price_display = f":red[~~{base_price}~~] **{current_price} тг**"
                else:
                    current_price = base_price
                    price_display = f"**{current_price} тг**"

                st.markdown(f"**{dish}**")
                st.write(f"Бағасы: {price_display}", unsafe_allow_html=True)

                qty = st.number_input(f"Саны:", min_value=1, max_value=10, key=f"q_{dish}")
                if st.button(f"🛒 Қосу", key=f"btn_{dish}"):
                    st.session_state.basket.append({
                        "dish": dish, "qty": qty, "price": current_price, "sum": qty * current_price
                    })
                    st.toast(f"✅ {dish} қосылды!")
                    st.rerun()

    # --- ТӨЛЕМ ЖАСАУ ЖӘНЕ ЧЕК АЛУ БӨЛІМІ ---
    if st.session_state.basket:
        st.write("---")
        st.subheader("💳 Төлем әдісін таңдаңыз")
        pay_method = st.radio("Төлем түрі:", ["Kaspi QR арқылы төлеу", "Қолма-қол (Кассада)"], horizontal=True)
        
        if st.button("✅ ТАПСЫРЫСТЫ РӘСІМДЕУ ЖӘНЕ ТӨЛЕУ", use_container_width=True):
            if not u_name:
                st.error("⚠️ Аты-жөніңізді жазыңыз!")
            else:
                order_id = random.randint(1000, 9999)
                final_total = sum(item['sum'] for item in st.session_state.basket)
                items_summary = ", ".join([f"{i['dish']}({i['qty']})" for i in st.session_state.basket])
                
                # Төлем деректерін CSV-ге сақтау
                save_data(u_name, u_place, items_summary, final_total, order_id, status_label, pay_method)
                
                st.success("🎉 Тапсырыс сәтті қабылданды!")
                
                col_receipt, col_qr = st.columns([1, 1])
                
                # Чек көрсету
                with col_receipt:
                    items_html = "".join([f"<p style='margin: 2px 0;'>• {i['dish']} x {i['qty']} = {i['sum']} тг</p>" for i in st.session_state.basket])
                    receipt_html = f"""
                    <div class="receipt-box">
                        <h3 style="text-align: center; margin-bottom: 5px;">№144 SMART ЧЕК</h3>
                        <p style="text-align: center; margin-top: 0;"><b>ID: #{order_id} | {status_label}</b></p>
                        <hr>
                        <p style="margin: 3px 0;"><b>Клиент:</b> {u_name}</p>
                        <p style="margin: 3px 0;"><b>Орны:</b> {u_place}</p>
                        <p style="margin: 3px 0;"><b>Төлем түрі:</b> {pay_method}</p>
                        <hr>
                        {items_html}
                        <hr>
                        <h3 style="text-align: right; color: #1E3A8A; margin-top: 5px;">ЖАЛПЫ: {final_total} тг</h3>
                    </div>
                    """
                    st.markdown(receipt_html, unsafe_allow_html=True)

                # Kaspi QR немесе Қолма-қол ақша нұсқаулығы
                with col_qr:
                    if pay_method == "Kaspi QR арқылы төлеу" and final_total > 0:
                        st.markdown("<h4 style='text-align: center;'>📲 Kaspi QR арқылы төлеңіз:</h4>", unsafe_allow_html=True)
                        
                        # Kaspi төлем сілтемесі
                        kaspi_pay_data = f"https://kaspi.kz/pay?amount={final_total}&comment=Order_{order_id}"
                        qr_img_path = generate_qr(kaspi_pay_data)
                        
                        st.image(qr_img_path, caption=f"Төлейтін суммаңыз: {final_total} тг", width=250)
                        st.info("💡 Kaspi.kz қосымшасын ашып, QR-кодты сканерлеңіз.")
                    elif final_total == 0:
                        st.success("🎉 Төлем талап етілмейді! Тапсырысыңыз тегін рәсімделді.")
                    else:
                        st.warning("💵 Тапсырысыңызды алып жатқанда асхана кассасына қолма-қол ақша төлеңіз.")

                st.balloons()
                st.session_state.basket = []

with tab2:
    if st.text_input("Пароль:", type="password", key="adm_login") == "144":
        st.subheader("👨‍🏫 Басқару және Статистика")
        
        if os.path.exists(DATA_FILE):
            try:
                sales_df = pd.read_csv(DATA_FILE, sep=';')
                sales_df['Уақыты'] = pd.to_datetime(sales_df['Уақыты'], dayfirst=True)
                now = datetime.datetime.now()
                today_data = sales_df[sales_df['Уақыты'].dt.date == now.date()]
                month_data = sales_df[(sales_df['Уақыты'].dt.month == now.month) & (sales_df['Уақыты'].dt.year == now.year)]
                
                m_col1, m_col2, m_col3 = st.columns(3)
                m_col1.metric("Күнделікті табыс", f"{today_data['Сомма'].sum()} тг")
                m_col2.metric("Айлық табыс", f"{month_data['Сомма'].sum()} тг")
                m_col3.metric("Жалпы тапсырыс", len(sales_df))
                
                st.write("---")
                st.dataframe(sales_df.sort_values(by='Уақыты', ascending=False), use_container_width=True)
            except Exception as e:
                st.error(f"Статистика қатесі: {e}")

        c_adm1, c_adm2 = st.columns(2)
        with c_adm1:
            with st.expander("➕ Жаңа тағам қосу"):
                n_dish = st.text_input("Тағам аты:")
                n_price = st.number_input("Бағасы (тг):", min_value=0, step=50)
                n_cat = st.selectbox("Бөлімі:", ["1-тағамдар", "2-тағамдар", "Сусындар", "Тәттілер"])
                n_img = st.file_uploader("Суретін жүктеу", type=["jpg", "png", "jpeg"])
                if st.button("Мәзірге қосу"):
                    if n_dish and n_img:
                        path = os.path.join("images", n_img.name)
                        with open(path, "wb") as f: f.write(n_img.getbuffer())
                        m = load_menu()
                        m[n_dish] = {"price": n_price, "image": path, "category": n_cat}
                        save_menu(m)
                        st.success("Қосылды!"); st.rerun()

        with c_adm2:
            with st.expander("🗑️ Мәзірден өшіру"):
                m = load_menu()
                if m:
                    target = st.selectbox("Таңдаңыз:", list(m.keys()))
                    if st.button("Жою"):
                        del m[target]
                        save_menu(m); st.rerun()
        
        if st.button("🗑️ Барлық сатылым тарихын тазалау"):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE); st.rerun()
