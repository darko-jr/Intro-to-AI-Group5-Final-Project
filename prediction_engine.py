import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FEATURE_METADATA = {
    "G1": {
        "name": "First Period Grade (G1)",
        "desc": "First term academic score (0-20 scale)",
        "min": 0, "max": 20, "default": 11, "step": 1,
        "category": "academic",
        "direction": -1,
        "mean": 11.4273, "scale": 2.7427,
        "importance": 0.4468,
        "tip": "Grades <= 9 strongly indicate academic distress."
    },
    "failures": {
        "name": "Past Class Failures",
        "desc": "Number of past class failures (0 to 3)",
        "min": 0, "max": 3, "default": 0, "step": 1,
        "category": "academic",
        "direction": 1,
        "mean": 0.2379, "scale": 0.6302,
        "importance": 0.1695,
        "tip": "Past failures are a primary indicator of foundational learning gaps."
    },
    "absences": {
        "name": "Term Absences",
        "desc": "Number of days absent in current term (0-40+)",
        "min": 0, "max": 40, "default": 4, "step": 1,
        "category": "attendance",
        "direction": 1,
        "mean": 3.6278, "scale": 4.5903,
        "importance": 0.1082,
        "tip": "Absences >= 8 significantly elevate likelihood of falling behind."
    },
    "age": {
        "name": "Student Age",
        "desc": "Age in years (15-22)",
        "min": 15, "max": 22, "default": 17, "step": 1,
        "category": "demographic",
        "direction": 1,
        "mean": 16.7379, "scale": 1.2291,
        "importance": 0.0573,
        "tip": "Older age within grade often indicates previous grade retention."
    },
    "health": {
        "name": "Health Status",
        "desc": "Self-reported health rating (1=very poor, 5=very good)",
        "min": 1, "max": 5, "default": 4, "step": 1,
        "category": "wellbeing",
        "direction": -1,
        "mean": 3.5374, "scale": 1.4502,
        "importance": 0.0456,
        "tip": "Chronic health issues or low vitality impact focus and consistency."
    },
    "freetime": {
        "name": "Free Time After School",
        "desc": "Free time availability (1=very low, 5=very high)",
        "min": 1, "max": 5, "default": 3, "step": 1,
        "category": "lifestyle",
        "direction": 1,
        "mean": 3.1608, "scale": 1.0756,
        "importance": 0.0441,
        "tip": "Excessive unstructured free time often displaces academic study."
    },
    "Walc": {
        "name": "Weekend Alcohol Consumption",
        "desc": "Weekend alcohol use (1=very low, 5=very high)",
        "min": 1, "max": 5, "default": 1, "step": 1,
        "category": "lifestyle",
        "direction": 1,
        "mean": 2.2511, "scale": 1.2623,
        "importance": 0.0384,
        "tip": "Elevated alcohol consumption impairs cognitive recovery and attendance."
    },
    "goout": {
        "name": "Going Out with Friends",
        "desc": "Socializing frequency (1=very low, 5=very high)",
        "min": 1, "max": 5, "default": 3, "step": 1,
        "category": "lifestyle",
        "direction": 1,
        "mean": 3.2181, "scale": 1.1830,
        "importance": 0.0352,
        "tip": "Very high social frequency without balance reduces revision time."
    },
    "Medu": {
        "name": "Mother's Education Level",
        "desc": "0=none, 1=primary, 2=middle, 3=secondary, 4=higher",
        "min": 0, "max": 4, "default": 2, "step": 1,
        "category": "family",
        "direction": -1,
        "mean": 2.4824, "scale": 1.1120,
        "importance": 0.0306,
        "tip": "Parental education level correlates with at-home academic guidance."
    },
    "famrel": {
        "name": "Family Relationship Quality",
        "desc": "Quality of family relationships (1=very poor, 5=excellent)",
        "min": 1, "max": 5, "default": 4, "step": 1,
        "category": "family",
        "direction": -1,
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
        "desc": "Low early grade, 2 prior failures, high absences",
        "badge": "High Risk Profile",
        "values": {
            "G1": 6, "failures": 2, "absences": 18, "age": 18,
            "health": 2, "freetime": 4, "Walc": 4, "goout": 4,
            "Medu": 1, "famrel": 2
        }
    },
    "borderline": {
        "title": "Moderate Risk Student",
        "desc": "Passing grade, 1 failure, mild attendance slippage",
        "badge": "Medium Risk Profile",
        "values": {
            "G1": 10, "failures": 1, "absences": 8, "age": 17,
            "health": 3, "freetime": 3, "Walc": 2, "goout": 3,
            "Medu": 2, "famrel": 3
        }
    },
    "thriving": {
        "title": "Low Risk Student",
        "desc": "Solid academic standing, regular attendance, high family support",
        "badge": "Low Risk Profile",
        "values": {
            "G1": 16, "failures": 0, "absences": 1, "age": 16,
            "health": 5, "freetime": 2, "Walc": 1, "goout": 2,
            "Medu": 4, "famrel": 5
        }
    },
    "social_drift": {
        "title": "Attendance Slippage",
        "desc": "Passing grades with increasing absences and social outings",
        "badge": "Emerging Risk Profile",
        "values": {
            "G1": 11, "failures": 0, "absences": 14, "age": 17,
            "health": 4, "freetime": 5, "Walc": 4, "goout": 5,
            "Medu": 3, "famrel": 4
        }
    }
}

