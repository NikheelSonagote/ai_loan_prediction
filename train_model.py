import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
import joblib

# Load dataset
df = pd.read_csv("loan_data.csv")

# 🔹 Feature engineering
df["DTI"] = df["loan_amount"] / df["income"]

X = df[["income", "age", "credit_score", "DTI"]]
y = df["decision"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = DecisionTreeClassifier(max_depth=5)
model.fit(X_train, y_train)

# Evaluate
preds = model.predict(X_test)
accuracy = accuracy_score(y_test, preds)

print("Model accuracy:", accuracy)

# Save model
joblib.dump(model, "loan_model.pkl")
