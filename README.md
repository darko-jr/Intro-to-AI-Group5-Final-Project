# Smartech: Student Academic Risk Early-Warning & Decision Support System

---

## 1. Project Overview

**Smartech** is an Explainable AI (XAI) early-warning and decision-support system designed to forecast secondary student risk of academic failure in Portuguese language courses ($G3 \le 9/20$) early in the academic term. By synthesizing first-period academic performance ($G1$), historical course failures, attendance patterns, and lifestyle support indicators, the platform provides actionable, multi-tiered risk classifications and prescriptive intervention workflows for academic advisors and educators.

### Key Model Performance (Sprint 2 Tuned Model)
- **Algorithm:** Random Forest Classifier (Optimized via 5-Fold Stratified Cross-Validation)
- **Test Accuracy:** **80.61%** (vs. 76.53% Sprint 1 baseline)
- **Macro F1-Score:** **0.7101** | **Weighted F1-Score:** **0.7910**
- **Critical Safety:** **0.0% False Negatives** (Zero High-Risk students classified as Low-Risk on held-out test data)
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
│   ├── FINAL_PROJECT_REPORT.docx        # Editable Word Document Final Report
│   ├── FINAL_PROJECT_REPORT.md          # Complete Markdown Final Report
│   └── USER_GUIDE_AND_INTERPRETATION.md # Comprehensive User Guide & Technical Manual
├── templates/
│   └── index.html                       # Responsive web portal with SVG gauges & roster grid
├── static/
│   ├── styles.css                       # HSL-tailored design system, tokens, and animations
│   └── app.js                           # Client-side inference, roster filtering, and persistence
├── app.py                               # FastAPI ASGI web application & REST API server
├── prediction_engine.py                 # Self-contained ML engine, alias mapping & recommendations
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
Open your web browser and navigate to:
**`http://127.0.0.1:7860`** *(or the port printed in your console)*

### Dashboard Architecture & Feature Tour:
1. **Teacher Command Center & Class Roster (Dashboard):**
   * **Class Roster Grid:** Displays enrolled students with ID tags, risk badges, and baseline scores ($G1$, absences, failures).
   * **One-Click Student Inspection:** Selecting any student instantly loads their indicators into the 10 interactive sliders and recalculates risk in real time.
   * **Quick Risk Filtering:** Filter roster by `All`, `High Risk`, `Moderate`, or `Low Risk`.
   * **Random Student Picker:** 1-click random case testing.
   * **Live Visual Gauges:** 3 animated circular SVG gauges for Composite Academic Risk (%), Model Certainty (%), and $G1$ Grade.
   * **Explainable AI (XAI):** Real-time breakdown of top risk drivers versus protective factors.

2. **Prescriptive Recommendations (Intervention Plan):**
   * Multi-pillar intervention plan spanning Academic Remediation, Attendance Monitoring, Health/Counseling, and Habit Coaching.
   * Interactive check-off steps for counselors with direct audit logging to session history.

3. **What-If Scenario Simulator:**
   * Dual-panel sandbox evaluating projected student improvements (e.g. reducing absences from 16 to 4 days or raising $G1$ from 7 to 12).
   * Visualizes the Delta ($\Delta$) risk reduction and category shift.

4. **Cohort Batch Triage:**
   * Drag-and-drop CSV batch upload or 1-click loading of the sample test cohort ($N=98$).
   * **Smart Column Mapping:** Automatically maps common column aliases (e.g., `attendance` $\rightarrow$ `absences`, `grade1` $\rightarrow$ `G1`).
   * **Fallback Imputation:** Missing non-critical columns are automatically filled with neutral cohort medians without pipeline failure.
   * Generates cohort risk distribution KPIs and exportable CSV triage reports.
   * **Reset to Main Roster:** Toggle back to the full 649 enrolled database anytime.

5. **Session History Log:**
   * Chronological record of logged assessments with one-click CSV export.

6. **User Guide & Technical Interpretation Manual (`/guide`):**
   * Integrated documentation accessible via the top-navigation **User Guide** button, detailing feature weights, risk mathematics, clinical workflows, and FAQs.

7. **Full State Persistence:**
   * Uploaded datasets, selected student records, and active navigation tabs persist across browser page reloads via local storage caching.

### Method 2: Run via Jupyter Notebook
To run inference programmatically or inspect exploratory data analysis:
```bash
jupyter notebook notebooks/GUI_PREDICTION.ipynb
```

---

## 5. Short Usage Example (Python API)

You can import and run the self-contained prediction engine in Python:

```python
from prediction_engine import engine

# 1. Define a student profile using Student ID and top 10 indicators
sample_student = {
    "id": "STU-042",
    "G1": 7,          # First period grade (0-20, passing cutoff >= 10)
    "failures": 2,    # Past course failures (0-3+)
    "absences": 16,   # Term absences in days
    "age": 18,        # Student age
    "health": 2,      # Self-reported health status (1-5)
    "freetime": 4,    # Free time after school (1-5)
    "Walc": 4,        # Weekend alcohol consumption (1-5)
    "goout": 4,       # Social outing frequency (1-5)
    "Medu": 1,        # Mother's education level (0=None, 1=Primary, 2=Middle, 3=Secondary, 4=Higher Ed)
    "famrel": 2       # Family relationship quality (1-5)
}

# 2. Run model inference
result = engine.predict(sample_student)

# 3. View predicted risk tier and certainty
print("Predicted Risk Tier :", result["predicted_class"])  # 'High', 'Medium', or 'Low'
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
 - First Period Grade (G1): Low G1 Grade (7/20) falls below passing threshold (<= 9) (+44.7% impact)
 - Past Class Failures: 2 previous course failures (+17.0% impact)
 - Term Absences: 16 days missed exceeds safe threshold (+10.8% impact)

Recommended Action: [Urgent] Assign Peer Tutor and Remedial Review
Details: Student has early score of 7/20 and 2 prior failure(s). Foundational topic review recommended before midterm exams.
```

---

## 6. Academic Honesty & Responsible AI Governance

* **Course Context:** CS 254 Introduction to Artificial Intelligence, Ashesi University.
* **Human-in-the-Loop Safeguard:** Smartech is strictly an early-warning decision-support system. It does not replace teacher judgment or automate disciplinary actions.
* **Data Privacy:** Raw records are identified solely by anonymized Student IDs (`STU-001`, `STU-POR-008`). No Personally Identifiable Information (PII) is ingested or stored.

---

## 7. Team Contributions

* **Daniel Darko:** Machine learning pipeline development, Random Forest hyperparameter optimization, and Explainable AI (XAI) feature contribution engine.
* **Victoria Kyeremeh:** Data preprocessing, stratified train/validation/test partitioning, exploratory data analysis, and documentation.
* **Esbert A. Agbadi:** FastAPI backend server development, REST API endpoints, and What-If scenario simulation logic.
* **Vera Okyere-Ampofo:** User interface design system, SVG progress gauge visualizations, interactive class roster components, and documentation.
