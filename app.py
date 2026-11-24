import io
import os
import json
import time
import socket
import threading
import webbrowser
import urllib.request
import urllib.parse
import http.cookiejar
from datetime import datetime, timezone, timedelta
IST = timezone(timedelta(hours=5, minutes=30))
from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
from pattern_detector import (
    analyze_dataframe,
    detect_all_patterns,
    find_pivots,
    evaluate_weekly_hl_ll,
    evaluate_multiyear_breakout,
)

try:
    from curl_cffi import requests as cffi_requests
    YF_SESSION = cffi_requests.Session(impersonate="chrome")
except Exception:
    YF_SESSION = None

app = Flask(__name__)

CACHE = {}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NSE_CACHE_FILE = os.path.join(BASE_DIR, "nse_stocks_cache.json")
BASKETS_CACHE_FILE = os.path.join(BASE_DIR, "nse_baskets_cache.json")

NIFTY_STOCKS_CACHE = {"ts": 0, "data": []}
BASKETS_CACHE = {"ts": 0, "data": {}}

TIMEFRAME_CONFIG = {
    "1m":  {"period": "7d",   "interval": "1m",  "resample": None,   "ttl": 45},
    "3m":  {"period": "7d",   "interval": "1m",  "resample": "3min", "ttl": 45},
    "5m":  {"period": "60d",  "interval": "5m",  "resample": None,   "ttl": 60},
    "15m": {"period": "60d",  "interval": "15m", "resample": None,   "ttl": 120},
    "30m": {"period": "60d",  "interval": "30m", "resample": None,   "ttl": 180},
    "1h":  {"period": "730d", "interval": "1h",  "resample": None,   "ttl": 300},
    "2h":  {"period": "730d", "interval": "1h",  "resample": "2h",   "ttl": 300},
    "4h":  {"period": "730d", "interval": "1h",  "resample": "4h",   "ttl": 300},
    "1d":  {"period": "5y",   "interval": "1d",  "resample": None,   "ttl": 900},
    "1wk": {"period": "5y",   "interval": "1wk", "resample": None,   "ttl": 1800},
    "1mo": {"period": "5y",   "interval": "1mo", "resample": None,   "ttl": 3600},
}

NSE_INDICES = [
    {"symbol": "^NSEI", "name": "NIFTY 50 Index"},
    {"symbol": "^NSEBANK", "name": "NIFTY BANK Index"},
    {"symbol": "^CNXIT", "name": "NIFTY IT Index"},
    {"symbol": "^CNXAUTO", "name": "NIFTY AUTO Index"},
    {"symbol": "^CNXPHARMA", "name": "NIFTY PHARMA Index"},
    {"symbol": "^CNXFMCG", "name": "NIFTY FMCG Index"},
    {"symbol": "^CNXMETAL", "name": "NIFTY METAL Index"},
    {"symbol": "^CNXENERGY", "name": "NIFTY ENERGY Index"},
    {"symbol": "^CNXREALTY", "name": "NIFTY REALTY Index"},
    {"symbol": "^NSEMDCP50", "name": "NIFTY MIDCAP 50 Index"},
]

INDEX_CSV_URLS = {
    "nifty50": "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv",
    "nifty100": "https://nsearchives.nseindia.com/content/indices/ind_nifty100list.csv",
    "nifty_midcap": "https://nsearchives.nseindia.com/content/indices/ind_niftymidcap150list.csv",
    "nifty_smallcap": "https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap250list.csv",
    "nifty500": "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv",
    "nifty750": "https://nsearchives.nseindia.com/content/indices/ind_niftytotalmarket_list.csv",
}


def _create_nse_http_client():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/csv,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if YF_SESSION:
        try:
            s = cffi_requests.Session(impersonate="chrome")
            s.get("https://www.nseindia.com", headers=headers, timeout=10)
            return ("cffi", s, headers)
        except Exception:
            pass

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = list(headers.items())
    try:
        opener.open("https://www.nseindia.com", timeout=10).read()
    except Exception:
        pass
    return ("urllib", opener, headers)


