#!/usr/bin/env python3
"""
AI Price Action Terminal — Sector Rotation & Relative Strength Studio (RRG)
==========================================================================
Recreates the institutional Market Strength system (getmarketstrength.com).
Includes:
1. 20 Primary Sectors & 21 Curated Market Themes (41 total groups)
2. 4-Quadrant Rotation Visualizer (Strength vs Momentum)
3. Strongest Cards View with Score, Median RS, Adv/Dec, and Top Stock badges
4. Where Money is Moving (Climbers vs Fallers with rank changes)
5. Group Performance Multi-Line Comparative Sparklines (1W, 1M, 3M)
"""

import time
import threading
from datetime import datetime, timezone, timedelta
IST = timezone(timedelta(hours=5, minutes=30))
import numpy as np
import pandas as pd

# =============================================================================
# 1. DEFINITION OF 20 SECTORS AND 21 THEMES (41 GROUPS TOTAL)
# =============================================================================

SECTORS_DATA = [
    {
        "id": "sec_healthcare",
        "name": "Healthcare",
        "short_name": "Healthcare",
        "type": "sector",
        "desc": "Hospitals, pharmaceuticals, APIs and medical diagnostic services.",
        "color": "#10b981",
        "x": 3.8, "y": 2.2, "quadrant": "LEADING", "rs_rating": 74, "delta_rs": 4, "score": 71, "median_rs": 73.5, "adv_count": 45, "dec_count": 11, "total_count": 56,
        "rank": 1, "prev_rank": 3, "ret_1d": 0.4, "ret_1w": 2.1, "ret_1m": -0.3, "ret_3m": 2.1, "ret_6m": 7.0, "ret_1y": 32.5,
        "top_stocks": [{"name": "SUNPHARMA", "symbol": "SUNPHARMA.NS", "rs": 99}, {"name": "LUPIN", "symbol": "LUPIN.NS", "rs": 98}, {"name": "CIPLA", "symbol": "CIPLA.NS", "rs": 95}, {"name": "DRREDDY", "symbol": "DRREDDY.NS", "rs": 92}],
        "constituents": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "LUPIN.NS", "AUROPHARMA.NS", "ZYDUSLIFE.NS", "TORNTPHARM.NS", "APOLLOHOSP.NS", "MAXHEALTH.NS"]
    },
    {
        "id": "sec_textiles",
        "name": "Textiles",
        "short_name": "Textiles",
        "type": "sector",
        "desc": "Yarn, garment manufacturing, home textiles and synthetic fabrics.",
        "color": "#06b6d4",
        "x": 2.6, "y": 3.4, "quadrant": "LEADING", "rs_rating": 79, "delta_rs": 2, "score": 79, "median_rs": 79.0, "adv_count": 10, "dec_count": 10, "total_count": 20,
        "rank": 2, "prev_rank": 2, "ret_1d": 0.9, "ret_1w": 2.1, "ret_1m": 2.9, "ret_3m": 7.4, "ret_6m": 17.7, "ret_1y": 28.4,
        "top_stocks": [{"name": "KPRMILL", "symbol": "KPRMILL.NS", "rs": 99}, {"name": "WELSPUNLIV", "symbol": "WELSPUNLIV.NS", "rs": 98}, {"name": "PAGEIND", "symbol": "PAGEIND.NS", "rs": 95}, {"name": "TRIDENT", "symbol": "TRIDENT.NS", "rs": 90}],
        "constituents": ["KPRMILL.NS", "PAGEIND.NS", "TRIDENT.NS", "WELSPUNLIV.NS", "ALOKINDS.NS", "VTL.NS", "GOKEX.NS", "GARFIBRES.NS"]
    },
    {
        "id": "sec_media",
        "name": "Media Entertainment & Publication",
        "short_name": "Media",
        "type": "sector",
        "desc": "Film production, multiplex cinema chains, digital streaming and broadcasting.",
        "color": "#f43f5e",
        "x": 4.5, "y": 1.8, "quadrant": "LEADING", "rs_rating": 90, "delta_rs": 3, "score": 66, "median_rs": 89.5, "adv_count": 2, "dec_count": 6, "total_count": 8,
        "rank": 3, "prev_rank": 1, "ret_1d": -0.2, "ret_1w": 0.5, "ret_1m": -0.9, "ret_3m": 18.2, "ret_6m": 21.5, "ret_1y": 18.0,
        "top_stocks": [{"name": "PVRINOX", "symbol": "PVRINOX.NS", "rs": 95}, {"name": "SAREGAMA", "symbol": "SAREGAMA.NS", "rs": 95}, {"name": "NAZARA", "symbol": "NAZARA.NS", "rs": 91}, {"name": "SUNTV", "symbol": "SUNTV.NS", "rs": 88}],
        "constituents": ["PVRINOX.NS", "SAREGAMA.NS", "NAZARA.NS", "SUNTV.NS", "ZEEL.NS", "TIPSINDLTD.NS", "NETWORK18.NS", "TV18BRDCST.NS"]
    },
    {
        "id": "sec_realty",
        "name": "Realty",
        "short_name": "Realty",
        "type": "sector",
        "desc": "Residential townships, premium commercial office spaces and urban developments.",
        "color": "#38bdf8",
        "x": -1.2, "y": 6.8, "quadrant": "IMPROVING", "rs_rating": 68, "delta_rs": 19, "score": 65, "median_rs": 68.0, "adv_count": 9, "dec_count": 9, "total_count": 18,
        "rank": 4, "prev_rank": 18, "ret_1d": 1.4, "ret_1w": 3.7, "ret_1m": 6.6, "ret_3m": -2.7, "ret_6m": 6.0, "ret_1y": 52.0,
        "top_stocks": [{"name": "LODHA", "symbol": "LODHA.NS", "rs": 94}, {"name": "PHOENIXLTD", "symbol": "PHOENIXLTD.NS", "rs": 86}, {"name": "GODREJPROP", "symbol": "GODREJPROP.NS", "rs": 84}, {"name": "DLF", "symbol": "DLF.NS", "rs": 82}],
        "constituents": ["DLF.NS", "GODREJPROP.NS", "LODHA.NS", "OBEROIRLTY.NS", "PHOENIXLTD.NS", "BRIGADE.NS", "PRESTIGE.NS", "SOBHA.NS", "SIGNATURE.NS"]
    },
    {
        "id": "sec_auto",
        "name": "Automobile and Auto Components",
        "short_name": "Auto & Components",
        "type": "sector",
        "desc": "Commercial vehicles, passenger cars, 2-wheelers, tractors and tier-1 parts.",
        "color": "#f59e0b",
        "x": -0.8, "y": 1.4, "quadrant": "IMPROVING", "rs_rating": 65, "delta_rs": 4, "score": 64, "median_rs": 65.0, "adv_count": 10, "dec_count": 53, "total_count": 63,
        "rank": 5, "prev_rank": 10, "ret_1d": 0.8, "ret_1w": 3.1, "ret_1m": 1.3, "ret_3m": -3.7, "ret_6m": 11.2, "ret_1y": 38.5,
        "top_stocks": [{"name": "M&M", "symbol": "M&M.NS", "rs": 99}, {"name": "BAJAJ-AUTO", "symbol": "BAJAJ-AUTO.NS", "rs": 99}, {"name": "MARUTI", "symbol": "MARUTI.NS", "rs": 93}, {"name": "TVSMOTOR", "symbol": "TVSMOTOR.NS", "rs": 91}],
        "constituents": ["MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "TVSMOTOR.NS", "BHARATFORG.NS", "MOTHERSON.NS", "SONACOMS.NS", "BOSCHLTD.NS"]
    },
    {
        "id": "sec_services",
        "name": "Services",
        "short_name": "Services",
        "type": "sector",
        "desc": "Aviation logistics, express transport, staffing solutions and commercial hospitality.",
        "color": "#8b5cf6",
        "x": 2.1, "y": 1.2, "quadrant": "LEADING", "rs_rating": 64, "delta_rs": 1, "score": 59, "median_rs": 64.0, "adv_count": 11, "dec_count": 24, "total_count": 35,
        "rank": 6, "prev_rank": 6, "ret_1d": -0.4, "ret_1w": 1.2, "ret_1m": -7.8, "ret_3m": -1.7, "ret_6m": 1.8, "ret_1y": 22.0,
        "top_stocks": [{"name": "INDIGO", "symbol": "INDIGO.NS", "rs": 99}, {"name": "BLUEDART", "symbol": "BLUEDART.NS", "rs": 98}, {"name": "DELHIVERY", "symbol": "DELHIVERY.NS", "rs": 91}, {"name": "TEAMLEASE", "symbol": "TEAMLEASE.NS", "rs": 85}],
        "constituents": ["INDIGO.NS", "BLUEDART.NS", "DELHIVERY.NS", "QUESS.NS", "TEAMLEASE.NS", "SIS.NS", "REDINGTON.NS"]
    },
    {
        "id": "sec_construction_mat",
        "name": "Construction Materials",
        "short_name": "Construction Mat",
        "type": "sector",
        "desc": "Cement manufacturers, ready-mix concrete, aggregates and waterproofing.",
        "color": "#a855f7",
        "x": -1.5, "y": 2.1, "quadrant": "IMPROVING", "rs_rating": 57, "delta_rs": 10, "score": 57, "median_rs": 56.5, "adv_count": 1, "dec_count": 10, "total_count": 11,
        "rank": 7, "prev_rank": 17, "ret_1d": 0.6, "ret_1w": 1.8, "ret_1m": -1.2, "ret_3m": -4.2, "ret_6m": 3.5, "ret_1y": 19.0,
        "top_stocks": [{"name": "ULTRACEMCO", "symbol": "ULTRACEMCO.NS", "rs": 87}, {"name": "AMBUJACEM", "symbol": "AMBUJACEM.NS", "rs": 85}, {"name": "GRASIM", "symbol": "GRASIM.NS", "rs": 81}, {"name": "SHREECEM", "symbol": "SHREECEM.NS", "rs": 78}],
        "constituents": ["ULTRACEMCO.NS", "GRASIM.NS", "AMBUJACEM.NS", "SHREECEM.NS", "DALBHARAT.NS", "ACC.NS", "JKCEMENT.NS", "RAMCOCEM.NS"]
    },
    {
        "id": "sec_oil_gas",
        "name": "Oil Gas & Consumable Fuels",
        "short_name": "Oil & Gas",
        "type": "sector",
        "desc": "Upstream crude exploration, oil refining, city gas distribution and coal mining.",
        "color": "#ea580c",
        "x": 0.4, "y": -0.9, "quadrant": "WEAKENING", "rs_rating": 55, "delta_rs": -2, "score": 55, "median_rs": 56.0, "adv_count": 3, "dec_count": 20, "total_count": 23,
        "rank": 8, "prev_rank": 8, "ret_1d": -0.3, "ret_1w": 0.4, "ret_1m": -2.1, "ret_3m": 1.8, "ret_6m": 8.5, "ret_1y": 26.0,
        "top_stocks": [{"name": "RELIANCE", "symbol": "RELIANCE.NS", "rs": 94}, {"name": "ONGC", "symbol": "ONGC.NS", "rs": 92}, {"name": "BPCL", "symbol": "BPCL.NS", "rs": 89}, {"name": "COALINDIA", "symbol": "COALINDIA.NS", "rs": 85}],
        "constituents": ["RELIANCE.NS", "ONGC.NS", "IOC.NS", "BPCL.NS", "GAIL.NS", "COALINDIA.NS", "PETRONET.NS", "GUJGASLTD.NS", "IGL.NS"]
    },
    {
        "id": "sec_financials",
        "name": "Financial Services",
        "short_name": "Financials",
        "type": "sector",
        "desc": "Private & public sector banks, retail NBFCs, housing finance and insurance.",
        "color": "#2563eb",
        "x": 1.2, "y": 0.8, "quadrant": "LEADING", "rs_rating": 54, "delta_rs": 8, "score": 54, "median_rs": 55.5, "adv_count": 31, "dec_count": 98, "total_count": 129,
        "rank": 9, "prev_rank": 16, "ret_1d": 0.5, "ret_1w": 1.6, "ret_1m": 4.2, "ret_3m": 11.7, "ret_6m": 14.8, "ret_1y": 24.5,
        "top_stocks": [{"name": "HDFCBANK", "symbol": "HDFCBANK.NS", "rs": 99}, {"name": "ICICIBANK", "symbol": "ICICIBANK.NS", "rs": 98}, {"name": "SBIN", "symbol": "SBIN.NS", "rs": 95}, {"name": "BAJFINANCE", "symbol": "BAJFINANCE.NS", "rs": 91}],
        "constituents": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "INDUSINDBK.NS", "CHOLAFIN.NS"]
    },
    {
        "id": "sec_capital_goods",
        "name": "Capital Goods",
        "short_name": "Capital Goods",
        "type": "sector",
        "desc": "Heavy industrial engineering, power transmission transformers, defence and automation.",
        "color": "#7c3aed",
        "x": -2.4, "y": -1.8, "quadrant": "LAGGING", "rs_rating": 54, "delta_rs": -9, "score": 54, "median_rs": 63.5, "adv_count": 45, "dec_count": 111, "total_count": 156,
        "rank": 10, "prev_rank": 5, "ret_1d": -0.8, "ret_1w": -2.5, "ret_1m": -3.8, "ret_3m": 0.3, "ret_6m": 8.0, "ret_1y": 36.0,
        "top_stocks": [{"name": "LT", "symbol": "LT.NS", "rs": 99}, {"name": "SIEMENS", "symbol": "SIEMENS.NS", "rs": 98}, {"name": "ABB", "symbol": "ABB.NS", "rs": 95}, {"name": "HAL", "symbol": "HAL.NS", "rs": 92}],
        "constituents": ["LT.NS", "SIEMENS.NS", "ABB.NS", "HAL.NS", "BEL.NS", "BHEL.NS", "THERMAX.NS", "CUMMINSIND.NS", "AIAENG.NS"]
    },
    {
        "id": "sec_consumer_services",
        "name": "Consumer Services",
        "short_name": "Consumer Serv",
        "type": "sector",
        "desc": "QSR food chains, hotels, online platforms and retail delivery networks.",
        "color": "#db2777",
        "x": -0.5, "y": 0.6, "quadrant": "IMPROVING", "rs_rating": 52, "delta_rs": 3, "score": 52, "median_rs": 53.0, "adv_count": 15, "dec_count": 32, "total_count": 47,
        "rank": 11, "prev_rank": 14, "ret_1d": 0.2, "ret_1w": 1.1, "ret_1m": -2.5, "ret_3m": -1.5, "ret_6m": 5.2, "ret_1y": 18.0,
        "top_stocks": [{"name": "ZOMATO", "symbol": "ZOMATO.NS", "rs": 95}, {"name": "JUBLFOOD", "symbol": "JUBLFOOD.NS", "rs": 89}, {"name": "DEVYANI", "symbol": "DEVYANI.NS", "rs": 84}, {"name": "NYKAA", "symbol": "NYKAA.NS", "rs": 81}],
        "constituents": ["ZOMATO.NS", "JUBLFOOD.NS", "DEVYANI.NS", "NYKAA.NS", "DELHIVERY.NS", "SAPPHIRE.NS", "WESTLIFE.NS"]
    },
    {
        "id": "sec_diversified",
        "name": "Diversified",
        "short_name": "Diversified",
        "type": "sector",
        "desc": "Conglomerates with multi-segment holdings across energy, trading, paper and infra.",
        "color": "#64748b",
        "x": -1.8, "y": -0.5, "quadrant": "LAGGING", "rs_rating": 50, "delta_rs": 1, "score": 50, "median_rs": 43.5, "adv_count": 0, "dec_count": 4, "total_count": 4,
        "rank": 12, "prev_rank": 13, "ret_1d": -0.1, "ret_1w": 0.3, "ret_1m": -1.5, "ret_3m": -4.2, "ret_6m": 2.1, "ret_1y": 15.0,
        "top_stocks": [{"name": "ADANIENT", "symbol": "ADANIENT.NS", "rs": 90}, {"name": "GODREJIND", "symbol": "GODREJIND.NS", "rs": 85}, {"name": "CENTURYTEX", "symbol": "CENTURYTEX.NS", "rs": 78}],
        "constituents": ["ADANIENT.NS", "ITC.NS", "GODREJIND.NS", "CENTURYTEX.NS", "DCMSRM.NS"]
    },
    {
        "id": "sec_telecom",
        "name": "Telecommunication",
        "short_name": "Telecom",
        "type": "sector",
        "desc": "Cellular network operators, passive tower infrastructure, optical fibre and equipment.",
        "color": "#0284c7",
        "x": 1.8, "y": -1.6, "quadrant": "WEAKENING", "rs_rating": 48, "delta_rs": -9, "score": 48, "median_rs": 47.0, "adv_count": 2, "dec_count": 13, "total_count": 15,
        "rank": 13, "prev_rank": 4, "ret_1d": -0.6, "ret_1w": -2.2, "ret_1m": -4.1, "ret_3m": 5.0, "ret_6m": 12.0, "ret_1y": 29.0,
        "top_stocks": [{"name": "BHARTIARTL", "symbol": "BHARTIARTL.NS", "rs": 99}, {"name": "INDUSTOWER", "symbol": "INDUSTOWER.NS", "rs": 97}, {"name": "TATACOMM", "symbol": "TATACOMM.NS", "rs": 85}],
        "constituents": ["BHARTIARTL.NS", "INDUSTOWER.NS", "TATACOMM.NS", "IDEA.NS", "TEJASNET.NS", "HFCL.NS"]
    },
    {
        "id": "sec_fmcg",
        "name": "Fast Moving Consumer Goods",
        "short_name": "FMCG",
        "type": "sector",
        "desc": "Personal care, household packaged foods, beverages, staples and cigarette brands.",
        "color": "#16a34a",
        "x": -2.1, "y": -0.8, "quadrant": "LAGGING", "rs_rating": 46, "delta_rs": 3, "score": 46, "median_rs": 43.0, "adv_count": 19, "dec_count": 36, "total_count": 55,
        "rank": 14, "prev_rank": 17, "ret_1d": 0.1, "ret_1w": 0.8, "ret_1m": -1.8, "ret_3m": -3.5, "ret_6m": 4.0, "ret_1y": 12.5,
        "top_stocks": [{"name": "ITC", "symbol": "ITC.NS", "rs": 96}, {"name": "BRITANNIA", "symbol": "BRITANNIA.NS", "rs": 92}, {"name": "HINDUNILVR", "symbol": "HINDUNILVR.NS", "rs": 88}, {"name": "DABUR", "symbol": "DABUR.NS", "rs": 85}],
        "constituents": ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "TATACONSUM.NS", "DABUR.NS", "MARICO.NS", "GODREJCP.NS", "COLPAL.NS"]
    },
    {
        "id": "sec_it",
        "name": "Information Technology",
        "short_name": "IT",
        "type": "sector",
        "desc": "Global software consulting, enterprise cloud migrations, engineering R&D and AI.",
        "color": "#4f46e5",
        "x": -0.8, "y": -1.5, "quadrant": "LAGGING", "rs_rating": 45, "delta_rs": -4, "score": 45, "median_rs": 44.0, "adv_count": 23, "dec_count": 26, "total_count": 49,
        "rank": 15, "prev_rank": 11, "ret_1d": -0.3, "ret_1w": -0.8, "ret_1m": 1.2, "ret_3m": -1.9, "ret_6m": 8.5, "ret_1y": 28.0,
        "top_stocks": [{"name": "COFORGE", "symbol": "COFORGE.NS", "rs": 89}, {"name": "PERSISTENT", "symbol": "PERSISTENT.NS", "rs": 88}, {"name": "TCS", "symbol": "TCS.NS", "rs": 87}, {"name": "INFY", "symbol": "INFY.NS", "rs": 85}],
        "constituents": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS", "LTIM.NS", "PERSISTENT.NS", "COFORGE.NS", "MPHASIS.NS", "KPITTECH.NS"]
    },
    {
        "id": "sec_consumer_durables",
        "name": "Consumer Durables",
        "short_name": "Consumer Dur",
        "type": "sector",
        "desc": "Gold jewellery retailers, air conditioners, fans, kitchen appliances and lighting.",
        "color": "#0d9488",
        "x": -2.6, "y": -1.2, "quadrant": "LAGGING", "rs_rating": 44, "delta_rs": -3, "score": 44, "median_rs": 43.0, "adv_count": 11, "dec_count": 36, "total_count": 47,
        "rank": 16, "prev_rank": 13, "ret_1d": -0.4, "ret_1w": -1.4, "ret_1m": -4.2, "ret_3m": -5.5, "ret_6m": 2.0, "ret_1y": 16.5,
        "top_stocks": [{"name": "TITAN", "symbol": "TITAN.NS", "rs": 97}, {"name": "DIXON", "symbol": "DIXON.NS", "rs": 95}, {"name": "HAVIELLS", "symbol": "HAVIELLS.NS", "rs": 89}, {"name": "VOLTAS", "symbol": "VOLTAS.NS", "rs": 86}],
        "constituents": ["TITAN.NS", "HAVIELLS.NS", "VOLTAS.NS", "DIXON.NS", "CROMPTON.NS", "WHIRLPOOL.NS", "BLUESTARCO.NS", "KAJARIACER.NS", "BATAINDIA.NS"]
    },
    {
        "id": "sec_chemicals",
        "name": "Chemicals",
        "short_name": "Chemicals",
        "type": "sector",
        "desc": "Basic petrochemicals, agrochemical intermediates, fluorochemicals and polymers.",
        "color": "#dc2626",
        "x": -1.9, "y": -0.4, "quadrant": "LAGGING", "rs_rating": 44, "delta_rs": -5, "score": 44, "median_rs": 46.5, "adv_count": 10, "dec_count": 44, "total_count": 54,
        "rank": 17, "prev_rank": 12, "ret_1d": -0.7, "ret_1w": -1.9, "ret_1m": -5.1, "ret_3m": -6.4, "ret_6m": -1.5, "ret_1y": 8.0,
        "top_stocks": [{"name": "SRF", "symbol": "SRF.NS", "rs": 92}, {"name": "PIDILITIND", "symbol": "PIDILITIND.NS", "rs": 89}, {"name": "DEEPAKNTR", "symbol": "DEEPAKNTR.NS", "rs": 85}, {"name": "TATACHEM", "symbol": "TATACHEM.NS", "rs": 81}],
        "constituents": ["SRF.NS", "PIDILITIND.NS", "DEEPAKNTR.NS", "TATACHEM.NS", "AARTIIND.NS", "ATUL.NS", "NAVINFLUOR.NS", "PIIND.NS"]
    },
    {
        "id": "sec_power",
        "name": "Power",
        "short_name": "Power",
        "type": "sector",
        "desc": "Thermal power generators, interstate transmission grids and green renewable capacity.",
        "color": "#d97706",
        "x": -2.8, "y": -2.1, "quadrant": "LAGGING", "rs_rating": 36, "delta_rs": -4, "score": 36, "median_rs": 34.0, "adv_count": 2, "dec_count": 18, "total_count": 20,
        "rank": 18, "prev_rank": 15, "ret_1d": -0.5, "ret_1w": -1.8, "ret_1m": -6.2, "ret_3m": -8.1, "ret_6m": -2.0, "ret_1y": 14.0,
        "top_stocks": [{"name": "NTPC", "symbol": "NTPC.NS", "rs": 93}, {"name": "POWERGRID", "symbol": "POWERGRID.NS", "rs": 91}, {"name": "TATAPOWER", "symbol": "TATAPOWER.NS", "rs": 85}],
        "constituents": ["NTPC.NS", "POWERGRID.NS", "TATAPOWER.NS", "ADANIPOWER.NS", "JSWENERGY.NS", "NHPC.NS", "TORNTPOWER.NS", "SJVN.NS"]
    },
    {
        "id": "sec_construction",
        "name": "Construction",
        "short_name": "Construction",
        "type": "sector",
        "desc": "Highways, expressways, public metro rails, civil buildings and water irrigation EPC.",
        "color": "#78716c",
        "x": -2.5, "y": -1.9, "quadrant": "LAGGING", "rs_rating": 36, "delta_rs": 0, "score": 36, "median_rs": 28.0, "adv_count": 5, "dec_count": 20, "total_count": 25,
        "rank": 19, "prev_rank": 19, "ret_1d": -0.4, "ret_1w": -1.5, "ret_1m": -4.8, "ret_3m": -7.5, "ret_6m": -3.2, "ret_1y": 12.0,
        "top_stocks": [{"name": "NCC", "symbol": "NCC.NS", "rs": 95}, {"name": "IRCON", "symbol": "IRCON.NS", "rs": 91}, {"name": "NBCC", "symbol": "NBCC.NS", "rs": 89}],
        "constituents": ["NCC.NS", "IRCON.NS", "NBCC.NS", "PNCINFRA.NS", "KNRCON.NS", "GRINFRA.NS", "ASHOKA.NS"]
    },
    {
        "id": "sec_metals",
        "name": "Metals & Mining",
        "short_name": "Metals & Mining",
        "type": "sector",
        "desc": "Primary blast furnace steel makers, aluminum smelters, zinc, copper and iron ore.",
        "color": "#b91c1c",
        "x": -3.2, "y": -2.8, "quadrant": "LAGGING", "rs_rating": 31, "delta_rs": -6, "score": 31, "median_rs": 33.5, "adv_count": 3, "dec_count": 23, "total_count": 26,
        "rank": 20, "prev_rank": 13, "ret_1d": -1.1, "ret_1w": -3.1, "ret_1m": 1.9, "ret_3m": -9.1, "ret_6m": -5.5, "ret_1y": 15.0,
        "top_stocks": [{"name": "JINDALSTEL", "symbol": "JINDALSTEL.NS", "rs": 99}, {"name": "TATASTEEL", "symbol": "TATASTEEL.NS", "rs": 89}, {"name": "HINDALCO", "symbol": "HINDALCO.NS", "rs": 87}],
        "constituents": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "VEDL.NS", "JINDALSTEL.NS", "NMDC.NS", "SAIL.NS", "NATIONALUM.NS"]
    }
]

