"""
Student Risk Early-Warning System — Gradio Web Interface
"""

import gradio as gr
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from prediction_engine import engine, FEATURE_METADATA, PRESET_PERSONAS


def make_gauge_chart(probs, predicted_class):
    """Generates an aesthetic donut chart representing the risk probability distribution."""
    plt.close("all")
    colors = {"High": "#EF4444", "Medium": "#F59E0B", "Low": "#10B981"}
    labels = ["High", "Medium", "Low"]
    sizes = [probs.get(l, 0) for l in labels]
    wedge_colors = [colors[l] for l in labels]

    fig, ax = plt.subplots(figsize=(3.2, 3.2), dpi=100)
    ax.pie(
        sizes,
        colors=wedge_colors,
        startangle=90,
        wedgeprops=dict(width=0.36, edgecolor="white", linewidth=2)
    )
    
    top_color = colors.get(predicted_class, "#0F172A")
    ax.text(0, 0.12, predicted_class, ha="center", va="center", fontsize=15, fontweight="bold", color=top_color)
    ax.text(0, -0.15, f"{probs.get(predicted_class, 0):.1f}% Likely", ha="center", va="center", fontsize=10, color="#64748B", fontweight="semibold")
    ax.set(aspect="equal")
    fig.patch.set_alpha(0)
    plt.tight_layout()
    return fig


def predict_single(G1, failures, absences, age, health, freetime, Walc, goout, Medu, famrel):
    """Runs prediction on student inputs."""
    input_dict = {
        "G1": G1, "failures": failures, "absences": absences, "age": age,
        "health": health, "freetime": freetime, "Walc": Walc,
        "goout": goout, "Medu": Medu, "famrel": famrel
    }
    result = engine.predict(input_dict)
    
    # 1. Label
    pred_label = {
        "High Risk": result["probabilities"]["High"] / 100,
        "Medium Risk": result["probabilities"]["Medium"] / 100,
        "Low Risk": result["probabilities"]["Low"] / 100
    }
    
    # 2. Gauge Plot
    gauge = make_gauge_chart(result["probabilities"], result["predicted_class"])
    
    # 3. Explainable Factors
    drivers = result["contributions"]["risk_drivers"]
    protective = result["contributions"]["protective_factors"]
    
    xai_md = "### 🔍 Key Contributing Factors\n"
    if drivers:
        xai_md += "\n**Risk Elevating Factors:**\n" + "\n".join(f"- 🔴 **{d['name']}**: {d['description']} *(+{d['weight']} impact)*" for d in drivers)
    if protective:
        xai_md += "\n\n**Protective Factors:**\n" + "\n".join(f"- 🟢 **{p['name']}**: {p['description']} *(-{p['weight']} protective)*" for p in protective)
    if not drivers and not protective:
        xai_md += "\n*Balanced profile without extreme risk drivers.*"
        
    # 4. Rich Recommendations & Action Plan
    recs = result["recommendations"]
    recs_md = "### 📋 Recommended Action Plan & Interventions\n"
    if recs:
        for r in recs:
            timeline_str = f" • *Timeline: {r.get('timeline', 'Immediate')}*" if 'timeline' in r else ""
            recs_md += f"\n#### **[{r['urgency']}] {r['action']}**{timeline_str}\n{r['detail']}\n"
            if r.get("steps"):
                for s in r["steps"]:
                    recs_md += f"- › {s}\n"
    else:
        recs_md += "\n*Student is on track. Standard academic monitoring recommended.*"
        
    return pred_label, gauge, xai_md, recs_md


def assess_and_log(G1, failures, absences, age, health, freetime, Walc, goout, Medu, famrel, history):
    """Assesses student risk and logs to history dataframe."""
    pred_label, gauge, xai_md, recs_md = predict_single(G1, failures, absences, age, health, freetime, Walc, goout, Medu, famrel)
    
    input_dict = {
        "G1": G1, "failures": failures, "absences": absences, "age": age,
        "health": health, "freetime": freetime, "Walc": Walc,
        "goout": goout, "Medu": Medu, "famrel": famrel
    }
    result = engine.predict(input_dict)
    
    row = {
        "#": len(history) + 1,
        "Risk Level": result["predicted_class"],
        "Confidence": f"{result['confidence']}%",
        "G1 Grade": f"{int(G1)}/20",
        "Failures": int(failures),
        "Absences": int(absences),
        "Primary Concern": result["contributions"]["risk_drivers"][0]["name"] if result["contributions"]["risk_drivers"] else "None",
        "Recommended Action": result["recommendations"][0]["action"] if result["recommendations"] else "Monitor"
    }
    new_history = [row] + history
    df = pd.DataFrame(new_history)
    return pred_label, gauge, xai_md, recs_md, new_history, df


def batch_evaluate_file(file):
    """Processes uploaded CSV and returns triage summary and dataframe."""
    if file is None:
        return "Please upload a CSV file.", pd.DataFrame()
    
    df = pd.read_csv(file.name, sep=";" if ";" in open(file.name).readline() else ",")
    result = engine.process_batch(df)
    
    summary_md = f"""
    ### 📊 Cohort Triage Summary (Total: {result['total_students']} Students)
    - 🔴 **High Risk**: {result['counts']['High']} ({result['percentages']['High']}%) — *Urgent action required*
    - 🟡 **Medium Risk**: {result['counts']['Medium']} ({result['percentages']['Medium']}%) — *Monitor & check-ins*
    - 🟢 **Low Risk**: {result['counts']['Low']} ({result['percentages']['Low']}%) — *On track*
    - **Average Cohort Risk Score**: {result['avg_risk_score']} / 100
    """
    return summary_md, result["data"]


