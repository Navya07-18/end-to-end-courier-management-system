import streamlit as st
import pandas as pd
import sqlite3
import random
import string
from datetime import datetime, timedelta
import hashlib

# Shipment status lifecycle definitions
SHIPMENT_LIFECYCLE_STATUSES = [
    'Pending',
    'Picked Up',
    'In Transit',
    'Out for Delivery',
    'Delivered'
]
SHIPMENT_STATUS_OPTIONS = SHIPMENT_LIFECYCLE_STATUSES + ['Cancelled']
DEFAULT_SHIPMENT_STATUS = 'Pending'

st.set_page_config(page_title='Courier Management System', layout='wide', initial_sidebar_state='expanded')

st.markdown("""
<style>
/* app overall */
.stApp {
    background: radial-gradient(circle at 20% 0%, #0d1c37 0%, #020813 90%) !important;
    color: #e6f7ff !important;
}
section.main {
    background-color: transparent !important;
}

/* body & text */
body, .css-9s5bis, .css-1d391kg, .css-12oz5g7 {
    color: #e2f1ff !important;
    background: #030a18 !important;
}

/* headers */
h1, h2, h3, h4, h5, h6 {
    color: #9ad3ff !important;
}

/* sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #021028 0%, #04122e 100%) !important;
    color: #ccedff !important;
    border-right: 1px solid #153e8a;
}

/* cards */
.css-1v3fvcr, .css-1d391kg, .css-1lz4m02 {
    background-color: rgba(4, 16, 47, 0.75) !important;
    border: 1px solid #2d61b3 !important;
    box-shadow: 0 0 16px rgba(29, 93, 200, 0.35) !important;
}

/* buttons */
.stButton>button {
    background: linear-gradient(135deg, #1a62d9, #0643b8) !important;
    color: #fff;
    border: 1px solid #4e8ee1;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #3c83e0, #0963dc) !important;
}

/* inputs */
div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stSelectbox"] button, div[data-testid="stDateInput"] input {
    background-color: #021b45 !important;
    color: #ccedff !important;
    border: 1px solid #3385ff !important;
}

/* status metric colors */
.stMetric {
    background: rgba(8, 25, 60, 0.8) !important;
    border: 1px solid #1772d3 !important;
}

/* dataframes */
[data-testid="stDataFrame"] { background-color: rgba(2, 14, 34, 0.75) !important; }

/* Alerts for “Please login/register” messages */
[data-testid="stAlert"] {
    color: #d6f2ff !important;
    border-color: #4ca6ff !important;
    background-color: rgba(2, 34, 70, 0.85) !important;
}

/* Everything inside the alert text if needed */
[data-testid="stAlert"] .css-1v0mbdj { color: #d6f2ff !important; }

/* footer */
footer { color: #80bfff !important; }
</style>
""", unsafe_allow_html=True)

