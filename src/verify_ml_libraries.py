
import sys
import os

# =====================================================
# 1. ADD GEO MINE PACKAGE DIRECTORY
# =====================================================

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

package_dir = os.path.join(
    project_dir,
    "ml_packages"
)

sys.path.insert(0, package_dir)

print("======================================")
print("ML LIBRARY COMPATIBILITY TEST")
print("======================================")

print("Python:", sys.version)

# =====================================================
# 2. IMPORT LIBRARIES
# =====================================================

import numpy as np
import scipy
import sklearn
import joblib
import threadpoolctl

print("\nLIBRARY VERSIONS")
print("--------------------------------------")

print("NumPy:", np.__version__)
print("SciPy:", scipy.__version__)
print("Scikit-learn:", sklearn.__version__)
print("Joblib:", joblib.__version__)
print("Threadpoolctl:", threadpoolctl.__version__)

# =====================================================
# 3. RANDOM FOREST TEST
# =====================================================

print("\nTESTING RANDOM FOREST")
print("--------------------------------------")

from sklearn.ensemble import RandomForestClassifier

X = np.array([
    [0.1, 0.2],
    [0.2, 0.3],
    [0.8, 0.7],
    [0.9, 0.8],
    [0.15, 0.25],
    [0.85, 0.75]
])

y = np.array([0, 0, 1, 1, 0, 1])

model = RandomForestClassifier(
    n_estimators=10,
    random_state=42,
    n_jobs=1
)

model.fit(X, y)

predictions = model.predict(X)

print("Model:", type(model).__name__)
print("Training completed:", True)
print("Predictions:", predictions.tolist())

# =====================================================
# 4. JOBLIB TEST
# =====================================================

print("\nTESTING JOBLIB")
print("--------------------------------------")

model_file = os.path.join(
    project_dir,
    "models",
    "ml_library_test.joblib"
)

os.makedirs(os.path.dirname(model_file), exist_ok=True)

joblib.dump(model, model_file)

loaded_model = joblib.load(model_file)

print("Model saved:", os.path.exists(model_file))
print("Model loaded:", loaded_model is not None)

# =====================================================
# 5. FINAL VALIDATION
# =====================================================

print("\nFINAL VALIDATION")
print("--------------------------------------")

if len(predictions) != 6:
    raise Exception("Random Forest test failed.")

if not os.path.exists(model_file):
    raise Exception("Joblib save test failed.")

print("NumPy and SciPy imports: SUCCESS")
print("Scikit-learn import: SUCCESS")
print("Random Forest training: SUCCESS")
print("Joblib save/load: SUCCESS")

print("\nML LIBRARY VERIFICATION COMPLETED")
