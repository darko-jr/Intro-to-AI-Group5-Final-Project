# Smartech: Student Academic Risk Early-Warning System
## Comprehensive User Guide & Technical Interpretation Manual

**Course:** CS 254 Introduction to Artificial Intelligence  
**Institution:** Ashesi University, Ghana (Class of 2026)  
**Project Group:** Group 5 (Daniel, Victoria, Esbert, Vera)  
**Release Version:** Sprint 2 Production Release (v2.1)

---

## 1. Executive Summary & Clinical Intent

Smartech is an Explainable AI (XAI) early-warning decision support portal engineered to identify secondary school students at risk of academic failure before final examinations ($G3$). By analyzing multi-dimensional student indicators—spanning foundational academic standing, term attendance metrics, and lifestyle/support factors—the system discretizes student outcomes into three actionable risk tiers:

1. **High Academic Risk ($G3 \le 9/20$):** Student is forecasted to fail the course without immediate remedial intervention.
2. **Moderate Academic Risk ($10 \le G3 \le 14/20$):** Student is currently meeting minimum passing thresholds but exhibits vulnerability factors (e.g., attendance slippage or past failures).
3. **Low Academic Risk ($G3 \ge 15/20$):** Student exhibits strong academic mastery and stability.

> **Human-in-the-Loop Principle:** Smartech is strictly designed as an advisor-support mechanism. It does not automate disciplinary actions or final grading; rather, it empowers academic counselors and teachers with transparent, prescriptive guidance.

---

## 2. Machine Learning Architecture & Validation Metrics

The core predictive engine is powered by an optimized **Tuned Random Forest Classifier** ($n=100$ estimators, `max_depth=6`, `min_samples_split=5`, `class_weight='balanced'`), trained on the UCI Portuguese Secondary School dataset ($N=649$) and validated via 5-Fold Stratified Cross-Validation.

### 2.1 Benchmark Performance Metrics

| Evaluation Metric | Baseline Decision Tree | Baseline Random Forest | Tuned Random Forest (Deployed) |
| :--- | :--- | :--- | :--- |
| **Test Accuracy** | 71.43% | 76.53% | **80.61%** |
| **Macro F1-Score** | 0.5842 | 0.6481 | **0.7101** |
| **Weighted F1-Score** | 0.7024 | 0.7512 | **0.7910** |
| **Critical False Negatives** | 3 Students | 1 Student | **0 Students (0.0% FN Rate)** |

*Critical False Negatives represent High-Risk students mistakenly predicted as Low-Risk. Smartech achieves a 0.0% critical failure rate on held-out test data ($N=98$), ensuring zero at-risk students slip through the early-warning safety net.*

---

## 3. The 10 Key Indicators & Importance Weights

The model extracts 10 multi-dimensional features selected via Gini Impurity and Permutation Feature Importance:

| Rank | Feature Code | Feature Name | Measurement Scale | Importance Weight | Description & Thresholds |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `G1` | First Period Grade | 0 to 20 points | **44.68%** | Primary academic indicator. $\le 9$ is failing cutoff. |
| **2** | `failures` | Past Course Failures | 0 to 3+ courses | **16.95%** | Historical academic struggles across previous years. |
| **3** | `absences` | School Absences | 0 to 40+ days | **10.82%** | Unexcused missed school days during current term. $\ge 8$ triggers alert. |
| **4** | `age` | Student Age | 15 to 22 years | **5.73%** | Age relative to typical grade cohort. |
| **5** | `health` | Current Health Status | 1 (Poor) to 5 (Excellent) | **4.56%** | Self-reported physical and mental well-being. |
| **6** | `freetime` | Free Time After School | 1 (Very Low) to 5 (Very High)| **4.41%** | Available unstructured leisure time post-classes. |
| **7** | `Walc` | Weekend Alcohol Consumption | 1 (Very Low) to 5 (Very High)| **3.84%** | Self-reported weekend alcohol intake level. |
| **8** | `goout` | Social Outings with Friends | 1 (Very Low) to 5 (Very High)| **3.52%** | Frequency of socializing with peers on evenings. |
| **9** | `Medu` | Mother's Education Level | 0 (None) to 4 (Higher Ed) | **3.06%** | Socioeconomic and parental educational attainment. |
| **10**| `famrel` | Family Relationship Quality | 1 (Very Bad) to 5 (Excellent)| **2.43%** | Perceived domestic harmony and family support. |

