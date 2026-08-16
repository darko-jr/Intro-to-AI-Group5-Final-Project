# Smartech: Student Academic Risk Early-Warning System

**Ashesi University · CS 254 Introduction to Artificial Intelligence · Cohort 2026**  
**Group 5 Members:** Daniel, Victoria, Esbert, and Vera

---

## 1. Project Overview

**Smartech** is an Explainable AI (XAI) early-warning and decision-support system designed to identify secondary students at risk of academic failure in Portuguese language courses ($G3 \le 9/20$) using early academic performance ($G1$), attendance records, and behavioral factors.

### Key Model Performance (Sprint 2 Tuned Model)
- **Algorithm:** Random Forest Classifier (Optimized with 5-Fold Cross-Validation)
- **Test Accuracy:** **80.6%** (vs. 76.5% baseline)
- **Macro F1-Score:** **0.710**
- **Weighted F1-Score:** **0.791**
- **Critical Misclassification Rate:** **0%** (Zero High-Risk students classified as Low-Risk)
- **Feature Space:** Reduced from 30+ to **Top 10 most influential features** ($G1$, `failures`, `absences`, `age`, `health`, `freetime`, `Walc`, `goout`, `Medu`, `famrel`)

---

## 2. Repository Structure

```text
Intro-to-AI-Group5-Final-Project/
├── data/
│   ├── raw/
│   │   ├── student-mat.csv
│   │   └── student-por.csv
│   └── processed/
│       ├── X_train.csv
│       ├── X_val.csv
│       ├── X_test.csv
│       ├── y_train.csv
│       ├── y_val.csv
│       └── y_test.csv
├── models/
│   ├── student_risk_model.pkl
│   └── student_risk_pipeline.pkl
├── notebooks/
│   ├── data_preprocessing.ipynb
│   ├── Final_Development_Sprint1&2.ipynb
│   └── GUI_PREDICTION.ipynb
├── docs/
│   ├── USER_GUIDE_AND_INTERPRETATION.md
│   ├── explanation_of_graphs.txt
│   └── FINAL_REPORT_TEMPLATE_AND_CHECKLIST.md
├── templates/
│   └── index.html
├── static/
│   ├── app.js
│   └── styles.css
├── app.py
├── prediction_engine.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 3. Quickstart & Reproducibility Guide

### Step 1: Clone & Navigate
```bash
git clone https://github.com/darko-jr/Intro-to-AI-Group5-Final-Project.git
cd Intro-to-AI-Group5-Final-Project
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Launch Web Application

```bash
python app.py
```
Open **http://127.0.0.1:7860** in your web browser.

---