def _download_with_client(client, url: str) -> str:
    mode, obj, headers = client
    try:
        if mode == "cffi":
            resp = obj.get(url, headers={**headers, "Referer": "https://www.nseindia.com/"}, timeout=15)
            if resp.status_code == 200 and len(resp.text) > 100:
                return resp.text
        else:
            with obj.open(url, timeout=15) as r:
                txt = r.read().decode("utf-8", errors="ignore")
                if len(txt) > 100:
                    return txt
    except Exception:
        pass
    return ""


def _parse_symbols_from_csv(csv_text: str) -> list:
    if not csv_text:
        return []
    try:
        df = pd.read_csv(io.StringIO(csv_text))
        df.columns = [c.strip().upper() for c in df.columns]
        sym_col = "SYMBOL" if "SYMBOL" in df.columns else None
        if not sym_col:
            return []
        out = []
        seen = set()
        for idx in df.index:
            sym = str(df.loc[idx, sym_col]).strip().upper()
            if "SERIES" in df.columns:
                series = str(df.loc[idx, "SERIES"]).strip().upper()
                if series not in ("EQ", "BE", "BZ", "SM", "ST"):
                    continue
            if sym and sym != "NAN" and not sym.startswith("DUMMY"):
                full_sym = f"{sym}.NS"
                if full_sym not in seen:
                    seen.add(full_sym)
                    out.append(full_sym)
        return out
    except Exception:
        return []


