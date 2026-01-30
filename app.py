from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import sqlite3, os, joblib, secrets, csv

ADMIN_TOKEN = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "loans.db")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

model = joblib.load("loan_model.pkl")


@app.route("/")
def home():
    return "Loan AI backend is running 🚀"


# ---------- LOGIN ----------
@app.route("/login", methods=["POST"])
def login():
    global ADMIN_TOKEN
    data = request.json

    if data["username"] == "admin" and data["password"] == "admin123":
        ADMIN_TOKEN = secrets.token_hex(16)
        return jsonify({"token": ADMIN_TOKEN})

    return jsonify({"error": "Invalid credentials"}), 401


# ---------- PREDICT ----------
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json

    income = float(data["income"])
    age = int(data["age"])
    loan_amount = float(data["loan_amount"])
    credit_score = int(data["credit_score"])

    prediction = model.predict([[income, age, loan_amount, credit_score]])[0]

    reason = "Loan approved" if prediction == "Approved" else "Loan rejected"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO applications (income, age, loan_amount, credit_score, decision, reason)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (income, age, loan_amount, credit_score, prediction, reason))
    conn.commit()
    conn.close()

    return jsonify({"decision": prediction, "reason": reason})


# ---------------- LOAN PREDICTION (FIXED LOGIC) ----------------
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json

    income = float(data["income"])
    age = int(data["age"])
    loan_amount = float(data["loan_amount"])
    credit_score = int(data["credit_score"])

    # ---- 1️⃣ ML PREDICTION ----
    ml_prediction = model.predict([[income, age, loan_amount, credit_score]])[0]

    # ---- 2️⃣ BUSINESS SAFETY RULES (IMPORTANT FIX) ----
    decision = ml_prediction
    reason = ""

    # Rule 1: Credit score too low
    if credit_score < 600:
        decision = "Rejected"
        reason = "Rejected due to low credit score"

    # Rule 2: Loan too high compared to income
    elif loan_amount > income * 10:
        decision = "Rejected"
        reason = "Rejected due to loan amount too high compared to income"

    # Rule 3: Age risk (optional)
    elif age < 21:
        decision = "Rejected"
        reason = "Rejected due to age below minimum eligibility"

    # Approved case
    else:
        decision = "Approved"
        reason = "Approved based on acceptable income, credit score, and loan ratio"

    # ---- 3️⃣ SAVE TO DATABASE ----
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO applications (income, age, loan_amount, credit_score, decision, reason)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (income, age, loan_amount, credit_score, decision, reason))

    conn.commit()
    conn.close()

    return jsonify({
        "decision": decision,
        "reason": reason
    })


# ---------- STATS ----------
@app.route("/stats")
def stats():
    token = request.headers.get("Authorization")
    if token != ADMIN_TOKEN:
        return jsonify({"error": "Unauthorized"}), 403

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT decision, COUNT(*) FROM applications GROUP BY decision")
    decisions = dict(cursor.fetchall())

    cursor.execute("SELECT COUNT(*) FROM applications")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(loan_amount) FROM applications")
    avg_loan = cursor.fetchone()[0] or 0

    conn.close()

    return jsonify({
        "decisions": decisions,
        "total_applications": total,
        "average_loan": round(avg_loan, 2)
    })


# ---------- EXPORT ----------
@app.route("/export")
def export():
    token = request.headers.get("Authorization")
    if token != ADMIN_TOKEN:
        return jsonify({"error": "Unauthorized"}), 403

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications")
    rows = cursor.fetchall()
    conn.close()

    def generate():
        yield "Income,Age,Loan,Credit,Decision,Reason\n"
        for r in rows:
            yield f"{r[1]},{r[2]},{r[3]},{r[4]},{r[5]},{r[6]}\n"

    return Response(generate(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=loans.csv"})
