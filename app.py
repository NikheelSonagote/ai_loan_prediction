from flask import session
from flask import Flask, jsonify, request
from flask_cors import CORS
import joblib
import sqlite3
import os
import csv
from flask import Response
import secrets



ADMIN_TOKEN = None
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "loans.db")
 
app = Flask(__name__)

app.secret_key = "super_secret_key_123"

app.config.update(
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_DOMAIN=".onrender.com"   # 👈 ADD THIS
)


app.secret_key = 'super_secret_key_123'  # For session management 
CORS(
    app,
    supports_credentials=True,
    resources={
        r"/*": {
            "origins": [
                "http://127.0.0.1:5500",
                "http://localhost:5500",
                "https://*.github.io"
            ]
        }
    }
)



model = joblib.load('loan_model.pkl')

@app.route("/")
def home():
    return "Loan AI backend is running 🚀"

@app.route("/predict", methods=["POST"])
def predict():

    try:            
        data = request.get_json()

        income = float(data.get("income", 0))
        age = int(data.get("age", 0))
        loan_amount = float(data.get("loan_amount", 0)) 
        credit_score = int(data.get("credit_score", 0))

        #Hard Validation (Bank Rules)
        if income <=0 or loan_amount <=0:
            return jsonify({
                "decision": "Rejected",
                "reason": "Income and Loan Amount must be positive value."
                })
        if age < 18:
            return jsonify({
                "decision": "Rejected",
                "reason": "Applicant must be at least 18 years old."
                })
        
        if credit_score < 300 or credit_score > 850:
            return jsonify({
                "decision": "Rejected",
                "reason": "Invalid credit score range."
                })
        
        prediction = model.predict([[income, age, loan_amount, credit_score]])[0]

        reasons = []

        if income < 30000:
            reasons.append("Income is too low")
        if credit_score < 700:
            reasons.append("Credit score is below 630")

        if loan_amount > income * 5:
            reasons.append("Loan amount is too high compared to income")

        if prediction == "Approved":
            reason_text = "Loan approved based on strong financial profile"
        else:
            reason_text = ", ".join(reasons) if reasons else "Does not meet bank policies"
            

        #SAVE TO DATABASE
        
        conn = sqlite3.connect('loans.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO applications (income, age, loan_amount, credit_score, decision, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (income, age, loan_amount, credit_score, prediction, reason_text))
       
        conn.commit()
        conn.close()

        
        return jsonify({
            "decision": prediction,
            "reason": reason_text
        })
    
    except Exception as e:
        return jsonify({
            "decision": "Error",
            "reason": str(e)
        }), 500
@app.route("/applications", methods=["GET"])
def get_applications():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403

    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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

    except Exception as e:
        print("🔥 APPLICATIONS ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/stats")
def stats():
    token = request.headers.get("Authorization")

    if token != ADMIN_TOKEN:
        return jsonify({"error": "Unauthorized"}), 403

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("SELECT decision, COUNT(*) FROM applications GROUP BY decision")
    decisions = cursor.fetchall()

    cursor.execute("SELECT AVG(loan_amount) FROM applications")
    avg_loan = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM applications")
    total = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "decisions": dict(decisions),
        "average_loan": round(avg_loan, 2),
        "total_applications": total
    })


    
@app.route("/export", methods=["GET"])
def export_csv():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT income, age, loan_amount, credit_score, decision, reason
        FROM applications
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    def generate():
        yield "Income,Age,Loan Amount,Credit Score,Decision,Reason\n"
        for row in rows:
            yield f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]}\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=loan_applications.csv"
        }
    )



@app.route("/clear", methods=["POST"])
def clear_applications():
        conn = sqlite3.connect("loans.db", check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM applications")
        conn.commit()
        conn.close()

        return jsonify({"message": "All applications cleared."})

@app.route("/login", methods=["POST"])
def login():
    global ADMIN_TOKEN
    data = request.json

    if data["username"] == "admin" and data["password"] == "admin123":
        ADMIN_TOKEN = secrets.token_hex(16)
        return jsonify({"token": ADMIN_TOKEN})

    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("admin", None)
    return jsonify({"message": "Logged out"})


if __name__ == "__main__":
    app.run()
 