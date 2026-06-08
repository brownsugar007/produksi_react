"""
Production Calculations — Filtering, Plan, Actual, Achievement, Stock
"""
import pandas as pd


def filter_data(sheets: dict, date_range: tuple, selected_pit: str) -> dict:
    """
    Filter production DataFrames by a date range and PIT.
    Returns dict with filtered DataFrames and visibility flags.

    NEW FILE FORMAT (2026-03-15): Uses "PIT Fix" column (not "PIT")
    OLD FILE FORMAT: Uses "PIT" column for OB
    """
    prod_ob = sheets["prod_ob"]
    prod_ch = sheets["prod_ch"]
    prod_ct = sheets["prod_ct"]

    start_date, end_date = date_range
    # Ensure they are pandas Timestamps for safe comparison with datetime64[ns] columns
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    # Ensure Date columns are datetime (they may still be object/string after normalize)
    for key in ["prod_ob", "prod_ch", "prod_ct"]:
        if key in sheets and not sheets[key].empty and "Date" in sheets[key].columns:
            if sheets[key]["Date"].dtype == "object" or str(sheets[key]["Date"].dtype) == "object":
                sheets[key]["Date"] = pd.to_datetime(sheets[key]["Date"], errors="coerce")

    # 1. Ob (Overburden)
    if "PIT Fix" in prod_ob.columns and not prod_ob.empty:
        # Explicitly ensure Date is datetime even if empty check bypassed
        if str(prod_ob["Date"].dtype) != "datetime64[ns]":
            prod_ob["Date"] = pd.to_datetime(prod_ob["Date"], errors="coerce")
            
        ob_f = prod_ob[
            (prod_ob["Date"] >= start_date) &
            (prod_ob["Date"] <= end_date) &
            (prod_ob["PIT Fix"] == selected_pit)
        ]
    elif "PIT" in prod_ob.columns and not prod_ob.empty:
        if str(prod_ob["Date"].dtype) != "datetime64[ns]":
            prod_ob["Date"] = pd.to_datetime(prod_ob["Date"], errors="coerce")
        ob_f = prod_ob[
            (prod_ob["Date"] >= start_date) &
            (prod_ob["Date"] <= end_date) &
            (prod_ob["PIT"] == selected_pit)
        ]
    else:
        ob_f = pd.DataFrame(columns=prod_ob.columns if not prod_ob.empty else [])

    # 2. CH (Coal Hauling)
    if "PIT Fix" in prod_ch.columns and not prod_ch.empty:
        if str(prod_ch["Date"].dtype) != "datetime64[ns]":
            prod_ch["Date"] = pd.to_datetime(prod_ch["Date"], errors="coerce")
            
        ch_f = prod_ch[
            (prod_ch["Date"] >= start_date) &
            (prod_ch["Date"] <= end_date) &
            (prod_ch["PIT Fix"] == selected_pit)
        ]
    elif "PIT" in prod_ch.columns and not prod_ch.empty:
        if str(prod_ch["Date"].dtype) != "datetime64[ns]":
            prod_ch["Date"] = pd.to_datetime(prod_ch["Date"], errors="coerce")
        ch_f = prod_ch[
            (prod_ch["Date"] >= start_date) &
            (prod_ch["Date"] <= end_date) &
            (prod_ch["PIT"] == selected_pit)
        ]
    else:
        ch_f = pd.DataFrame(columns=prod_ch.columns if not prod_ch.empty else [])

    # 3. CT (Coal Transit)
    if "PIT Fix" in prod_ct.columns and not prod_ct.empty:
        if str(prod_ct["Date"].dtype) != "datetime64[ns]":
            prod_ct["Date"] = pd.to_datetime(prod_ct["Date"], errors="coerce")
            
        ct_f = prod_ct[
            (prod_ct["Date"] >= start_date) &
            (prod_ct["Date"] <= end_date) &
            (prod_ct["PIT Fix"] == selected_pit)
        ]
    elif "PIT" in prod_ct.columns and not prod_ct.empty:
        if str(prod_ct["Date"].dtype) != "datetime64[ns]":
            prod_ct["Date"] = pd.to_datetime(prod_ct["Date"], errors="coerce")
        ct_f = prod_ct[
            (prod_ct["Date"] >= start_date) &
            (prod_ct["Date"] <= end_date) &
            (prod_ct["PIT"] == selected_pit)
        ]
    else:
        ct_f = pd.DataFrame(columns=prod_ct.columns if not prod_ct.empty else [])

    # Rain: Filter by date and PIT
    if "rain" in sheets and not sheets["rain"].empty:
        rain_df = sheets["rain"]
        if "Date" in rain_df.columns and rain_df["Date"].dtype == "object":
            rain_df["Date"] = pd.to_datetime(rain_df["Date"], errors="coerce")
        # Check for PIT Fix first, then PIT
        if "PIT Fix" in rain_df.columns:
            rain_f = rain_df[
                (rain_df["Date"] >= start_date) &
                (rain_df["Date"] <= end_date) &
                (rain_df["PIT Fix"] == selected_pit)
            ]
        elif "PIT" in rain_df.columns:
            rain_f = rain_df[
                (rain_df["Date"] >= start_date) &
                (rain_df["Date"] <= end_date) &
                (rain_df["PIT"] == selected_pit)
            ]
        else:
            rain_f = rain_df[
                (rain_df["Date"] >= start_date) &
                (rain_df["Date"] <= end_date)
            ]
    else:
        rain_f = pd.DataFrame()

    return {"ob_f": ob_f, "ch_f": ch_f, "ct_f": ct_f, "rain_f": rain_f}


