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
      <title>System & Model Interpretation Guide</title>
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
      <style>
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; max-width: 920px; margin: 40px auto; padding: 0 24px; line-height: 1.65; color: #2D2535; background: #FAF8F5; }}
        pre {{ background: #EFECE6; padding: 16px; border-radius: 12px; overflow-x: auto; font-family: 'JetBrains Mono', monospace; font-size: 13px; border: 1px solid #E5DFD7; }}
        code {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; background: #EFECE6; padding: 2px 6px; border-radius: 6px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 24px 0; background: #FFFFFF; border-radius: 12px; overflow: hidden; border: 1px solid #E5DFD7; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }}
        th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #EFECE6; font-size: 13.5px; }}
        th {{ background: #EFECE6; font-weight: 700; color: #2D2535; }}
        h1, h2, h3 {{ color: #2D2535; font-weight: 700; }}
        h1 {{ border-bottom: 2px solid #E5DFD7; padding-bottom: 12px; font-size: 26px; }}
        .badge {{ background: #6C5CE7; color: white; padding: 2px 8px; border-radius: 999px; font-size: 12px; }}
        .back-btn {{ display: inline-flex; align-items: center; gap: 8px; background: #2D2535; color: white; text-decoration: none; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; margin-bottom: 24px; }}
        .back-btn:hover {{ background: #453A50; }}
      </style>
      <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    </head>
    <body>
      <a href="/" class="back-btn">← Back to Dashboard</a>
      <div id="content"></div>
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