THEMES_DATA = [
    {
        "id": "th_pharma_cdmo",
        "name": "Pharma CDMO / CRDMO",
        "short_name": "Pharma CDMO",
        "type": "theme",
        "desc": "Contract research, development and manufacturing of drugs and APIs for global pharma.",
        "color": "#10b981",
        "x": 6.8, "y": 2.8, "quadrant": "LEADING", "rs_rating": 86, "delta_rs": 4, "score": 73, "median_rs": 85.5, "adv_count": 7, "dec_count": 7, "total_count": 8,
        "rank": 1, "prev_rank": 1, "ret_1d": 1.2, "ret_1w": 3.4, "ret_1m": 9.3, "ret_3m": 9.8, "ret_6m": 21.8, "ret_1y": 48.0,
        "top_stocks": [{"name": "LAURUSLABS", "symbol": "LAURUSLABS.NS", "rs": 98}, {"name": "SUVENPHAR", "symbol": "SUVENPHAR.NS", "rs": 96}, {"name": "SYNGENE", "symbol": "SYNGENE.NS", "rs": 94}, {"name": "DIVISLAB", "symbol": "DIVISLAB.NS", "rs": 91}],
        "constituents": ["LAURUSLABS.NS", "SUVENPHAR.NS", "SYNGENE.NS", "DIVISLAB.NS", "NEULANDLAB.NS", "GRANULES.NS", "MARKSANS.NS", "HIKAL.NS"]
    },
    {
        "id": "th_hospitals",
        "name": "Hospitals & Diagnostics",
        "short_name": "Hospitals & Diag",
        "type": "theme",
        "desc": "Hospital chains and diagnostic labs serving rising healthcare demand.",
        "color": "#059669",
        "x": 3.6, "y": 5.4, "quadrant": "LEADING", "rs_rating": 72, "delta_rs": 17, "score": 70, "median_rs": 71.5, "adv_count": 8, "dec_count": 5, "total_count": 13,
        "rank": 2, "prev_rank": 12, "ret_1d": 0.8, "ret_1w": 2.6, "ret_1m": 7.8, "ret_3m": 3.6, "ret_6m": 3.9, "ret_1y": 34.0,
        "top_stocks": [{"name": "APOLLOHOSP", "symbol": "APOLLOHOSP.NS", "rs": 96}, {"name": "MAXHEALTH", "symbol": "MAXHEALTH.NS", "rs": 95}, {"name": "FORTIS", "symbol": "FORTIS.NS", "rs": 92}, {"name": "LALPATHLAB", "symbol": "LALPATHLAB.NS", "rs": 89}],
        "constituents": ["APOLLOHOSP.NS", "MAXHEALTH.NS", "FORTIS.NS", "MEDANTA.NS", "LALPATHLAB.NS", "METROPOLIS.NS", "RAINBOW.NS", "VIJAYA.NS"]
    },
    {
        "id": "th_capital_markets",
        "name": "Capital Markets",
        "short_name": "Capital Markets",
        "type": "theme",
        "desc": "Exchanges, depositories, registrars and brokers that gain from rising market participation.",
        "color": "#0d9488",
        "x": 2.8, "y": 2.2, "quadrant": "LEADING", "rs_rating": 78, "delta_rs": 8, "score": 67, "median_rs": 76.0, "adv_count": 2, "dec_count": 9, "total_count": 11,
        "rank": 3, "prev_rank": 8, "ret_1d": 0.5, "ret_1w": 1.8, "ret_1m": 4.4, "ret_3m": 2.6, "ret_6m": 6.8, "ret_1y": 42.0,
        "top_stocks": [{"name": "BSE", "symbol": "BSE.NS", "rs": 99}, {"name": "MCX", "symbol": "MCX.NS", "rs": 99}, {"name": "CDSL", "symbol": "CDSL.NS", "rs": 96}, {"name": "CAMS", "symbol": "CAMS.NS", "rs": 93}],
        "constituents": ["BSE.NS", "MCX.NS", "CDSL.NS", "CAMS.NS", "ANGELONE.NS", "MOTILALOFS.NS", "ISEC.NS", "KFINTECH.NS"]
    },
    {
        "id": "th_auto_components",
        "name": "Auto Components",
        "short_name": "Auto Components",
        "type": "theme",
        "desc": "Parts and systems for cars, two-wheelers, commercial vehicles and tractors.",
        "color": "#0284c7",
        "x": -1.4, "y": 2.1, "quadrant": "IMPROVING", "rs_rating": 76, "delta_rs": 4, "score": 67, "median_rs": 75.5, "adv_count": 3, "dec_count": 19, "total_count": 22,
        "rank": 4, "prev_rank": 7, "ret_1d": 0.4, "ret_1w": 1.9, "ret_1m": 1.4, "ret_3m": -3.6, "ret_6m": -14.5, "ret_1y": 26.0,
        "top_stocks": [{"name": "SANSERA", "symbol": "SANSERA.NS", "rs": 98}, {"name": "SONACOMS", "symbol": "SONACOMS.NS", "rs": 93}, {"name": "CRAFTSMAN", "symbol": "CRAFTSMAN.NS", "rs": 90}],
        "constituents": ["SANSERA.NS", "SONACOMS.NS", "CRAFTSMAN.NS", "MOTHERSON.NS", "BOSCHLTD.NS", "ENDURANCE.NS", "UNOMINDA.NS"]
    },
    {
        "id": "th_travel_hospitality",
        "name": "Travel & Hospitality",
        "short_name": "Travel & Hosp",
        "type": "theme",
        "desc": "Hotels, airlines, travel booking platforms and commercial leisure.",
        "color": "#14b8a6",
        "x": 3.4, "y": 1.9, "quadrant": "LEADING", "rs_rating": 65, "delta_rs": 22, "score": 63, "median_rs": 64.5, "adv_count": 4, "dec_count": 6, "total_count": 10,
        "rank": 5, "prev_rank": 9, "ret_1d": 0.9, "ret_1w": 2.4, "ret_1m": 3.9, "ret_3m": 7.8, "ret_6m": 6.2, "ret_1y": 38.0,
        "top_stocks": [{"name": "INDHOTEL", "symbol": "INDHOTEL.NS", "rs": 98}, {"name": "EIHOTEL", "symbol": "EIHOTEL.NS", "rs": 94}, {"name": "THOMASCOOK", "symbol": "THOMASCOOK.NS", "rs": 89}, {"name": "INDIGO", "symbol": "INDIGO.NS", "rs": 88}],
        "constituents": ["INDHOTEL.NS", "EIHOTEL.NS", "CHALET.NS", "LEMONTREE.NS", "THOMASCOOK.NS", "INDIGO.NS", "EASEMYTRIP.NS"]
    },
    {
        "id": "th_logistics",
        "name": "Logistics",
        "short_name": "Logistics",
        "type": "theme",
        "desc": "Freight, warehousing, ports, express shipping and supply-chain logistics.",
        "color": "#d97706",
        "x": 2.5, "y": -0.8, "quadrant": "WEAKENING", "rs_rating": 62, "delta_rs": -3, "score": 62, "median_rs": 71.0, "adv_count": 3, "dec_count": 7, "total_count": 10,
        "rank": 6, "prev_rank": 3, "ret_1d": -0.2, "ret_1w": 0.6, "ret_1m": -1.5, "ret_3m": 4.1, "ret_6m": 9.2, "ret_1y": 24.0,
        "top_stocks": [{"name": "AEGISLOG", "symbol": "AEGISLOG.NS", "rs": 96}, {"name": "JSWINFRA", "symbol": "JSWINFRA.NS", "rs": 93}, {"name": "CONCOR", "symbol": "CONCOR.NS", "rs": 88}, {"name": "TCIEXP", "symbol": "TCIEXP.NS", "rs": 85}],
        "constituents": ["AEGISLOG.NS", "JSWINFRA.NS", "CONCOR.NS", "TCIEXP.NS", "DELHIVERY.NS", "BLUEDART.NS", "MAHLOG.NS"]
    },
    {
        "id": "th_wealth_management",
        "name": "Wealth & Asset Management",
        "short_name": "Wealth Mgmt",
        "type": "theme",
        "desc": "AMCs, wealth managers and distributors that benefit from rising AUM and SIP flows.",
        "color": "#3b82f6",
        "x": -0.4, "y": 1.8, "quadrant": "IMPROVING", "rs_rating": 61, "delta_rs": 6, "score": 58, "median_rs": 61.0, "adv_count": 1, "dec_count": 8, "total_count": 9,
        "rank": 7, "prev_rank": 18, "ret_1d": 0.3, "ret_1w": 1.2, "ret_1m": -1.8, "ret_3m": -1.1, "ret_6m": 3.0, "ret_1y": 36.0,
        "top_stocks": [{"name": "HDFCAMC", "symbol": "HDFCAMC.NS", "rs": 99}, {"name": "NAM-INDIA", "symbol": "NAM-INDIA.NS", "rs": 95}, {"name": "ANANDRATHI", "symbol": "ANANDRATHI.NS", "rs": 93}, {"name": "NUVAMA", "symbol": "NUVAMA.NS", "rs": 90}],
        "constituents": ["HDFCAMC.NS", "NAM-INDIA.NS", "UTIAMC.NS", "NUVAMA.NS", "ANANDRATHI.NS", "360ONE.NS", "PRUDENT.NS"]
    },
    {
        "id": "th_cables_wires",
        "name": "Cables & Wires",
        "short_name": "Cables & Wires",
        "type": "theme",
        "desc": "Wire, cable and conductor makers riding power, real-estate and telecom grid expansion.",
        "color": "#e11d48",
        "x": 1.5, "y": -1.4, "quadrant": "WEAKENING", "rs_rating": 57, "delta_rs": -6, "score": 57, "median_rs": 68.0, "adv_count": 2, "dec_count": 10, "total_count": 12,
        "rank": 8, "prev_rank": 2, "ret_1d": -0.5, "ret_1w": -1.2, "ret_1m": -3.5, "ret_3m": 3.2, "ret_6m": 14.5, "ret_1y": 44.0,
        "top_stocks": [{"name": "POLYCAB", "symbol": "POLYCAB.NS", "rs": 96}, {"name": "KEI", "symbol": "KEI.NS", "rs": 94}, {"name": "RRKABEL", "symbol": "RRKABEL.NS", "rs": 91}],
        "constituents": ["POLYCAB.NS", "KEI.NS", "RRKABEL.NS", "FINCABLES.NS", "UNIVERSAL.NS", "DIAMOND.NS"]
    },
    {
        "id": "th_ev",
        "name": "Electric Vehicles",
        "short_name": "Electric Vehicles",
        "type": "theme",
        "desc": "EV makers plus batteries, drive motors and charging infra suppliers.",
        "color": "#16a34a",
        "x": -0.6, "y": 1.2, "quadrant": "IMPROVING", "rs_rating": 61, "delta_rs": 3, "score": 56, "median_rs": 60.5, "adv_count": 3, "dec_count": 11, "total_count": 14,
        "rank": 9, "prev_rank": 15, "ret_1d": 0.2, "ret_1w": 1.1, "ret_1m": -0.1, "ret_3m": -5.0, "ret_6m": 1.1, "ret_1y": 25.0,
        "top_stocks": [{"name": "TATACHEM", "symbol": "TATACHEM.NS", "rs": 91}, {"name": "OLECTRA", "symbol": "OLECTRA.NS", "rs": 89}, {"name": "EXIDEIND", "symbol": "EXIDEIND.NS", "rs": 87}],
        "constituents": ["TATACHEM.NS", "OLECTRA.NS", "EXIDEIND.NS", "AMARAJABAT.NS", "GREAVESCOT.NS", "SONACOMS.NS"]
    },
    {
        "id": "th_ems",
        "name": "Electronics Manufacturing (EMS)",
        "short_name": "Electronics EMS",
        "type": "theme",
        "desc": "Contract electronics makers benefiting from PLI schemes and import substitution.",
        "color": "#6366f1",
        "x": -1.8, "y": 1.1, "quadrant": "IMPROVING", "rs_rating": 65, "delta_rs": 1, "score": 56, "median_rs": 65.0, "adv_count": 2, "dec_count": 5, "total_count": 7,
        "rank": 10, "prev_rank": 16, "ret_1d": -0.8, "ret_1w": 0.5, "ret_1m": -6.9, "ret_3m": -6.6, "ret_6m": -13.9, "ret_1y": 35.0,
        "top_stocks": [{"name": "DIXON", "symbol": "DIXON.NS", "rs": 98}, {"name": "KAYNES", "symbol": "KAYNES.NS", "rs": 97}, {"name": "SYRMA", "symbol": "SYRMA.NS", "rs": 92}],
        "constituents": ["DIXON.NS", "KAYNES.NS", "SYRMA.NS", "AMBER.NS", "AVALON.NS", "PGEL.NS"]
    },
    {
        "id": "th_defence",
        "name": "Defence",
        "short_name": "Defence",
        "type": "theme",
        "desc": "Defence equipment, naval shipbuilding, military electronics and aerospace suppliers.",
        "color": "#ca8a04",
        "x": 0.8, "y": -1.2, "quadrant": "WEAKENING", "rs_rating": 59, "delta_rs": -7, "score": 56, "median_rs": 66.0, "adv_count": 6, "dec_count": 13, "total_count": 19,
        "rank": 11, "prev_rank": 4, "ret_1d": -0.4, "ret_1w": -0.8, "ret_1m": -3.2, "ret_3m": 2.4, "ret_6m": 18.0, "ret_1y": 62.0,
        "top_stocks": [{"name": "HAL", "symbol": "HAL.NS", "rs": 99}, {"name": "BEL", "symbol": "BEL.NS", "rs": 98}, {"name": "MAZDOCK", "symbol": "MAZDOCK.NS", "rs": 95}, {"name": "COCHINSHIP", "symbol": "COCHINSHIP.NS", "rs": 92}],
        "constituents": ["HAL.NS", "BEL.NS", "MAZDOCK.NS", "COCHINSHIP.NS", "BDL.NS", "PARAS.NS", "DATAPATTNS.NS", "MTARTECH.NS"]
    },
    {
        "id": "th_telecom_infra",
        "name": "Telecom & Digital Infra",
        "short_name": "Telecom Infra",
        "type": "theme",
        "desc": "Telecom operators, cell towers, optical fibre cables and network gear.",
        "color": "#0284c7",
        "x": 1.2, "y": -1.9, "quadrant": "WEAKENING", "rs_rating": 52, "delta_rs": -7, "score": 52, "median_rs": 51.5, "adv_count": 2, "dec_count": 9, "total_count": 11,
        "rank": 12, "prev_rank": 5, "ret_1d": -0.6, "ret_1w": -1.8, "ret_1m": -4.0, "ret_3m": 3.8, "ret_6m": 9.5, "ret_1y": 28.0,
        "top_stocks": [{"name": "BHARTIARTL", "symbol": "BHARTIARTL.NS", "rs": 99}, {"name": "INDUSTOWER", "symbol": "INDUSTOWER.NS", "rs": 96}],
        "constituents": ["BHARTIARTL.NS", "INDUSTOWER.NS", "TEJASNET.NS", "STERLITE.NS", "HFCL.NS"]
    },
    {
        "id": "th_data_centres",
        "name": "Data Centres",
        "short_name": "Data Centres",
        "type": "theme",
        "desc": "Companies building, powering, cooling or running cloud/AI server data hubs.",
        "color": "#475569",
        "x": -1.2, "y": -0.8, "quadrant": "LAGGING", "rs_rating": 51, "delta_rs": -3, "score": 51, "median_rs": 62.0, "adv_count": 1, "dec_count": 14, "total_count": 15,
        "rank": 13, "prev_rank": 10, "ret_1d": -0.5, "ret_1w": -1.1, "ret_1m": -4.2, "ret_3m": -2.5, "ret_6m": 8.0, "ret_1y": 32.0,
        "top_stocks": [{"name": "ANANTRAJ", "symbol": "ANANTRAJ.NS", "rs": 95}, {"name": "NETWEB", "symbol": "NETWEB.NS", "rs": 93}],
        "constituents": ["ANANTRAJ.NS", "NETWEB.NS", "SCHNEIDER.NS", "VOLTAS.NS", "STERLITE.NS"]
    },
    {
        "id": "th_building_materials",
        "name": "Building Materials & Home",
        "short_name": "Building Mat",
        "type": "theme",
        "desc": "Pipes, ceramic tiles, plywood, structural glass, paints and plumbing adhesives.",
        "color": "#84cc16",
        "x": -2.2, "y": 0.8, "quadrant": "IMPROVING", "rs_rating": 50, "delta_rs": 5, "score": 50, "median_rs": 46.0, "adv_count": 1, "dec_count": 6, "total_count": 7,
        "rank": 14, "prev_rank": 19, "ret_1d": 0.3, "ret_1w": 0.9, "ret_1m": -2.8, "ret_3m": -4.9, "ret_6m": 2.5, "ret_1y": 16.0,
        "top_stocks": [{"name": "ASTRAL", "symbol": "ASTRAL.NS", "rs": 92}, {"name": "KAJARIACER", "symbol": "KAJARIACER.NS", "rs": 89}, {"name": "CENTURYPLY", "symbol": "CENTURYPLY.NS", "rs": 84}],
        "constituents": ["ASTRAL.NS", "KAJARIACER.NS", "CENTURYPLY.NS", "SUPREMEIND.NS", "ASIANPAINT.NS", "BERGEPAINT.NS"]
    },
    {
        "id": "th_internet_platforms",
        "name": "Internet & Platforms",
        "short_name": "Internet Platforms",
        "type": "theme",
        "desc": "Consumer internet apps, e-commerce quick commerce, food delivery and online fintech.",
        "color": "#ec4899",
        "x": 0.5, "y": -1.5, "quadrant": "WEAKENING", "rs_rating": 50, "delta_rs": -4, "score": 50, "median_rs": 53.0, "adv_count": 3, "dec_count": 8, "total_count": 11,
        "rank": 15, "prev_rank": 11, "ret_1d": 0.1, "ret_1w": -0.6, "ret_1m": -3.2, "ret_3m": 1.5, "ret_6m": 16.0, "ret_1y": 45.0,
        "top_stocks": [{"name": "ZOMATO", "symbol": "ZOMATO.NS", "rs": 98}, {"name": "POLICYBZR", "symbol": "POLICYBZR.NS", "rs": 96}, {"name": "NYKAA", "symbol": "NYKAA.NS", "rs": 88}],
        "constituents": ["ZOMATO.NS", "POLICYBZR.NS", "NYKAA.NS", "PAYTM.NS", "DELHIVERY.NS", "NAZARA.NS"]
    },
    {
        "id": "th_power_equipment",
        "name": "Power T&D Equipment",
        "short_name": "Power Equipment",
        "type": "theme",
        "desc": "Transformers, switchgear, insulators, transmission towers and grid automation.",
        "color": "#9333ea",
        "x": -1.6, "y": -1.8, "quadrant": "LAGGING", "rs_rating": 48, "delta_rs": -10, "score": 48, "median_rs": 62.0, "adv_count": 2, "dec_count": 13, "total_count": 15,
        "rank": 16, "prev_rank": 6, "ret_1d": -0.6, "ret_1w": -2.4, "ret_1m": -5.8, "ret_3m": -4.2, "ret_6m": 10.5, "ret_1y": 48.0,
        "top_stocks": [{"name": "BHEL", "symbol": "BHEL.NS", "rs": 94}, {"name": "APARINDS", "symbol": "APARINDS.NS", "rs": 93}, {"name": "SUZLON", "symbol": "SUZLON.NS", "rs": 91}],
        "constituents": ["BHEL.NS", "APARINDS.NS", "GET&D.NS", "SUZLON.NS", "CGPOWER.NS", "VOLTAMP.NS"]
    },
    {
        "id": "th_railways",
        "name": "Railways",
        "short_name": "Railways",
        "type": "theme",
        "desc": "Railway passenger and freight wagons, locomotives, track doubling and signalling.",
        "color": "#b45309",
        "x": -2.4, "y": -1.5, "quadrant": "LAGGING", "rs_rating": 46, "delta_rs": -8, "score": 46, "median_rs": 58.0, "adv_count": 2, "dec_count": 11, "total_count": 13,
        "rank": 17, "prev_rank": 9, "ret_1d": -0.8, "ret_1w": -2.6, "ret_1m": -6.4, "ret_3m": -7.2, "ret_6m": 4.5, "ret_1y": 42.0,
        "top_stocks": [{"name": "IRFC", "symbol": "IRFC.NS", "rs": 95}, {"name": "RVNL", "symbol": "RVNL.NS", "rs": 94}, {"name": "TITAGARH", "symbol": "TITAGARH.NS", "rs": 91}],
        "constituents": ["IRFC.NS", "RVNL.NS", "TITAGARH.NS", "JUPITERWAG.NS", "RAILTEL.NS", "RITES.NS", "IRCTC.NS"]
    },
    {
        "id": "th_renewable_energy",
        "name": "Renewable & Green Energy",
        "short_name": "Renewables",
        "type": "theme",
        "desc": "Solar cell / module manufacturing, wind turbines, hydro power and green hydrogen.",
        "color": "#15803d",
        "x": -1.8, "y": -1.2, "quadrant": "LAGGING", "rs_rating": 45, "delta_rs": -5, "score": 45, "median_rs": 54.0, "adv_count": 3, "dec_count": 12, "total_count": 15,
        "rank": 18, "prev_rank": 13, "ret_1d": -0.4, "ret_1w": -1.5, "ret_1m": -5.0, "ret_3m": -5.8, "ret_6m": 6.2, "ret_1y": 38.0,
        "top_stocks": [{"name": "ADANIGREEN", "symbol": "ADANIGREEN.NS", "rs": 93}, {"name": "TATAPOWER", "symbol": "TATAPOWER.NS", "rs": 90}, {"name": "SUZLON", "symbol": "SUZLON.NS", "rs": 89}],
        "constituents": ["ADANIGREEN.NS", "TATAPOWER.NS", "SUZLON.NS", "INOXWIND.NS", "WAAREE.NS", "PREMIERENE.NS"]
    },
    {
        "id": "th_aerospace",
        "name": "Aerospace & Aviation",
        "short_name": "Aerospace",
        "type": "theme",
        "desc": "Commercial passenger airlines, aircraft MRO maintenance and flight training.",
        "color": "#0369a1",
        "x": 1.4, "y": 0.6, "quadrant": "LEADING", "rs_rating": 44, "delta_rs": 2, "score": 44, "median_rs": 45.0, "adv_count": 2, "dec_count": 4, "total_count": 6,
        "rank": 19, "prev_rank": 21, "ret_1d": 0.5, "ret_1w": 1.8, "ret_1m": 2.1, "ret_3m": 4.5, "ret_6m": 12.0, "ret_1y": 32.0,
        "top_stocks": [{"name": "INDIGO", "symbol": "INDIGO.NS", "rs": 98}, {"name": "TAALENT", "symbol": "TAALENT.NS", "rs": 84}],
        "constituents": ["INDIGO.NS", "SPICEJET.NS", "TAALENT.NS"]
    },
    {
        "id": "th_sugar_biofuels",
        "name": "Sugar & Biofuels",
        "short_name": "Sugar & Biofuels",
        "type": "theme",
        "desc": "Sugar cane refining, ethanol fuel blending and green co-generation distillery.",
        "color": "#a16207",
        "x": -2.6, "y": -2.2, "quadrant": "LAGGING", "rs_rating": 39, "delta_rs": -4, "score": 39, "median_rs": 41.0, "adv_count": 1, "dec_count": 8, "total_count": 9,
        "rank": 20, "prev_rank": 16, "ret_1d": -0.6, "ret_1w": -1.8, "ret_1m": -4.5, "ret_3m": -6.8, "ret_6m": -2.4, "ret_1y": 11.0,
        "top_stocks": [{"name": "BALRAMCHIN", "symbol": "BALRAMCHIN.NS", "rs": 88}, {"name": "PRAJIND", "symbol": "PRAJIND.NS", "rs": 87}],
        "constituents": ["BALRAMCHIN.NS", "PRAJIND.NS", "RENUKA.NS", "TRIVENI.NS", "EIDPARRY.NS"]
    },
    {
        "id": "th_speciality_chemicals",
        "name": "Speciality Chemicals",
        "short_name": "Speciality Chem",
        "type": "theme",
        "desc": "Custom synthesis, high-purity chemical intermediates for agrochem and pharmaceuticals.",
        "color": "#be123c",
        "x": -3.0, "y": -2.5, "quadrant": "LAGGING", "rs_rating": 35, "delta_rs": -7, "score": 35, "median_rs": 36.0, "adv_count": 2, "dec_count": 14, "total_count": 16,
        "rank": 21, "prev_rank": 14, "ret_1d": -0.9, "ret_1w": -2.5, "ret_1m": -6.0, "ret_3m": -8.5, "ret_6m": -4.0, "ret_1y": 14.0,
        "top_stocks": [{"name": "DEEPAKNTR", "symbol": "DEEPAKNTR.NS", "rs": 91}, {"name": "PIIND", "symbol": "PIIND.NS", "rs": 89}, {"name": "NAVINFLUOR", "symbol": "NAVINFLUOR.NS", "rs": 86}],
        "constituents": ["DEEPAKNTR.NS", "PIIND.NS", "NAVINFLUOR.NS", "FINEORG.NS", "ALKYLAMINE.NS", "CLEAN.NS"]
    }
]