def get_plan_values(sheets: dict, selected_pit: str) -> dict:
    """
    Extract Plan_Daily values for OB, CH, CT from Plan Hourly sheets.
    Returns dict with plan values and has_ct flag.
    Note: Currently returns the *daily* plan as the base target. 
    If spanning multiple days, this might need multiplying by date range length.
    """
    plan_h_ob = sheets["plan_h_ob"]
    plan_h_ch = sheets["plan_h_ch"]
    plan_h_ct = sheets["plan_h_ct"]

    def _get_daily(df, pit):
        match = df[df["PIT"] == pit]
        return match["Plan_Daily"].iloc[0] if len(match) > 0 else 0

    plan_ob = _get_daily(plan_h_ob, selected_pit)
    plan_ch = _get_daily(plan_h_ch, selected_pit)
    plan_ct = _get_daily(plan_h_ct, selected_pit)
    has_ct = plan_ct > 0

    return {
        "plan_ob": plan_ob,
        "plan_ch": plan_ch,
        "plan_ct": plan_ct,
        "has_ct": has_ct,
    }


def calc_actuals(filtered: dict) -> dict:
    """
    Calculate actual production volumes from filtered DataFrames.

    NEW FILE FORMAT (2026-03-15):
    - CH Volume is already in MT (not kg), no division needed
    - CT uses "Volume" column (not "Production")

    OLD FILE FORMAT:
    - CH Netto is in kg, needs /1000 to convert to MT
    - CT uses "Production" column
    """
    # OB: Same for both formats
    actual_ob = filtered["ob_f"]["Volume"].sum() if not filtered["ob_f"].empty and "Volume" in filtered["ob_f"].columns else 0

    # CH: Check which column exists and format
    if not filtered["ch_f"].empty:
        if "Netto" in filtered["ch_f"].columns:
            # OLD FORMAT: kg -> MT conversion needed
            actual_ch = filtered["ch_f"]["Netto"].sum() / 1000
        elif "Volume" in filtered["ch_f"].columns:
            # NEW FORMAT: Already in MT
            actual_ch = filtered["ch_f"]["Volume"].sum()
        else:
            actual_ch = 0
    else:
        actual_ch = 0

    # CT: Check which column exists
    if not filtered["ct_f"].empty:
        if "Production" in filtered["ct_f"].columns:
            # OLD FORMAT: Production column
            actual_ct = filtered["ct_f"]["Production"].sum()
        elif "Volume" in filtered["ct_f"].columns:
            # NEW FORMAT: Volume column
            actual_ct = filtered["ct_f"]["Volume"].sum()
        else:
            actual_ct = 0
    else:
        actual_ct = 0

    return {"actual_ob": actual_ob, "actual_ch": actual_ch, "actual_ct": actual_ct}


