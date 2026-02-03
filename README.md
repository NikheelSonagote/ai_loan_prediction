# loan-ai
# loan-ai
# 🏦 AI Loan Approval System (Full-Stack Project)

A full-stack AI-powered loan approval system that evaluates loan applications using
machine learning, business rules, and explainable decision logic.
The project includes a public frontend, secure admin dashboard, analytics, and CSV export.

---

## 🚀 Live Demo
- **Frontend:** https://<your-username>.github.io/<repo-name>/
- **Backend API:** https://ai-loan-prediction-a3gd.onrender.com

---

## 🧠 Features

### 👤 User Side
- Submit loan application (income, age, loan amount, credit score)
- Instant AI-based decision (Approved / Rejected)
- Clear, human-readable explanation for each decision

### 🔐 Admin Side
- Secure admin login (token-based authentication)
- View all loan applications
- Analytics dashboard (approval vs rejection)
- Export applications as CSV
- Clear all applications (admin only)

---

## 🤖 AI & Decision Logic

- Machine Learning model trained using:
  - Income
  - Age
  - Credit Score
  - **Debt-to-Income Ratio (DTI)**

- Decisions are made using a **hybrid approach**:
  1. **Business rules** (hard financial constraints)
  2. **ML prediction** for nuanced risk patterns
  3. **Explainable AI reasons** returned for every decision

This ensures decisions are:
- Realistic
- Safe
- Auditable
- Easy to explain

---

## 🛠️ Tech Stack

### Frontend
- HTML, CSS, JavaScript
- Chart.js (analytics dashboard)
- GitHub Pages (deployment)

### Backend
- Python
- Flask
- SQLite
- scikit-learn
- Token-based authentication
- Render (deployment)

---

## 📊 Dashboard Preview
- Approval vs Rejection chart
- Total applications count
- Average loan amount

---

## 🧪 Example Decision

