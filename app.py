import streamlit as st
import sqlite3

DB_FILE = "marketplace_web.db"

# ==================== DATABASE SETUP ====================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Tables are created ONLY IF they do not exist (Data is preserved!)
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
                        status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Page Configuration
st.set_page_config(page_title="B2B Construction Marketplace", page_icon="🏗️", layout="wide")

# ==================== APP INTERFACE ====================
st.title("🏗️ B2B Construction Marketplace")
st.markdown("---")

# Sidebar for Navigation
menu = st.sidebar.selectbox("Navigation", ["Contractor Portal", "Supplier Portal", "Admin Dashboard"])

# ==================== 1. CONTRACTOR PORTAL ====================
if menu == "Contractor Portal":
    st.header("👷 Contractor Portal: Post Requirement")
    
    with st.form("req_form", clear_on_submit=True):
        contractor_name = st.text_input("Contractor / Company Name")
        contractor_phone = st.text_input("📱 Contractor Mobile Number (Mandatory)")
        material = st.selectbox("Select Material", ["UltraTech Cement (Bags)", "TMT Steel Bars (Tons)", "River Sand (Brass)", "Crushed Aggregate (Brass)"])
        quantity = st.text_input("Quantity Required (e.g., 100 Bags / 10 Tons)")
        location = st.text_input("📍 Delivery Site Location (Mandatory)")
        
        submitted = st.form_submit_button("Broadcast Requirement to Suppliers")
        
        if submitted:
            if contractor_name and contractor_phone and location and quantity:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO requirements (contractor_name, contractor_phone, material, quantity, location, status) VALUES (?, ?, ?, ?, ?, ?)",
                               (contractor_name, contractor_phone, material, quantity, location, "OPEN"))
                conn.commit()
                conn.close()
                st.success("🎉 Requirement broadcasted successfully to all verified suppliers!")
            else:
                st.error("⚠️ Please fill in all fields, including contact number and delivery location!")

    st.markdown("### 📋 Your Active Requirements & Private Bids")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT req_id, material, quantity, location, contractor_phone, status FROM requirements")
    reqs = cursor.fetchall()
    conn.close()
    
    if not reqs:
        st.info("No requirements posted yet.")
    else:
        for req in reqs:
            req_id, mat, qty, loc, c_phone, status = req
            with st.expander(f"Req #{req_id}: {qty} {mat} at {loc} [Status: {status}]"):
                conn_bids = sqlite3.connect(DB_FILE)
                cursor_bids = conn_bids.cursor()
                cursor_bids.execute("SELECT bid_id, supplier_name, supplier_phone, material_price, transport_charge, service_charge, total_price, platform_fee, payment_status, status FROM bids WHERE req_id = ?", (req_id,))
                bids = cursor_bids.fetchall()
                conn_bids.close()
                
                if not bids:
                    st.info("Waiting for private supplier bids...")
                else:
                    for bid in bids:
                        bid_id, sup_name, s_phone, m_price, trans, serv, total, p_fee, pay_status, b_status = bid
                        st.write(f"🏢 **Supplier:** {sup_name} | 📱 **Contact:** {s_phone}")
                        st.write(f"   - Material Base Price: ₹{m_price}")
                        st.write(f"   - Transport/Logistics: ₹{trans}")
                        st.write(f"   - Supplier Service Charge: ₹{serv}")
                        st.markdown(f"   - **Supplier Total Quote (Payable after delivery):** **₹{total}**")
                        st.markdown(f"   - *Platform Convenience Fee (Online Advance):* **₹{p_fee}**")
                        
                        if b_status == "ACCEPTED":
                            st.success(f"✅ Deal Locked! Supplier Contact: {s_phone}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if pay_status != "PAID" and st.button(f"Pay Platform Fee ₹{p_fee} Online", key=f"pay_{bid_id}"):
                                    conn_pay = sqlite3.connect(DB_FILE)
                                    cur_pay = conn_pay.cursor()
                                    cur_pay.execute("UPDATE bids SET payment_status = 'PAID' WHERE bid_id = ?", (bid_id,))
                                    conn_pay.commit()
                                    conn_pay.close()
                                    st.success("💳 Platform Fee Paid Successfully!")
                                    st.rerun()
                                elif pay_status == "PAID":
                                    st.info("🔒 Platform Fee: PAID")
                            
                            with col2:
                                if st.button(f"❌ Cancel Order", key=f"cancel_{bid_id}"):
                                    conn_can = sqlite3.connect(DB_FILE)
                                    cur_can = conn_can.cursor()
                                    cur_can.execute("UPDATE bids SET status = 'CANCELLED', payment_status = 'REFUNDED' WHERE bid_id = ?", (bid_id,))
                                    cur_can.execute("UPDATE requirements SET status = 'OPEN' WHERE req_id = ?", (req_id,))
                                    conn_can.commit()
                                    conn_can.close()
                                    st.warning("🔄 Order cancelled.")
                                    st.rerun()
                        else:
                            if st.button(f"Accept Deal & Pay Platform Fee (Bid #{bid_id})", key=f"accept_{bid_id}"):
                                conn_acc = sqlite3.connect(DB_FILE)
                                cur_acc = conn_acc.cursor()
                                cur_acc.execute("UPDATE bids SET status = 'ACCEPTED', payment_status = 'PENDING' WHERE bid_id = ?", (bid_id,))
                                cur_acc.execute("UPDATE requirements SET status = 'CLOSED' WHERE req_id = ?", (req_id,))
                                conn_acc.commit()
                                conn_acc.close()
                                st.rerun()

# ==================== 2. SUPPLIER PORTAL ====================
elif menu == "Supplier Portal":
    st.header("🚚 Supplier / Depot Portal: Send Private Bid")
    st.info("💡 **Supplier Perk:** Get direct contractor orders without middlemen.")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT req_id, material, quantity, location, contractor_name, contractor_phone FROM requirements WHERE status = 'OPEN'")
    open_reqs = cursor.fetchall()
    conn.close()
    
    if not open_reqs:
        st.info("No open requirements right now. Please check back later or ask contractor to post a new requirement.")
    else:
        req_options = {f"Req #{r[0]} - {r[2]} {r[1]} (Loc: {r[3]}) | Contractor: {r[4]}": r[0] for r in open_reqs}
        selected_req_label = st.selectbox("Select Open Requirement", list(req_options.keys()))
        selected_req_id = req_options[selected_req_label]
        
        with st.form("bid_form", clear_on_submit=True):
            supplier_name = st.text_input("Depot / Supplier Name")
            supplier_phone = st.text_input("📱 Supplier Mobile Number (Mandatory)")
            material_price = st.number_input("Material Base Price (₹)", min_value=0.0, step=500.0)
            transport_charge = st.number_input("Transport / Delivery Charges (₹)", min_value=0.0, step=100.0)
            service_charge = st.number_input("Service / Handling Charges (₹)", min_value=0.0, step=100.0)
            
            submit_bid = st.form_submit_button("Submit Private Bid")
            
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
                    st.success("🔒 Private bid submitted securely to the contractor!")
                else:
                    st.error("⚠️ Please fill in depot name, mobile number, and valid material price.")

# ==================== 3. ADMIN DASHBOARD ====================
elif menu == "Admin Dashboard":
    st.header("📊 Admin Platform Revenue & Analytics")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(platform_fee) FROM bids WHERE status = 'ACCEPTED' AND payment_status = 'PAID'")
    row = cursor.fetchone()
    total_revenue = row[0] if row and row[0] else 0.0
    
    st.metric(label="Total Platform Earnings (Collected Convenience Fees)", value=f"₹{total_revenue}")
    
    st.subheader("All Accepted Deals & Payment Statuses")
    cursor.execute("SELECT b.req_id, r.contractor_name, r.contractor_phone, b.supplier_name, b.supplier_phone, b.total_price, b.platform_fee, b.payment_status FROM bids b JOIN requirements r ON b.req_id = r.req_id WHERE b.status = 'ACCEPTED'")
    deals = cursor.fetchall()
    conn.close()
    
    if deals:
        for d in deals:
            st.write(f"Req #{d[0]} | 👷 {d[1]} ({d[2]}) 🤝 🏢 {d[3]} ({d[4]}) | Total: ₹{d[5]} | Platform Fee: ₹{d[6]} | Status: **{d[7]}**")
    else:
        st.info("No closed deals yet.")