from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import sqlite3, os, joblib, secrets

# ---------------- CONFIG ----------------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "loans.db")

model = joblib.load("loan_model.pkl")

ADMIN_TOKEN = None


# ---------------- HOME ----------------
@app.route("/")
def home():
    return "Loan AI backend is running 🚀"


# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    global ADMIN_TOKEN
    data = request.json

    if data.get("username") == "admin" and data.get("password") == "admin123":
        ADMIN_TOKEN = secrets.token_hex(16)
        return jsonify({"token": ADMIN_TOKEN})

    return jsonify({"error": "Invalid credentials"}), 401


# ---------------- PREDICT (FIXED LOGIC) ----------------
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json

    income = float(data["income"])
    age = int(data["age"])
    loan_amount = float(data["loan_amount"])
    credit_score = int(data["credit_score"])

    # Derived feature
    dti = loan_amount / income

    # ML prediction (uses DTI-based model)
    ml_prediction = model.predict([[income, age, credit_score, dti]])[0]

    # ---------------- EXPLAINABLE LOGIC ----------------

    # Hard rejection rules (bank rules)
    if credit_score < 600:
        decision = "Rejected"
        reason = "Rejected due to low credit score (below 600)"

    elif dti > 10:
        decision = "Rejected"
        reason = "Rejected because loan amount is too high compared to income"

    elif age < 21:
        decision = "Rejected"
        reason = "Rejected because applicant is below minimum eligible age"

    # ML-based approval / rejection
    else:
        decision = ml_prediction

        if decision == "Approved":
            reason = (
                "Approved due to acceptable credit score, "
                "manageable loan-to-income ratio, and stable age profile"
            )
        else:
            if credit_score < 680:
                reason = "Rejected due to moderate credit score risk"
            else:
                reason = "Rejected due to overall financial risk pattern"

    # Interest rate calculation (only if approved)
    interest_rate = None

    if decision == "Approved":
       if credit_score >= 750 and dti < 4:
        interest_rate = 8.5
       elif credit_score >= 700 and dti < 6:
        interest_rate = 10.5
       else:
        interest_rate = 13.0
    

    # ---------------- SAVE TO DATABASE ----------------
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
    "reason": reason,
    "interest_rate": interest_rate
})



# ---------------- APPLICATIONS (ADMIN) ----------------
@app.route("/applications")
def applications():
    token = request.headers.get("Authorization")
    if token != ADMIN_TOKEN:
        return jsonify({"error": "Unauthorized"}), 403

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT income, age, loan_amount, credit_score, decision, reason
        FROM applications
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            "income": r[0],
            "age": r[1],
            "loan_amount": r[2],
            "credit_score": r[3],
            "decision": r[4],
            "reason": r[5]
        } for r in rows
    ])


# ---------------- STATS (ADMIN) ----------------
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


# ---------------- EXPORT CSV (ADMIN) ----------------
@app.route("/export")
def export():
    token = request.headers.get("Authorization")
    if token != ADMIN_TOKEN:
        return jsonify({"error": "Unauthorized"}), 403

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT income, age, loan_amount, credit_score, decision, reason
        FROM applications
    """)
    rows = cursor.fetchall()
    conn.close()

    def generate():
        yield "Income,Age,Loan Amount,Credit Score,Decision,Reason\n"
        for r in rows:
            yield f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]},{r[5]}\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=loan_applications.csv"}
    )
    
@app.route("/clear", methods=["POST"])
def clear_applications():
    token = request.headers.get("Authorization")
    if token != ADMIN_TOKEN:
        return jsonify({"error": "Unauthorized"}), 403

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM applications")
    conn.commit()
    conn.close()

    return jsonify({"message": "All applications cleared successfully"})


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