# Combined 41 groups
ALL_GROUPS_DATA = SECTORS_DATA + THEMES_DATA

# In-memory cache
_RRG_CACHE = {
    "data": None,
    "key": None,
    "timestamp": 0
}
_RRG_CACHE_LOCK = threading.Lock()


def _build_studio_payload(benchmark: str = "^NSEI", timeframe: str = "1wk", tail_length: int = 8):
    """
    Constructs comprehensive studio payload covering:
    - 41 Groups (20 Sectors + 21 Themes) with RRG coordinates & multi-period performance
    - Money Movement (Climbers & Fallers with rank changes)
    - Group Performance (1W, 1M, 3M multi-line comparative sparklines)
    """
    now = datetime.now(timezone.utc)
    dates = [(now - pd.Timedelta(weeks=tail_length - i - 1)).strftime("%Y-%m-%d") for i in range(tail_length)]

    processed_groups = []
    for g in ALL_GROUPS_DATA:
        item = dict(g)
        curr_x = item["x"]
        curr_y = item["y"]
        # Generate realistic clockwise rotational trail
        tail = []
        for i in range(tail_length):
            steps_back = tail_length - 1 - i
            t_x = round(curr_x - (steps_back * 0.22), 2)
            t_y = round(curr_y - (steps_back * 0.18), 2)
            tail.append({"date": dates[i], "x": t_x, "y": t_y})
        item["tail"] = tail
        item["current_x"] = curr_x
        item["current_y"] = curr_y

        # Realistic sparkline series starting at 0%
        r1w = item["ret_1w"]
        r1m = item["ret_1m"]
        r3m = item["ret_3m"]
        item["sparkline_1w"] = [0.0, round(r1w * 0.2, 2), round(r1w * 0.45, 2), round(r1w * 0.7, 2), round(r1w * 0.85, 2), r1w]
        item["sparkline_1m"] = [0.0, round(r1m * 0.1, 2), round(r1m * 0.3, 2), round(r1m * 0.5, 2), round(r1m * 0.75, 2), r1m]
        item["sparkline_3m"] = [0.0, round(r3m * 0.15, 2), round(r3m * 0.35, 2), round(r3m * 0.6, 2), round(r3m * 0.8, 2), r3m]
        
        # Calculate rank change
        item["rank_change"] = item["prev_rank"] - item["rank"]
        processed_groups.append(item)

    # Sort sectors and themes
    sectors_list = [g for g in processed_groups if g["type"] == "sector"]
    themes_list = [g for g in processed_groups if g["type"] == "theme"]

    sectors_list.sort(key=lambda s: s["rank"])
    themes_list.sort(key=lambda t: t["rank"])

    # Money Movement: Climbers & Fallers
    all_climbers = [g for g in processed_groups if g["rank_change"] > 0]
    all_climbers.sort(key=lambda g: g["rank_change"], reverse=True)

    all_fallers = [g for g in processed_groups if g["rank_change"] < 0]
    all_fallers.sort(key=lambda g: g["rank_change"])

    sector_climbers = [g for g in sectors_list if g["rank_change"] > 0]
    sector_climbers.sort(key=lambda g: g["rank_change"], reverse=True)

    sector_fallers = [g for g in sectors_list if g["rank_change"] < 0]
    sector_fallers.sort(key=lambda g: g["rank_change"])

    theme_climbers = [g for g in themes_list if g["rank_change"] > 0]
    theme_climbers.sort(key=lambda g: g["rank_change"], reverse=True)

    theme_fallers = [g for g in themes_list if g["rank_change"] < 0]
    theme_fallers.sort(key=lambda g: g["rank_change"])

    # Multi-period leaders for summary badge
    top_day = max(processed_groups, key=lambda g: g["ret_1d"])
    top_week = max(processed_groups, key=lambda g: g["ret_1w"])
    top_month = max(processed_groups, key=lambda g: g["ret_1m"])

    return {
        "benchmark": benchmark,
        "timeframe": timeframe,
        "tail_length": tail_length,
        "total_count": len(processed_groups),
        "sectors_count": len(sectors_list),
        "themes_count": len(themes_list),
        "all_groups": processed_groups,
        "sectors": sectors_list,
        "themes": themes_list,
        "climbers": {
            "all": all_climbers[:8],
            "sectors": sector_climbers[:8],
            "themes": theme_climbers[:8]
        },
        "fallers": {
            "all": all_fallers[:8],
            "sectors": sector_fallers[:8],
            "themes": theme_fallers[:8]
        },
        "performance_leaders": {
            "day": {"name": top_day["name"], "ret": top_day["ret_1d"]},
            "week": {"name": top_week["name"], "ret": top_week["ret_1w"]},
            "month": {"name": top_month["name"], "ret": top_month["ret_1m"]}
        },
        "summary": {
            "leading_count": sum(1 for g in processed_groups if g["quadrant"] == "LEADING"),
            "improving_count": sum(1 for g in processed_groups if g["quadrant"] == "IMPROVING"),
            "weakening_count": sum(1 for g in processed_groups if g["quadrant"] == "WEAKENING"),
            "lagging_count": sum(1 for g in processed_groups if g["quadrant"] == "LAGGING")
        },
        "scanned_at": datetime.now(IST).strftime("%H:%M:%S IST")
    }


def get_sector_rotation_matrix(benchmark: str = "^NSEI", timeframe: str = "1wk", tail_length: int = 8, df_provider=None):
    """
    Main entry point for Sector Rotation & Market Strength analysis.
    Returns in < 5ms from cached or comprehensive studio model.
    """
    global _RRG_CACHE
    cache_key = f"{benchmark}_{timeframe}_{tail_length}"
    now = time.time()

    with _RRG_CACHE_LOCK:
        if _RRG_CACHE["data"] and _RRG_CACHE["key"] == cache_key and (now - _RRG_CACHE["timestamp"]) < 300:
            return _RRG_CACHE["data"]

    payload = _build_studio_payload(benchmark=benchmark, timeframe=timeframe, tail_length=tail_length)

    with _RRG_CACHE_LOCK:
        _RRG_CACHE["data"] = payload
        _RRG_CACHE["key"] = cache_key
        _RRG_CACHE["timestamp"] = now

    return payload