def get_nifty_total_stocks():
    now = time.time()
    if NIFTY_STOCKS_CACHE["data"] and len(NIFTY_STOCKS_CACHE["data"]) > 500 and (now - NIFTY_STOCKS_CACHE["ts"]) < 86400:
        return NIFTY_STOCKS_CACHE["data"]

    if os.path.exists(NSE_CACHE_FILE):
        try:
            age = now - os.path.getmtime(NSE_CACHE_FILE)
            with open(NSE_CACHE_FILE, "r", encoding="utf-8") as f:
                disk_data = json.load(f)
            if isinstance(disk_data, list) and len(disk_data) > 500 and age < 604800:
                NIFTY_STOCKS_CACHE["ts"] = now
                NIFTY_STOCKS_CACHE["data"] = disk_data
                return disk_data
        except Exception:
            pass

    stocks = list(NSE_INDICES)
    seen = {item["symbol"] for item in stocks}

    client = _create_nse_http_client()
    csv_text = _download_with_client(client, "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv")
    if csv_text and "SYMBOL" in csv_text.upper():
        try:
            df = pd.read_csv(io.StringIO(csv_text))
            df.columns = [c.strip().upper() for c in df.columns]
            for idx in df.index:
                sym = str(df.loc[idx, "SYMBOL"]).strip().upper() if "SYMBOL" in df.columns else ""
                series = str(df.loc[idx, "SERIES"]).strip().upper() if "SERIES" in df.columns else "EQ"
                comp = str(df.loc[idx, "NAME OF COMPANY"]).strip() if "NAME OF COMPANY" in df.columns else sym
                if sym and sym != "NAN" and series in ("EQ", "BE", "BZ", "SM", "ST"):
                    full_sym = f"{sym}.NS"
                    if full_sym not in seen:
                        seen.add(full_sym)
                        stocks.append({"symbol": full_sym, "name": comp})
        except Exception as e:
            print(f"[NSE CSV Parse Error] {e}")

    if len(stocks) > 500:
        NIFTY_STOCKS_CACHE["ts"] = now
        NIFTY_STOCKS_CACHE["data"] = stocks
        try:
            with open(NSE_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(stocks, f)
        except Exception:
            pass
        return stocks

    return NIFTY_STOCKS_CACHE["data"] or stocks


def get_index_baskets():
    now = time.time()
    if BASKETS_CACHE["data"] and len(BASKETS_CACHE["data"].get("all", [])) > 500 and (now - BASKETS_CACHE["ts"]) < 86400:
        return BASKETS_CACHE["data"]

    if os.path.exists(BASKETS_CACHE_FILE):
        try:
            age = now - os.path.getmtime(BASKETS_CACHE_FILE)
            with open(BASKETS_CACHE_FILE, "r", encoding="utf-8") as f:
                disk_baskets = json.load(f)
            if isinstance(disk_baskets, dict) and len(disk_baskets.get("all", [])) > 500 and age < 604800:
                BASKETS_CACHE["ts"] = now
                BASKETS_CACHE["data"] = disk_baskets
                return disk_baskets
        except Exception:
            pass

    all_nse_objs = get_nifty_total_stocks()
    all_symbols = [x["symbol"] for x in all_nse_objs if x["symbol"].endswith(".NS")]

    client = _create_nse_http_client()
    baskets = {}
    for key, url in INDEX_CSV_URLS.items():
        csv_txt = _download_with_client(client, url)
        parsed = _parse_symbols_from_csv(csv_txt)
        if parsed:
            baskets[key] = parsed

    # Ensure every basket has clean constituents even if a single NSE index file timed out
    if all_symbols:
        baskets.setdefault("nifty50", all_symbols[:50])
        baskets.setdefault("nifty100", all_symbols[:100])
        baskets.setdefault("nifty_midcap", all_symbols[100:250])
        baskets.setdefault("nifty_smallcap", all_symbols[250:500])
        baskets.setdefault("nifty500", all_symbols[:500])
        baskets.setdefault("nifty750", all_symbols[:750])
        baskets["all"] = all_symbols

    # Guarantee user's tracked Pharma watchlist stocks are included in Nifty 750 & All
    for must_have in ("SHILPAMED.NS", "EMCURE.NS"):
        if must_have not in baskets.get("nifty750", []):
            baskets.setdefault("nifty750", []).append(must_have)
        if must_have not in baskets.get("all", []):
            baskets.setdefault("all", []).append(must_have)

    if len(baskets.get("all", [])) > 500:
        BASKETS_CACHE["ts"] = now
        BASKETS_CACHE["data"] = baskets
        try:
            with open(BASKETS_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(baskets, f)
        except Exception:
            pass

    return baskets


def _normalize_df(df: pd.DataFrame, resample_rule: str = None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.reset_index()
    date_col = "Datetime" if "Datetime" in df.columns else "Date"
    if date_col not in df.columns:
        return pd.DataFrame()

    ts = pd.to_datetime(df[date_col])
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize("UTC")
    else:
        ts = ts.dt.tz_convert("UTC")

    df["dt"] = ts
    df = df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })
    required = ["dt", "open", "high", "low", "close", "volume"]
    if not all(c in df.columns for c in required):
        return pd.DataFrame()

    df = df[required].dropna().drop_duplicates(subset=["dt"]).sort_values("dt")

    if resample_rule:
        df = df.set_index("dt").resample(resample_rule).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna().reset_index()

    df["time"] = (df["dt"].astype("int64") // 10**9).astype(int)
    return df[["time", "open", "high", "low", "close", "volume"]].reset_index(drop=True)


def _fetch_yahoo_v8_direct(symbol: str, period: str, interval: str, resample_rule: str = None) -> pd.DataFrame:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    encoded_sym = urllib.parse.quote(symbol)
    for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        url = f"https://{host}/v8/finance/chart/{encoded_sym}?range={period}&interval={interval}&includePrePost=false"
        try:
            if YF_SESSION:
                resp = YF_SESSION.get(url, headers=headers, timeout=10)
                data = resp.json()
            else:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as r:
                    data = json.loads(r.read().decode("utf-8"))

            result = data.get("chart", {}).get("result")
            if not result:
                continue
            item = result[0]
            timestamps = item.get("timestamp", [])
            quote = item.get("indicators", {}).get("quote", [{}])[0]
            if not timestamps or not quote.get("close"):
                continue

            raw_df = pd.DataFrame({
                "Date": pd.to_datetime(timestamps, unit="s", utc=True),
                "Open": quote.get("open"),
                "High": quote.get("high"),
                "Low": quote.get("low"),
                "Close": quote.get("close"),
                "Volume": quote.get("volume", [0] * len(timestamps)),
            })
            norm = _normalize_df(raw_df, resample_rule)
            if not norm.empty:
                return norm
        except Exception:
            continue
    return pd.DataFrame()


def fetch_ohlcv(symbol: str, tf: str) -> pd.DataFrame:
    cfg = TIMEFRAME_CONFIG.get(tf, TIMEFRAME_CONFIG["1d"])
    period = cfg["period"]
    interval = cfg["interval"]
    resample_rule = cfg.get("resample")

    norm = _fetch_yahoo_v8_direct(symbol, period, interval, resample_rule)
    if not norm.empty:
        return norm

    try:
        ticker = yf.Ticker(symbol, session=YF_SESSION) if YF_SESSION else yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=True)
        norm = _normalize_df(df, resample_rule)
        if not norm.empty:
            return norm
    except Exception:
        pass

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=True)
        norm = _normalize_df(df, resample_rule)
        if not norm.empty:
            return norm
    except Exception:
        pass

    return pd.DataFrame()


