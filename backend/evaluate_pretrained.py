import os
import pandas as pd
import numpy as np
import joblib
import torch

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support
)

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "Diseases_and_Symptoms_dataset.csv"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "model"
)

PRETRAINED_MODEL = "Iloriayomide/Symptom_Prediction"

EVALUATION_SAMPLES = 1000
BATCH_SIZE = 16


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize_label(label):
    return " ".join(
        str(label).strip().lower().split()
    )


def calculate_metrics(y_true, y_pred):
    accuracy = accuracy_score(
        y_true,
        y_pred
    )

    precision, recall, f1, _ = (
        precision_recall_fscore_support(
            y_true,
            y_pred,
            average="macro",
            zero_division=0
        )
    )

    return accuracy, precision, recall, f1


def row_to_text(row, symptom_columns):
    active_symptoms = [
        symptom
        for symptom in symptom_columns
        if row[symptom] == 1
    ]

    if not active_symptoms:
        return "no symptoms"

    return ", ".join(active_symptoms)


# ============================================================
# 1. LOAD DATASET
# ============================================================

print("\n========================================")
print("LOADING DATASET")
print("========================================")

df = pd.read_csv(DATA_PATH)

print("Dataset:", df.shape)
print("Diseases:", df["diseases"].nunique())


# ============================================================
# 2. PREPARE DATA
# ============================================================

X = df.drop(
    columns=["diseases"]
)

y = df["diseases"]

symptom_columns = list(
    X.columns
)


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# ============================================================
# 3. CREATE EVALUATION SET
# ============================================================

test_df = X_test.copy()

test_df["diseases"] = y_test.values


if len(test_df) > EVALUATION_SAMPLES:

    test_df = test_df.sample(
        n=EVALUATION_SAMPLES,
        random_state=42
    )


test_df = test_df.reset_index(
    drop=True
)


X_eval = test_df.drop(
    columns=["diseases"]
)

y_eval = test_df["diseases"]


print(
    "Evaluation samples:",
    len(X_eval)
)


# ============================================================
# 4. LOAD EXISTING MODEL
# ============================================================

print("\n========================================")
print("LOADING EXISTING MODEL")
print("========================================")

logistic_model = joblib.load(
    os.path.join(
        MODEL_DIR,
        "logistic_model.pkl"
    )
)

nb_model = joblib.load(
    os.path.join(
        MODEL_DIR,
        "nb_model.pkl"
    )
)

print(
    "Old Logistic Regression model loaded"
)

print(
    "Old Naive Bayes model loaded"
)


# ============================================================
# 5. OLD ENSEMBLE EVALUATION
# ============================================================

print("\n========================================")
print("OLD ENSEMBLE EVALUATION")
print("========================================")


logistic_prob = (
    logistic_model.predict_proba(
        X_eval
    )
)

nb_prob = (
    nb_model.predict_proba(
        X_eval
    )
)


ensemble_prob = (
    0.60 * logistic_prob
    +
    0.40 * nb_prob
)


ensemble_prediction = (
    logistic_model.classes_[
        ensemble_prob.argmax(
            axis=1
        )
    ]
)


old_accuracy, old_precision, old_recall, old_f1 = (
    calculate_metrics(
        y_eval,
        ensemble_prediction
    )
)


print("\nOLD MODEL RESULTS")
print("------------------------------")

print(
    f"Accuracy : {old_accuracy:.4f}"
)

print(
    f"Precision: {old_precision:.4f}"
)

print(
    f"Recall   : {old_recall:.4f}"
)

print(
    f"F1 Score : {old_f1:.4f}"
)


# ============================================================
# 6. LOAD PRETRAINED MODEL
# ============================================================

print("\n========================================")
print("LOADING PRETRAINED MODEL")
print("========================================")


print(
    "Model:",
    PRETRAINED_MODEL
)


tokenizer = AutoTokenizer.from_pretrained(
    PRETRAINED_MODEL
)


pretrained_model = (
    AutoModelForSequenceClassification
    .from_pretrained(
        PRETRAINED_MODEL
    )
)


pretrained_model.eval()


print(
    "Pretrained model loaded successfully"
)


# ============================================================
# 7. PREPARE LABELS
# ============================================================

old_labels = list(
    logistic_model.classes_
)


pretrained_id2label = (
    pretrained_model.config.id2label
)


pretrained_labels = [
    pretrained_id2label[i]
    for i in range(
        pretrained_model.config.num_labels
    )
]


