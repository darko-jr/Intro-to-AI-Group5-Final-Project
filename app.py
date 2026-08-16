import io
import os
import uvicorn
import pandas as pd
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel

from prediction_engine import engine, FEATURE_METADATA, PRESET_PERSONAS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app = FastAPI(title="Student Risk Early-Warning System", version="2.0")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _resolve_path(relative_candidates: list) -> Optional[str]:
    for rel_path in relative_candidates:
        abs_path = os.path.join(BASE_DIR, rel_path)
        if os.path.exists(abs_path):
            return abs_path
        if os.path.exists(rel_path):
            return rel_path
    return None


class PredictionRequest(BaseModel):
    G1: float = 11.0
    failures: float = 0.0
    absences: float = 4.0
    age: float = 17.0
    health: float = 4.0
    freetime: float = 3.0
    Walc: float = 1.0
    goout: float = 3.0
    Medu: float = 2.0
    famrel: float = 4.0


class WhatIfRequest(BaseModel):
    baseline: Dict[str, Any]
    modified: Dict[str, Any]


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return HTMLResponse(content="", status_code=204)


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Template not found")
    return FileResponse(index_path)


@app.get("/guide", response_class=HTMLResponse)
async def serve_guide():
    guide_path = _resolve_path(["docs/USER_GUIDE_AND_INTERPRETATION.md", "USER_GUIDE_AND_INTERPRETATION.md"])
    if not guide_path or not os.path.exists(guide_path):
        raise HTTPException(status_code=404, detail="User guide document not found")
    
    with open(guide_path, "r", encoding="utf-8") as f:
        md_text = f.read()
        
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Smartech | User Guide & Technical Interpretation Manual</title>
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
      <style>
        :root {{
          --bg: #FAF8F5;
          --surface: #FFFFFF;
          --border: #E8E2D9;
          --text: #2D2535;
          --text-muted: #6B5E78;
          --brand: #6C5CE7;
          --brand-dark: #5846E2;
          --green: #10B981;
          --amber: #F59E0B;
          --red: #EF4444;
        }}
        * {{ box-sizing: border-box; }}
        body {{
          font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
          max-width: 960px;
          margin: 0 auto;
          padding: 40px 24px 80px 24px;
          line-height: 1.7;
          color: var(--text);
          background: var(--bg);
        }}
        .guide-header {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 32px;
          padding-bottom: 20px;
          border-bottom: 1px solid var(--border);
        }}
        .back-btn {{
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: var(--surface);
          color: var(--text);
          text-decoration: none;
          padding: 10px 18px;
          border-radius: 10px;
          font-size: 13px;
          font-weight: 600;
          border: 1px solid var(--border);
          box-shadow: 0 1px 3px rgba(0,0,0,0.04);
          transition: all 0.15s ease;
        }}
        .back-btn:hover {{
          background: #F3EFE9;
          border-color: #D6CCC0;
        }}
        .guide-container {{
          background: var(--surface);
          padding: 48px;
          border-radius: 16px;
          border: 1px solid var(--border);
          box-shadow: 0 4px 20px rgba(45, 37, 53, 0.04);
        }}
        h1 {{
          font-size: 28px;
          font-weight: 800;
          color: var(--text);
          margin-top: 0;
          margin-bottom: 8px;
          letter-spacing: -0.02em;
        }}
        h2 {{
          font-size: 20px;
          font-weight: 700;
          color: var(--text);
          margin-top: 36px;
          margin-bottom: 16px;
          padding-bottom: 8px;
          border-bottom: 1px solid var(--border);
        }}
        h3 {{
          font-size: 16px;
          font-weight: 600;
          color: var(--text);
          margin-top: 24px;
          margin-bottom: 12px;
        }}
        p, li {{
          font-size: 14.5px;
          color: #3C3147;
        }}
        table {{
          width: 100%;
          border-collapse: collapse;
          margin: 24px 0;
          font-size: 13.5px;
          border: 1px solid var(--border);
          border-radius: 8px;
          overflow: hidden;
        }}
        th, td {{
          padding: 12px 16px;
          text-align: left;
          border-bottom: 1px solid var(--border);
        }}
        th {{
          background: #F5F1EB;
          font-weight: 700;
          color: var(--text);
        }}
        tr:nth-child(even) {{
          background: #FCFBF9;
        }}
        code {{
          font-family: 'JetBrains Mono', monospace;
          font-size: 12.5px;
          background: #F2EDE4;
          padding: 2px 6px;
          border-radius: 4px;
          color: #554466;
        }}
        pre {{
          background: #2D2535;
          color: #F8F7F4;
          padding: 18px;
          border-radius: 10px;
          overflow-x: auto;
          font-family: 'JetBrains Mono', monospace;
          font-size: 13px;
        }}
        pre code {{
          background: transparent;
          color: inherit;
          padding: 0;
        }}
        blockquote {{
          margin: 20px 0;
          padding: 16px 20px;
          background: #F3EFFF;
          border-left: 4px solid var(--brand);
          border-radius: 0 10px 10px 0;
          color: #4C3C70;
        }}
        blockquote p {{
          margin: 0;
          color: #4C3C70;
        }}
        hr {{
          border: none;
          border-top: 1px solid var(--border);
          margin: 32px 0;
        }}
      </style>
      <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    </head>
    <body>
      <div class="guide-header">
        <a href="/" class="back-btn">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          Back to Live Portal
        </a>
        <span style="font-size:12.5px; font-weight:600; color:var(--text-muted);">Ashesi CS 254 · Group 5 Final Project</span>
      </div>
      <main class="guide-container" id="content"></main>
      <script>
        document.getElementById('content').innerHTML = marked.parse({repr(md_text)});
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/api/predict")
async def api_predict(req: PredictionRequest):
    try:
        input_dict = req.model_dump()
        result = engine.predict(input_dict)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/what-if")