---

## 4. User Guide: How to Operate the Dashboard

### 4.1 Student Directory & Class Roster (Homepage)
1. **Browse Enrolled Students:** View cards representing enrolled students with their Student ID, risk classification tag, and baseline indicators ($G1$, absences, failures).
2. **Filter by Risk Tier:** Click `High Risk`, `Moderate`, `Low Risk`, or `All` filter buttons to isolate specific student groups.
3. **Select a Student:** Click any student card to load their full profile into the dashboard.
4. **Random Student Inspection:** Click **Random Student** to quickly test individual evaluations.

### 4.2 Real-Time Slider Adjustments & What-If Simulations
1. Adjust any of the 10 feature sliders in the **Academic Standing**, **Attendance & Engagement**, or **Health & Family Background** panels.
2. Observe instant recalculation of:
   * **Academic Risk Probability Gauge (SVG Circular Ring)**
   * **Model Confidence (%)**
   * **First Period Grade Scale**
   * **Explainable AI (XAI) Top Risk Drivers vs. Protective Factors**
   * **Prescriptive Action Plan**

### 4.3 Intervention Plan & Action Checklist
1. Navigate to the **Recommendations** tab.
2. Review tailored action items grouped across 4 core pillars:
   * *Academic Remediation:* Peer tutoring, structured office hours, diagnostic review.
   * *Attendance Monitoring:* Absence threshold warnings, parental attendance notifications.
   * *Health & Counseling:* School counselor check-ins, study-life balance guidance.
   * *Habit Coaching:* Structured time-blocking and study routines.
3. Check off completed intervention steps and click **Log to Session History** to maintain an audit trail.

### 4.4 What-If Scenario Simulator
1. Navigate to the **What-If Simulator** tab.
2. Modify projected improvements (e.g. reducing term absences from 16 to 4 days, improving $G1$ from 7 to 12).
3. The simulator visualizes the **Delta ($\Delta$) trajectory reduction**, calculating the exact percentage reduction in academic failure probability.

### 4.5 Cohort Batch Ingestion & Triage
1. Navigate to the **Cohort Triage** tab.
2. Drag and drop any class CSV file or click **Load Sample Cohort (98 Students)**.
3. The system automatically performs:
   * Automated header matching (e.g. `attendance` $\rightarrow$ `absences`, `grade1` $\rightarrow$ `G1`).
   * Fallback imputation for missing attributes.
   * Cohort-wide triage categorization with exportable CSV audit reports.

---

## 5. Frequently Asked Questions (FAQ)

**Q: What if our school spreadsheet is missing some lifestyle columns (like `Walc` or `famrel`)?**  
*A: Smartech features automated fallback imputation. If non-critical lifestyle columns are missing, the engine automatically populates them with neutral cohort medians ($Walc=1, famrel=4$) and classifies students based on the primary academic and attendance signals without errors.*

**Q: How does the system protect student privacy?**  
*A: Smartech strictly operates with anonymized Student IDs (e.g., `STU-001`). No Personally Identifiable Information (PII) such as phone numbers, physical addresses, or financial records is ever ingested or stored.*

---

## 6. Academic Honesty & Contact Information

This software is developed in fulfillment of the **CS 254 Introduction to Artificial Intelligence** coursework at **Ashesi University**. All model algorithms, preprocessing pipelines, and user interfaces were designed and validated by Group 5.

*For inquiries, feedback, or institutional integration, contact Ashesi University CS 254 Instruction Team.*
