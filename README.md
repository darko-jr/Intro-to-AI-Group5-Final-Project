# Smartech: Student Academic Risk Early-Warning & Decision Support System

**Ashesi University · Department of Computer Science & Information Systems**  
**CS 254: Introduction to Artificial Intelligence · End of Semester Project (Cohort 2026)**  
**Group 5 Members:** Daniel, Victoria, Esbert, and Vera

---

## 1. Project Overview

**Smartech** is an Explainable AI (XAI) early-warning and decision-support system designed to forecast secondary student risk of academic failure in Portuguese language courses ($G3 \le 9/20$) early in the term using first-period academic performance ($G1$), term attendance records, and behavioral factors.

### Key Model Performance (Sprint 2 Tuned Model)
- **Algorithm:** Random Forest Classifier (Optimized via 5-Fold Stratified Cross-Validation)
- **Test Accuracy:** **80.61%** (vs. 76.53% Sprint 1 baseline)
- **Macro F1-Score:** **0.7101** | **Weighted F1-Score:** **0.7910**
- **Critical Safety:** **0.0% False Negatives** (Zero High-Risk students classified as Low-Risk)
- **Feature Space:** Reduced from 30+ to **Top 10 most influential features** ($G1$, `failures`, `absences`, `age`, `health`, `freetime`, `Walc`, `goout`, `Medu`, `famrel`) — a 66.7% dimensionality reduction.

---

## 2. Repository Structure

```text
Intro-to-AI-Group5-Final-Project/
├── data/
│   ├── raw/
│   │   ├── student-mat.csv              # Benchmark math student records
│   │   └── student-por.csv              # Primary Portuguese student dataset (N=649)
│   └── processed/
│       ├── X_train.csv, y_train.csv     # 70% Stratified Training partition (N=454)
│       ├── X_val.csv, y_val.csv         # 15% Stratified Validation partition (N=97)
│       └── X_test.csv, y_test.csv       # 15% Stratified Test partition (N=98)
├── models/
│   ├── student_risk_model.pkl           # Trained Random Forest estimator
│   └── student_risk_pipeline.pkl        # Serialized pipeline with StandardScaler & top features
├── notebooks/
│   ├── data_preprocessing.ipynb         # EDA, target discretization, and stratified splitting
│   ├── Final_Development_Sprint1&2.ipynb# Sprint 1 vs Sprint 2 modeling and hyperparameter tuning
│   └── GUI_PREDICTION.ipynb             # Decision-support demo and model inference notebook
├── docs/
│   ├── FINAL_PROJECT_REPORT.docx        # Editable Word Document Final Report (6-10 pages)
│   ├── FINAL_PROJECT_REPORT.md          # Complete Markdown Final Report
│   └── USER_GUIDE_AND_INTERPRETATION.md # Technical documentation and XAI metric guide
├── templates/
│   └── index.html                       # Executive dashboard interface with SVG progress gauges
├── static/
│   ├── styles.css                       # Design tokens, layouts, and animations
│   └── app.js                           # Real-time inference client, search, and triage logic
├── app.py                               # FastAPI ASGI web application & REST API server
├── prediction_engine.py                 # Self-contained ML engine, XAI attribution & recommendations
├── requirements.txt                     # Reproducible environment dependencies
├── .gitignore                           # Git exclusion rules
└── README.md                            # Project overview, setup, and usage documentation
```

---

## 3. Setup & Installation Instructions

### Step 1: Clone the Repository
```bash
git clone https://github.com/darko-jr/Intro-to-AI-Group5-Final-Project.git
cd Intro-to-AI-Group5-Final-Project
```

### Step 2: Create and Activate Virtual Environment
```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 4. How to Run the System

### Method 1: Launch the Interactive Web Dashboard (Primary Interface)
Start the FastAPI server:
```bash
python app.py
```
Open your browser and navigate to:
**`http://127.0.0.1:7860`** *(or the dynamic port printed in your console)*

**Key Dashboard Features:**
1. **Dashboard Tab:** Live multi-feature sliders with real-time animated SVG progress rings for Academic Risk, Model Confidence, and $G1$ score.
2. **Recommendations Tab:** 4-Pillar prescriptive action plans with interactive check-off steps for counselors.
3. **What-If Simulator Tab:** Dual-slider simulation calculating projected risk score reductions and category shifts in real time.
4. **Cohort Triage Tab:** Drag-and-drop CSV dataset upload with real-time search, risk filtering, and CSV report export.
5. **Model Validation Tab:** Full academic validation metrics, 5-fold cross-validation results, and test confusion matrix.

### Method 2: Run via Jupyter Notebook
To run inference programmatically or explore data preprocessing:
```bash
jupyter notebook notebooks/GUI_PREDICTION.ipynb
```

---

## 5. Short Usage Example (Python API)

You can import and run the self-contained prediction engine in Python:

```python
from prediction_engine import engine

# 1. Define a student profile
sample_student = {
    "G1": 7,          # First period grade (0-20)
    "failures": 2,    # Past class failures (0-3)
    "absences": 16,   # Term absences
    "age": 18,        # Student age
    "health": 2,      # Health status (1-5)
    "freetime": 4,    # Free time after school (1-5)
    "Walc": 4,        # Weekend alcohol consumption (1-5)
    "goout": 4,       # Going out frequency (1-5)
    "Medu": 1,        # Mother's education level (0-4)
    "famrel": 2       # Family relationship quality (1-5)
}

# 2. Run model inference
result = engine.predict(sample_student)

# 3. View predicted risk tier and certainty
print("Predicted Risk Tier :", result["predicted_class"])  # e.g., 'High'
print("Certainty Confidence :", f"{result['confidence']}%")
print("Composite Risk Score :", f"{result['risk_score']} / 100")

# 4. View Explainable AI (XAI) contributing factors
print("\nPrimary Risk Drivers:")
for driver in result["contributions"]["risk_drivers"]:
    print(f" - {driver['name']}: {driver['description']} (+{driver['weight']}% impact)")

# 5. View top recommended counselor intervention
top_action = result["recommendations"][0]
print(f"\nRecommended Action: [{top_action['urgency']}] {top_action['action']}")
print(f"Details: {top_action['detail']}")
```

### Expected Output:
```text
Predicted Risk Tier : High
Certainty Confidence : 98.4%
Composite Risk Score : 79.2 / 100

Primary Risk Drivers:
 - First Period Grade (G1): Score of 7/20 is below passing threshold (+44.7% impact)
 - Past Class Failures: 2 previous course failures (+17.0% impact)
 - Term Absences: 16 days missed exceeds safe threshold (+10.8% impact)

Recommended Action: [High] Academic Tutoring & Foundational Remediation
Details: Schedule 2 hours/week of mandatory subject tutoring and conduct a diagnostic review.
```

---



