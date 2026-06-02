from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
from datetime import datetime

from backend.data_loader import load_data, extract_sheets, normalize_dataframes, parse_input_plan
from calculations.production import (
    filter_data, get_plan_values, calc_actuals, 
    calc_achievements, calc_stripping_ratio, calc_coal_stock, calc_global_stripping_ratio
)

app = FastAPI(title="Production Dashboard API")

# Setup CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import time

# Global Memory Cache to prevent heavy processing on every request
_data_cache = None
_last_load_time = 0
CACHE_TTL = 300  # 5 minutes in seconds

def get_data():
    global _data_cache, _last_load_time
    
    current_time = time.time()
    
    # If cache exists and is fresh, return it immediately (lightning fast)
    if _data_cache and (current_time - _last_load_time < CACHE_TTL):
        return _data_cache
    
    # Otherwise, perform the heavy loading and processing
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Cache expired or empty. Reloading data...")
    data = load_data()
    
    if isinstance(data, dict) and "sheets" in data:
        processed = {"sheets": data["sheets"], "input_values": data["input_values"]}
    else:
        sheets = extract_sheets(data)
        normalize_dataframes(sheets)
        processed = {
            "sheets": sheets,
            "input_values": parse_input_plan(sheets["input_plan"])
        }
    
    # Update global cache
    _data_cache = processed
    _last_load_time = current_time
    return _data_cache

import numpy as np

def clean_types(obj):
    if isinstance(obj, dict):
        return {k: clean_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_types(i) for i in obj]
    elif isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32)):
        if pd.isna(obj): return 0.0
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif pd.isna(obj):
        return None
    return obj

@app.get("/api/test")
def test_api():
    return {"status": "ok", "message": "API is reachable"}