# ==========================================================================
#  Clean Modern Theme
# ==========================================================================
custom_theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="slate",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Plus Jakarta Sans"), gr.themes.GoogleFont("Inter"), "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "monospace"],
).set(
    button_primary_background_fill="#4F46E5",
    button_primary_background_fill_hover="#4338CA",
    button_primary_text_color="#FFFFFF",
    block_title_text_color="#0F172A",
    block_label_text_color="#475569",
    block_background_fill="#FFFFFF"
)

CUSTOM_CSS = """
#header-title h1 { color: #0F172A; font-weight: 700; font-size: 24px; margin-bottom: 2px; }
"""

with gr.Blocks(title="Student Risk Early-Warning System", theme=custom_theme, css=CUSTOM_CSS) as demo:
    gr.Markdown(
        "# Student Risk Early-Warning System",
        elem_id="header-title"
    )

    with gr.Tabs():
        # TAB 1: INDIVIDUAL ASSESSMENT
        with gr.TabItem("👤 Individual Assessment"):
            with gr.Row():
                with gr.Column(scale=3):
                    with gr.Group():
                        gr.Markdown("### Academic Standing")
                        G1 = gr.Slider(0, 20, value=11, step=1, label="First Period Grade (G1) [0-20]")
                        failures = gr.Slider(0, 3, value=0, step=1, label="Past Course Failures [0-3]")

                    with gr.Group():
                        gr.Markdown("### Attendance & Engagement")
                        absences = gr.Slider(0, 40, value=4, step=1, label="Term Absences [0-40+]")
                        freetime = gr.Slider(1, 5, value=3, step=1, label="Free Time After School [1-5]")
                        goout = gr.Slider(1, 5, value=3, step=1, label="Going Out with Friends [1-5]")

                    with gr.Group():
                        gr.Markdown("### Lifestyle & Background")
                        health = gr.Slider(1, 5, value=4, step=1, label="Health Status [1-5]")
                        Walc = gr.Slider(1, 5, value=1, step=1, label="Weekend Alcohol Consumption [1-5]")
                        age = gr.Slider(15, 22, value=17, step=1, label="Student Age [15-22]")
                        Medu = gr.Slider(0, 4, value=2, step=1, label="Mother's Education [0=None, 4=Higher]")
                        famrel = gr.Slider(1, 5, value=4, step=1, label="Family Relationships [1-5]")

                    with gr.Row():
                        assess_btn = gr.Button("Assess & Log Profile", variant="primary", scale=2)
                        clear_btn = gr.ClearButton(scale=1)

                with gr.Column(scale=2):
                    gr.Markdown("### Assessment Results")
                    gauge_plot = gr.Plot(label="Probability Breakdown")
                    risk_label = gr.Label(label="Predicted Risk Category", num_top_classes=3)
                    recs_output = gr.Markdown()
                    xai_output = gr.Markdown()

            inputs_list = [G1, failures, absences, age, health, freetime, Walc, goout, Medu, famrel]

            gr.Examples(
                examples=[
                    [6, 2, 18, 18, 2, 4, 4, 4, 1, 2],  # High Risk
                    [10, 1, 8, 17, 3, 3, 2, 3, 2, 3],   # Borderline Medium
                    [16, 0, 1, 16, 5, 2, 1, 2, 4, 5],   # Thriving Low
                    [11, 0, 14, 17, 4, 5, 4, 5, 3, 4]   # Social Drift
                ],
                inputs=inputs_list,
                outputs=[risk_label, gauge_plot, xai_output, recs_output],
                fn=predict_single,
                label="Quick Student Personas",
                cache_examples=False
            )

            gr.Markdown("### Session Assessment Log")
            history_state = gr.State([])
            history_table = gr.Dataframe(
                headers=["#", "Risk Level", "Confidence", "G1 Grade", "Failures", "Absences", "Primary Concern", "Recommended Action"],
                label="Evaluated Student Profiles in this Session",
                interactive=False
            )

            # Live reactive changes
            for inp in inputs_list:
                inp.change(fn=predict_single, inputs=inputs_list, outputs=[risk_label, gauge_plot, xai_output, recs_output])

            # Button assesses and logs to dataframe
            assess_btn.click(
                fn=assess_and_log,
                inputs=inputs_list + [history_state],
                outputs=[risk_label, gauge_plot, xai_output, recs_output, history_state, history_table]
            )

            clear_btn.add(inputs_list + [risk_label, xai_output, recs_output])

        # TAB 2: BATCH EVALUATION
        with gr.TabItem("📂 Cohort Triage"):
            gr.Markdown("### Batch Student CSV Assessment")
            file_upload = gr.File(label="Upload CSV Dataset", file_types=[".csv"])
            triage_btn = gr.Button("Run Cohort Triage", variant="primary")
            batch_summary = gr.Markdown()
            batch_table = gr.Dataframe(label="Cohort Triage Report & Priority Actions", interactive=False)

            triage_btn.click(fn=batch_evaluate_file, inputs=[file_upload], outputs=[batch_summary, batch_table])

        # TAB 3: MODEL PERFORMANCE
        with gr.TabItem("📊 Model Analytics"):
            gr.Markdown(
                """
                ### Model Performance Summary
                - **Architecture**: Tuned Random Forest Classifier (Optimized via 5-Fold CV)
                - **Test Accuracy**: **80.6%**
                - **Macro F1-Score**: **0.710**
                - **Weighted F1-Score**: **0.791**
                - **Severe False Negatives**: 0% (High-Risk students are never misclassified as Low-Risk).

                ### Grade Cutoffs
                - 🔴 **High Risk**: Final Grade (G3) $\\le$ 9 / 20
                - 🟡 **Medium Risk**: Final Grade (G3) 10 – 14 / 20
                - 🟢 **Low Risk**: Final Grade (G3) $\\ge$ 15 / 20
                """
            )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7861, share=False)
