
import os
import json

# =====================================================
# 1. PROJECT PATH
# =====================================================

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

config_dir = os.path.join(
    project_dir,
    "config"
)

output_file = os.path.join(
    config_dir,
    "pu_learning_config.json"
)

os.makedirs(config_dir, exist_ok=True)

# =====================================================
# 2. PU LEARNING CONFIGURATION
# =====================================================

config = {
    "model_name": "Random Forest PU Ranking",

    "learning_strategy": "Repeated Unlabelled Sampling",

    "dataset": {
        "input_file": "data/processed/ml_training_dataset.csv",
        "positive_label": 1,
        "unlabelled_label": None,
        "expected_positive_cells": 16,
        "expected_unlabelled_cells": 112163,
        "expected_predictors": 31
    },

    "sampling": {
        "unlabelled_per_positive": 5,
        "repetitions": 10,
        "random_seed": 42,
        "sampling_with_replacement": False
    },

    "random_forest": {
        "n_estimators": 300,
        "max_depth": 12,
        "min_samples_leaf": 2,
        "max_features": "sqrt",
        "class_weight": "balanced",
        "random_state": 42,
        "n_jobs": 1
    },

    "spatial_validation": {
        "method": "Leave-One-Positive-Block-Out",
        "block_size_metres": 50000,
        "number_of_positive_blocks": 4
    },

    "feature_policy": {
        "use_geological_predictors_only": True,
        "exclude_expert_baseline": True,
        "exclude_ga_baseline": True,
        "exclude_deposit_coordinates": True,
        "exclude_block_id_as_predictor": True
    },

    "output": {
        "model_directory": "models",
        "prediction_directory": "outputs",
        "report_directory": "reports"
    }
}

# =====================================================
# 3. SAVE CONFIGURATION
# =====================================================

with open(
    output_file,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        config,
        file,
        indent=4
    )

# =====================================================
# 4. DISPLAY SUMMARY
# =====================================================

print("======================================")
print("PU LEARNING CONFIGURATION")
print("======================================")

print("Model:", config["model_name"])
print("Strategy:", config["learning_strategy"])
print("Positive cells:", config["dataset"]["expected_positive_cells"])
print("Unlabelled cells:", config["dataset"]["expected_unlabelled_cells"])
print("Predictors:", config["dataset"]["expected_predictors"])
print("Sampling repetitions:", config["sampling"]["repetitions"])
print("Unlabelled per positive:", config["sampling"]["unlabelled_per_positive"])
print("Random Forest trees:", config["random_forest"]["n_estimators"])
print("Spatial block size:", config["spatial_validation"]["block_size_metres"])

print("\nOutput:", output_file)
print("\nPU CONFIGURATION CREATED")
