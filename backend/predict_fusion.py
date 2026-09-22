import os
import json
import joblib
import numpy as np
import torch
import pandas as pd

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification
)


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
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


# ============================================================
# LOAD FUSION CONFIGURATION
# ============================================================

with open(
    FUSION_CONFIG_PATH,
    "r",
    encoding="utf-8"
) as file:

    fusion_config = json.load(file)


OLD_MODEL_WEIGHT = float(
    fusion_config[
        "fusion"
    ][
        "old_model_weight"
    ]
)

PRETRAINED_MODEL_WEIGHT = float(
    fusion_config[
        "fusion"
    ][
        "pretrained_model_weight"
    ]
)


# ============================================================
# LOAD OLD MODELS
# ============================================================

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

available_symptoms = joblib.load(
    os.path.join(
        MODEL_DIR,
        "symptoms.pkl"
    )
)

ensemble_info = joblib.load(
    os.path.join(
        MODEL_DIR,
        "ensemble_info.pkl"
    )
)


# ============================================================
# LOAD PRETRAINED MODEL
# ============================================================

device = torch.device(
    "cpu"
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

pretrained_model.to(
    device
)


# ============================================================
# LABEL NORMALIZATION
# ============================================================

def normalize_label(label):
    """
    Normalize disease labels so that
    case/spacing differences do not create
    duplicate classes.
    """

    return " ".join(
        str(label)
        .strip()
        .lower()
        .split()
    )


# ============================================================
# BUILD LABEL MAPS
# ============================================================

old_classes = list(
    logistic_model.classes_
)


pretrained_id2label = (
    pretrained_model.config.id2label
)


pretrained_labels = [
    pretrained_id2label[index]
    for index in range(
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


# ============================================================
# ALIGN LABEL INDICES
# ============================================================

old_indices = []
pretrained_indices = []


for normalized_label in common_labels:

    old_original_label = (
        old_label_map[
            normalized_label
        ]
    )

    pretrained_original_label = (
        pretrained_label_map[
            normalized_label
        ]
    )


    old_indices.append(
        old_classes.index(
            old_original_label
        )
    )


    pretrained_indices.append(
        pretrained_labels.index(
            pretrained_original_label
        )
    )


# ============================================================
# SYMPTOMS → FEATURE VECTOR
# ============================================================

def create_feature_vector(
    matched_symptoms
):
    """
    Create a pandas DataFrame using the
    exact feature names used during training.
    """

    feature_vector = np.zeros(
        len(available_symptoms),
        dtype=np.float32
    )

    symptom_index = {
        symptom: index
        for index, symptom
        in enumerate(available_symptoms)
    }

    for symptom in matched_symptoms:

        if symptom in symptom_index:

            feature_vector[
                symptom_index[symptom]
            ] = 1

    # Keep the original feature names
    # used while training the sklearn models.
    X = pd.DataFrame(
        [feature_vector],
        columns=available_symptoms
    )

    return X


# ============================================================
# OLD MODEL PREDICTION
# ============================================================

def get_old_model_probabilities(
    matched_symptoms
):
    """
    Get Logistic Regression + Naive Bayes
    ensemble probabilities.
    """

    X = create_feature_vector(
        matched_symptoms
    )


    logistic_prob = (
        logistic_model
        .predict_proba(X)[0]
    )


    nb_prob = (
        nb_model
        .predict_proba(X)[0]
    )


    logistic_weight = float(
        ensemble_info.get(
            "logistic_weight",
            0.60
        )
    )


    nb_weight = float(
        ensemble_info.get(
            "nb_weight",
            0.40
        )
    )


    old_probability = (
        logistic_weight * logistic_prob
        +
        nb_weight * nb_prob
    )


    return old_probability


# ============================================================
# PRETRAINED MODEL PREDICTION
# ============================================================

def get_pretrained_probabilities(
    matched_symptoms
):
    """
    Convert symptoms to text and obtain
    pretrained model probabilities.
    """

    if not matched_symptoms:

        text = "no symptoms"

    else:

        text = ", ".join(
            matched_symptoms
        )


    inputs = tokenizer(
        text,
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


    return probabilities[
        0
    ].cpu().numpy()


# ============================================================
# FUSION PREDICTION
# ============================================================

def predict_fusion(
    matched_symptoms,
    top_k=3
):
    """
    Final hybrid prediction.

    Old model:
        Logistic Regression 60%
        Naive Bayes 40%

    Fusion:
        Old model 20%
        Pretrained model 80%
    """

    if not matched_symptoms:

        return []


    # --------------------------------------------------------
    # OLD MODEL
    # --------------------------------------------------------

    old_probability = (
        get_old_model_probabilities(
            matched_symptoms
        )
    )


    # --------------------------------------------------------
    # PRETRAINED MODEL
    # --------------------------------------------------------

    pretrained_probability = (
        get_pretrained_probabilities(
            matched_symptoms
        )
    )


    # --------------------------------------------------------
    # ALIGN BOTH MODELS TO COMMON 100 CLASSES
    # --------------------------------------------------------

    old_common_probability = (
        old_probability[
            old_indices
        ]
    )


    pretrained_common_probability = (
        pretrained_probability[
            pretrained_indices
        ]
    )


    # --------------------------------------------------------
    # FINAL FUSION
    # --------------------------------------------------------

    fused_probability = (
        OLD_MODEL_WEIGHT
        * old_common_probability
        +
        PRETRAINED_MODEL_WEIGHT
        * pretrained_common_probability
    )


    # --------------------------------------------------------
    # TOP PREDICTIONS
    # --------------------------------------------------------

    top_indices = np.argsort(
        fused_probability
    )[::-1][
        :top_k
    ]


    predictions = []


    for index in top_indices:

        normalized_label = (
            common_labels[index]
        )


        disease = (
            old_label_map[
                normalized_label
            ]
        )


        score = float(
            fused_probability[index]
            * 100
        )


        predictions.append(
            {
                "disease": str(
                    disease
                ),
                "confidence": round(
                    score,
                    2
                )
            }
        )


    return predictions


# ============================================================
# MODEL INFORMATION
# ============================================================

def get_fusion_info():
    """
    Return information about the loaded
    fusion system.
    """

    return {
        "old_model_weight": OLD_MODEL_WEIGHT,
        "pretrained_model_weight": PRETRAINED_MODEL_WEIGHT,
        "old_classes": len(old_classes),
        "pretrained_classes": len(pretrained_labels),
        "common_classes": len(common_labels),
        "pretrained_model": PRETRAINED_MODEL,
    }


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    print("\n========================================")
    print("AYUSHMED AI FUSION PREDICTOR")
    print("========================================")

    print(
        "Old model weight       :",
        OLD_MODEL_WEIGHT
    )

    print(
        "Pretrained model weight:",
        PRETRAINED_MODEL_WEIGHT
    )

    print(
        "Common classes        :",
        len(common_labels)
    )


    test_symptoms = [
        "fever",
        "headache",
        "cough"
    ]


    print("\nTest symptoms:")

    for symptom in test_symptoms:

        print(
            " -",
            symptom
        )


    predictions = predict_fusion(
        test_symptoms,
        top_k=3
    )


    print("\n========================================")
    print("FUSION PREDICTIONS")
    print("========================================")


    for number, prediction in enumerate(
        predictions,
        start=1
    ):

        print(
            f"{number}. "
            f"{prediction['disease']} "
            f"-> "
            f"{prediction['confidence']}%"
        )


    print("\n========================================")
    print("FUSION PREDICTOR READY")
    print("========================================")