def _fetch_batch_ohlcv_map(symbols: list, period: str, interval: str) -> dict:
    """Downloads OHLCV in chunks of 60 tickers so large baskets (Nifty 500/750/All) never drop stocks."""
    df_map = {}
    chunk_size = 60
    for i in range(0, len(symbols), chunk_size):
        chunk = symbols[i:i + chunk_size]
        try:
            batch_df = yf.download(
                tickers=chunk,
                period=period,
                interval=interval,
                group_by="ticker",
                auto_adjust=True,
                threads=True,
                progress=False
            )
            for sym in chunk:
                try:
                    if len(chunk) == 1:
                        sub_df = batch_df
                    elif isinstance(batch_df.columns, pd.MultiIndex) and sym in batch_df.columns.get_level_values(0):
                        sub_df = batch_df[sym]
                    else:
                        sub_df = pd.DataFrame()

                    norm_df = _normalize_df(sub_df)
                    if norm_df.empty:
                        norm_df = _fetch_yahoo_v8_direct(sym, period, interval)
                    if not norm_df.empty:
                        df_map[sym] = norm_df
                except Exception:
                    continue
        except Exception:
            for sym in chunk:
                norm_df = _fetch_yahoo_v8_direct(sym, period, interval)
                if not norm_df.empty:
                    df_map[sym] = norm_df
    return df_map


def _evaluate_cup_handle_setup(symbol: str, df: pd.DataFrame, tf: str):
    if df.empty or len(df) < 34:
        return None

    order = 5 if tf == "1d" else 4
    _, high_idx, low_idx = find_pivots(df, order=order)
    patterns = detect_all_patterns(df, high_idx, low_idx)

    n = len(df)
    active_cups = [
        p for p in patterns
        if p["name"] == "Cup and Handle" and p["endIdx"] >= (n - 15)
    ]
    if not active_cups:
        return None

    best = max(active_cups, key=lambda p: (p["endIdx"] - p["startIdx"]))
    s_idx = best["startIdx"]
    e_idx = best["endIdx"]
    meta = best.get("meta", {})

    breakout_price = float(meta.get("breakout", df["high"].iloc[s_idx:e_idx + 1].max()))
    cup_bottom = float(meta.get("cupBottom", df["low"].iloc[s_idx:e_idx + 1].min()))
    handle_low = float(meta.get("handleLow", df["low"].iloc[max(s_idx, e_idx - 10):e_idx + 1].min()))
    low_cheat = float(meta.get("lowCheat", round(cup_bottom + 0.60 * (breakout_price - cup_bottom), 2)))
    mid_cheat = float(meta.get("midCheat", round(cup_bottom + 0.80 * (breakout_price - cup_bottom), 2)))

    cmp = round(float(df["close"].iloc[-1]), 2)
    cup_height = max(0.01, breakout_price - cup_bottom)
    recovery_pct = round(((cmp - cup_bottom) / cup_height) * 100.0, 1)

    if recovery_pct >= 94.0:
        status = "BREAKOUT (100%)"
        active_pivot = breakout_price
    elif recovery_pct >= 72.0:
        status = "MID CHEAT (80%)"
        active_pivot = mid_cheat
    elif recovery_pct >= 54.0:
        status = "LOW CHEAT (60%)"
        active_pivot = low_cheat
    else:
        return None

    stop_loss = round(handle_low * 0.99, 2)
    cup_depth_pct = round((cup_height / (breakout_price + 1e-9)) * 100, 1)
    target_price = round(breakout_price + cup_height, 2)
    dist_to_100_pct = round(((breakout_price - cmp) / (cmp + 1e-9)) * 100, 2)

    avg_vol = float(df["volume"].iloc[-21:-1].mean()) if len(df) > 21 else float(df["volume"].mean())
    rel_vol = round(float(df["volume"].iloc[-1]) / (avg_vol + 1e-9), 2)

    dt_start = datetime.fromtimestamp(best["startTime"], tz=timezone.utc).strftime("%Y-%m-%d")
    dt_end = datetime.fromtimestamp(best["endTime"], tz=timezone.utc).strftime("%Y-%m-%d")

    return {
        "symbol": symbol,
        "status": status,
        "recoveryPct": recovery_pct,
        "cmp": cmp,
        "lowCheat": round(low_cheat, 2),
        "midCheat": round(mid_cheat, 2),
        "pivot": round(breakout_price, 2),
        "activeTrigger": round(active_pivot, 2),
        "distPct": dist_to_100_pct,
        "stopLoss": stop_loss,
        "target": target_price,
        "depthPct": cup_depth_pct,
        "baseBars": int(e_idx - s_idx + 1),
        "relVol": rel_vol,
        "dateLabel": f"{dt_start} → {dt_end}",
        "startTime": best["startTime"],
        "endTime": best["endTime"]
    }

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/nifty-stocks")
def nifty_stocks():
    return jsonify(get_nifty_total_stocks())