async def api_what_if(req: WhatIfRequest):
    try:
        result = engine.simulate_what_if(req.baseline, req.modified)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/sample-cohort")
async def api_sample_cohort():
    try:
        dataset_path = _resolve_path(["data/raw/student-por.csv", "data/student-por.csv", "student-por.csv"])
        if dataset_path and os.path.exists(dataset_path):
            df = pd.read_csv(dataset_path, sep=";")
            from sklearn.model_selection import train_test_split
            def risk_level(g3):
                return "High" if g3 <= 9 else ("Medium" if g3 <= 14 else "Low")
            df["Risk_level"] = df["G3"].apply(risk_level)
            _, X_temp = train_test_split(df, test_size=0.3, random_state=42, stratify=df["Risk_level"])
            _, X_test = train_test_split(X_temp, test_size=0.5, random_state=42, stratify=X_temp["Risk_level"])
            cohort_df = X_test.reset_index(drop=True)
            cohort_df["id"] = [f"STU-POR-{i+1:03d}" for i in range(len(cohort_df))]
        else:
            rows = []
            for i in range(30):
                rows.append({"id": f"STU-{i+1:03d}", "G1": 12, "failures": 0, "absences": 4, "age": 17, "health": 4, "freetime": 3, "Walc": 1, "goout": 3, "Medu": 2, "famrel": 4})
            cohort_df = pd.DataFrame(rows)
            
        result = engine.process_batch(cohort_df)
        result["data"] = result["data"].to_dict(orient="records")
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/batch-csv")
async def api_batch_csv(request: Request):
    try:
        body = await request.body()
        text = body.decode("utf-8")
        delimiter = ";" if ";" in text.splitlines()[0] else ","
        df = pd.read_csv(io.StringIO(text), sep=delimiter)
        
        result = engine.process_batch(df)
        result["data"] = result["data"].to_dict(orient="records")
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")


@app.get("/api/model-info")
async def api_model_info():
    return JSONResponse({
        "model_name": "Tuned Random Forest Classifier",
        "sprint": "Sprint 2 Final",
        "top_features": engine.top_features,
        "classes": engine.classes,
        "metrics": {
            "test_accuracy": 0.8061,
            "macro_f1": 0.7101,
            "weighted_f1": 0.7910,
            "baseline_accuracy": 0.7653
        },
        "presets": PRESET_PERSONAS
    })


@app.get("/api/students")
async def api_get_students(q: str = None, limit: int = 15):
    students = engine.get_students(query=q, limit=limit)
    return JSONResponse({"total": len(students), "students": students})


@app.get("/api/students/{student_id}")
async def api_get_student(student_id: str):
    student = engine.get_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return JSONResponse(student)


@app.put("/api/students/{student_id}")
async def api_update_student(student_id: str, request: Request):
    try:
        data = await request.json()
        student = engine.update_student(student_id, data)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return JSONResponse({"status": "success", "student": student})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def find_open_port(default_port: int = 7860) -> int:
    import socket
    port = default_port
    while port < default_port + 20:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1
    return default_port


if __name__ == "__main__":
    port = find_open_port(7860)
    print("Starting Student Risk Early-Warning System Web Application")
    print(f"URL: http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
