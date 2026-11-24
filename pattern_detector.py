import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from scipy.stats import linregress


def _r2(val):
    return round(float(val), 2)


def find_pivots(df: pd.DataFrame, order: int = 5):
    highs = df["high"].values
    lows = df["low"].values
    times = df["time"].values

    high_idx = argrelextrema(highs, np.greater_equal, order=order)[0]
    low_idx = argrelextrema(lows, np.less_equal, order=order)[0]

    filtered_highs = []
    for idx in high_idx:
        if not filtered_highs or idx - filtered_highs[-1] >= order:
            filtered_highs.append(int(idx))
        elif highs[idx] > highs[filtered_highs[-1]]:
            filtered_highs[-1] = int(idx)

    filtered_lows = []
    for idx in low_idx:
        if not filtered_lows or idx - filtered_lows[-1] >= order:
            filtered_lows.append(int(idx))
        elif lows[idx] < lows[filtered_lows[-1]]:
            filtered_lows[-1] = int(idx)

    pivots = []
    for i in filtered_highs:
        pivots.append({"idx": i, "time": int(times[i]), "price": _r2(highs[i]), "type": "H"})
    for i in filtered_lows:
        pivots.append({"idx": i, "time": int(times[i]), "price": _r2(lows[i]), "type": "L"})

    pivots.sort(key=lambda x: x["idx"])
    return pivots, filtered_highs, filtered_lows


def detect_support_resistance(df: pd.DataFrame, high_idx: list, low_idx: list, tolerance_pct: float = 0.012):
    n = len(df)
    if n < 10:
        return []

    lookback_start = max(0, n - 260)
    recent_highs = [i for i in high_idx if i >= lookback_start]
    recent_lows = [i for i in low_idx if i >= lookback_start]

    levels = []
    for i in recent_highs:
        recency_weight = 1.0 + 2.5 * ((i - lookback_start) / max(1, n - lookback_start))
        levels.append({"price": float(df["high"].iloc[i]), "weight": recency_weight, "idx": i})
    for i in recent_lows:
        recency_weight = 1.0 + 2.5 * ((i - lookback_start) / max(1, n - lookback_start))
        levels.append({"price": float(df["low"].iloc[i]), "weight": recency_weight, "idx": i})

    if not levels:
        return []

    recent_df = df.iloc[lookback_start:]
    atr_pct = float(((recent_df["high"] - recent_df["low"]) / (recent_df["close"] + 1e-9)).tail(30).mean())
    tol = max(0.008, min(0.022, atr_pct * 0.75)) if not np.isnan(atr_pct) else tolerance_pct

    levels.sort(key=lambda x: x["price"])
    clusters = []
    current_cluster = [levels[0]]

    for lvl in levels[1:]:
        avg_price = np.mean([x["price"] for x in current_cluster])
        if abs(lvl["price"] - avg_price) / avg_price <= tol:
            current_cluster.append(lvl)
        else:
            clusters.append(current_cluster)
            current_cluster = [lvl]
    clusters.append(current_cluster)

    last_close = float(df["close"].iloc[-1])
    candidates = []
    for c in clusters:
        max_recency = max(x["idx"] for x in c)
        is_very_recent = (n - 1 - max_recency) <= 35
        if len(c) >= 2 or is_very_recent:
            avg_p = _r2(np.mean([x["price"] for x in c]))
            score = sum(x["weight"] for x in c)
            dist_pct = abs(avg_p - last_close) / (last_close + 1e-9)
            if dist_pct <= 0.18:
                score *= 1.5
            zone_type = "resistance" if avg_p >= last_close else "support"
            candidates.append({
                "price": avg_p,
                "touches": len(c),
                "type": zone_type,
                "score": score
            })

    min_gap = max(0.02, tol * 2.2)

    def pick_spaced(items, limit=3):
        items.sort(key=lambda x: -x["score"])
        chosen = []
        for item in items:
            if all(abs(item["price"] - c["price"]) / (c["price"] + 1e-9) >= min_gap for c in chosen):
                chosen.append({
                    "price": item["price"],
                    "touches": item["touches"],
                    "type": item["type"]
                })
            if len(chosen) >= limit:
                break
        return chosen

    resistances = pick_spaced([x for x in candidates if x["type"] == "resistance"], limit=3)
    supports = pick_spaced([x for x in candidates if x["type"] == "support"], limit=3)

    combined = resistances + supports
    combined.sort(key=lambda x: -x["price"])
    return combined