@app.route("/api/index-baskets")
def index_baskets():
    return jsonify(get_index_baskets())


@app.route("/api/chart-data")
def chart_data():
    symbol = request.args.get("symbol", "^NSEI").strip().upper()
    tf = request.args.get("tf", "1d").strip()
    force = request.args.get("force", "0") == "1"

    if tf not in TIMEFRAME_CONFIG:
        tf = "1d"

    ttl = TIMEFRAME_CONFIG[tf]["ttl"]
    cache_key = (symbol, tf)
    now = time.time()

    if not force and cache_key in CACHE and (now - CACHE[cache_key][0]) < ttl:
        cached_payload = dict(CACHE[cache_key][1])
        cached_payload["source"] = "cache"
        return jsonify(cached_payload)

    try:
        df = fetch_ohlcv(symbol, tf)
        if df.empty:
            if cache_key in CACHE:
                stale = dict(CACHE[cache_key][1])
                stale["source"] = "stale-cache"
                return jsonify(stale)
            return jsonify({"error": f"No data returned for '{symbol}' ({tf}). Verify symbol or retry in 30s."}), 429

        candles = []
        prev_close = None
        for row in df.itertuples():
            c_val = round(float(row.close), 2)
            chg_pct = round(((c_val - prev_close) / prev_close) * 100, 2) if prev_close else 0.0
            prev_close = c_val
            candles.append({
                "time": int(row.time),
                "open": round(float(row.open), 2),
                "high": round(float(row.high), 2),
                "low": round(float(row.low), 2),
                "close": c_val,
                "volume": int(row.volume),
                "changePct": chg_pct
            })

        analysis = analyze_dataframe(df, tf)

        for p in analysis["patterns"]:
            dt_start = datetime.fromtimestamp(p["startTime"], tz=IST)
            dt_end = datetime.fromtimestamp(p["endTime"], tz=IST)
            fmt = "%Y-%m-%d" if tf in ("1d", "1wk", "1mo") else "%Y-%m-%d %H:%M"
            suffix = "" if tf in ("1d", "1wk", "1mo") else " IST"
            p["dateLabel"] = f"{dt_start.strftime(fmt)} → {dt_end.strftime(fmt)}{suffix}"

        payload = {
            "symbol": symbol,
            "timeframe": tf,
            "timezone": "IST",
            "candles": candles,
            "analysis": analysis,
            "updatedAt": datetime.now(IST).strftime("%H:%M:%S IST"),
            "source": "live"
        }

        CACHE[cache_key] = (now, payload)
        return jsonify(payload)

    except Exception as e:
        if cache_key in CACHE:
            stale = dict(CACHE[cache_key][1])
            stale["source"] = "stale-cache"
            return jsonify(stale)

        err_msg = str(e)
        if "Too Many Requests" in err_msg or "Rate" in err_msg:
            err_msg = "Yahoo rate limit hit. Wait 60s and click Go."
        return jsonify({"error": err_msg}), 429


