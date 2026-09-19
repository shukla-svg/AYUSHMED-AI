import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import BernoulliNB
from sklearn.metrics import accuracy_score


# ==========================================
# 1. Paths
# ==========================================

DATA_PATH = "data/Diseases_and_Symptoms_dataset.csv"
MODEL_DIR = "model"

os.makedirs(MODEL_DIR, exist_ok=True)


# ==========================================
# 2. Load Dataset
# ==========================================

print("Loading dataset...")

df = pd.read_csv(DATA_PATH)

print("Dataset loaded successfully!")
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Diseases:", df["diseases"].nunique())
print(df.info())

# ==========================================
# 3. Features and Target
# ==========================================

X = df.drop(columns=["diseases"])
y = df["diseases"]


# ==========================================
# 4. Train-Test Split
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))
print("Features:", len(X.columns))


# ==========================================
# 5. Logistic Regression
# ==========================================

print("\nTraining Logistic Regression...")

logistic_model = LogisticRegression(
    max_iter=500,
    solver="lbfgs",
    random_state=42
)

logistic_model.fit(X_train, y_train)

print("Logistic Regression completed!")


# ==========================================
# 6. Bernoulli Naive Bayes
# ==========================================

print("\nTraining Bernoulli Naive Bayes...")

nb_model = BernoulliNB()

nb_model.fit(X_train, y_train)

print("Bernoulli Naive Bayes completed!")


# ==========================================
# 7. Individual Predictions
# ==========================================

print("\nCalculating predictions...")

logistic_prob = logistic_model.predict_proba(X_test)
nb_prob = nb_model.predict_proba(X_test)


# ==========================================
# 8. Ensemble
# ==========================================

print("Combining models...")

# Weighted ensemble
ensemble_prob = (
    0.60 * logistic_prob +
    0.40 * nb_prob
)

# Find class with highest probability
ensemble_prediction = logistic_model.classes_[
    ensemble_prob.argmax(axis=1)
]


# ==========================================
# 9. Accuracy
# ==========================================

logistic_prediction = logistic_model.predict(X_test)
nb_prediction = nb_model.predict(X_test)

logistic_accuracy = accuracy_score(
    y_test,
    logistic_prediction
)

nb_accuracy = accuracy_score(
    y_test,
    nb_prediction
)

ensemble_accuracy = accuracy_score(
    y_test,
    ensemble_prediction
)


print("\n================================")
print("MODEL RESULTS")
print("================================")

print(
    "Logistic Regression Accuracy:",
    round(logistic_accuracy * 100, 2),
    "%"
)

print(
    "Bernoulli NB Accuracy:",
    round(nb_accuracy * 100, 2),
    "%"
)

print(
    "Ensemble Accuracy:",
    round(ensemble_accuracy * 100, 2),
    "%"
)


# ==========================================
# 10. Save Models
# ==========================================

print("\nSaving models...")

joblib.dump(
    logistic_model,
    os.path.join(MODEL_DIR, "logistic_model.pkl")
)

joblib.dump(
    nb_model,
    os.path.join(MODEL_DIR, "nb_model.pkl")
)

joblib.dump(
    list(X.columns),
    os.path.join(MODEL_DIR, "symptoms.pkl")
)


# Save ensemble weights
ensemble_info = {
    "logistic_weight": 0.60,
    "nb_weight": 0.40,
    "accuracy": ensemble_accuracy
}

joblib.dump(
    ensemble_info,
    os.path.join(MODEL_DIR, "ensemble_info.pkl")
)


print("\nModels saved successfully!")

print("→ model/logistic_model.pkl")
print("→ model/nb_model.pkl")
print("→ model/symptoms.pkl")
print("→ model/ensemble_info.pkl")

print("\n================================")
print("TRAINING COMPLETED SUCCESSFULLY")
print("================================")