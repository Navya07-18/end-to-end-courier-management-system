# 🚚 End-to-End Courier Management System (Prototype)

A modern, interactive **prototype of a Courier Management System** built using **Python, Streamlit, and SQLite**, demonstrating real-world courier operations such as booking, tracking, delivery workflows, and admin management.

---

## 📌 Project Goal

This project is designed as an **academic prototype** to simulate a real-world courier system.
It demonstrates **full-stack functionality within a single framework (Streamlit)**, integrating frontend UI, backend logic, and database operations.

---

## ✨ Key Features

### 🔐 User Authentication & Roles

* Secure login system using **SHA-256 password hashing**
* Role-based access:

  * 👤 Customer
  * 🚚 Delivery Staff
  * 📊 Admin

---

### 📦 Shipment Booking

* Enter sender & receiver details
* Select delivery type (Normal / Express)
* Automatic:

  * 🏷️ Tracking ID generation
  * 📅 Delivery date estimation
  * 💰 Payment calculation (based on weight & product type)

---

### 🧠 Smart Delivery Estimation

* **Normal Delivery:** 3–5 days
* **Express Delivery:** 1–2 days
* Based on delivery type using dynamic logic

---

### 🔍 Shipment Tracking

* Track shipments using tracking ID
* View complete shipment details
* Visual status indicators
* 📊 Progress bar showing delivery lifecycle

---

### 🚫 Shipment Cancellation

* Customers can cancel active shipments
* Restrictions:

  * Cannot cancel Delivered or Cancelled shipments

---

### 🚚 Delivery Staff Dashboard

* View active shipments
* Update delivery status:

  * Picked Up → In Transit → Out for Delivery → Delivered

---

### 📊 Admin Dashboard

* Real-time analytics:

  * Total shipments
  * Delivered
  * Pending
  * Cancelled
* Manage shipments:

  * Update status
  * Cancel shipments
  * Edit records
* 📥 Export data to CSV

---

## 🛠️ Technology Stack

* **Programming Language:** Python
* **Framework:** Streamlit
* **Database:** SQLite
* **Libraries:** Pandas, Hashlib, Datetime

---

## ⚙️ Installation & Setup

### Prerequisites

* Python 3.7 or higher
* pip package manager

### Steps

1. Clone the repository:

```bash
git clone https://github.com/your-username/end-to-end-courier-management-system.git
cd end-to-end-courier-management-system
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
streamlit run app.py
```

4. Open in browser:

```
http://localhost:8501
```

---

## 📁 Project Structure

```
├── app.py              # Main application file
├── database.db         # SQLite database (auto-created)
├── requirements.txt    # Dependencies
└── README.md
```

---

## 🎮 How to Use

### For Users:

1. Register a new account
2. Login to the system
3. Book a shipment
4. Track shipment using tracking ID
5. Cancel shipment (if required)

---

### For Delivery Staff:

1. Login with Delivery Staff role
2. View assigned shipments
3. Update shipment status

---

### For Admin:

1. Login with Admin role
2. Access dashboard analytics
3. Manage and update shipments
4. Export shipment data

---

## 🗄️ Database Schema

### Users Table

* id, username, email, password, role

### Shipments Table

* tracking_id, sender, receiver
* source, destination
* delivery_type, status
* weight, product_type, payment
* estimated_delivery, created_at

---

## 🎨 UI Features

* Responsive and interactive interface
* Real-time feedback (alerts, notifications)
* Styled dashboards and tables
* Progress tracking visualization
* Clean modern design

---

## 🔒 Security Features

* Password hashing using SHA-256
* Session-based authentication
* Role-based authorization
* Input validation

---

## 🐛 Troubleshooting

### Common Issues:

1. **Database Lock Error** → Close other running instances
2. **Port already in use** →

```bash
streamlit run app.py --server.port 8502
```

3. **Modules not found** → Install requirements again
4. **Permission issues** → Run with proper access

### Reset Database:

Delete `database.db` and restart the app

---

## ⚠️ Note

This is a **prototype system** demonstrating courier management functionality.
It is not production-ready but showcases **real-world system design and implementation concepts**.

---

## 🚀 Future Enhancements

* 📍 GPS-based real-time tracking
* 📱 Mobile application
* 💳 Payment gateway integration
* 📩 Email/SMS notifications
* 🤖 AI-based delivery prediction

---

## 🌍 Contribution to Society

* Improves delivery efficiency
* Reduces manual errors
* Supports small-scale logistics
* Encourages digital transformation

---

## 👩‍💻 Author

**Navya Myadarapu**
B.Tech CSE (AIML)
Aspiring AI Specialist

---

## ⭐ Acknowledgement

Developed as part of **Software Engineering coursework** to demonstrate system design, development, and deployment.

---

**🚚 Built with ❤️ using Streamlit**
