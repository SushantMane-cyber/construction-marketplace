import streamlit as st
import sqlite3
import urllib.parse
from PIL import Image
import io

DB_FILE = "marketplace_web.db"

# ==================== DATABASE SETUP ====================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        name TEXT, 
                        phone TEXT UNIQUE, 
                        password TEXT, 
                        role TEXT)''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS requirements (
                        req_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        contractor_name TEXT, 
                        contractor_phone TEXT,
                        material TEXT, 
                        quantity TEXT, 
                        location TEXT, 
                        status TEXT)''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS bids (
                        bid_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        req_id INTEGER, 
                        supplier_name TEXT, 
                        supplier_phone TEXT,
                        material_price REAL, 
                        transport_charge REAL, 
                        service_charge REAL, 
                        total_price REAL,
                        platform_fee REAL,
                        payment_status TEXT,
                        utr_number TEXT,
                        payment_proof BLOB,
                        status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Page Configuration
st.set_page_config(page_title="B2B Construction Marketplace", page_icon="🏗️", layout="wide")

st.title("🏗️ B2B Construction Marketplace")
st.markdown("---")

# Session State Initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_phone = ""
    st.session_state.user_role = ""
    st.session_state.user_name = ""

# ==================== SIDEBAR AUTHENTICATION ====================
st.sidebar.header("🔐 User Authentication")

if not st.session_state.logged_in:
    auth_mode = st.sidebar.radio("Choose Action:", ["Login", "Register"])
    
    if auth_mode == "Register":
        st.sidebar.subheader("📝 Create New Account")
        reg_name = st.sidebar.text_input("Full Name / Company Name")
        reg_phone = st.sidebar.text_input("📱 Mobile Number (Username)")
        reg_pass = st.sidebar.text_input("🔑 Set Password", type="password")
        reg_role = st.sidebar.selectbox("Select Role", ["Contractor", "Supplier / Depot"])
        
        if st.sidebar.button("Register Now"):
            if reg_name and reg_phone and reg_pass:
                try:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (name, phone, password, role) VALUES (?, ?, ?, ?)",
                                   (reg_name, reg_phone, reg_pass, reg_role))
                    conn.commit()
                    conn.close()
                    st.sidebar.success("🎉 Registration successful! Please switch to Login tab.")
                except sqlite3.IntegrityError:
                    st.sidebar.error("⚠️ Mobile number already registered! Please login.")
            else:
                st.sidebar.error("⚠️ Please fill in all fields.")
                
    elif auth_mode == "Login":
        st.sidebar.subheader("🔑 Sign In to Portal")
        login_phone = st.sidebar.text_input("📱 Registered Mobile Number")
        login_pass = st.sidebar.text_input("🔑 Password", type="password")
        
        if st.sidebar.button("Login"):
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT name, role FROM users WHERE phone = ? AND password = ?", (login_phone, login_pass))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                st.session_state.logged_in = True
                st.session_state.user_phone = login_phone
                st.session_state.user_name = user[0]
                st.session_state.user_role = user[1]
                st.success("✅ Login Successful!")
                st.rerun()
            else:
                st.sidebar.error("❌ Invalid Mobile Number or Password!")

    # Hidden / Secret Admin Access (Key: sushant@2007)
    with st.sidebar.expander("🛠️ Admin Portal Access"):
        admin_key = st.text_input("Admin Secret Key", type="password")
        if admin_key == "sushant@2007":
            st.session_state.logged_in = True
            st.session_state.user_role = "Admin"
            st.session_state.user_name = "Super Admin"
            st.rerun()

else:
    st.sidebar.success(f"👤 Welcome, {st.session_state.user_name}!")
    st.sidebar.info(f"🏷️ Role: **{st.session_state.user_role}**")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user_phone = ""
        st.session_state.user_role = ""
        st.session_state.user_name = ""
        st.rerun()

# ==================== MAIN PORTAL LOGIC ====================
if not st.session_state.logged_in:
    st.info("👈 Please **Register** or **Login** from the sidebar to access the B2B Marketplace portals.")
    