def detect_smc_swings(df: pd.DataFrame, pivots: list):
    swing_markers = []
    smc_lines = []

    last_high = None
    last_low = None
    trend = None

    for p in pivots:
        label = ""
        color = "#94a3b8"
        if p["type"] == "H":
            if last_high is None:
                label = "H"
            elif p["price"] > last_high["price"]:
                label = "HH"
                color = "#22c55e"
                if trend == "bearish":
                    smc_lines.append({
                        "label": "CHoCH",
                        "color": "#38bdf8",
                        "startTime": last_high["time"],
                        "endTime": p["time"],
                        "price": last_high["price"]
                    })
                elif trend == "bullish":
                    smc_lines.append({
                        "label": "BOS",
                        "color": "#22c55e",
                        "startTime": last_high["time"],
                        "endTime": p["time"],
                        "price": last_high["price"]
                    })
                trend = "bullish"
            else:
                label = "LH"
                color = "#f97316"
            last_high = p
        else:
            if last_low is None:
                label = "L"
            elif p["price"] < last_low["price"]:
                label = "LL"
                color = "#ef4444"
                if trend == "bullish":
                    smc_lines.append({
                        "label": "CHoCH",
                        "color": "#f43f5e",
                        "startTime": last_low["time"],
                        "endTime": p["time"],
                        "price": last_low["price"]
                    })
                elif trend == "bearish":
                    smc_lines.append({
                        "label": "BOS",
                        "color": "#ef4444",
                        "startTime": last_low["time"],
                        "endTime": p["time"],
                        "price": last_low["price"]
                    })
                trend = "bearish"
            else:
                label = "HL"
                color = "#4ade80"
            last_low = p

        swing_markers.append({
            "time": p["time"],
            "position": "aboveBar" if p["type"] == "H" else "belowBar",
            "color": color,
            "shape": "arrowDown" if p["type"] == "H" else "arrowUp",
            "text": label
        })

    return swing_markers, smc_lines[-12:]


def detect_trendlines(df: pd.DataFrame, high_idx: list, low_idx: list, tolerance_pct: float = 0.005):
    trendlines = []
    times = df["time"].values
    highs = df["high"].values
    lows = df["low"].values

    def scan_side(indices, prices, side):
        n = len(indices)
        if n < 3:
            return
        recent = indices[-18:]
        m = len(recent)
        found = []
        for i in range(m - 2):
            for j in range(i + 1, m - 1):
                x1, y1 = recent[i], prices[recent[i]]
                x2, y2 = recent[j], prices[recent[j]]
                if x2 == x1:
                    continue
                slope = (y2 - y1) / (x2 - x1)
                intercept = y1 - slope * x1

                touches = [x1, x2]
                violated = False
                for k in range(x1 + 1, len(prices)):
                    line_val = slope * k + intercept
                    if side == "resistance" and prices[k] > line_val * (1 + tolerance_pct * 1.5):
                        if k > x2:
                            break
                        violated = True
                        break
                    if side == "support" and prices[k] < line_val * (1 - tolerance_pct * 1.5):
                        if k > x2:
                            break
                        violated = True
                        break
                    if k in indices and k > x2:
                        if abs(prices[k] - line_val) / line_val <= tolerance_pct:
                            touches.append(k)

                if not violated and len(touches) >= 3:
                    end_bar = min(len(prices) - 1, touches[-1] + 10)
                    found.append({
                        "side": side,
                        "touches": len(touches),
                        "points": [
                            {"time": int(times[x1]), "value": _r2(y1)},
                            {"time": int(times[end_bar]), "value": _r2(slope * end_bar + intercept)}
                        ]
                    })
        found.sort(key=lambda x: -x["touches"])
        trendlines.extend(found[:3])

    scan_side(high_idx, highs, "resistance")
    scan_side(low_idx, lows, "support")
    return trendlines


def _fit_line(indices, values):
    if len(indices) < 2:
        return 0.0, float(values[0])
    slope, intercept, _, _, _ = linregress(indices, values)
    return float(slope), float(intercept)