@app.route("/api/scan-cup-handle", methods=["POST"])
def scan_cup_handle():
    body = request.get_json(silent=True) or {}
    raw_symbols = body.get("symbols", [])
    tf = body.get("tf", "1d").strip()
    if tf not in ("1d", "1wk"):
        tf = "1d"

    symbols = []
    for s in raw_symbols:
        sym = str(s).strip().upper()
        if not sym:
            continue
        if not sym.startswith("^") and "." not in sym and "-" not in sym:
            sym = f"{sym}.NS"
        if sym not in symbols:
            symbols.append(sym)

    if not symbols:
        return jsonify({"error": "No valid symbols provided for scan."}), 400

    try:
        df_map = _fetch_batch_ohlcv_map(symbols, period="3y", interval=tf)
        results = []
        for sym, norm_df in df_map.items():
            try:
                hit = _evaluate_cup_handle_setup(sym, norm_df, tf)
                if hit:
                    results.append(hit)
            except Exception:
                continue

        status_rank = {"BREAKOUT (100%)": 0, "MID CHEAT (80%)": 1, "LOW CHEAT (60%)": 2}
        results.sort(key=lambda r: (status_rank.get(r["status"], 3), -r["recoveryPct"]))

        return jsonify({
            "scannedCount": len(symbols),
            "matchesCount": len(results),
            "timeframe": tf,
            "results": results,
            "scannedAt": datetime.now(IST).strftime("%H:%M:%S IST")
        })
    except Exception as e:
        return jsonify({"error": f"Batch scan error: {str(e)}"}), 500


@app.route("/api/scan-weekly-structure", methods=["POST"])
def scan_weekly_structure():
    body = request.get_json(silent=True) or {}
    raw_symbols = body.get("symbols", [])
    filter_type = body.get("filter", "ALL").strip().upper()

    symbols = []
    for s in raw_symbols:
        sym = str(s).strip().upper()
        if not sym:
            continue
        if not sym.startswith("^") and "." not in sym and "-" not in sym:
            sym = f"{sym}.NS"
        if sym not in symbols:
            symbols.append(sym)

    if not symbols:
        return jsonify({"error": "No valid symbols provided."}), 400

    try:
        df_map = _fetch_batch_ohlcv_map(symbols, period="3y", interval="1wk")
        results = []
        for sym, norm_df in df_map.items():
            try:
                hit = evaluate_weekly_hl_ll(sym, norm_df)
                if hit:
                    if filter_type in ("HL", "LL") and hit["swingType"] != filter_type:
                        continue
                    results.append(hit)
            except Exception:
                continue

        results.sort(key=lambda r: -r["score"])

        return jsonify({
            "scannedCount": len(symbols),
            "matchesCount": len(results),
            "results": results,
            "scannedAt": datetime.now(IST).strftime("%H:%M:%S IST")
        })
    except Exception as e:
        return jsonify({"error": f"Weekly scan error: {str(e)}"}), 500

@app.route("/api/scan-multiyear-breakout", methods=["POST"])
def scan_multiyear_breakout():
    body = request.get_json(silent=True) or {}
    raw_symbols = body.get("symbols", [])
    years = int(body.get("years", 3))  # 2, 3, 5, or 0 (All-Time High)

    symbols = []
    for s in raw_symbols:
        sym = str(s).strip().upper()
        if not sym:
            continue
        if not sym.startswith("^") and "." not in sym and "-" not in sym:
            sym = f"{sym}.NS"
        if sym not in symbols:
            symbols.append(sym)

    if not symbols:
        return jsonify({"error": "No valid symbols provided."}), 400

    period = "max" if years in (0, 5) else f"{years + 1}y"

    try:
        df_map = _fetch_batch_ohlcv_map(symbols, period=period, interval="1wk")
        results = []
        for sym, norm_df in df_map.items():
            try:
                hit = evaluate_multiyear_breakout(sym, norm_df, years=years)
                if hit:
                    results.append(hit)
            except Exception:
                continue

        status_rank = {"BREAKOUT": 0, "RETEST": 1, "NEAR BREAKOUT": 2}
        results.sort(key=lambda r: (status_rank.get(r["status"], 3), -r["relVol"], -r["distPct"]))

        return jsonify({
            "scannedCount": len(symbols),
            "matchesCount": len(results),
            "horizon": "ATH" if years == 0 else f"{years}Y",
            "results": results,
            "scannedAt": datetime.now(IST).strftime("%H:%M:%S IST")
        })
    except Exception as e:
        return jsonify({"error": f"Multi-year scan error: {str(e)}"}), 500