else:
    current_role = st.session_state.user_role
    
    # ==================== 1. CONTRACTOR PORTAL ====================
    if current_role == "Contractor":
        st.header("👷 Contractor Dashboard: Post & Manage Requirements")
        
        tab1, tab2 = st.tabs(["📝 Post Requirement", "📋 Active Bids & Deal Lock"])
        
        with tab1:
            with st.form("req_form", clear_on_submit=True):
                contractor_name = st.text_input("Contractor / Company Name", value=st.session_state.user_name)
                contractor_phone = st.text_input("📱 Mobile Number", value=st.session_state.user_phone)
                
                material = st.selectbox("Select Material", [
                    "UltraTech Cement (Bags)", 
                    "Ambuja Cement (Bags)", 
                    "ACC Cement (Bags)",
                    "TMT Steel Bars - Fe 500D (Tons)", 
                    "Structural Steel / Beams (Tons)",
                    "River Sand / Fine Sand (Brass)", 
                    "M-Sand / Manufactured Sand (Brass)",
                    "Crushed Aggregate 20mm (Brass)", 
                    "Crushed Aggregate 10mm (Brass)",
                    "Red Clay Bricks (Pieces)",
                    "AAC Blocks / Autoclaved Aerated Concrete (Pieces)",
                    "Fly Ash Bricks (Pieces)",
                    "Ready Mix Concrete - RMC M25/M30 (Cubic Meters)",
                    "Ceramic / Vitrified Floor Tiles (Sq. Ft.)",
                    "PVC Plumbing Pipes & Fittings (Bundle/Lot)",
                    "Waterproofing Chemical & Compounds (Liters/Kg)"
                ])
                
                quantity = st.text_input("Quantity Required (e.g., 500 Bags / 20 Tons / 5000 Bricks)")
                location = st.text_input("📍 Site Location / Address")
                
                submitted = st.form_submit_button("Broadcast Requirement")
                
                if submitted:
                    if contractor_name and contractor_phone and location and quantity:
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO requirements (contractor_name, contractor_phone, material, quantity, location, status) VALUES (?, ?, ?, ?, ?, ?)",
                                       (contractor_name, contractor_phone, material, quantity, location, "OPEN"))
                        conn.commit()
                        conn.close()
                        st.success("🎉 Requirement broadcasted to verified suppliers successfully!")
                    else:
                        st.error("⚠️ Please fill in all details!")

        with tab2:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT req_id, material, quantity, location, contractor_phone, status FROM requirements WHERE contractor_phone = ?", (st.session_state.user_phone,))
            reqs = cursor.fetchall()
            conn.close()
            
            if not reqs:
                st.info("You haven't posted any requirements yet.")
            else:
                for req in reqs:
                    req_id, mat, qty, loc, c_phone, status = req
                    with st.expander(f"Requirement #{req_id}: {qty} {mat} at {loc} [Status: {status}]"):
                        conn_bids = sqlite3.connect(DB_FILE)
                        cursor_bids = conn_bids.cursor()
                        cursor_bids.execute("SELECT bid_id, supplier_name, supplier_phone, material_price, transport_charge, service_charge, total_price, platform_fee, payment_status, status FROM bids WHERE req_id = ?", (req_id,))
                        bids = cursor_bids.fetchall()
                        conn_bids.close()
                        
                        if not bids:
                            st.info("⏳ Waiting for private quotes from suppliers...")
                        else:
                            for bid in bids:
                                bid_id, sup_name, s_phone, m_price, trans, serv, total, p_fee, pay_status, b_status = bid
                                st.write(f"🏢 **Supplier Depot:** {sup_name} | 📱 **Contact:** {s_phone}")
                                st.write(f"   - Material Price: ₹{m_price}")
                                st.write(f"   - Transport/Logistics: ₹{trans}")
                                st.write(f"   - Service Charges: ₹{serv}")
                                st.markdown(f"   - **Supplier Total Quote (Payable on delivery):** **₹{total}**")
                                st.markdown(f"   - *Platform Convenience Fee (Online):* **₹{p_fee}** *(100% Refundable if order fails)*")
                                
                                if b_status == "ACCEPTED":
                                    st.success(f"✅ Deal Accepted! Supplier Contact: {s_phone}")
                                    
                                    # Payment not done yet -> Show QR code & proof upload (No cancel option here)
                                    if pay_status != "PAID":
                                        st.markdown(f"📱 **Scan & Pay Exact Platform Fee (₹{p_fee}) via GPay/PhonePe:**")
                                        
                                        my_upi_id = "sushantmane3893@okicici"
                                        merchant_name = "Sushant Mane"
                                        upi_string = f"upi://pay?pa={my_upi_id}&pn={merchant_name}&am={p_fee}&cu=INR"
                                        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={urllib.parse.quote(upi_string)}"
                                        
                                        st.image(qr_code_url, width=200)
                                        st.caption(f"UPI ID: {my_upi_id} | Scan to pay exact ₹{p_fee}")
                                        
                                        st.markdown("---")
                                        st.subheader("📸 Submit Payment Proof")
                                        utr_input = st.text_input("Enter UTR / UPI Transaction Reference No.", key=f"utr_{bid_id}")
                                        uploaded_proof = st.file_uploader("Upload Payment Screenshot (JPG/PNG)", type=["jpg", "jpeg", "png"], key=f"file_{bid_id}")
                                        
                                        if st.button(f"✅ Submit Proof & Confirm Order #{bid_id}", key=f"pay_{bid_id}"):
                                            if utr_input and uploaded_proof:
                                                image_bytes = uploaded_proof.read()
                                                conn_pay = sqlite3.connect(DB_FILE)
                                                cur_pay = conn_pay.cursor()
                                                cur_pay.execute("UPDATE bids SET payment_status = 'PAID', utr_number = ?, payment_proof = ? WHERE bid_id = ?", 
                                                                (utr_input, image_bytes, bid_id))
                                                conn_pay.commit()
                                                conn_pay.close()
                                                st.success("🎉 Payment Proof Uploaded & Order Confirmed!")
                                                st.rerun()
                                            else:
                                                st.error("⚠️ Please enter UTR number AND upload payment screenshot!")
                                    
                                    # Payment IS done -> Show success message AND Cancel/Refund option now
                                    else:
                                        st.info("🔒 Platform Fee Status: PAID (Proof Submitted & Verified)")
                                        
                                        st.markdown("---")
                                        if st.button(f"❌ Request Order Cancellation & Fee Refund", key=f"cancel_{bid_id}"):
                                            conn_can = sqlite3.connect(DB_FILE)
                                            cur_can = conn_can.cursor()
                                            cur_can.execute("UPDATE bids SET status = 'CANCELLED', payment_status = 'REFUND_REQUESTED' WHERE bid_id = ?", (bid_id,))
                                            cur_can.execute("UPDATE requirements SET status = 'OPEN' WHERE req_id = ?", (req_id,))
                                            conn_can.commit()
                                            conn_can.close()
                                            st.warning("⚠️ Cancellation requested! Admin has been notified for refund processing.")
                                            st.rerun()
                                else:
                                    if st.button(f"Accept Deal from {sup_name}", key=f"accept_{bid_id}"):
                                        conn_acc = sqlite3.connect(DB_FILE)
                                        cur_acc = conn_acc.cursor()
                                        cur_acc.execute("UPDATE bids SET status = 'ACCEPTED', payment_status = 'PENDING' WHERE bid_id = ?", (bid_id,))
                                        cur_acc.execute("UPDATE requirements SET status = 'CLOSED' WHERE req_id = ?", (req_id,))
                                        conn_acc.commit()
                                        conn_acc.close()
                                        st.rerun()

    # ==================== 2. SUPPLIER PORTAL ====================
    elif current_role == "Supplier / Depot":
        st.header("🚚 Supplier / Depot Dashboard")
        st.info("💡 **Private Bidding:** Submit secure quotes directly to contractors without competitor visibility.")
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT req_id, material, quantity, location, contractor_name, contractor_phone FROM requirements WHERE status = 'OPEN'")
        open_reqs = cursor.fetchall()
        conn.close()
        
        if not open_reqs:
            st.info("No active contractor requirements at the moment.")
        else:
            req_options = {f"Req #{r[0]}: {r[2]} {r[1]} at {r[3]} (Contractor: {r[4]})": r[0] for r in open_reqs}
            selected_req_label = st.selectbox("Select Open Requirement:", list(req_options.keys()))
            selected_req_id = req_options[selected_req_label]
            
            with st.form("bid_form", clear_on_submit=True):
                supplier_name = st.text_input("Depot / Supplier Firm Name", value=st.session_state.user_name)
                supplier_phone = st.text_input("📱 Depot Contact Number", value=st.session_state.user_phone)
                material_price = st.number_input("Material Base Price (₹)", min_value=0.0, step=500.0)
                transport_charge = st.number_input("Transport & Freight Charges (₹)", min_value=0.0, step=100.0)
                service_charge = st.number_input("Handling / Service Charges (₹)", min_value=0.0, step=100.0)
                
                submit_bid = st.form_submit_button("Submit Private Quote")
                
                if submit_bid:
                    if supplier_name and supplier_phone and material_price > 0:
                        total_price = material_price + transport_charge + service_charge
                        platform_fee = round(material_price * 0.02, 2)
                        
                        conn_b = sqlite3.connect(DB_FILE)
                        cursor_b = conn_b.cursor()
                        cursor_b.execute("INSERT INTO bids (req_id, supplier_name, supplier_phone, material_price, transport_charge, service_charge, total_price, platform_fee, payment_status, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                       (selected_req_id, supplier_name, supplier_phone, material_price, transport_charge, service_charge, total_price, platform_fee, "PENDING", "PENDING"))
                        conn_b.commit()
                        conn_b.close()
                        st.success("🔒 Private quote submitted successfully!")
                    else:
                        st.error("⚠️ Please fill in all required fields.")

    # ==================== 3. ADMIN DASHBOARD ====================
    elif current_role == "Admin":
        st.header("📊 Admin Platform Revenue & Analytics")
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Notification/Alert for Refund Requests
        cursor.execute("SELECT COUNT(*) FROM bids WHERE payment_status = 'REFUND_REQUESTED'")
        refund_count = cursor.fetchone()[0]
        if refund_count > 0:
            st.error(f"🔔 **ALERT:** {refund_count} order(s) have requested cancellation & fee refund!")
        
        cursor.execute("SELECT SUM(platform_fee) FROM bids WHERE status = 'ACCEPTED' AND payment_status = 'PAID'")
        row = cursor.fetchone()
        total_revenue = row[0] if row and row[0] else 0.0
        
        st.metric(label="Total Collected Platform Fees", value=f"₹{total_revenue}")
        
        st.markdown("---")
        st.subheader("All Confirmed Orders & Payment Proofs")
        cursor.execute("SELECT b.req_id, r.contractor_name, r.contractor_phone, b.supplier_name, b.supplier_phone, b.total_price, b.platform_fee, b.payment_status, b.utr_number, b.payment_proof FROM bids b JOIN requirements r ON b.req_id = r.req_id WHERE b.status = 'ACCEPTED' OR b.payment_status = 'REFUND_REQUESTED'")
        deals = cursor.fetchall()
        conn.close()
        
        if deals:
            for d in deals:
                req_id, c_name, c_phone, s_name, s_phone, total, p_fee, p_status, utr, proof = d
                
                # Highlight refunded/cancelled orders in admin
                box_color = "🔴 Refund Requested" if p_status == 'REFUND_REQUESTED' else f"Status: {p_status}"
                
                with st.expander(f"Req #{req_id} | Contractor: {c_name} | Fee: ₹{p_fee} | [{box_color}]"):
                    st.write(f"👷 **Contractor:** {c_name} ({c_phone})")
                    st.write(f"🤝 **Supplier:** {s_name} ({s_phone})")
                    st.write(f"💰 **Total Deal:** ₹{total} | **Platform Fee:** ₹{p_fee}")
                    st.write(f"🔢 **UTR / Transaction ID:** `{utr}`")
                    st.write(f"📌 **Payment Status:** `{p_status}`")
                    
                    if proof:
                        try:
                            img = Image.open(io.BytesIO(proof))
                            st.image(img, caption=f"Payment Screenshot (UTR: {utr})", width=300)
                        except Exception:
                            st.warning("Could not display image proof.")
        else:
            st.info("No accepted deals recorded yet.")