def detect_all_patterns(df: pd.DataFrame, high_idx: list, low_idx: list):
    patterns = []
    times = df["time"].values
    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values
    n = len(df)

    def add_pattern(name, p_type, start_idx, end_idx, lines, color="#38bdf8", dedup_bars=8, meta=None):
        start_idx = max(0, int(start_idx))
        end_idx = min(n - 1, int(end_idx))
        if end_idx <= start_idx:
            return
        for existing in patterns:
            if existing["name"] == name and abs(existing["endIdx"] - end_idx) < dedup_bars:
                return
        entry = {
            "id": f"{name.replace(' ', '_')}_{end_idx}",
            "name": name,
            "direction": p_type,
            "startIdx": start_idx,
            "endIdx": end_idx,
            "startTime": int(times[start_idx]),
            "endTime": int(times[end_idx]),
            "color": color,
            "lines": lines
        }
        if meta:
            entry["meta"] = meta
        patterns.append(entry)

    # 1. Double Top & Double Bottom
    for i in range(len(high_idx) - 1):
        h1, h2 = high_idx[i], high_idx[i + 1]
        if 5 <= (h2 - h1) <= 45:
            p1, p2 = highs[h1], highs[h2]
            if abs(p1 - p2) / max(p1, p2) <= 0.015:
                valley_idx = h1 + int(np.argmin(lows[h1:h2 + 1]))
                valley_p = lows[valley_idx]
                if (max(p1, p2) - valley_p) / valley_p >= 0.015:
                    end_b = min(n - 1, h2 + 4)
                    add_pattern(
                        "Double Top", "bearish", h1, end_b,
                        [
                            [{"time": int(times[h1]), "value": _r2(p1)}, {"time": int(times[valley_idx]), "value": _r2(valley_p)}, {"time": int(times[h2]), "value": _r2(p2)}],
                            [{"time": int(times[h1]), "value": _r2(valley_p)}, {"time": int(times[end_b]), "value": _r2(valley_p)}]
                        ],
                        "#ef4444"
                    )

    for i in range(len(low_idx) - 1):
        l1, l2 = low_idx[i], low_idx[i + 1]
        if 5 <= (l2 - l1) <= 45:
            p1, p2 = lows[l1], lows[l2]
            if abs(p1 - p2) / min(p1, p2) <= 0.015:
                peak_idx = l1 + int(np.argmax(highs[l1:l2 + 1]))
                peak_p = highs[peak_idx]
                if (peak_p - min(p1, p2)) / min(p1, p2) >= 0.015:
                    end_b = min(n - 1, l2 + 4)
                    add_pattern(
                        "Double Bottom", "bullish", l1, end_b,
                        [
                            [{"time": int(times[l1]), "value": _r2(p1)}, {"time": int(times[peak_idx]), "value": _r2(peak_p)}, {"time": int(times[l2]), "value": _r2(p2)}],
                            [{"time": int(times[l1]), "value": _r2(peak_p)}, {"time": int(times[end_b]), "value": _r2(peak_p)}]
                        ],
                        "#22c55e"
                    )

    # 2. Head and Shoulders & Inverse Head and Shoulders
    for i in range(len(high_idx) - 2):
        ls, hd, rs = high_idx[i], high_idx[i + 1], high_idx[i + 2]
        if 8 <= (rs - ls) <= 75:
            p_ls, p_hd, p_rs = highs[ls], highs[hd], highs[rs]
            if p_hd > p_ls * 1.012 and p_hd > p_rs * 1.012 and abs(p_ls - p_rs) / p_hd <= 0.025:
                v1 = ls + int(np.argmin(lows[ls:hd + 1]))
                v2 = hd + int(np.argmin(lows[hd:rs + 1]))
                add_pattern(
                    "Head and Shoulders", "bearish", ls, rs,
                    [
                        [
                            {"time": int(times[ls]), "value": _r2(p_ls)},
                            {"time": int(times[v1]), "value": _r2(lows[v1])},
                            {"time": int(times[hd]), "value": _r2(p_hd)},
                            {"time": int(times[v2]), "value": _r2(lows[v2])},
                            {"time": int(times[rs]), "value": _r2(p_rs)},
                        ],
                        [{"time": int(times[v1]), "value": _r2(lows[v1])}, {"time": int(times[v2]), "value": _r2(lows[v2])}]
                    ],
                    "#f43f5e"
                )

    for i in range(len(low_idx) - 2):
        ls, hd, rs = low_idx[i], low_idx[i + 1], low_idx[i + 2]
        if 8 <= (rs - ls) <= 75:
            p_ls, p_hd, p_rs = lows[ls], lows[hd], lows[rs]
            if p_hd < p_ls * 0.988 and p_hd < p_rs * 0.988 and abs(p_ls - p_rs) / p_hd <= 0.025:
                v1 = ls + int(np.argmax(highs[ls:hd + 1]))
                v2 = hd + int(np.argmax(highs[hd:rs + 1]))
                add_pattern(
                    "Inverse Head and Shoulders", "bullish", ls, rs,
                    [
                        [
                            {"time": int(times[ls]), "value": _r2(p_ls)},
                            {"time": int(times[v1]), "value": _r2(highs[v1])},
                            {"time": int(times[hd]), "value": _r2(p_hd)},
                            {"time": int(times[v2]), "value": _r2(highs[v2])},
                            {"time": int(times[rs]), "value": _r2(p_rs)},
                        ],
                        [{"time": int(times[v1]), "value": _r2(highs[v1])}, {"time": int(times[v2]), "value": _r2(highs[v2])}]
                    ],
                    "#10b981"
                )

    # 3. Triangles & Wedges
    window = 28
    step = 10
    for start in range(0, n - window, step):
        end = start + window
        w_highs = [idx for idx in high_idx if start <= idx <= end]
        w_lows = [idx for idx in low_idx if start <= idx <= end]
        if len(w_highs) >= 2 and len(w_lows) >= 2:
            s_hi, i_hi = _fit_line(w_highs, highs[w_highs])
            s_lo, i_lo = _fit_line(w_lows, lows[w_lows])
            mid_price = float(np.mean(closes[start:end]))
            norm_hi = (s_hi * window) / mid_price
            norm_lo = (s_lo * window) / mid_price

            upper_line = [
                {"time": int(times[start]), "value": _r2(s_hi * start + i_hi)},
                {"time": int(times[end]), "value": _r2(s_hi * end + i_hi)}
            ]
            lower_line = [
                {"time": int(times[start]), "value": _r2(s_lo * start + i_lo)},
                {"time": int(times[end]), "value": _r2(s_lo * end + i_lo)}
            ]

            gap_start = (s_hi * start + i_hi) - (s_lo * start + i_lo)
            gap_end = (s_hi * end + i_hi) - (s_lo * end + i_lo)

            if gap_start > 0 and 0 < gap_end < gap_start * 0.78:
                if abs(norm_hi) < 0.008 and norm_lo > 0.012:
                    add_pattern("Ascending Triangle", "bullish", start, end, [upper_line, lower_line], "#22c55e")
                elif norm_hi < -0.012 and abs(norm_lo) < 0.008:
                    add_pattern("Descending Triangle", "bearish", start, end, [upper_line, lower_line], "#ef4444")
                elif norm_hi < -0.010 and norm_lo > 0.010:
                    add_pattern("Symmetrical Triangle", "neutral", start, end, [upper_line, lower_line], "#eab308")
                elif norm_hi > 0.012 and norm_lo > norm_hi * 1.25:
                    add_pattern("Rising Wedge", "bearish", start, end, [upper_line, lower_line], "#f97316")
                elif norm_lo < -0.012 and norm_hi < norm_lo * 1.25:
                    add_pattern("Falling Wedge", "bullish", start, end, [upper_line, lower_line], "#06b6d4")

    # 4. Bull Flag & Bear Flag
    for start in range(12, n - 14, 8):
        pole_start = start - 10
        pole_move = (closes[start] - closes[pole_start]) / closes[pole_start]
        flag_end = start + 12
        x_range = np.arange(start, flag_end + 1)
        s_hi, i_hi = _fit_line(x_range, highs[start:flag_end + 1])
        s_lo, i_lo = _fit_line(x_range, lows[start:flag_end + 1])
        flag_drift = (closes[flag_end] - closes[start]) / closes[start]

        upper_line = [
            {"time": int(times[start]), "value": _r2(s_hi * start + i_hi)},
            {"time": int(times[flag_end]), "value": _r2(s_hi * flag_end + i_hi)}
        ]
        lower_line = [
            {"time": int(times[start]), "value": _r2(s_lo * start + i_lo)},
            {"time": int(times[flag_end]), "value": _r2(s_lo * flag_end + i_lo)}
        ]
        pole_line = [
            {"time": int(times[pole_start]), "value": _r2(closes[pole_start])},
            {"time": int(times[start]), "value": _r2(closes[start])}
        ]

        if pole_move > 0.035 and -0.025 <= flag_drift <= 0.002:
            add_pattern("Bull Flag", "bullish", pole_start, flag_end, [pole_line, upper_line, lower_line], "#22c55e")
        elif pole_move < -0.035 and -0.002 <= flag_drift <= 0.025:
            add_pattern("Bear Flag", "bearish", pole_start, flag_end, [pole_line, upper_line, lower_line], "#ef4444")

    # 5. Rounding Top & Rounding Bottom
    r_win = 35
    for start in range(0, n - r_win, 14):
        end = start + r_win
        x = np.arange(r_win)
        y = closes[start:end]
        coeffs = np.polyfit(x, y, 2)
        a, b, _ = coeffs
        fitted = np.polyval(coeffs, x)
        r2_score = 1 - (np.sum((y - fitted) ** 2) / (np.sum((y - np.mean(y)) ** 2) + 1e-9))
        vertex_x = -b / (2 * a + 1e-12)

        if r2_score > 0.72 and 8 <= vertex_x <= (r_win - 8):
            curve_pts = [
                {"time": int(times[start + idx]), "value": _r2(fitted[idx])}
                for idx in range(0, r_win, 3)
            ]
            if a < 0:
                add_pattern("Rounding Top", "bearish", start, end - 1, [curve_pts], "#ec4899")
            elif a > 0:
                add_pattern("Rounding Bottom", "bullish", start, end - 1, [curve_pts], "#3b82f6")

    # 6. Cup Formation with 60% Low Cheat, 80% Mid Cheat & 100% Breakout Levels
    cup_windows = [30, 50, 80, 120, 180]
    for cup_win in cup_windows:
        if n < cup_win + 4:
            continue
        step_size = max(6, cup_win // 6)
        min_handle = max(4, cup_win // 12)
        max_handle = max(14, cup_win // 4)

        for start in range(0, n - (cup_win + min_handle), step_size):
            cup_end = start + cup_win
            avail_handle = min(max_handle, n - cup_end)
            if avail_handle < min_handle:
                continue

            left_zone = max(3, cup_win // 8)
            mid_margin = max(5, cup_win // 5)

            left_rim = float(np.max(highs[start:start + left_zone]))
            cup_bottom = float(np.min(lows[start + mid_margin:cup_end - 2]))
            cup_height = left_rim - cup_bottom
            if cup_height <= 0:
                continue

            cup_depth = cup_height / (left_rim + 1e-9)
            min_depth = 0.07 if cup_win >= 50 else 0.045
            if not (min_depth <= cup_depth <= 0.50):
                continue

            # Cup bottom must occur in the left-to-center portion before the right-side recovery
            rel_bottom_idx = int(np.argmin(lows[start + mid_margin:cup_end - 2])) + mid_margin
            if not (0.18 * cup_win <= rel_bottom_idx <= 0.78 * cup_win):
                continue

            # Evaluate recovery % at the right edge of the cup + handle consolidation
            for h_len in range(min_handle, avail_handle + 1):
                h_end = cup_end + h_len
                right_edge_close = float(closes[h_end - 1])
                right_edge_high = float(np.max(highs[cup_end - 3:h_end]))
                h_low = float(np.min(lows[cup_end:h_end]))
                h_low_idx = cup_end + int(np.argmin(lows[cup_end:h_end]))

                # Recovery % from cup bottom (0%) to left rim (100%)
                recovery_pct = ((right_edge_close - cup_bottom) / cup_height) * 100.0

                # Classify into 60% Low Cheat (54-72%), 80% Mid Cheat (72-94%), or 100% Breakout (94-112%)
                if not (54.0 <= recovery_pct <= 112.0):
                    continue

                # Handle / shelf pullback must remain tight (< 14% from right-side peak)
                handle_pullback = (right_edge_high - h_low) / (right_edge_high + 1e-9)
                if handle_pullback > 0.14:
                    continue

                low_cheat_price = _r2(cup_bottom + 0.60 * cup_height)
                mid_cheat_price = _r2(cup_bottom + 0.80 * cup_height)
                breakout_price = _r2(left_rim)

                if recovery_pct >= 94.0:
                    stage = "BREAKOUT (100%)"
                    trigger_price = breakout_price
                    pat_color = "#22c55e"
                elif recovery_pct >= 72.0:
                    stage = "MID CHEAT (80%)"
                    trigger_price = mid_cheat_price
                    pat_color = "#14b8a6"
                else:
                    stage = "LOW CHEAT (60%)"
                    trigger_price = low_cheat_price
                    pat_color = "#eab308"

                # U-shaped cup curve from left rim -> bottom -> right rim/shelf
                x_pts = [0, rel_bottom_idx, cup_win - 1]
                y_pts = [left_rim, cup_bottom, float(highs[cup_end - 1])]
                poly = np.polyfit(x_pts, y_pts, 2)
                sample_step = max(2, cup_win // 15)
                cup_curve = [
                    {"time": int(times[start + idx]), "value": _r2(np.polyval(poly, idx))}
                    for idx in range(0, cup_win, sample_step)
                ]
                cup_curve.append({"time": int(times[cup_end - 1]), "value": _r2(highs[cup_end - 1])})

                handle_lines = [
                    {"time": int(times[cup_end - 1]), "value": _r2(highs[cup_end - 1])},
                    {"time": int(times[h_low_idx]), "value": _r2(h_low)},
                    {"time": int(times[h_end - 1]), "value": _r2(right_edge_close)}
                ]

                # 100% Breakout Rim Line + Active Cheat Level Line
                rim_line = [
                    {"time": int(times[start]), "value": breakout_price},
                    {"time": int(times[h_end - 1]), "value": breakout_price}
                ]
                cheat_line = [
                    {"time": int(times[start + rel_bottom_idx]), "value": trigger_price},
                    {"time": int(times[h_end - 1]), "value": trigger_price}
                ]

                lines_payload = [cup_curve, handle_lines, rim_line]
                if stage != "BREAKOUT (100%)":
                    lines_payload.append(cheat_line)

                add_pattern(
                    "Cup and Handle",
                    "bullish",
                    start,
                    h_end - 1,
                    lines_payload,
                    pat_color,
                    dedup_bars=max(12, cup_win // 3),
                    meta={
                        "stage": stage,
                        "recoveryPct": round(recovery_pct, 1),
                        "lowCheat": low_cheat_price,
                        "midCheat": mid_cheat_price,
                        "breakout": breakout_price,
                        "handleLow": _r2(h_low),
                        "cupBottom": _r2(cup_bottom)
                    }
                )
                break

    patterns.sort(key=lambda x: -x["endTime"])
    return patterns


def analyze_dataframe(df: pd.DataFrame, interval: str):
    order_map = {
        "1m": 4, "5m": 4, "15m": 5, "1h": 5,
        "1d": 5, "1wk": 4, "1mo": 3
    }
    order = order_map.get(interval, 5)
    pivots, high_idx, low_idx = find_pivots(df, order=order)
    sr_zones = detect_support_resistance(df, high_idx, low_idx)
    swing_markers, smc_lines = detect_smc_swings(df, pivots)
    trendlines = detect_trendlines(df, high_idx, low_idx)
    patterns = detect_all_patterns(df, high_idx, low_idx)

    return {
        "support_resistance": sr_zones,
        "swing_markers": swing_markers,
        "smc_lines": smc_lines,
        "trendlines": trendlines,
        "patterns": patterns
    }


def evaluate_weekly_hl_ll(symbol: str, df: pd.DataFrame):
    if df is None or df.empty or len(df) < 35:
        return None

    pivots, high_idx, low_idx = find_pivots(df, order=3)
    if len(low_idx) < 2:
        return None

    closes = df["close"].values
    highs = df["high"].values
    lows = df["low"].values
    volumes = df["volume"].values
    times = df["time"].values
    n = len(df)

    curr_low_idx = int(low_idx[-1])
    prev_low_idx = int(low_idx[-2])

    if (n - 1 - curr_low_idx) > 10:
        return None

    curr_low = float(lows[curr_low_idx])
    prev_low = float(lows[prev_low_idx])
    cmp = float(closes[-1])

    swing_type = "HL" if curr_low > prev_low else "LL"
    swing_diff_pct = round(((curr_low - prev_low) / (prev_low + 1e-9)) * 100, 2)

    sma30 = float(pd.Series(closes).rolling(30).mean().iloc[-1])
    sma30_prev = float(pd.Series(closes).rolling(30).mean().iloc[-5])
    sma30_rising = sma30 > sma30_prev
    above_sma30 = cmp > sma30

    delta = pd.Series(closes).diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    rsi_series = 100 - (100 / (1 + rs))

    curr_rsi = round(float(rsi_series.iloc[-1]), 1)
    rsi_at_curr_low = float(rsi_series.iloc[curr_low_idx])
    rsi_at_prev_low = float(rsi_series.iloc[prev_low_idx])
    bullish_div = (swing_type == "LL") and (rsi_at_curr_low > rsi_at_prev_low + 2.0)

    avg_vol = float(np.mean(volumes[-13:-1])) if n > 13 else float(np.mean(volumes))
    rel_vol = round(float(volumes[-1]) / (avg_vol + 1e-9), 2)
    bounce_pct = round(((cmp - curr_low) / (curr_low + 1e-9)) * 100, 2)
    spring_reclaim = (swing_type == "LL") and (cmp > prev_low)

    score = 0
    reasons = []

    if swing_type == "HL":
        score += 35
        reasons.append(f"Higher Low (+{swing_diff_pct}% above prior low)")
    else:
        score -= 25
        reasons.append(f"Lower Low ({swing_diff_pct}% below prior low)")

    if spring_reclaim:
        score += 35
        reasons.append("Spring undercut & reclaim above prior low")

    if bullish_div:
        score += 25
        reasons.append("14W RSI bullish divergence")

    if above_sma30 and sma30_rising:
        score += 30
        reasons.append("Above rising 30W SMA (Stage 2)")
    elif above_sma30:
        score += 15
        reasons.append("Reclaimed 30W SMA")
    elif not sma30_rising:
        score -= 25
        reasons.append("Below declining 30W SMA (Stage 4)")

    if bounce_pct >= 4.0 and rel_vol >= 1.15:
        score += 20
        reasons.append(f"Strong volume bounce (+{bounce_pct}%, {rel_vol}x vol)")
    elif bounce_pct < 1.5:
        score -= 15
        reasons.append("Weak follow-through near lows")

    if score >= 45:
        forecast = "BULLISH REVERSAL"
    elif score >= 15:
        forecast = "EARLY REVERSAL WATCH"
    elif score <= -30:
        forecast = "FURTHER SLIDE LIKELY"
    else:
        forecast = "WEAK / INDECISIVE"

    recent_swing_high = float(np.max(highs[curr_low_idx:]))
    if curr_low_idx > prev_low_idx:
        intervening_high = float(np.max(highs[prev_low_idx:curr_low_idx + 1]))
        breakout_trigger = round(max(recent_swing_high, intervening_high), 2)
    else:
        breakout_trigger = round(recent_swing_high, 2)

    invalidation_sl = round(curr_low * 0.985, 2)

    from datetime import datetime, timezone, timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    low_date = datetime.fromtimestamp(int(times[curr_low_idx]), tz=IST).strftime("%Y-%m-%d")

    return {
        "symbol": symbol,
        "swingType": swing_type,
        "lowDate": low_date,
        "swingLow": round(curr_low, 2),
        "prevLow": round(prev_low, 2),
        "cmp": round(cmp, 2),
        "bouncePct": bounce_pct,
        "sma30": round(sma30, 2),
        "rsi14": curr_rsi,
        "relVol": rel_vol,
        "forecast": forecast,
        "score": score,
        "triggerLevel": breakout_trigger,
        "stopLoss": invalidation_sl,
        "summary": " • ".join(reasons[:3]),
        "startTime": int(times[prev_low_idx]),
        "endTime": int(times[-1])
    }

def evaluate_multiyear_breakout(symbol: str, df: pd.DataFrame, years: int = 3):
    """
    Detects Multi-Year Breakouts (2Y, 3Y, 5Y, or All-Time Highs) on Weekly OHLCV data.
    Classifies setups into BREAKOUT, RETEST, or NEAR BREAKOUT (within 5% of multi-year ceiling).
    """
    if df is None or df.empty or len(df) < 52:
        return None

    # Number of weekly bars corresponding to lookback years (0 = All-Time High)
    bars_map = {2: 104, 3: 156, 5: 260}
    lookback_bars = bars_map.get(years, len(df)) if years > 0 else len(df)

    sub = df.iloc[-lookback_bars:].reset_index(drop=True) if len(df) > lookback_bars else df.reset_index(drop=True)
    m = len(sub)
    if m < 45:
        return None

    highs = sub["high"].values
    lows = sub["low"].values
    closes = sub["close"].values
    volumes = sub["volume"].values
    times = sub["time"].values

    # Exclude the most recent 12 weeks when finding the prior multi-year ceiling
    # so we identify genuine multi-year resistance bases rather than last week's high
    base_cutoff = m - 12
    if base_cutoff < 30:
        return None

    prior_highs = highs[:base_cutoff]
    peak_idx = int(np.argmax(prior_highs))
    myb_level = float(prior_highs[peak_idx])

    # Ensure the peak wasn't immediately broken right after forming (must act as a ceiling for >= 20 weeks)
    recent_12_high = float(np.max(highs[base_cutoff:]))
    between_high = float(np.max(highs[peak_idx + 1:base_cutoff])) if (base_cutoff - peak_idx) > 1 else 0.0
    if between_high > myb_level * 1.03:
        return None

    cmp = float(closes[-1])
    dist_pct = round(((cmp - myb_level) / (myb_level + 1e-9)) * 100.0, 2)

    # Filter: must be within -6% below ceiling up to +18% fresh breakout above ceiling
    if not (-6.0 <= dist_pct <= 18.0):
        return None

    # Base depth from multi-year peak to lowest trough between peak and current
    trough_slice = lows[peak_idx:]
    base_low = float(np.min(trough_slice))
    base_depth_pct = round(((myb_level - base_low) / (myb_level + 1e-9)) * 100.0, 1)

    # Volume confirmation: latest weekly volume vs 20-week average
    avg_vol = float(np.mean(volumes[-21:-1])) if m > 21 else float(np.mean(volumes))
    rel_vol = round(float(volumes[-1]) / (avg_vol + 1e-9), 2)

    # Classify stage
    if cmp >= myb_level:
        # Check if price poked higher recently and is now retesting within 3.5% of the breakout level
        if recent_12_high > myb_level * 1.04 and dist_pct <= 3.5:
            status = "RETEST"
        else:
            status = "BREAKOUT"
    else:
        status = "NEAR BREAKOUT"

    # Risk-Reward Levels: Stop-loss below recent 6-week swing low or 7% below breakout level
    recent_swing_low = float(np.min(lows[-6:]))
    stop_loss = round(max(recent_swing_low * 0.99, myb_level * 0.92), 2)
    target_price = round(myb_level + (myb_level - base_low) * 0.65, 2)
    if target_price <= cmp * 1.05:
        target_price = round(myb_level * 1.25, 2)

    from datetime import datetime, timezone, timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    peak_date = datetime.fromtimestamp(int(times[peak_idx]), tz=IST).strftime("%Y-%m-%d")
    age_weeks = int(m - 1 - peak_idx)
    age_years = round(age_weeks / 52.0, 1)

    return {
        "symbol": symbol,
        "status": status,
        "horizon": "ATH" if years == 0 else f"{years}Y",
        "cmp": round(cmp, 2),
        "mybLevel": round(myb_level, 2),
        "distPct": dist_pct,
        "peakDate": peak_date,
        "ageYears": age_years,
        "baseDepthPct": base_depth_pct,
        "stopLoss": stop_loss,
        "target": target_price,
        "relVol": rel_vol,
        "startTime": int(times[peak_idx]),
        "endTime": int(times[-1])
    }