@app.route("/api/backtest", methods=["POST"])
def run_backtest_api():
    body = request.get_json(silent=True) or {}
    strategy = body.get("strategy", "cup_handle")
    raw_symbols = body.get("symbols", [])
    period = body.get("period", "3y")
    tf = body.get("tf", "1d")
    capital = float(body.get("capital", 1000000.0))
    risk_pct = float(body.get("risk", 1.0))
    max_trades = int(body.get("maxTrades", 5))
    friction_pct = float(body.get("friction", 0.15))

    symbols = []
    for s in raw_symbols:
        sym = str(s).strip().upper()
        if not sym:
            continue
        if not sym.startswith("^") and "." not in sym and "-" not in sym:
            sym = f"{sym}.NS"
        if sym not in symbols:
            symbols.append(sym)

    if not symbols:
        return jsonify({"error": "No valid symbols provided for backtest."}), 400

    try:
        from backtester import BacktestEngine
        engine = BacktestEngine(
            strategy=strategy,
            initial_capital=capital,
            risk_per_trade_pct=risk_pct,
            max_open_trades=max_trades,
            friction_pct=friction_pct / 100.0,
            max_holding_bars=35 if tf == "1d" else 15,
        )

        if len(symbols) == 1:
            sym = symbols[0]
            norm_df = fetch_ohlcv(sym, tf)
            if not norm_df.empty:
                df_map = {sym: norm_df}
            else:
                df_map = _fetch_batch_ohlcv_map(symbols, period=period, interval=tf)
        else:
            df_map = _fetch_batch_ohlcv_map(symbols, period=period, interval=tf)

        processed = 0
        if len(df_map) == 1:
            sym, norm_df = next(iter(df_map.items()))
            if norm_df is not None and not norm_df.empty:
                engine.run_on_dataframe(sym, norm_df, tf)
                processed = 1
        else:
            engine.run_portfolio(df_map, tf)
            processed = len([k for k, v in df_map.items() if v is not None and not v.empty])

        stats = engine.calculate_statistics()
        trades = [t.to_dict() for t in engine.trades]
        # Sort trades by entry date descending
        trades.sort(key=lambda x: str(x.get("Entry Date", "")), reverse=True)

        return jsonify({
            "scannedCount": len(symbols),
            "processedCount": processed,
            "strategy": strategy,
            "timeframe": tf,
            "period": period,
            "stats": stats,
            "trades": trades,
            "scannedAt": datetime.now(IST).strftime("%H:%M:%S IST")
        })
    except Exception as e:
        return jsonify({"error": f"Backtest execution error: {str(e)}"}), 500


@app.route("/api/sector-rotation", methods=["GET", "POST"])
def api_sector_rotation():
    """
    RRG Sector Rotation & Market Strength Matrix API endpoint.
    Returns RS-Ratio, RS-Momentum, Directional Tails, Multi-timeframe performance,
    and Market Breadth across all NSE Sectors vs Benchmark.
    """
    try:
        data = request.get_json(silent=True) or {}
        benchmark = request.args.get("benchmark") or data.get("benchmark") or "^NSEI"
        timeframe = request.args.get("tf") or data.get("tf") or "1wk"
        tail_length = int(request.args.get("tail") or data.get("tail") or 8)

        from sector_rotation import get_sector_rotation_matrix
        results = get_sector_rotation_matrix(
            benchmark=benchmark,
            timeframe=timeframe,
            tail_length=tail_length,
            df_provider=_fetch_batch_ohlcv_map
        )
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": f"Sector rotation error: {str(e)}"}), 500



def open_browser(port=5000):
    """Wait for Flask server to bind to the port and launch the default web browser."""
    url = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.1)
    webbrowser.open(url)


if __name__ == "__main__":
    get_nifty_total_stocks()
    get_index_baskets()

    # Automatically open the browser on app startup
    # Gated by WERKZEUG_RUN_MAIN so it opens once and doesn't duplicate on code reloads
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Thread(target=open_browser, args=(5000,), daemon=True).start()

    app.run(debug=True, host="127.0.0.1", port=5000)