@app.get("/api/kpi")
def get_kpi(pit: str = Query("North JO IC"), start_date: str = Query(None), end_date: str = Query(None)):
    try:
        data = get_data()
        sheets = data["sheets"]
        input_values = data["input_values"]
    except Exception as e:
        logger.error(f"Error in /api/kpi: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=str(e))
    
    # Resolve dates
    if start_date and end_date:
        date_range = (pd.Timestamp(start_date), pd.Timestamp(end_date))
    else:
        # Default to latest date
        valid_dates = sheets["prod_ob"]["Date"].dropna()
        valid_dates = valid_dates[valid_dates.dt.year > 2000].unique()
        valid_dates = sorted(valid_dates)
        latest = pd.Timestamp(valid_dates[-1]) if valid_dates else pd.Timestamp.today()
        date_range = (latest, latest)
        
    filtered = filter_data(sheets, date_range, pit)
    plans = get_plan_values(sheets, pit)
    actuals = calc_actuals(filtered)
    achs = calc_achievements(actuals, plans)
    sr = calc_stripping_ratio(actuals)
    global_sr = calc_global_stripping_ratio(sheets, date_range)
    stock = calc_coal_stock(sheets, date_range, input_values)
    
    return clean_types({
        "date_range": [date_range[0].strftime("%Y-%m-%d"), date_range[1].strftime("%Y-%m-%d")],
        "pit": pit,
        "kpi": {
            "actuals": actuals,
            "plans": plans,
            "achievements": achs,
            "sr": sr,
            "global_sr": global_sr,
            "stock": stock
        }
    })

@app.get("/api/charts/hourly")
def get_hourly_chart(pit: str = Query("North JO IC"), start_date: str = Query(None), end_date: str = Query(None)):
    try:
        data = get_data()
        sheets = data["sheets"]
    except Exception as e:
        logger.error(f"Error in /api/charts/hourly: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=str(e))
    
    # Resolve dates
    if start_date and end_date:
        date_range = (pd.Timestamp(start_date), pd.Timestamp(end_date))
    else:
        valid_dates = sheets["prod_ob"]["Date"].dropna()
        valid_dates = valid_dates[valid_dates.dt.year > 2000].unique()
        valid_dates = sorted(valid_dates)
        latest = pd.Timestamp(valid_dates[-1]) if valid_dates else pd.Timestamp.today()
        date_range = (latest, latest)
        
    filtered = filter_data(sheets, date_range, pit)
    
    # Prepare OB Data
    ob_df = filtered["ob_f"].groupby("Hour LU")["Volume"].sum().reset_index()
    
    # Prepare CH Data
    ch_df = filtered["ch_f"]
    ch_col = "Volume" if "Volume" in ch_df.columns else "Netto"
    if ch_col == "Netto":
        ch_df = ch_df.copy()
        ch_df["Volume"] = ch_df["Netto"] / 1000
        ch_col = "Volume"
    ch_grouped = ch_df.groupby("Hour LU")[ch_col].sum().reset_index() if not ch_df.empty else pd.DataFrame(columns=["Hour LU", ch_col])
    
    # Rain Data
    rain_df = pd.DataFrame(columns=["Hour LU", "Rain"])
    if not filtered["rain_f"].empty:
        rdf = filtered["rain_f"].copy()
        rain_val_col = "Minute" if "Minute" in rdf.columns else ("Duration" if "Duration" in rdf.columns else None)
        if rain_val_col:
            rdf[rain_val_col] = pd.to_numeric(rdf[rain_val_col], errors="coerce").fillna(0)
            if rain_val_col == "Duration":
                rdf["Rain"] = rdf[rain_val_col]
            else:
                rdf["Rain"] = rdf[rain_val_col] / 60.0
            rain_df = rdf.groupby("Hour LU")["Rain"].sum().reset_index()
    
    # Combine hours (using "O" prefix for hours after midnight to match the pandas dataframe format)
    hours = [f"{i:02d}" for i in range(6, 24)] + ["O0", "O1", "O2", "O3", "O4", "O5"]
    
    result = []
    for h in hours:
        ob_val = ob_df[ob_df["Hour LU"] == h]["Volume"].sum() if not ob_df.empty else 0
        ch_val = ch_grouped[ch_grouped["Hour LU"] == h][ch_col].sum() if not ch_grouped.empty else 0
        rain_val = rain_df[rain_df["Hour LU"] == h]["Rain"].sum() if not rain_df.empty else 0
        # Convert "O0" back to "00" for the frontend display
        display_hour = h.replace("O", "0") if h.startswith("O") else h
        
        result.append({
            "hour": display_hour,
            "ob": float(ob_val),
            "ch": float(ch_val),
            "rain": float(rain_val)
        })
        
    # Extract hourly plan from cumm_plan sheet
    cumm_plan_df = sheets.get("cumm_plan", pd.DataFrame())
    pit_plan = cumm_plan_df[cumm_plan_df["PIT"] == pit] if not cumm_plan_df.empty else pd.DataFrame()
    
    plan_ob_hourly = []
    plan_ch_hourly = []
    
    for h in hours:
        row = pit_plan[pit_plan["Hour LU"] == h]
        if not row.empty:
            plan_ob_hourly.append(float(row["Cumm OB"].iloc[0]))
            plan_ch_hourly.append(float(row["Cumm CH"].iloc[0]))
        else:
            # Fallback or fill (ffill) logic could go here, but simple 0 for now or ffill
            last_ob = plan_ob_hourly[-1] if plan_ob_hourly else 0
            last_ch = plan_ch_hourly[-1] if plan_ch_hourly else 0
            plan_ob_hourly.append(last_ob)
            plan_ch_hourly.append(last_ch)

    plans = get_plan_values(sheets, pit)
    
    return clean_types({
        "data": result,
        "targets": {
            "ob_hourly": plans["plan_ob"] / 24 if plans["plan_ob"] else 0,
            "ch_hourly": plans["plan_ch"] / 24 if plans["plan_ch"] else 0,
            "ob_plan_line": plan_ob_hourly,
            "ch_plan_line": plan_ch_hourly,
            "daily_ob": plans["plan_ob"],
            "daily_ch": plans["plan_ch"]
        }
    })

if __name__ == "__main__":
    uvicorn.run("api_main:app", host="0.0.0.0", port=8000, reload=True)
