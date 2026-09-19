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

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "Diseases_and_Symptoms_dataset.csv"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "model"
)

FUSION_CONFIG_PATH = os.path.join(
    BASE_DIR,
    "models",
    "fusion",
    "fusion_config.json"
)

PRETRAINED_MODEL = (
    "Iloriayomide/Symptom_Prediction"
)

BATCH_SIZE = 16

# Final test set size
TEST_SAMPLES = 5000


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize_label(label):
    return " ".join(
        str(label).strip().lower().split()
    )


def metrics(y_true, y_pred):

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

    return (
        accuracy,
        precision,
        recall,
        f1
    )


def row_to_text(row, symptoms):

    active = [
        symptom
        for symptom in symptoms
        if row[symptom] == 1
    ]

    if not active:
        return "no symptoms"

    return ", ".join(active)


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
# 2. CREATE SAME TEST SPLIT
# ============================================================

X = df.drop(
    columns=["diseases"]
)

y = df["diseases"]

symptoms = list(
    X.columns
)


_, X_test, _, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# Use a larger independent test sample
if len(X_test) > TEST_SAMPLES:

    X_test = X_test.sample(
        n=TEST_SAMPLES,
        random_state=123
    )

    y_test = y_test.loc[
        X_test.index
    ]


X_test = X_test.reset_index(
    drop=True
)

y_test = y_test.reset_index(
    drop=True
)


print(
    "Independent test samples:",
    len(X_test)
)


# ============================================================
# 3. LOAD FUSION CONFIG
# ============================================================

print("\n========================================")
print("LOADING FUSION CONFIGURATION")
print("========================================")


with open(
    FUSION_CONFIG_PATH,
    "r",
    encoding="utf-8"
) as file:

    fusion_config = json.load(
        file
    )


old_weight = (
    fusion_config[
        "fusion"
    ][
        "old_model_weight"
    ]
)

pretrained_weight = (
    fusion_config[
        "fusion"
    ][
        "pretrained_model_weight"
    ]
)


print(
    f"Old model weight       : "
    f"{old_weight}"
)

print(
    f"Pretrained model weight: "
    f"{pretrained_weight}"
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
print("OLD MODEL PREDICTIONS")
print("========================================")


logistic_prob = (
    logistic_model.predict_proba(
        X_test
    )
)

nb_prob = (
    nb_model.predict_proba(
        X_test
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


old_prediction_indices = old_prob.argmax(axis=1)

old_predictions = [
    old_classes[index]
    for index in old_prediction_indices
]


old_accuracy, old_precision, old_recall, old_f1 = (
    metrics(
        y_test,
        old_predictions
    )
)


print(
    f"Old model accuracy : "
    f"{old_accuracy:.4f}"
)

print(
    f"Old model F1       : "
    f"{old_f1:.4f}"
)


# ============================================================
# 6. LOAD PRETRAINED MODEL
# ============================================================

print("\n========================================")
print("LOADING PRETRAINED MODEL")
print("========================================")


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
# 7. LABEL MAPPING
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


old_indices = []
pretrained_indices = []


for label in common_labels:

    old_indices.append(
        old_classes.index(
            old_label_map[label]
        )
    )

    pretrained_indices.append(
        pretrained_labels.index(
            pretrained_label_map[label]
        )
    )


old_common_prob = (
    old_prob[
        :,
        old_indices
    ]
)


# ============================================================
# 8. CONVERT TEST SYMPTOMS TO TEXT
# ============================================================

print("\n========================================")
print("PREPARING TEST TEXT")
print("========================================")


texts = [
    row_to_text(
        row,
        symptoms
    )
    for _, row in X_test.iterrows()
]


print(
    "Test texts:",
    len(texts)
)


# ============================================================
# 9. PRETRAINED PREDICTIONS
# ============================================================

print("\n========================================")
print("PRETRAINED MODEL PREDICTIONS")
print("========================================")


pretrained_probabilities = []

total = len(texts)


for start in range(
    0,
    total,
    BATCH_SIZE
):

    batch = texts[
        start:start + BATCH_SIZE
    ]

    inputs = tokenizer(
        batch,
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


print()


pretrained_common_prob = (
    pretrained_probabilities[
        :,
        pretrained_indices
    ]
)


# ============================================================
# 10. PRETRAINED ONLY RESULT
# ============================================================

pretrained_prediction_indices = (
    pretrained_common_prob.argmax(
        axis=1
    )
)


pretrained_predictions = [
    common_labels[index]
    for index in pretrained_prediction_indices
]


true_labels = [
    normalize_label(label)
    for label in y_test
]


pre_accuracy, pre_precision, pre_recall, pre_f1 = (
    metrics(
        true_labels,
        pretrained_predictions
    )
)


# ============================================================
# 11. FINAL FUSION
# ============================================================

print("\n========================================")
print("FINAL FUSION")
print("========================================")


fused_probability = (
    old_weight * old_common_prob
    +
    pretrained_weight * pretrained_common_prob
)


fusion_prediction_indices = (
    fused_probability.argmax(
        axis=1
    )
)


fusion_predictions = [
    common_labels[index]
    for index in fusion_prediction_indices
]


fusion_accuracy, fusion_precision, fusion_recall, fusion_f1 = (
    metrics(
        true_labels,
        fusion_predictions
    )
)


# ============================================================
# 12. FINAL RESULTS
# ============================================================

print("\n========================================")
print("INDEPENDENT TEST RESULTS")
print("========================================")


print(
    "\n                    ACCURACY    F1"
)

print(
    "--------------------------------------"
)

print(
    f"Old Model           "
    f"{old_accuracy:.4f}      "
    f"{old_f1:.4f}"
)

print(
    f"Pretrained Model    "
    f"{pre_accuracy:.4f}      "
    f"{pre_f1:.4f}"
)

print(
    f"Fusion Model        "
    f"{fusion_accuracy:.4f}      "
    f"{fusion_f1:.4f}"
)


print("\n========================================")
print("FULL FUSION METRICS")
print("========================================")


print(
    f"Accuracy : {fusion_accuracy:.4f}"
)

print(
    f"Precision: {fusion_precision:.4f}"
)

print(
    f"Recall   : {fusion_recall:.4f}"
)

print(
    f"F1 Score : {fusion_f1:.4f}"
)


print("\n========================================")
print("TEST COMPLETE")
print("========================================")


print(
    "\nOld model files were NOT modified."
)

print(
    "Fusion configuration was only READ."
)