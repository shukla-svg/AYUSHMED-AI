import os
import json
import joblib
import numpy as np
import pandas as pd
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

FUSION_DIR = os.path.join(
    BASE_DIR,
    "models",
    "fusion"
)

PRETRAINED_MODEL = "Iloriayomide/Symptom_Prediction"

EVALUATION_SAMPLES = 1000
BATCH_SIZE = 16


# ============================================================
# CREATE NEW FUSION DIRECTORY
# ============================================================

os.makedirs(
    FUSION_DIR,
    exist_ok=True
)


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

df = pd.read_csv(
    DATA_PATH
)

print(
    "Dataset:",
    df.shape
)

print(
    "Diseases:",
    df["diseases"].nunique()
)


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
# 3. CREATE VALIDATION SET
# ============================================================

validation_df = X_test.copy()

validation_df["diseases"] = (
    y_test.values
)


if len(validation_df) > EVALUATION_SAMPLES:

    validation_df = validation_df.sample(
        n=EVALUATION_SAMPLES,
        random_state=42
    )


validation_df = validation_df.reset_index(
    drop=True
)


X_val = validation_df.drop(
    columns=["diseases"]
)

y_val = validation_df["diseases"]


print(
    "Validation samples:",
    len(X_val)
)


# ============================================================
# 4. LOAD OLD MODELS
# ============================================================

print("\n========================================")
print("LOADING OLD MODELS")
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
    "Logistic Regression loaded"
)

print(
    "Naive Bayes loaded"
)


# ============================================================
# 5. OLD MODEL PROBABILITIES
# ============================================================

print("\n========================================")
print("CALCULATING OLD MODEL PROBABILITIES")
print("========================================")


logistic_prob = (
    logistic_model.predict_proba(
        X_val
    )
)

nb_prob = (
    nb_model.predict_proba(
        X_val
    )
)


old_prob = (
    0.60 * logistic_prob
    +
    0.40 * nb_prob
)


old_classes = list(
    logistic_model.classes_
)


print(
    "Old model probabilities ready"
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


device = torch.device(
    "cpu"
)

pretrained_model.to(
    device
)


print(
    "Pretrained model loaded"
)


# ============================================================
# 7. PREPARE LABEL MAPPING
# ============================================================

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
    for label in old_classes
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
    "Old classes:",
    len(old_classes)
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
print("PREPARING TEXT INPUT")
print("========================================")


texts = [
    row_to_text(
        row,
        symptom_columns
    )
    for _, row in X_val.iterrows()
]


print(
    "Text samples:",
    len(texts)
)


# ============================================================
# 9. PRETRAINED PROBABILITIES
# ============================================================

print("\n========================================")
print("CALCULATING PRETRAINED PROBABILITIES")
print("========================================")


pretrained_probabilities = []

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


    pretrained_probabilities.extend(
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


pretrained_probabilities = np.array(
    pretrained_probabilities
)


print("\n")


# ============================================================
# 10. ALIGN PRETRAINED PROBABILITIES
# ============================================================

print("========================================")
print("ALIGNING MODEL LABELS")
print("========================================")


pretrained_indices = []

old_indices = []


for normalized_label in common_labels:

    pretrained_original = (
        pretrained_label_map[
            normalized_label
        ]
    )

    old_original = (
        old_label_map[
            normalized_label
        ]
    )


    pretrained_index = (
        pretrained_labels.index(
            pretrained_original
        )
    )

    old_index = old_classes.index(
        old_original
    )


    pretrained_indices.append(
        pretrained_index
    )

    old_indices.append(
        old_index
    )


old_common_prob = (
    old_prob[
        :,
        old_indices
    ]
)


pretrained_common_prob = (
    pretrained_probabilities[
        :,
        pretrained_indices
    ]
)


print(
    "Common probability matrix:",
    old_common_prob.shape
)


# ============================================================
# 11. TEST FUSION WEIGHTS
# ============================================================

print("\n========================================")
print("TESTING FUSION WEIGHTS")
print("========================================")


weights = [
    0.0,
    0.1,
    0.2,
    0.3,
    0.4,
    0.5,
    0.6,
    0.7,
    0.8,
    0.9,
    1.0
]


results = []


best_weight = None
best_f1 = -1


for old_weight in weights:

    pretrained_weight = (
        1.0 - old_weight
    )


    fused_probability = (
        old_weight * old_common_prob
        +
        pretrained_weight
        * pretrained_common_prob
    )


    prediction_indices = (
        fused_probability.argmax(
            axis=1
        )
    )


    predictions = [
        common_labels[index]
        for index in prediction_indices
    ]


    true_normalized = [
        normalize_label(label)
        for label in y_val
    ]


    accuracy = accuracy_score(
        true_normalized,
        predictions
    )


    precision, recall, f1, _ = (
        precision_recall_fscore_support(
            true_normalized,
            predictions,
            average="macro",
            zero_division=0
        )
    )


    results.append(
        {
            "old_weight": old_weight,
            "pretrained_weight": pretrained_weight,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1
        }
    )


    print(
        f"Old={old_weight:.1f} | "
        f"Pretrained={pretrained_weight:.1f} | "
        f"Accuracy={accuracy:.4f} | "
        f"F1={f1:.4f}"
    )


    if f1 > best_f1:

        best_f1 = f1

        best_weight = old_weight


# ============================================================
# 12. SAVE BEST FUSION CONFIGURATION
# ============================================================

best_pretrained_weight = (
    1.0 - best_weight
)


fusion_config = {
    "old_model": {
        "logistic_weight": 0.60,
        "naive_bayes_weight": 0.40
    },
    "fusion": {
        "old_model_weight": best_weight,
        "pretrained_model_weight": best_pretrained_weight
    },
    "validation_samples": len(X_val),
    "common_classes": len(common_labels),
    "pretrained_model": PRETRAINED_MODEL,
    "selection_metric": "macro_f1",
    "best_macro_f1": float(best_f1)
}


config_path = os.path.join(
    FUSION_DIR,
    "fusion_config.json"
)


with open(
    config_path,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        fusion_config,
        file,
        indent=4
    )


# ============================================================
# 13. FINAL RESULT
# ============================================================

print("\n========================================")
print("BEST FUSION CONFIGURATION")
print("========================================")


print(
    f"Old model weight       : "
    f"{best_weight:.1f}"
)


print(
    f"Pretrained model weight: "
    f"{best_pretrained_weight:.1f}"
)


print(
    f"Best Macro F1          : "
    f"{best_f1:.4f}"
)


print(
    "\nSaved configuration:"
)

print(
    config_path
)


print("\n========================================")
print("FUSION VALIDATION COMPLETE")
print("========================================")


print(
    "\nOLD MODEL FILES WERE NOT MODIFIED."
)

print(
    "New fusion configuration was saved separately."
)