COLUMN_ALIASES = {
    "G1": ["g1", "g1_grade", "grade1", "first_period", "g1_score", "first_grade", "period1", "first_term_grade"],
    "failures": ["failures", "failure", "past_failures", "class_failures", "failed_courses", "fail", "past_fails"],
    "absences": ["absences", "absence", "absent", "days_absent", "attendance", "missed_days", "missed_classes"],
    "age": ["age", "student_age", "years"],
    "health": ["health", "health_status", "vitality"],
    "freetime": ["freetime", "free_time", "leisure"],
    "Walc": ["walc", "weekend_alcohol", "alcohol", "weekend_alc", "alcohol_use"],
    "goout": ["goout", "going_out", "social", "outing", "outings"],
    "Medu": ["medu", "mother_education", "mother_edu", "mom_edu", "m_edu"],
    "famrel": ["famrel", "family_rel", "family_relationship", "family_quality", "fam_support"],
    "Name": ["name", "student_name", "full_name", "student"],
    "id": ["id", "student_id", "roll_no", "stu_id"]
}


def _find_file(filename: str) -> str:
    candidates = [
        os.path.join(BASE_DIR, "models", filename),
        os.path.join(BASE_DIR, filename),
        os.path.join(BASE_DIR, "data", "raw", filename),
        os.path.join(BASE_DIR, "data", filename),
        filename
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return filename


class StudentRiskEngine:
    def __init__(self, model_path: str = "student_risk_pipeline.pkl"):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.top_features = ORDERED_FEATURES
        self.classes = ["High", "Low", "Medium"]
        self.students_db = []
        self._load_pipeline()
        self._init_students_db()

    def _load_pipeline(self):
        pipeline_file = _find_file(self.model_path)
        model_file = _find_file("student_risk_model.pkl")

        if os.path.exists(pipeline_file):
            bundle = joblib.load(pipeline_file)
            if isinstance(bundle, dict):
                self.model = bundle["model"]
                self.scaler = bundle.get("scaler")
                self.top_features = bundle.get("top_features", ORDERED_FEATURES)
                self.classes = list(bundle.get("classes", ["High", "Low", "Medium"]))
            else:
                self.model = bundle
        elif os.path.exists(model_file):
            self.model = joblib.load(model_file)
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
        row_raw = {feat: float(input_dict.get(feat, FEATURE_METADATA[feat]["default"])) for feat in self.top_features}
        raw_df = pd.DataFrame([row_raw])
        
        scaled_vals = []
        for feat in self.top_features:
            val = row_raw[feat]
            mean = FEATURE_METADATA[feat]["mean"]
            scale = FEATURE_METADATA[feat]["scale"]
            scaled_vals.append((val - mean) / scale)
            
        scaled_df = pd.DataFrame([scaled_vals], columns=self.top_features)
        return raw_df, scaled_df

    def predict(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        raw_df, scaled_df = self.preprocess_input(input_dict)
        
        probs = self.model.predict_proba(scaled_df[self.top_features])[0]
        prob_dict = {cls: float(prob) for cls, prob in zip(self.classes, probs)}
        
        high_p = prob_dict.get("High", 0.0)
        med_p = prob_dict.get("Medium", 0.0)
        low_p = prob_dict.get("Low", 0.0)
        
        predicted_class = max(prob_dict, key=prob_dict.get)
        confidence = prob_dict[predicted_class]
        
        risk_score = round((high_p * 100) + (med_p * 50), 1)
        
        explanations = self._compute_explanations(raw_df.iloc[0].to_dict(), scaled_df.iloc[0].to_dict())
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
        drivers = []
        protective = []
        
        for feat in self.top_features:
            meta = FEATURE_METADATA[feat]
            direction = meta["direction"]
            z_score = scaled[feat]
            importance = meta["importance"]
            
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
        val = int(val) if float(val).is_integer() else val
        if feat == "G1":
            if val <= 9:
                return f"Low G1 Grade ({val}/20) falls below passing threshold (<= 9)"
            elif val <= 13:
                return f"Moderate G1 Grade ({val}/20) leaves limited academic cushion"
            else:
                return f"Strong G1 Grade ({val}/20) provides solid foundation"
        elif feat == "failures":
            if val > 0:
                return f"{val} past class failure{'s' if val > 1 else ''} recorded"
            return "No past course failures"
        elif feat == "absences":
            if val >= 10:
                return f"{val} absences: high attendance concern"
            elif val >= 5:
                return f"{val} absences: moderate attendance concern"
            return f"Low absences ({val} days)"
        elif feat == "Walc":
            if val >= 3:
                return f"Weekend alcohol consumption (level {val}/5)"
            return f"Low alcohol consumption (level {val}/5)"
        elif feat == "goout":
            if val >= 4:
                return f"High frequency of social outings ({val}/5)"
            return f"Moderate social outings ({val}/5)"
        elif feat == "health":
            if val <= 2:
                return f"Low health rating ({val}/5)"
            return f"Good health status ({val}/5)"
        elif feat == "Medu":
            levels = ["None", "Primary", "Middle School", "Secondary", "Higher Education"]
            return f"Mother's education: {levels[min(int(val), 4)]}"
        elif feat == "famrel":
            if val <= 2:
                return f"Low family relationship rating ({val}/5)"
            return f"Supportive family relationships ({val}/5)"
        elif feat == "freetime":
            if val >= 4:
                return f"High unstructured free time ({val}/5)"
            return f"Balanced free time ({val}/5)"
        elif feat == "age":
            return f"Age {val} years"
        return f"{feat}: {val}"

    def _generate_recommendations(self, raw: Dict[str, float], predicted_class: str, high_p: float) -> List[Dict[str, Any]]:
        recs = []
        
        if raw["G1"] <= 9 or raw["failures"] > 0:
            recs.append({
                "category": "Academic Remediation",
                "urgency": "Urgent",
                "icon": "academic",
                "action": "Assign Peer Tutor and Remedial Review",
                "detail": f"Student has early score of {int(raw['G1'])}/20 and {int(raw['failures'])} prior failure(s). Foundational topic review recommended before midterm exams.",
                "timeline": "Within 48 hours",
                "steps": [
                    "Pair student with peer tutor for 2 hours per week",
                    "Conduct diagnostic review on first period topics",
                    "Schedule weekly assignment check-ins"
                ]
            })
        elif raw["G1"] <= 12:
            recs.append({
                "category": "Academic Support",
                "urgency": "Moderate",
                "icon": "academic",
                "action": "Study Skills and Office Hours Attendance",
                "detail": f"With G1={int(raw['G1'])}/20, student is passing but near the risk threshold. Structured revision recommended.",
                "timeline": "Next 1-2 weeks",
                "steps": [
                    "Provide review worksheets and practice questions",
                    "Encourage instructor office hours visit",
                    "Suggest joining a course study group"
                ]
            })
        else:
            recs.append({
                "category": "Academic Enrichment",
                "urgency": "Maintenance",
                "icon": "academic",
                "action": "Maintain Academic Progress",
                "detail": f"Strong academic baseline (G1={int(raw['G1'])}/20). Student is on track in the course.",
                "timeline": "Ongoing",
                "steps": [
                    "Provide extension or honors problem sets if interested",
                    "Consider student for peer tutoring opportunities"
                ]
            })
            
        if raw["absences"] >= 8:
            recs.append({
                "category": "Attendance and Retention",
                "urgency": "Urgent" if raw["absences"] >= 12 else "Moderate",
                "icon": "attendance",
                "action": "Attendance Review and Advisor Meeting",
                "detail": f"Student has accumulated {int(raw['absences'])} absences this term. High absence rates correlate with lower course completion.",
                "timeline": "Immediate",
                "steps": [
                    "Review attendance policy with academic advisor",
                    "Set up automated attendance notifications",
                    "Identify underlying reasons for missed classes"
                ]
            })
        elif raw["absences"] >= 4:
            recs.append({
                "category": "Attendance Monitoring",
                "urgency": "Low",
                "icon": "attendance",
                "action": "Attendance Check-In",
                "detail": f"Moderate absence count ({int(raw['absences'])} days). Ensure student stays within attendance limits.",
                "timeline": "Next class cycle",
                "steps": [
                    "Send check-in note regarding class attendance"
                ]
            })

        if raw["Walc"] >= 3 or raw["goout"] >= 4:
            recs.append({
                "category": "Student Habits",
                "urgency": "Moderate",
                "icon": "lifestyle",
                "action": "Time Management Coaching",
                "detail": "Frequent social activities and weekend habits may reduce dedicated revision time.",
                "timeline": "Within 1 week",
                "steps": [
                    "Introduce weekly time-blocking schedule",
                    "Discuss balance between social activities and study commitments"
                ]
            })

        if raw["health"] <= 2 or raw["famrel"] <= 2:
            recs.append({
                "category": "Student Wellbeing",
                "urgency": "Urgent" if raw["health"] == 1 or raw["famrel"] == 1 else "Moderate",
                "icon": "wellness",
                "action": "Counseling and Support Services Referral",
                "detail": "Indicators suggest potential health or personal factors affecting academic focus.",
                "timeline": "Within 3 days",
                "steps": [
                    "Provide confidential counseling center contact details",
                    "Review academic accommodation options if health-related"
                ]
            })

        return recs

    def simulate_what_if(self, baseline_inputs: Dict[str, Any], modified_inputs: Dict[str, Any]) -> Dict[str, Any]:
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
                "category_shift": f"{base_result['predicted_class']} Risk to {mod_result['predicted_class']} Risk"
            }
        }

    def process_batch(self, df: pd.DataFrame) -> Dict[str, Any]:
        results = []
        working_df = df.copy()
        
        # 1. Normalize column names and map aliases
        col_map = {}
        for c in working_df.columns:
            clean_c = str(c).strip().lower()
            for target_feat, aliases in COLUMN_ALIASES.items():
                if clean_c == target_feat.lower() or clean_c in aliases:
                    col_map[c] = target_feat
                    break
        working_df = working_df.rename(columns=col_map)
        
        # 2. Impute any completely missing feature columns with default baselines
        for feat in self.top_features:
            if feat not in working_df.columns:
                working_df[feat] = FEATURE_METADATA[feat]["default"]
            else:
                # Handle individual NaN values within existing columns
                working_df[feat] = pd.to_numeric(working_df[feat], errors="coerce").fillna(FEATURE_METADATA[feat]["default"])
                
        for idx, row in working_df.iterrows():
            input_dict = row.to_dict()
            pred = self.predict(input_dict)
            
            top_drivers = pred["contributions"]["risk_drivers"]
            flag = top_drivers[0]["name"] if top_drivers else "None"
            
            stu_id = str(row.get("Student ID", row.get("id", f"STU-{idx+1:03d}")))
            stu_name = str(row.get("Name", row.get("name", stu_id)))
            
            results.append({
                "Student ID": stu_id,
                "Name": stu_name,
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

    def _init_students_db(self):
        self.students_db = []
        dataset_path = _find_file("student-por.csv")
        
        if os.path.exists(dataset_path):
            try:
                df = pd.read_csv(dataset_path, sep=";" if ";" in open(dataset_path).readline() else ",")
                for idx, row in df.iterrows():
                    stu_id = f"STU-{idx+1:03d}"
                    sex = str(row.get("sex", "F")).strip()
                    stu_name = str(row.get("Name", row.get("name", stu_id)))
                    
                    g3 = float(row.get("G3", 11))
                    actual_risk = "High" if g3 <= 9 else ("Low" if g3 >= 15 else "Medium")
                    
                    student_inputs = {}
                    for feat in self.top_features:
                        student_inputs[feat] = float(row.get(feat, FEATURE_METADATA[feat]["default"]))
                        
                    self.students_db.append({
                        "id": stu_id,
                        "name": stu_name,
                        "sex": sex,
                        "school": str(row.get("school", "GP")),
                        "inputs": student_inputs,
                        "actual_g3": int(g3),
                        "actual_risk": actual_risk
                    })
            except Exception as e:
                print("Error loading students DB from CSV:", e)
                
        if not self.students_db:
            for i in range(30):
                stu_id = f"STU-{i+1:03d}"
                p_key = list(PRESET_PERSONAS.keys())[i % len(PRESET_PERSONAS)]
                inputs = dict(PRESET_PERSONAS[p_key]["values"])
                self.students_db.append({
                    "id": stu_id,
                    "name": stu_id,
                    "sex": "F" if i % 2 == 0 else "M",
                    "school": "GP",
                    "inputs": inputs,
                    "actual_g3": 11,
                    "actual_risk": "Medium"
                })

    def get_students(self, query: str = None, limit: int = 15) -> List[Dict[str, Any]]:
        results = []
        q = (query or "").lower().strip()
        
        for student in self.students_db:
            matches = True
            if q:
                matches = (
                    q in student["id"].lower() or
                    q in student["name"].lower() or
                    q in student["actual_risk"].lower() or
                    (q == "high" and student["inputs"]["G1"] <= 9) or
                    (q == "absence" and student["inputs"]["absences"] >= 8) or
                    (q == "failure" and student["inputs"]["failures"] > 0)
                )
            
            if matches:
                pred = self.predict(student["inputs"])
                primary_concern = pred["contributions"]["risk_drivers"][0]["name"] if pred["contributions"]["risk_drivers"] else "None"
                urgent_action = pred["recommendations"][0]["action"] if pred["recommendations"] else "Standard Monitoring"
                
                results.append({
                    "id": student["id"],
                    "name": student["name"],
                    "sex": student["sex"],
                    "school": student["school"],
                    "inputs": student["inputs"],
                    "predicted_class": pred["predicted_class"],
                    "confidence": pred["confidence"],
                    "risk_score": pred["risk_score"],
                    "G1": student["inputs"]["G1"],
                    "absences": student["inputs"]["absences"],
                    "failures": student["inputs"]["failures"],
                    "primary_concern": primary_concern,
                    "urgent_action": urgent_action
                })
                
                if len(results) >= limit:
                    break
                    
        return results

    def get_student_by_id(self, student_id: str) -> Dict[str, Any]:
        for student in self.students_db:
            if student["id"].lower() == student_id.lower():
                pred = self.predict(student["inputs"])
                return {
                    "id": student["id"],
                    "name": student["name"],
                    "sex": student["sex"],
                    "school": student["school"],
                    "inputs": student["inputs"],
                    "prediction": pred
                }
        return None

    def update_student(self, student_id: str, updated_inputs: Dict[str, Any]) -> Dict[str, Any]:
        for student in self.students_db:
            if student["id"].lower() == student_id.lower():
                for k, v in updated_inputs.items():
                    if k in student["inputs"]:
                        student["inputs"][k] = float(v)
                pred = self.predict(student["inputs"])
                return {
                    "id": student["id"],
                    "name": student["name"],
                    "inputs": student["inputs"],
                    "prediction": pred
                }
        return None


engine = StudentRiskEngine()
