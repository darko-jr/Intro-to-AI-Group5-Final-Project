"""
Prediction and Explainability Engine for Student Risk Early-Warning System.
Ashesi University · Intro to AI · Group 5
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

# Baseline statistics and feature metadata
FEATURE_METADATA = {
    "G1": {
        "name": "First Period Grade (G1)",
        "desc": "First term academic score (0-20 scale)",
        "min": 0, "max": 20, "default": 11, "step": 1,
        "category": "academic",
        "direction": -1,  # higher is protective (lower risk)
        "mean": 11.4273, "scale": 2.7427,
        "importance": 0.4468,
        "tip": "Grades <= 9 strongly indicate academic distress."
    },
    "failures": {
        "name": "Past Class Failures",
        "desc": "Number of past class failures (0 to 3)",
        "min": 0, "max": 3, "default": 0, "step": 1,
        "category": "academic",
        "direction": 1,  # higher is risk
        "mean": 0.2379, "scale": 0.6302,
        "importance": 0.1695,
        "tip": "Past failures are a primary indicator of foundational learning gaps."
    },
    "absences": {
        "name": "Term Absences",
        "desc": "Number of days absent in current term (0-40+)",
        "min": 0, "max": 40, "default": 4, "step": 1,
        "category": "attendance",
        "direction": 1,  # higher is risk
        "mean": 3.6278, "scale": 4.5903,
        "importance": 0.1082,
        "tip": "Absences >= 8 significantly elevate likelihood of falling behind."
    },
    "age": {
        "name": "Student Age",
        "desc": "Age in years (15-22)",
        "min": 15, "max": 22, "default": 17, "step": 1,
        "category": "demographic",
        "direction": 1,  # older relative to grade often correlates with repetition
        "mean": 16.7379, "scale": 1.2291,
        "importance": 0.0573,
        "tip": "Older age within grade often indicates previous grade retention."
    },
    "health": {
        "name": "Health Status",
        "desc": "Self-reported health rating (1=very poor, 5=very good)",
        "min": 1, "max": 5, "default": 4, "step": 1,
        "category": "wellbeing",
        "direction": -1,  # higher is protective
        "mean": 3.5374, "scale": 1.4502,
        "importance": 0.0456,
        "tip": "Chronic health issues or low vitality impact focus and consistency."
    },
    "freetime": {
        "name": "Free Time After School",
        "desc": "Free time availability (1=very low, 5=very high)",
        "min": 1, "max": 5, "default": 3, "step": 1,
        "category": "lifestyle",
        "direction": 1,  # unstructured free time can correlate with low study engagement
        "mean": 3.1608, "scale": 1.0756,
        "importance": 0.0441,
        "tip": "Excessive unstructured free time often displaces academic study."
    },
    "Walc": {
        "name": "Weekend Alcohol Consumption",
        "desc": "Weekend alcohol use (1=very low, 5=very high)",
        "min": 1, "max": 5, "default": 1, "step": 1,
        "category": "lifestyle",
        "direction": 1,  # higher is risk
        "mean": 2.2511, "scale": 1.2623,
        "importance": 0.0384,
        "tip": "Elevated alcohol consumption impairs cognitive recovery and attendance."
    },
    "goout": {
        "name": "Going Out with Friends",
        "desc": "Socializing frequency (1=very low, 5=very high)",
        "min": 1, "max": 5, "default": 3, "step": 1,
        "category": "lifestyle",
        "direction": 1,  # higher is risk
        "mean": 3.2181, "scale": 1.1830,
        "importance": 0.0352,
        "tip": "Very high social frequency without balance reduces revision time."
    },
    "Medu": {
        "name": "Mother's Education Level",
        "desc": "0=none, 1=primary, 2=middle, 3=secondary, 4=higher",
        "min": 0, "max": 4, "default": 2, "step": 1,
        "category": "family",
        "direction": -1,  # higher is protective
        "mean": 2.4824, "scale": 1.1120,
        "importance": 0.0306,
        "tip": "Parental education level correlates with at-home academic guidance."
    },
    "famrel": {
        "name": "Family Relationship Quality",
        "desc": "Quality of family relationships (1=very poor, 5=excellent)",
        "min": 1, "max": 5, "default": 4, "step": 1,
        "category": "family",
        "direction": -1,  # higher is protective
        "mean": 3.9097, "scale": 0.9472,
        "importance": 0.0243,
        "tip": "Strong emotional support at home provides resilience during challenges."
    }
}

ORDERED_FEATURES = [
    "G1", "failures", "absences", "age", "health",
    "freetime", "Walc", "goout", "Medu", "famrel"
]

PRESET_PERSONAS = {
    "high_risk": {
        "title": "High Risk Student",
        "desc": "Low early grade, 2 prior failures, high absences & disengagement",
        "badge": "High Risk Profile",
        "values": {
            "G1": 6, "failures": 2, "absences": 18, "age": 18,
            "health": 2, "freetime": 4, "Walc": 4, "goout": 4,
            "Medu": 1, "famrel": 2
        }
    },
    "borderline": {
        "title": "Borderline / Moderate Risk",
        "desc": "Passing but fragile grade, 1 failure, mild attendance slippage",
        "badge": "Medium Risk Profile",
        "values": {
            "G1": 10, "failures": 1, "absences": 8, "age": 17,
            "health": 3, "freetime": 3, "Walc": 2, "goout": 3,
            "Medu": 2, "famrel": 3
        }
    },
    "thriving": {
        "title": "Thriving / Low Risk",
        "desc": "Solid academic standing, excellent attendance, high family support",
        "badge": "Low Risk Profile",
        "values": {
            "G1": 16, "failures": 0, "absences": 1, "age": 16,
            "health": 5, "freetime": 2, "Walc": 1, "goout": 2,
            "Medu": 4, "famrel": 5
        }
    },
    "social_drift": {
        "title": "Social & Attendance Drift",
        "desc": "Capable student with heavy socializing, rising absences & alcohol use",
        "badge": "Emerging Risk Profile",
        "values": {
            "G1": 11, "failures": 0, "absences": 14, "age": 17,
            "health": 4, "freetime": 5, "Walc": 4, "goout": 5,
            "Medu": 3, "famrel": 4
        }
    }
}


class StudentRiskEngine:
    def __init__(self, model_path: str = "student_risk_pipeline.pkl"):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.top_features = ORDERED_FEATURES
        self.classes = ["High", "Low", "Medium"]
        self._load_pipeline()

    def _load_pipeline(self):
        """Loads the trained model bundle or fallback direct model."""
        if os.path.exists(self.model_path):
            bundle = joblib.load(self.model_path)
            if isinstance(bundle, dict):
                self.model = bundle["model"]
                self.scaler = bundle.get("scaler")
                self.top_features = bundle.get("top_features", ORDERED_FEATURES)
                self.classes = list(bundle.get("classes", ["High", "Low", "Medium"]))
            else:
                self.model = bundle
        elif os.path.exists("student_risk_model.pkl"):
            self.model = joblib.load("student_risk_model.pkl")
            self.classes = list(getattr(self.model, "classes_", ["High", "Low", "Medium"]))

        if self.scaler is None:
            from sklearn.preprocessing import StandardScaler
            self.scaler = StandardScaler()
            self.scaler.mean_ = np.array([FEATURE_METADATA[f]["mean"] for f in self.top_features])
            self.scaler.scale_ = np.array([FEATURE_METADATA[f]["scale"] for f in self.top_features])
            self.scaler.var_ = self.scaler.scale_ ** 2
            self.scaler.n_features_in_ = len(self.top_features)
            self.scaler.feature_names_in_ = np.array(self.top_features)

    def preprocess_input(self, input_dict: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Preprocesses raw student features into standardized feature vectors."""
        row_raw = {feat: float(input_dict.get(feat, FEATURE_METADATA[feat]["default"])) for feat in self.top_features}
        raw_df = pd.DataFrame([row_raw])
        
        # Standardize features using the fitted scaler
        scaled_vals = []
        for feat in self.top_features:
            val = row_raw[feat]
            mean = FEATURE_METADATA[feat]["mean"]
            scale = FEATURE_METADATA[feat]["scale"]
            scaled_vals.append((val - mean) / scale)
            
        scaled_df = pd.DataFrame([scaled_vals], columns=self.top_features)
        return raw_df, scaled_df

    def predict(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Performs full risk inference, explainability attribution, and recommendation generation."""
        raw_df, scaled_df = self.preprocess_input(input_dict)
        
        # Run prediction
        probs = self.model.predict_proba(scaled_df[self.top_features])[0]
        prob_dict = {cls: float(prob) for cls, prob in zip(self.classes, probs)}
        
        # Normalize into clean order: High, Medium, Low
        high_p = prob_dict.get("High", 0.0)
        med_p = prob_dict.get("Medium", 0.0)
        low_p = prob_dict.get("Low", 0.0)
        
        # Predicted class & confidence
        predicted_class = max(prob_dict, key=prob_dict.get)
        confidence = prob_dict[predicted_class]
        
        # Composite Risk Score (0 - 100)
        risk_score = round((high_p * 100) + (med_p * 50), 1)
        
        # Explainable AI: Feature contributions
        explanations = self._compute_explanations(raw_df.iloc[0].to_dict(), scaled_df.iloc[0].to_dict())
        
        # Targeted recommendations
        recommendations = self._generate_recommendations(raw_df.iloc[0].to_dict(), predicted_class, high_p)
        
        return {
            "predicted_class": predicted_class,
            "confidence": round(confidence * 100, 1),
            "risk_score": risk_score,
            "probabilities": {
                "High": round(high_p * 100, 1),
                "Medium": round(med_p * 100, 1),
                "Low": round(low_p * 100, 1)
            },
            "raw_inputs": {k: float(v) for k, v in raw_df.iloc[0].to_dict().items()},
            "contributions": explanations,
            "recommendations": recommendations,
            "status_color": "#EF4444" if predicted_class == "High" else ("#F59E0B" if predicted_class == "Medium" else "#10B981")
        }

    def _compute_explanations(self, raw: Dict[str, float], scaled: Dict[str, float]) -> Dict[str, Any]:
        """Calculates risk-elevating vs protective feature attribution."""
        drivers = []
        protective = []
        
        for feat in self.top_features:
            meta = FEATURE_METADATA[feat]
            direction = meta["direction"]
            z_score = scaled[feat]
            importance = meta["importance"]
            
            # Impact on risk (+ means increases risk, - means reduces risk / protective)
            impact = z_score * direction * importance
            
            item = {
                "feature": feat,
                "name": meta["name"],
                "value": raw[feat],
                "impact": round(impact, 4),
                "weight": round(abs(impact) * 100, 1),
                "description": self._format_factor_text(feat, raw[feat])
            }
            
            if impact > 0.012:
                drivers.append(item)
            elif impact < -0.012:
                protective.append(item)
                
        drivers.sort(key=lambda x: x["impact"], reverse=True)
        protective.sort(key=lambda x: x["impact"])
        
        return {
            "risk_drivers": drivers,
            "protective_factors": protective,
            "all_features": sorted(drivers + protective, key=lambda x: abs(x["impact"]), reverse=True)
        }

    def _format_factor_text(self, feat: str, val: float) -> str:
        """Formats human-friendly insight text for a given feature."""
        val = int(val) if float(val).is_integer() else val
        if feat == "G1":
            if val <= 9:
                return f"Critical G1 Grade ({val}/20) falls below passing threshold (≤9)"
            elif val <= 13:
                return f"Moderate G1 Grade ({val}/20) leaves limited academic cushion"
            else:
                return f"Strong G1 Grade ({val}/20) provides solid academic foundation"
        elif feat == "failures":
            if val > 0:
                return f"{val} past class failure{'s' if val > 1 else ''} indicates prior difficulty"
            return "No past course failures"
        elif feat == "absences":
            if val >= 10:
                return f"{val} absences — severe attendance deficit"
            elif val >= 5:
                return f"{val} absences — moderate attendance concern"
            return f"Low absences ({val} days)"
        elif feat == "Walc":
            if val >= 3:
                return f"Elevated weekend alcohol consumption (level {val}/5)"
            return f"Low alcohol consumption (level {val}/5)"
        elif feat == "goout":
            if val >= 4:
                return f"High frequency of social outings ({val}/5)"
            return f"Moderate/low social outings ({val}/5)"
        elif feat == "health":
            if val <= 2:
                return f"Compromised health rating ({val}/5)"
            return f"Good health status ({val}/5)"
        elif feat == "Medu":
            levels = ["None", "Primary", "Middle School", "Secondary", "Higher Education"]
            return f"Mother's education: {levels[min(int(val), 4)]}"
        elif feat == "famrel":
            if val <= 2:
                return f"Strained family relationships ({val}/5)"
            return f"Supportive family relationships ({val}/5)"
        elif feat == "freetime":
            if val >= 4:
                return f"High unstructured free time ({val}/5)"
            return f"Structured free time ({val}/5)"
        elif feat == "age":
            return f"Age {val} years"
        return f"{feat}: {val}"

    def _generate_recommendations(self, raw: Dict[str, float], predicted_class: str, high_p: float) -> List[Dict[str, Any]]:
        """Generates concrete, highly actionable interventions based on student risk profile."""
        recs = []
        
        # 1. Primary Academic Strategy
        if raw["G1"] <= 9 or raw["failures"] > 0:
            recs.append({
                "category": "Academic Remediation",
                "urgency": "Urgent",
                "icon": "academic",
                "action": "Assign Dedicated Peer Tutor & Remedial Plan",
                "detail": f"Student has early score of {int(raw['G1'])}/20 and {int(raw['failures'])} prior failure(s). Immediate foundational review is required before midterm exams.",
                "timeline": "Within 48 hours",
                "steps": [
                    "Pair student with an upper-year peer tutor for 2 hours/week",
                    "Conduct diagnostics on core weak topics from first period",
                    "Require weekly homework submission check-ins"
                ]
            })
        elif raw["G1"] <= 12:
            recs.append({
                "category": "Academic Support",
                "urgency": "Moderate",
                "icon": "academic",
                "action": "Bi-Weekly Study Skills & Exam Preparation",
                "detail": f"With G1={int(raw['G1'])}/20, student is passing but vulnerable to downward grade drift. Structured revision will secure course completion.",
                "timeline": "Next 1-2 weeks",
                "steps": [
                    "Provide past exam revision worksheets",
                    "Schedule check-in with course instructor during office hours",
                    "Encourage joining an active study group"
                ]
            })
        else:
            recs.append({
                "category": "Academic Enrichment",
                "urgency": "Maintenance",
                "icon": "academic",
                "action": "Maintain Academic Trajectory & Extension Projects",
                "detail": f"Strong academic baseline (G1={int(raw['G1'])}/20). Student is excelling and ready for advanced topics.",
                "timeline": "Ongoing",
                "steps": [
                    "Offer optional honors exercises or research opportunities",
                    "Consider student as a candidate for peer tutoring leadership"
                ]
            })
            
        # 2. Attendance & Engagement Strategy
        if raw["absences"] >= 8:
            recs.append({
                "category": "Attendance & Retention",
                "urgency": "Urgent" if raw["absences"] >= 12 else "Moderate",
                "icon": "attendance",
                "action": "Attendance Contract & Academic Advisor Consultation",
                "detail": f"Student has accumulated {int(raw['absences'])} absences this term. Chronic absenteeism directly threatens credit retention.",
                "timeline": "Immediate",
                "steps": [
                    "Sign an attendance accountability plan with advisor",
                    "Establish automated SMS / email notifications for missed classes",
                    "Investigate root cause of absences (transportation, health, or schedule)"
                ]
            })
        elif raw["absences"] >= 4:
            recs.append({
                "category": "Attendance Monitoring",
                "urgency": "Low",
                "icon": "attendance",
                "action": "Attendance Monitoring & Schedule Alignment",
                "detail": f"Moderate absence count ({int(raw['absences'])} days). Ensure student stays within the acceptable term attendance threshold.",
                "timeline": "Next class cycle",
                "steps": [
                    "Advisor sends a friendly check-in reminder on class policy"
                ]
            })

        # 3. Wellbeing, Lifestyle & Social Balance Strategy
        if raw["Walc"] >= 3 or raw["goout"] >= 4:
            recs.append({
                "category": "Student Life & Habits",
                "urgency": "Moderate",
                "icon": "lifestyle",
                "action": "Time-Management & Healthy Routine Coaching",
                "detail": "High socializing / weekend alcohol patterns may displace sleep and dedicated weekend revision hours.",
                "timeline": "Within 1 week",
                "steps": [
                    "Provide time-blocking calendar template to balance social life with study blocks",
                    "Recommend on-campus wellness workshop on sleep hygiene and stress management"
                ]
            })

        # 4. Personal & Emotional Counseling Support
        if raw["health"] <= 2 or raw["famrel"] <= 2:
            recs.append({
                "category": "Personal Wellbeing",
                "urgency": "Urgent" if raw["health"] == 1 or raw["famrel"] == 1 else "Moderate",
                "icon": "wellness",
                "action": "Campus Counseling & Health Center Referral",
                "detail": "Indicators flag potential health limitations or home stress affecting study focus and emotional resilience.",
                "timeline": "Confidential / Within 3 days",
                "steps": [
                    "Provide confidential referral link to campus counseling center",
                    "Check eligibility for academic accommodations if health related"
                ]
            })

        return recs

    def simulate_what_if(self, baseline_inputs: Dict[str, Any], modified_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates delta between baseline student profile and proposed intervention changes."""
        base_result = self.predict(baseline_inputs)
        mod_result = self.predict(modified_inputs)
        
        risk_score_diff = round(mod_result["risk_score"] - base_result["risk_score"], 1)
        high_p_diff = round(mod_result["probabilities"]["High"] - base_result["probabilities"]["High"], 1)
        low_p_diff = round(mod_result["probabilities"]["Low"] - base_result["probabilities"]["Low"], 1)
        
        return {
            "baseline": base_result,
            "modified": mod_result,
            "deltas": {
                "risk_score_diff": risk_score_diff,
                "high_p_diff": high_p_diff,
                "low_p_diff": low_p_diff,
                "improved": risk_score_diff < 0,
                "category_shift": f"{base_result['predicted_class']} ➔ {mod_result['predicted_class']}"
            }
        }

    def process_batch(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Processes an entire cohort of students and generates summary metrics and triage tables."""
        results = []
        working_df = df.copy()
        
        for feat in self.top_features:
            if feat not in working_df.columns:
                working_df[feat] = FEATURE_METADATA[feat]["default"]
                
        for idx, row in working_df.iterrows():
            input_dict = row.to_dict()
            pred = self.predict(input_dict)
            
            top_drivers = pred["contributions"]["risk_drivers"]
            flag = top_drivers[0]["name"] if top_drivers else "None"
            
            results.append({
                "Student ID": row.get("id", f"STU-{idx+1:03d}"),
                "Predicted Risk": pred["predicted_class"],
                "Confidence": f"{pred['confidence']}%",
                "Risk Score": pred["risk_score"],
                "G1 Grade": int(row["G1"]),
                "Failures": int(row["failures"]),
                "Absences": int(row["absences"]),
                "Age": int(row["age"]),
                "Health": int(row["health"]),
                "Primary Concern": flag,
                "Urgent Action": pred["recommendations"][0]["action"] if pred["recommendations"] else "Monitor"
            })
            
        res_df = pd.DataFrame(results)
        total = len(res_df)
        high_cnt = int((res_df["Predicted Risk"] == "High").sum())
        med_cnt = int((res_df["Predicted Risk"] == "Medium").sum())
        low_cnt = int((res_df["Predicted Risk"] == "Low").sum())
        
        return {
            "total_students": total,
            "counts": {"High": high_cnt, "Medium": med_cnt, "Low": low_cnt},
            "percentages": {
                "High": round(high_cnt / total * 100, 1) if total > 0 else 0,
                "Medium": round(med_cnt / total * 100, 1) if total > 0 else 0,
                "Low": round(low_cnt / total * 100, 1) if total > 0 else 0
            },
            "avg_risk_score": round(res_df["Risk Score"].mean(), 1) if total > 0 else 0,
            "data": res_df
        }


# Singleton instance
engine = StudentRiskEngine()