old_label_map = {
    normalize_label(label): label
    for label in old_labels
}


pretrained_label_map = {
    normalize_label(label): label
    for label in pretrained_labels
}


common_labels = sorted(
    set(old_label_map)
    &
    set(pretrained_label_map)
)


print(
    "\nOld model classes:",
    len(old_labels)
)

print(
    "Pretrained classes:",
    len(pretrained_labels)
)

print(
    "Common classes:",
    len(common_labels)
)


# ============================================================
# 8. CONVERT SYMPTOMS TO TEXT
# ============================================================

print("\n========================================")
print("CONVERTING SYMPTOMS TO TEXT")
print("========================================")


texts = [
    row_to_text(
        row,
        symptom_columns
    )
    for _, row in X_eval.iterrows()
]


print(
    "Text samples created:",
    len(texts)
)


# ============================================================
# 9. PRETRAINED MODEL EVALUATION
# ============================================================

print("\n========================================")
print("PRETRAINED MODEL EVALUATION")
print("========================================")


device = torch.device("cpu")

pretrained_model.to(device)


pretrained_predictions = []


total = len(texts)


for start in range(
    0,
    total,
    BATCH_SIZE
):

    batch_texts = texts[
        start:start + BATCH_SIZE
    ]


    inputs = tokenizer(
        batch_texts,
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt"
    )


    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }


    with torch.no_grad():

        outputs = pretrained_model(
            **inputs
        )


        probabilities = torch.softmax(
            outputs.logits,
            dim=1
        )


    pretrained_predictions.extend(
        probabilities.cpu().numpy()
    )


    completed = min(
        start + BATCH_SIZE,
        total
    )


    print(
        f"Processed {completed}/{total}",
        end="\r"
    )


pretrained_predictions = np.array(
    pretrained_predictions
)


print()


# ============================================================
# 10. MAP COMMON LABELS
# ============================================================

print("\n========================================")
print("MAPPING LABELS")
print("========================================")


common_indices = []


for normalized_label in common_labels:

    original_label = (
        pretrained_label_map[
            normalized_label
        ]
    )

    label_index = (
        pretrained_labels.index(
            original_label
        )
    )

    common_indices.append(
        label_index
    )


common_probabilities = (
    pretrained_predictions[
        :,
        common_indices
    ]
)


pretrained_common_predictions = []


for row in common_probabilities:

    best_index = np.argmax(row)


    normalized_prediction = (
        common_labels[
            best_index
        ]
    )


    original_prediction = (
        old_label_map[
            normalized_prediction
        ]
    )


    pretrained_common_predictions.append(
        original_prediction
    )


# ============================================================
# 11. PRETRAINED MODEL METRICS
# ============================================================

pretrained_accuracy, pretrained_precision, pretrained_recall, pretrained_f1 = (
    calculate_metrics(
        y_eval,
        pretrained_common_predictions
    )
)


print("\nPRETRAINED MODEL RESULTS")
print("------------------------------")


print(
    f"Accuracy : {pretrained_accuracy:.4f}"
)

print(
    f"Precision: {pretrained_precision:.4f}"
)

print(
    f"Recall   : {pretrained_recall:.4f}"
)

print(
    f"F1 Score : {pretrained_f1:.4f}"
)


# ============================================================
# 12. FINAL COMPARISON
# ============================================================

print("\n========================================")
print("MODEL COMPARISON")
print("========================================")


print(
    "\n                    OLD MODEL     PRETRAINED"
)

print(
    "----------------------------------------------"
)


print(
    f"Accuracy            "
    f"{old_accuracy:.4f}        "
    f"{pretrained_accuracy:.4f}"
)


print(
    f"Macro Precision     "
    f"{old_precision:.4f}        "
    f"{pretrained_precision:.4f}"
)


print(
    f"Macro Recall        "
    f"{old_recall:.4f}        "
    f"{pretrained_recall:.4f}"
)


print(
    f"Macro F1            "
    f"{old_f1:.4f}        "
    f"{pretrained_f1:.4f}"
)


# ============================================================
# 13. COMPLETE
# ============================================================

print("\n========================================")
print("EVALUATION COMPLETE")
print("========================================")


print(
    "\nExisting old model files were NOT modified."
)

print(
    "Pretrained model was evaluated separately."
)

print(
    "Next step: build the validation-based fusion layer."
)