def calc_achievements(actuals: dict, plans: dict) -> dict:
    """Calculate achievement percentages."""
    def _ach(actual, plan):
        try:
            actual_val = float(actual)
            plan_val = float(plan)
            return (actual_val / plan_val * 100) if plan_val > 0 else 0
        except (ValueError, TypeError):
            return 0

    return {
        "ach_ob": _ach(actuals["actual_ob"], plans["plan_ob"]),
        "ach_ch": _ach(actuals["actual_ch"], plans["plan_ch"]),
        "ach_ct": _ach(actuals["actual_ct"], plans["plan_ct"]),
    }


def calc_stripping_ratio(actuals: dict) -> float:
    """Calculate actual stripping ratio (OB / CH).

    Standard Industri Tambang Batubara:
    - Overburden (OB): BCM (Bank Cubic Meter)
    - Coal Hauling (CH): MT (Metric Tons)
    - Stripping Ratio: BCM/MT (volume OB per ton batubara)

    Note: Stripping ratio yang normal biasanya berkisar 2-10 BCM/MT
    tergantung kondisi geologi dan kedalaman tambang.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        actual_ob = float(actuals["actual_ob"])
        actual_ch = float(actuals["actual_ch"])

        # Validasi: Jika tidak ada data CH, stripping ratio tidak dapat dihitung
        if actual_ch <= 0:
            return 0.0

        sr = actual_ob / actual_ch

        # Warning: Stripping ratio yang sangat tinggi (>50) mungkin indikasi data CH yang tidak lengkap
        if sr > 50:
            logger.warning(
                f"Stripping ratio sangat tinggi ({sr:.2f}). "
                f"OB={actual_ob:.0f}, CH={actual_ch:.0f}. "
                f"Kemungkinan data CH tidak lengkap."
            )

        return sr
    except (ValueError, TypeError):
        return 0


def calc_global_stripping_ratio(sheets: dict, date_range: tuple) -> float:
    """
    Calculate the global stripping ratio across all JOs.

    NEW FORMAT: CH Volume is already in MT
    OLD FORMAT: CH Netto is in kg, needs /1000
    """
    prod_ob = sheets["prod_ob"]
    prod_ch = sheets["prod_ch"]
    start_date, end_date = date_range
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    # Calculate total OB across all pits (from prod_ob)
    if not prod_ob.empty:
        if "Date" in prod_ob.columns and str(prod_ob["Date"].dtype) != "datetime64[ns]":
            prod_ob["Date"] = pd.to_datetime(prod_ob["Date"], errors="coerce")
        ob_range = prod_ob[
            (prod_ob["Date"] >= start_date) &
            (prod_ob["Date"] <= end_date)
        ]
        total_ob = ob_range["Volume"].sum() if "Volume" in ob_range.columns else 0.0
    else:
        total_ob = 0.0

    # Calculate total CH across all pits (from prod_ch)
    if not prod_ch.empty:
        if "Date" in prod_ch.columns and str(prod_ch["Date"].dtype) != "datetime64[ns]":
            prod_ch["Date"] = pd.to_datetime(prod_ch["Date"], errors="coerce")
        ch_range = prod_ch[
            (prod_ch["Date"] >= start_date) &
            (prod_ch["Date"] <= end_date)
        ]

        # Check which column exists and format
        if "Volume" in ch_range.columns:
            # NEW FORMAT: Already in MT
            total_ch = ch_range["Volume"].sum()
        elif "Netto" in ch_range.columns:
            # OLD FORMAT: kg -> MT conversion needed
            total_ch = ch_range["Netto"].sum() / 1000
        else:
            total_ch = 0.0
    else:
        total_ch = 0.0

    try:
        tob = float(total_ob)
        tch = float(total_ch)
        return tob / tch if tch > 0 else 0
    except (ValueError, TypeError):
        return 0


def calc_coal_stock(
    sheets: dict, date_range: tuple, input_values: dict
) -> dict:
    """
    Calculate Coal Stock ROM and Port (GLOBAL — same value for all JOs).

    NEW FORMAT (2026-03-15): Prioritize coal_rom sheet if available
    - Stock ROM  = Opening ROM + coal_rom Volume (dedicated ROM sheet)
    - Stock Port = Opening Port + total CH (all JOs) - Plan Barging

    FALLBACK (if coal_rom empty): Filter prod_ch by Seam
    - Stock ROM  = Opening ROM + CH where Seam in ('N-STOCK ROOM', 'N-STOCK ROOM 60', etc)
    - Stock Port = Opening Port + total CH (all JOs) - Plan Barging

    CH Volume is already in MT (NEW FORMAT) or kg (OLD FORMAT, needs /1000)
    """
    prod_ch = sheets["prod_ch"]
    coal_rom = sheets.get("coal_rom", pd.DataFrame())
    start_date, end_date = date_range
    
    # Ensure they are pandas Timestamps for safe comparison with datetime64[ns] columns
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    if not prod_ch.empty:
        if str(prod_ch["Date"].dtype) != "datetime64[ns]":
            prod_ch["Date"] = pd.to_datetime(prod_ch["Date"], errors="coerce")
        ch_range = prod_ch[
            (prod_ch["Date"] >= start_date) &
            (prod_ch["Date"] <= end_date)
        ]
    else:
        ch_range = pd.DataFrame(columns=prod_ch.columns)

    # Determine which column to use (Netto for old, Volume for new)
    if "Netto" in ch_range.columns:
        value_col = "Netto"
        needs_conversion = True  # kg -> MT
    elif "Volume" in ch_range.columns:
        value_col = "Volume"
        needs_conversion = False  # Already in MT
    else:
        value_col = None
        needs_conversion = False

    if value_col is None:
        # No data available
        ch_to_rom = 0
        total_ch = 0
    else:
        # Total CH across ALL JOs for this date range (not filtered by PIT)
        total_ch = ch_range[value_col].sum()

        # Stock ROM: Try NEW FORMAT first (coal_rom sheet), then FALLBACK to Seam filter
        # ============================================
        # METHOD 1: NEW FORMAT - Use coal_rom sheet if available and has data
        # ============================================
        if coal_rom is not None and not coal_rom.empty:
            # Filter coal_rom by date range
            rom_range = coal_rom[
                (coal_rom["Date"] >= start_date) &
                (coal_rom["Date"] <= end_date)
            ]

            # Determine value column in coal_rom
            if "Volume" in rom_range.columns:
                ch_to_rom = rom_range["Volume"].sum()
                needs_conversion_rom = False  # Volume is naturally MT
            elif "Netto" in rom_range.columns:
                ch_to_rom = rom_range["Netto"].sum()
                needs_conversion_rom = True  # kg -> MT
            else:
                ch_to_rom = 0
                needs_conversion_rom = needs_conversion
        else:
            # ============================================
            # METHOD 2: FALLBACK - Filter prod_ch by Seam (OLD FORMAT/BACKWARD COMPAT)
            # ============================================
            rom_seam_filter = [
                "N-STOCK ROOM", "N-STOCK ROOM 60",
                "N-STOCKROOM-60", "N-STOCKROOM"
            ]

            # Check if Seam column exists and has the target values
            if "Seam" in ch_range.columns:
                ch_seam_filtered = ch_range[ch_range["Seam"].isin(rom_seam_filter)]

                if not ch_seam_filtered.empty:
                    # Found data with ROM seam indicators
                    ch_to_rom = ch_seam_filtered[value_col].sum()
                else:
                    # No ROM-specific seams found, ALL CH goes to ROM (default behavior)
                    ch_to_rom = total_ch
            else:
                # No Seam column, ALL CH goes to ROM
                ch_to_rom = total_ch

            needs_conversion_rom = needs_conversion

        # Convert from kg to MT if needed
        if needs_conversion:
            total_ch = total_ch / 1000
        if needs_conversion_rom:
            ch_to_rom = ch_to_rom / 1000

    coal_stock_rom = input_values["opening_rom"] + ch_to_rom
    coal_stock_port = (
        input_values["opening_port"]
        + total_ch
        - input_values["plan_barging"]
    )

    return {"coal_stock_rom": coal_stock_rom, "coal_stock_port": coal_stock_port}