# Initialize database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'customer'
        )
    ''')
    
    # Create shipments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_id TEXT UNIQUE NOT NULL,
            sender_name TEXT NOT NULL,
            receiver_name TEXT NOT NULL,
            source_city TEXT NOT NULL,
            destination_city TEXT NOT NULL,
            delivery_type TEXT NOT NULL,
            estimated_delivery DATE NOT NULL,
            status TEXT DEFAULT 'Pending',
            weight REAL DEFAULT 0,
            product_type TEXT DEFAULT 'Other',
            payment REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Ensure migration for existing table columns
    c.execute("PRAGMA table_info(shipments)")
    existing_columns = [row[1] for row in c.fetchall()]
    if 'weight' not in existing_columns:
        c.execute("ALTER TABLE shipments ADD COLUMN weight REAL DEFAULT 0")
    if 'product_type' not in existing_columns:
        c.execute("ALTER TABLE shipments ADD COLUMN product_type TEXT DEFAULT 'Other'")
    if 'payment' not in existing_columns:
        c.execute("ALTER TABLE shipments ADD COLUMN payment REAL DEFAULT 0")
    
    conn.commit()
    conn.close()

def reset_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS users')
    c.execute('DROP TABLE IF EXISTS shipments')
    conn.commit()
    conn.close()
    init_db()

# Database functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def normalize_role(role):
    if not role:
        return 'customer'
    normalized = role.strip().lower().replace(" ", "_")
    if normalized in ('deliverystaff', 'delivery_staff'):
        return 'delivery_staff'
    if normalized == 'admin':
        return 'admin'
    return 'customer'

def register_user(username, email, password, role='customer'):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                (username, email, hash_password(password), role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?',
            (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def generate_tracking_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def calculate_payment(weight, product_type, delivery_type):
    base_rates = {
        'Document': 10,
        'Electronics': 30,
        'Clothing': 15,
        'Other': 20
    }
    rate = base_rates.get(product_type, base_rates['Other'])
    amount = weight * rate
    if delivery_type == 'Express':
        amount *= 1.5
    return round(amount, 2)


def book_shipment(sender_name, receiver_name, source_city, destination_city, delivery_type, weight, product_type):
    tracking_id = generate_tracking_id()
    
    # Calculate estimated delivery
    if delivery_type == 'Express':
        days = random.randint(1, 2)
    else:  # Normal
        days = random.randint(3, 5)
    
    estimated_delivery = datetime.now() + timedelta(days=days)
    payment = calculate_payment(weight, product_type, delivery_type)
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO shipments 
        (tracking_id, sender_name, receiver_name, source_city, destination_city, delivery_type, estimated_delivery, weight, product_type, payment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tracking_id, sender_name, receiver_name, source_city, destination_city, 
        delivery_type, estimated_delivery.strftime('%Y-%m-%d'), weight, product_type, payment))
    conn.commit()
    conn.close()
    
    return tracking_id, estimated_delivery.strftime('%Y-%m-%d'), payment

def track_shipment(tracking_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM shipments WHERE tracking_id = ?', (tracking_id,))
    shipment = c.fetchone()
    conn.close()
    return shipment

def get_shipment_stats():
    conn = sqlite3.connect('database.db')
    df = pd.read_sql('SELECT * FROM shipments', conn)
    conn.close()
    
    total = len(df)
    delivered = len(df[df['status'] == 'Delivered'])
    pending = len(df[df['status'] == 'Pending'])
    
    return total, delivered, pending

def get_all_shipments():
    conn = sqlite3.connect('database.db')
    df = pd.read_sql('SELECT * FROM shipments ORDER BY created_at DESC', conn)
    conn.close()
    return df

def cancel_shipment(tracking_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('UPDATE shipments SET status = ? WHERE tracking_id = ?', ('Cancelled', tracking_id))
    conn.commit()
    conn.close()
    return True


def is_valid_shipment_status(status):
    return status in SHIPMENT_STATUS_OPTIONS


def update_shipment_status(tracking_id, new_status):
    if not is_valid_shipment_status(new_status):
        return False
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT id FROM shipments WHERE tracking_id = ?', (tracking_id,))
    if not c.fetchone():
        conn.close()
        return False
    c.execute('UPDATE shipments SET status = ? WHERE tracking_id = ?', (new_status, tracking_id))
    conn.commit()
    conn.close()
    return True


def notify(message, message_type='success'):
    if message_type == 'success':
        st.success(message)
    elif message_type == 'info':
        st.info(message)
    elif message_type == 'warning':
        st.warning(message)
    elif message_type == 'error':
        st.error(message)
    else:
        st.write(message)


def ensure_shipment_status_column():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('PRAGMA table_info(shipments)')
    existing_columns = [row[1] for row in c.fetchall()]
    if 'status' not in existing_columns:
        c.execute("ALTER TABLE shipments ADD COLUMN status TEXT DEFAULT 'Pending'")
        conn.commit()
    c.execute('UPDATE shipments SET status = ? WHERE status IS NULL OR TRIM(status) = ?',(DEFAULT_SHIPMENT_STATUS, ''))
    conn.commit()
    conn.close()


def get_user_shipments(username):
    conn = sqlite3.connect('database.db')
    df = pd.read_sql('SELECT * FROM shipments WHERE sender_name = ? ORDER BY created_at DESC', conn, params=(username,))
    conn.close()
    return df

# Initialize database
init_db()
ensure_shipment_status_column()

# Session management
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏠 Home"

# Sidebar navigation
st.sidebar.title("🚚 Courier Management System")
st.sidebar.markdown("---")

if st.session_state.logged_in:
    st.sidebar.success(f"👤 Logged in as: {st.session_state.username}")
    st.sidebar.markdown(f"🔑 Role: {st.session_state.user_role}")
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_role = None
        st.rerun()
else:
    st.sidebar.markdown("<div style='color: #ffffff; font-weight: 600; padding: 8px;'>🔒 Please login or register</div>", unsafe_allow_html=True)

st.sidebar.markdown("---")

# Navigation buttons for manual control
if st.session_state.logged_in:
    if st.sidebar.button("🏠 Home"):
        st.session_state.current_page = "🏠 Home"
        st.rerun()
    if st.session_state.user_role == 'customer':
        if st.sidebar.button("📦 Book Shipment"):
            st.session_state.current_page = "📦 Book Shipment"
            st.rerun()
        if st.sidebar.button("🚫 Cancel Shipment"):
            st.session_state.current_page = "🚫 Cancel Shipment"
            st.rerun()
        if st.sidebar.button("🔍 Track Shipment"):
            st.session_state.current_page = "🔍 Track Shipment"
            st.rerun()
    elif st.session_state.user_role == 'delivery_staff':
        if st.sidebar.button("🚚 Delivery Dashboard"):
            st.session_state.current_page = "🚚 Delivery Dashboard"
            st.rerun()
        if st.sidebar.button("🔍 Track Shipment"):
            st.session_state.current_page = "🔍 Track Shipment"
            st.rerun()
    elif st.session_state.user_role == 'admin':
        if st.sidebar.button("📊 Admin Dashboard"):
            st.session_state.current_page = "📊 Admin Dashboard"
            st.rerun()
        if st.sidebar.button("📊 Manage Shipments"):
            st.session_state.current_page = "📊 Manage Shipments"
            st.rerun()
else:
    if st.sidebar.button("👤 Register"):
        st.session_state.current_page = "👤 Register"
        st.rerun()
    if st.sidebar.button("🔐 Login"):
        st.session_state.current_page = "🔐 Login"
        st.rerun()
    if st.sidebar.button("🔍 Track Shipment"):
        st.session_state.current_page = "🔍 Track Shipment"
        st.rerun()

st.sidebar.markdown("---")

if st.session_state.current_page == "🏠 Home":
    st.title("🚚 Courier Management System")
    st.markdown("---")
    
    st.markdown("""
    ### 📋 About This System
    
    This is a **prototype** demonstrating the functionality of a Courier Management System.
    
    **Features:**
    - 📝 User Registration & Authentication
    - 📦 Shipment Booking with Tracking
    - 📊 Smart Delivery Time Estimation
    - 🔍 Real-time Shipment Tracking
    - 📈 Admin Analytics Dashboard
    
    """)
    
    if st.session_state.logged_in:
        st.success(f"🎉 Welcome back, {st.session_state.username}!")
        st.info("Use the sidebar to navigate through different features.")
    else:
        st.markdown("<div style='color:#ffffff; font-weight: 600; background-color: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px;'>👋 Please register or login to use the system features.</div>", unsafe_allow_html=True)

# Registration Page
elif st.session_state.current_page == "👤 Register":
    st.title("👤 User Registration")
    st.markdown("---")
    
    with st.form("register_form"):
        st.subheader("Create New Account")
        
        username = st.text_input("👤 Username", placeholder="Choose a unique username")
        email = st.text_input("📧 Email", placeholder="your@email.com")
        password = st.text_input("🔒 Password", type="password", placeholder="Create a strong password")
        role = st.selectbox("🎭 Role", ["Customer", "Delivery Staff", "Admin"])
        
        submit_button = st.form_submit_button("Register", type="primary")
        
        if submit_button:
            if username and email and password:
                role_key = normalize_role(role)
                if register_user(username, email, password, role_key):
                    st.success("✅ Registration successful! Redirecting to login...")
                    st.balloons()
                    # Auto-navigate to login after successful registration
                    st.session_state.current_page = "🔐 Login"
                    st.rerun()
                else:
                    st.error("❌ Username or email already exists!")
            else:
                st.error("❌ Please fill all fields!")

# Login Page
elif st.session_state.current_page == "🔐 Login":
    st.title("🔐 User Login")
    st.markdown("---")
    
    with st.form("login_form"):
        st.subheader("Sign In")
        
        username = st.text_input("👤 Username", placeholder="Enter your username")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        
        submit_button = st.form_submit_button("Login", type="primary")
        
        if submit_button:
            if username and password:
                user = authenticate_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user[1]
                    user_role = normalize_role(user[4])
                    st.session_state.user_role = user_role
                    if user_role == 'admin':
                        st.success(f"✅ Welcome admin {user[1]}! Redirecting to admin dashboard...")
                        st.session_state.current_page = "📊 Admin Dashboard"
                    elif user_role == 'delivery_staff':
                        st.success(f"✅ Welcome back, {user[1]}! Redirecting to Delivery Staff dashboard...")
                        st.session_state.current_page = "🚚 Delivery Dashboard"
                    else:
                        st.success(f"✅ Welcome back, {user[1]}! Redirecting to booking...")
                        st.session_state.current_page = "📦 Book Shipment"
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password!")
            else:
                st.error("❌ Please fill all fields!")

# Book Shipment Page
elif st.session_state.current_page == "📦 Book Shipment":
    if not st.session_state.logged_in:
        st.error("❌ Please login to book shipments!")
        st.stop()
    if st.session_state.user_role != 'customer':
        st.error("❌ Only customers can book shipments. Delivery staff should use the Delivery Dashboard.")
        st.stop()
    
    st.title("📦 Book a Shipment")
    st.markdown("---")
    
    with st.form("booking_form"):
        st.subheader("Shipment Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            sender_name = st.text_input("👤 Sender Name", placeholder="Enter sender name")
            source_city = st.text_input("📍 Source City", placeholder="From city")
            weight = st.number_input("⚖️ Weight (kg)", min_value=0.1, max_value=1000.0, value=1.0, step=0.1)
        
        with col2:
            receiver_name = st.text_input("👥 Receiver Name", placeholder="Enter receiver name")
            destination_city = st.text_input("🎯 Destination City", placeholder="To city")
            product_type = st.selectbox("📦 Product Type", ["Document", "Electronics", "Clothing", "Other"])
        
        delivery_type = st.selectbox("🚚 Delivery Type", ["Normal", "Express"])
        
        submit_button = st.form_submit_button("Book Shipment", type="primary")
        
        if submit_button:
            if all([sender_name, receiver_name, source_city, destination_city]):
                tracking_id, estimated_date, payment = book_shipment(
                    sender_name, receiver_name, source_city, destination_city, delivery_type, weight, product_type
                )
                
                notify("✅ Shipment booked successfully! Your shipment is now Pending.")
                st.balloons()
                
                # Display booking confirmation
                st.markdown("### 📋 Booking Confirmation")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("🏷️ Tracking ID", tracking_id)
                with col2:
                    st.metric("📅 Estimated Delivery", estimated_date)
                with col3:
                    st.metric("🚚 Delivery Type", delivery_type)
                with col4:
                    st.metric("💰 Payment", f"₹ {payment}")
                
                st.markdown("**📌 Package Info**")
                st.write(f"Weight: {weight} kg")
                st.write(f"Product: {product_type}")
                
                # Store in session for display
                st.session_state.last_booking = {
                    'tracking_id': tracking_id,
                    'estimated_date': estimated_date,
                    'payment': payment,
                    'weight': weight,
                    'product_type': product_type
                }
            else:
                st.error("❌ Please fill all fields!")

# Cancel Shipment Page
elif st.session_state.current_page == "🚫 Cancel Shipment":
    if not st.session_state.logged_in:
        st.error("❌ Please login to cancel shipments!")
        st.stop()
    if st.session_state.user_role != 'customer':
        st.error("❌ Only customers can cancel their own shipments.")
        st.stop()
    
    st.title("🚫 Cancel Shipment")
    st.markdown("---")
    
    # Get user's shipments
    user_shipments = get_user_shipments(st.session_state.username)
    
    if user_shipments.empty:
        st.info("📭 You have no shipments to cancel.")
    else:
        st.subheader("📋 Your Shipments")
        
        # Filter only active shipments (not delivered or cancelled)
        active_shipments = user_shipments[~user_shipments['status'].isin(['Delivered', 'Cancelled'])]
        
        if active_shipments.empty:
            st.info("✅ You have no active shipments to cancel.")
        else:
            for index, shipment in active_shipments.iterrows():
                with st.expander(f"🏷️ {shipment['tracking_id']} - {shipment['status']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**👤 Sender:** {shipment['sender_name']}")
                        st.write(f"**👥 Receiver:** {shipment['receiver_name']}")
                        st.write(f"**📍 From:** {shipment['source_city']}")
                        st.write(f"**🎯 To:** {shipment['destination_city']}")
                    
                    with col2:
                        st.write(f"**🚚 Delivery Type:** {shipment['delivery_type']}")
                        st.write(f"**📅 Estimated Delivery:** {shipment['estimated_delivery']}")
                        st.write(f"**📦 Status:** {shipment['status']}")
                        st.write(f"**🕐 Created:** {shipment['created_at']}")
                    
                    # Cancel button for this shipment
                    if st.button(f"🚫 Cancel {shipment['tracking_id']}", key=f"cancel_{shipment['tracking_id']}"):
                        if cancel_shipment(shipment['tracking_id']):
                            st.success(f"✅ Shipment {shipment['tracking_id']} cancelled successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to cancel shipment {shipment['tracking_id']}")
        
        st.markdown("---")
        st.subheader("📋 All Your Shipments")
        
        # Display all shipments with status colors
        def color_status(val):
            if val == 'Delivered':
                return 'background-color: #d4edda'
            elif val == 'Out for Delivery':
                return 'background-color: #cfe2ff'
            elif val == 'In Transit':
                return 'background-color: #d1ecf1'
            elif val == 'Picked Up':
                return 'background-color: #fff3cd'
            elif val == 'Cancelled':
                return 'background-color: #f8d7da'
            else:
                return 'background-color: #fff3cd'
        
        styled_df = user_shipments.style.applymap(color_status, subset=['status'])
        st.dataframe(styled_df, use_container_width=True)

# Track Shipment Page
elif st.session_state.current_page == "🔍 Track Shipment":
    if st.session_state.user_role == 'admin':
        st.error("❌ Admin users should use Admin Dashboard/Manage Shipments instead.")
        st.stop()
    st.title("🔍 Track Shipment")
    st.markdown("---")
    
    with st.form("track_form"):
        tracking_id = st.text_input("🏷️ Enter Tracking ID", placeholder="Enter 10-digit tracking ID")
        submit_button = st.form_submit_button("Track", type="primary")
        
        if submit_button and tracking_id:
            shipment = track_shipment(tracking_id)
            
            if shipment:
                st.success("✅ Shipment found!")
                
                # Display shipment details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📋 Shipment Details")
                    st.write(f"**🏷️ Tracking ID:** {shipment[1]}")
                    st.write(f"**👤 Sender:** {shipment[2]}")
                    st.write(f"**👥 Receiver:** {shipment[3]}")
                    st.write(f"**📍 From:** {shipment[4]}")
                    st.write(f"**🎯 To:** {shipment[5]}")
                    st.write(f"**⚖️ Weight:** {shipment[10]} kg")
                    st.write(f"**📦 Product Type:** {shipment[11]}")

                with col2:
                    st.markdown("### 📊 Delivery Info")
                    st.write(f"**🚚 Delivery Type:** {shipment[6]}")
                    st.write(f"**📅 Estimated Delivery:** {shipment[7]}")
                    st.write(f"**💰 Payment:** ₹ {shipment[12]}")
                    status = shipment[8]
                    if status == "Delivered":
                        st.success(f"**📦 Status:** {status}")
                    elif status == "Out for Delivery":
                        st.info(f"**🚚 Status:** {status}")
                    elif status == "In Transit":
                        st.info(f"**🚚 Status:** {status}")
                    elif status == "Picked Up":
                        st.info(f"**📦 Status:** {status}")
                    elif status == "Cancelled":
                        st.error(f"**🚫 Status:** {status}")
                    else:
                        st.warning(f"**⏳ Status:** {status}")
                
                # Progress bar
                if status == "Delivered":
                    st.progress(1.0, "✅ Delivered")
                elif status == "Out for Delivery":
                    st.progress(0.8, "📦 Out for Delivery")
                elif status == "In Transit":
                    st.progress(0.6, "🚚 In Transit")
                elif status == "Picked Up":
                    st.progress(0.4, "📦 Picked Up")
                elif status == "Cancelled":
                    st.progress(0.0, "🚫 Cancelled")
                else:
                    st.progress(0.2, "⏳ Pending")
                    
            else:
                st.error("❌ Shipment not found! Please check the tracking ID.")

# Delivery Staff Dashboard
elif st.session_state.current_page == "🚚 Delivery Dashboard":
    if not st.session_state.logged_in:
        st.error("❌ Please login to access the delivery dashboard!")
        st.stop()
    if st.session_state.user_role != 'delivery_staff':
        st.error("❌ Delivery staff access required!")
        st.stop()

    st.title("🚚 Delivery Staff Dashboard")
    st.markdown("---")

    st.markdown("### 📋 Active Delivery Assignments")
    df = get_all_shipments()
    delivery_df = df[~df['status'].isin(['Delivered', 'Cancelled'])]

    if delivery_df.empty:
        st.info("📭 No active delivery assignments available.")
    else:
        def color_status(val):
            if val == 'Delivered':
                return 'background-color: #d4edda'
            elif val == 'Out for Delivery':
                return 'background-color: #cfe2ff'
            elif val == 'In Transit':
                return 'background-color: #d1ecf1'
            elif val == 'Picked Up':
                return 'background-color: #fff3cd'
            else:
                return 'background-color: #fff3cd'

        styled_df = delivery_df.style.applymap(color_status, subset=['status'])
        st.dataframe(styled_df, use_container_width=True)

    st.markdown("---")
    st.subheader("🔄 Update Shipment Status")

    delivery_status_options = ['Picked Up', 'In Transit', 'Out for Delivery', 'Delivered']
    with st.form("delivery_update_status_form"):
        update_tracking = st.text_input("📌 Tracking ID to update", placeholder="Enter tracking ID")
        update_status = st.selectbox("📍 New Status", delivery_status_options)
        update_submit = st.form_submit_button("✅ Update Status")

        if update_submit:
            if update_tracking and update_status:
                shipment = track_shipment(update_tracking)
                if shipment:
                    if shipment[8] == 'Cancelled':
                        st.warning("⚠️ Cancelled shipments cannot be updated.")
                    else:
                        if update_shipment_status(update_tracking, update_status):
                            st.success(f"✅ Shipment {update_tracking} status updated to {update_status}.")
                            st.experimental_rerun()
                        else:
                            st.error("❌ Invalid status selected.")
                else:
                    st.error("❌ Tracking ID not found.")
            else:
                st.error("❌ Please enter a tracking ID and select a status.")


# Admin Dashboard
elif st.session_state.current_page == "📊 Admin Dashboard":
    if not st.session_state.logged_in:
        st.error("❌ Please login to access dashboard!")
        st.stop()
    
    if st.session_state.user_role != 'admin':
        st.error("❌ Admin access required!")
        st.stop()
    
    st.title("📊 Admin Dashboard")
    st.markdown("---")
    
    # Get statistics
    total, delivered, pending = get_shipment_stats()
    
    # Get cancelled count
    conn = sqlite3.connect('database.db')
    df = pd.read_sql('SELECT * FROM shipments', conn)
    conn.close()
    cancelled = len(df[df['status'] == 'Cancelled'])
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 Total Shipments", total)
    with col2:
        st.metric("✅ Delivered", delivered)
    with col3:
        st.metric("⏳ Pending", pending)
    with col4:
        st.metric("🚫 Cancelled", cancelled)
    
    st.markdown("---")
    
    # Shipments table
    st.subheader("📋 All Shipments")
    
    df = get_all_shipments()
    
    if not df.empty:
        # Add status colors
        def color_status(val):
            if val == 'Delivered':
                return 'background-color: #d4edda'
            elif val == 'Out for Delivery':
                return 'background-color: #cfe2ff'
            elif val == 'In Transit':
                return 'background-color: #d1ecf1'
            elif val == 'Picked Up':
                return 'background-color: #fff3cd'
            elif val == 'Cancelled':
                return 'background-color: #f8d7da'
            else:
                return 'background-color: #fff3cd'
        
        styled_df = df.style.applymap(color_status, subset=['status'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Export button
        if st.button("📥 Export to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download shipments.csv",
                data=csv,
                file_name='shipments.csv',
                mime='text/csv'
            )
    else:
        st.info("📭 No shipments found in the system.")

# Manage Shipments
elif st.session_state.current_page == "📊 Manage Shipments":
    if not st.session_state.logged_in:
        st.error("❌ Please login to access!")
        st.stop()
    
    if st.session_state.user_role != 'admin':
        st.error("❌ Admin access required!")
        st.stop()
    
    st.title("📊 Manage Shipments")
    st.markdown("---")
    
    df = get_all_shipments()
    
    if df.empty:
        st.info("No shipments to manage.")
    else:
        st.subheader("🛠 Admin Actions")
        with st.form("admin_cancel_form"):
            cancel_tracking = st.text_input("📌 Tracking ID to cancel", placeholder="Enter tracking ID")
            cancel_submit = st.form_submit_button("🚫 Cancel Shipment")
            if cancel_submit:
                if cancel_tracking:
                    shipment = track_shipment(cancel_tracking)
                    if shipment:
                        if shipment[8] != 'Cancelled':
                            cancel_shipment(cancel_tracking)
                            st.success(f"✅ Shipment {cancel_tracking} is now Cancelled.")
                            st.experimental_rerun()
                        else:
                            st.warning(f"ℹ️ Shipment {cancel_tracking} is already Cancelled.")
                    else:
                        st.error("❌ Tracking ID not found.")
                else:
                    st.error("❌ Please enter a tracking ID.")

        st.markdown("---")

        st.subheader("🔄 Update Shipment Status")
        with st.form("admin_update_status_form"):
            update_tracking = st.text_input("📌 Tracking ID to update", placeholder="Enter tracking ID")
            update_status = st.selectbox("📍 New Status", SHIPMENT_STATUS_OPTIONS)
            update_submit = st.form_submit_button("✅ Update Status")
            if update_submit:
                if update_tracking and update_status:
                    if track_shipment(update_tracking):
                        if update_shipment_status(update_tracking, update_status):
                            notify(f"Your shipment is now {update_status}.")
                            st.rerun()
                        else:
                            st.error("❌ Invalid status selected.")
                    else:
                        st.error("❌ Tracking ID not found.")
                else:
                    st.error("❌ Please enter a tracking ID and select a status.")

        st.markdown("---")

        st.subheader("✏️ Edit Shipment Data")
        # Prepare for editing
        df['Delete'] = False
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
        if st.button("💾 Save Changes"):
            # Process deletions
            to_delete = edited_df[edited_df['Delete']]['id'].tolist()
            for shipment_id in to_delete:
                conn = sqlite3.connect('database.db')
                c = conn.cursor()
                c.execute('DELETE FROM shipments WHERE id = ?', (shipment_id,))
                conn.commit()
                conn.close()
            
            # Process inserts and updates
            original_ids = set(df['id'])
            for _, row in edited_df.iterrows():
                if pd.isna(row['id']) or row['id'] not in original_ids:
                    # Insert new shipment
                    conn = sqlite3.connect('database.db')
                    c = conn.cursor()
                    c.execute('''INSERT INTO shipments 
                        (tracking_id, sender_name, receiver_name, source_city, destination_city, delivery_type, estimated_delivery, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                        (row['tracking_id'], row['sender_name'], row['receiver_name'], row['source_city'], row['destination_city'], 
                         row['delivery_type'], row['estimated_delivery'], row['status']))
                    conn.commit()
                    conn.close()
                elif row['id'] in original_ids:
                    # Update existing
                    conn = sqlite3.connect('database.db')
                    c = conn.cursor()
                    c.execute('''UPDATE shipments SET 
                        tracking_id=?, sender_name=?, receiver_name=?, source_city=?, destination_city=?, 
                        delivery_type=?, estimated_delivery=?, status=? WHERE id=?''',
                        (row['tracking_id'], row['sender_name'], row['receiver_name'], row['source_city'], row['destination_city'], 
                         row['delivery_type'], row['estimated_delivery'], row['status'], row['id']))
                    conn.commit()
                    conn.close()
            
            st.success("✅ Changes saved successfully!")
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>🚚 Courier Management System Prototype | Built with Streamlit by LG-5</p>
</div>
""", unsafe_allow_html=True)
