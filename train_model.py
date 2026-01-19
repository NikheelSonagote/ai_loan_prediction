import numpy as np
from sklearn.tree import DecisionTreeClassifier
import joblib

#Feature :
# [income, age, loan_amount, credit_score]
X = np.array([
    [50000, 30, 200000, 750],
    [300000, 22, 150000, 800],
    [80000, 45, 300000, 700],
    [20000, 25, 250000, 850],
    [90000, 35, 100000, 900],
])

#Labels :
y = ["Approved", "Rejected", "Approved", "Rejected", "Approved"]

model = DecisionTreeClassifier()
model.fit(X, y)
joblib.dump(model, 'loan_model.pkl')

print("Loan model trained")