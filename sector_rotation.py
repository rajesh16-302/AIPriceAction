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

import os
import json
import time
import threading
from datetime import datetime, timezone, timedelta
IST = timezone(timedelta(hours=5, minutes=30))
import numpy as np
import pandas as pd

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sector_rotation_cache.json")

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
        "constituents": ["PVRINOX.NS", "SAREGAMA.NS", "NAZARA.NS", "SUNTV.NS", "ZEEL.NS", "TIPSMUSIC.NS", "NETWORK18.NS", "DBCORP.NS"]
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
        "constituents": ["RELIANCE.NS", "ONGC.NS", "IOC.NS", "BPCL.NS", "GAIL.NS", "COALINDIA.NS", "PETRONET.NS", "IGL.NS", "IGL.NS"]
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
        "top_stocks": [{"name": "ZOMATO", "symbol": "ETERNAL.NS", "rs": 95}, {"name": "JUBLFOOD", "symbol": "JUBLFOOD.NS", "rs": 89}, {"name": "DEVYANI", "symbol": "DEVYANI.NS", "rs": 84}, {"name": "NYKAA", "symbol": "NYKAA.NS", "rs": 81}],
        "constituents": ["ETERNAL.NS", "JUBLFOOD.NS", "DEVYANI.NS", "NYKAA.NS", "DELHIVERY.NS", "SAPPHIRE.NS", "WESTLIFE.NS"]
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
        "top_stocks": [{"name": "ADANIENT", "symbol": "ADANIENT.NS", "rs": 90}, {"name": "GODREJIND", "symbol": "GODREJIND.NS", "rs": 85}, {"name": "CENTURYTEX", "symbol": "ABREL.NS", "rs": 78}],
        "constituents": ["ADANIENT.NS", "ITC.NS", "GODREJIND.NS", "ABREL.NS", "DCMSRM.NS"]
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
        "constituents": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS", "PERSISTENT.NS", "COFORGE.NS", "MPHASIS.NS", "KPITTECH.NS"]
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
        "top_stocks": [{"name": "TITAN", "symbol": "TITAN.NS", "rs": 97}, {"name": "DIXON", "symbol": "DIXON.NS", "rs": 95}, {"name": "HAVIELLS", "symbol": "HAVELLS.NS", "rs": 89}, {"name": "VOLTAS", "symbol": "VOLTAS.NS", "rs": 86}],
        "constituents": ["TITAN.NS", "HAVELLS.NS", "VOLTAS.NS", "DIXON.NS", "CROMPTON.NS", "WHIRLPOOL.NS", "BLUESTARCO.NS", "KAJARIACER.NS", "BATAINDIA.NS"]
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
        "top_stocks": [{"name": "LAURUSLABS", "symbol": "LAURUSLABS.NS", "rs": 98}, {"name": "SUVENPHAR", "symbol": "COHANCE.NS", "rs": 96}, {"name": "SYNGENE", "symbol": "SYNGENE.NS", "rs": 94}, {"name": "DIVISLAB", "symbol": "DIVISLAB.NS", "rs": 91}],
        "constituents": ["LAURUSLABS.NS", "COHANCE.NS", "SYNGENE.NS", "DIVISLAB.NS", "NEULANDLAB.NS", "GRANULES.NS", "MARKSANS.NS", "HIKAL.NS"]
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
        "constituents": ["BSE.NS", "MCX.NS", "CDSL.NS", "CAMS.NS", "ANGELONE.NS", "MOTILALOFS.NS", "KFINTECH.NS"]
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
        "constituents": ["POLYCAB.NS", "KEI.NS", "RRKABEL.NS", "FINCABLES.NS", "FINCABLES.NS", "KEI.NS"]
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
        "constituents": ["TATACHEM.NS", "OLECTRA.NS", "EXIDEIND.NS", "ARE&M.NS", "GREAVESCOT.NS", "SONACOMS.NS"]
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
        "constituents": ["BHARTIARTL.NS", "INDUSTOWER.NS", "TEJASNET.NS", "STLTECH.NS", "HFCL.NS"]
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
        "constituents": ["ANANTRAJ.NS", "NETWEB.NS", "SCHNEIDER.NS", "VOLTAS.NS", "STLTECH.NS"]
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
        "top_stocks": [{"name": "ZOMATO", "symbol": "ETERNAL.NS", "rs": 98}, {"name": "POLICYBZR", "symbol": "POLICYBZR.NS", "rs": 96}, {"name": "NYKAA", "symbol": "NYKAA.NS", "rs": 88}],
        "constituents": ["ETERNAL.NS", "POLICYBZR.NS", "NYKAA.NS", "PAYTM.NS", "DELHIVERY.NS", "NAZARA.NS"]
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
        "constituents": ["BHEL.NS", "APARINDS.NS", "GVT&D.NS", "SUZLON.NS", "CGPOWER.NS", "VOLTAMP.NS"]
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
        "constituents": ["IRFC.NS", "RVNL.NS", "TITAGARH.NS", "JWL.NS", "RAILTEL.NS", "RITES.NS", "IRCTC.NS"]
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
        "constituents": ["ADANIGREEN.NS", "TATAPOWER.NS", "SUZLON.NS", "INOXWIND.NS", "WAAREEENER.NS", "PREMIERENE.NS"]
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
        "top_stocks": [{"name": "INDIGO", "symbol": "INDIGO.NS", "rs": 98}, {"name": "HAL", "symbol": "HAL.NS", "rs": 84}],
        "constituents": ["INDIGO.NS", "HAL.NS", "BEL.NS", "GMRAIRPORT.NS"]
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


def _safe_ret(series: np.ndarray, idx: int, lookback: int) -> float:
    """Computes percentage return ending at `idx` over `lookback` bars safely."""
    if idx < 1:
        return 0.0
    prev_idx = max(0, idx - lookback)
    curr = float(series[idx])
    prev = float(series[prev_idx])
    if prev <= 0 or np.isnan(curr) or np.isnan(prev):
        return 0.0
    return ((curr / prev) - 1.0) * 100.0


def _compute_rs_ratings_at_offset(close_mat: pd.DataFrame, offset: int) -> dict:
    """
    Computes cross-sectional IBD/Market-Strength RS Rating (1-99) for every stock
    at `len(close_mat) - 1 - offset`.
    """
    n_rows = len(close_mat)
    idx = n_rows - 1 - offset
    if idx < 22:
        return {col: 50.0 for col in close_mat.columns}

    raw_scores = {}
    for col in close_mat.columns:
        vals = close_mat[col].values
        if np.isnan(vals[idx]):
            continue
        r1m = _safe_ret(vals, idx, 21)
        r3m = _safe_ret(vals, idx, 63)
        r6m = _safe_ret(vals, idx, 126)
        r1y = _safe_ret(vals, idx, 250)
        raw_scores[col] = (0.40 * r3m) + (0.25 * r6m) + (0.20 * r1m) + (0.15 * r1y)

    if not raw_scores:
        return {col: 50.0 for col in close_mat.columns}

    s = pd.Series(raw_scores)
    pct_ranks = s.rank(pct=True, method="average") * 98.0 + 1.0
    return {sym: round(float(val), 1) for sym, val in pct_ranks.items()}


def _compute_group_scores_at_offset(
    close_mat: pd.DataFrame,
    rs_map: dict,
    offset: int,
) -> dict:
    """Computes composite Market Strength score for every group at a historical offset."""
    n_rows = len(close_mat)
    idx = n_rows - 1 - offset
    scores = {}
    for g in ALL_GROUPS_DATA:
        constituents = [s for s in g.get("constituents", []) if s in close_mat.columns]
        if not constituents or idx < 5:
            scores[g["id"]] = float(g.get("score", 50.0))
            continue

        rs_vals = []
        above_50 = 0
        above_200 = 0
        valid_cnt = 0

        for sym in constituents:
            vals = close_mat[sym].values
            c_now = vals[idx]
            if np.isnan(c_now) or c_now <= 0:
                continue
            valid_cnt += 1
            rs_vals.append(rs_map.get(sym, 50.0))

            start_50 = max(0, idx - 49)
            sma50 = float(np.nanmean(vals[start_50:idx + 1]))
            if c_now > sma50:
                above_50 += 1

            start_200 = max(0, idx - 199)
            sma200 = float(np.nanmean(vals[start_200:idx + 1]))
            if c_now > sma200:
                above_200 += 1

        if valid_cnt == 0:
            scores[g["id"]] = float(g.get("score", 50.0))
            continue

        med_rs = float(np.median(rs_vals)) if rs_vals else 50.0
        pct_50 = (above_50 / valid_cnt) * 100.0
        pct_200 = (above_200 / valid_cnt) * 100.0
        scores[g["id"]] = round(0.60 * med_rs + 0.20 * pct_50 + 0.20 * pct_200, 2)

    return scores


def _rank_groups_by_score(score_map: dict, group_ids: list) -> dict:
    """Returns {group_id: 1-based rank} sorted descending by score."""
    ordered = sorted(group_ids, key=lambda gid: (-score_map.get(gid, 0.0), gid))
    return {gid: r + 1 for r, gid in enumerate(ordered)}


def _build_movement_buckets(groups: list, curr_rank_key: str, prev_rank_key: str) -> dict:
    """Builds climbers & fallers lists for a given rank comparison."""
    climbers = []
    fallers = []
    for g in groups:
        c_rank = g[curr_rank_key]
        p_rank = g[prev_rank_key]
        diff = p_rank - c_rank
        entry = {
            "id": g["id"],
            "name": g["name"],
            "type": g["type"],
            "rank": c_rank,
            "prev_rank": p_rank,
            "rank_change": diff,
        }
        if diff > 0:
            climbers.append(entry)
        elif diff < 0:
            fallers.append(entry)
    climbers.sort(key=lambda x: (-x["rank_change"], x["rank"]))
    fallers.sort(key=lambda x: (x["rank_change"], -x["rank"]))
    return {"climbers": climbers[:8], "fallers": fallers[:8]}


def _compute_live_studio_payload(
    benchmark: str = "^CRSLDX",
    timeframe: str = "1wk",
    tail_length: int = 8,
    df_provider=None,
):
    """
    Fetches live 1-year daily OHLCV for all 263 constituent stocks + benchmark
    and computes real RS ratings, 4-quadrant RRG coordinates & historical trails,
    breadth (Adv/Dec, >50 DMA, >200 DMA), rank shifts (1D/1W/3W/6W), and
    comparative performance sparklines (1W, 1M, 3M).
    """
    if df_provider is None:
        return None

    unique_stocks = sorted({
        sym
        for g in ALL_GROUPS_DATA
        for sym in g.get("constituents", [])
    })
    fetch_list = list(unique_stocks)
    for b_sym in (benchmark, "^NSEI"):
        if b_sym and b_sym not in fetch_list:
            fetch_list.append(b_sym)

    df_map = df_provider(fetch_list, period="1y", interval="1d")
    if not df_map:
        return None

    # Resolve benchmark series (fallback to ^NSEI if ^CRSLDX unavailable)
    bench_df = df_map.get(benchmark)
    used_benchmark = benchmark
    if bench_df is None or bench_df.empty or len(bench_df) < 30:
        bench_df = df_map.get("^NSEI")
        used_benchmark = "^NSEI"

    # Build aligned close matrix keyed by UTC date string
    series_dict = {}
    for sym in unique_stocks:
        sdf = df_map.get(sym)
        if sdf is not None and not sdf.empty and len(sdf) >= 30:
            dt_idx = pd.to_datetime(sdf["time"], unit="s", utc=True).dt.strftime("%Y-%m-%d")
            s = pd.Series(sdf["close"].values, index=dt_idx)
            s = s[~s.index.duplicated(keep="last")]
            series_dict[sym] = s

    if len(series_dict) < 20:
        return None

    close_mat = pd.DataFrame(series_dict).sort_index()
    # Forward-fill occasional single-day holidays/halts, keep recent 260 trading days
    close_mat = close_mat.ffill(limit=3).tail(260)
    n_rows = len(close_mat)
    if n_rows < 30:
        return None

    dates_index = list(close_mat.index)

    # Align benchmark returns on the same dates
    if bench_df is not None and not bench_df.empty:
        b_idx = pd.to_datetime(bench_df["time"], unit="s", utc=True).dt.strftime("%Y-%m-%d")
        b_series = pd.Series(bench_df["close"].values, index=b_idx)
        b_series = b_series[~b_series.index.duplicated(keep="last")].reindex(close_mat.index).ffill()
        bench_vals = b_series.values
    else:
        # Synthetic equal-weight market average fallback if index ticker failed
        bench_vals = close_mat.mean(axis=1).values

    # Compute RS maps for today (0), 1M ago (21), and historical trail points
    step_bars = 5 if timeframe == "1wk" else 1
    trail_offsets = [k * step_bars for k in range(tail_length - 1, -1, -1)]
    needed_offsets = set(trail_offsets) | {0, 1, 5, 15, 21, 30}

    rs_by_offset = {}
    for off in needed_offsets:
        if off < n_rows - 22:
            rs_by_offset[off] = _compute_rs_ratings_at_offset(close_mat, off)
        else:
            rs_by_offset[off] = {col: 50.0 for col in close_mat.columns}

    # Compute scores at 0, 1, 5, 15, 30 trading days ago for rank shifts
    scores_0 = _compute_group_scores_at_offset(close_mat, rs_by_offset[0], 0)
    scores_1d = _compute_group_scores_at_offset(close_mat, rs_by_offset[1], 1)
    scores_1w = _compute_group_scores_at_offset(close_mat, rs_by_offset[5], 5)
    scores_3w = _compute_group_scores_at_offset(close_mat, rs_by_offset[15], 15)
    scores_6w = _compute_group_scores_at_offset(close_mat, rs_by_offset[30], 30)

    sector_ids = [g["id"] for g in ALL_GROUPS_DATA if g["type"] == "sector"]
    theme_ids = [g["id"] for g in ALL_GROUPS_DATA if g["type"] == "theme"]
    all_ids = [g["id"] for g in ALL_GROUPS_DATA]

    # Category-specific ranks (for Strongest cards & Money movement)
    sec_ranks_0 = _rank_groups_by_score(scores_0, sector_ids)
    sec_ranks_1d = _rank_groups_by_score(scores_1d, sector_ids)
    sec_ranks_1w = _rank_groups_by_score(scores_1w, sector_ids)
    sec_ranks_3w = _rank_groups_by_score(scores_3w, sector_ids)
    sec_ranks_6w = _rank_groups_by_score(scores_6w, sector_ids)

    th_ranks_0 = _rank_groups_by_score(scores_0, theme_ids)
    th_ranks_1d = _rank_groups_by_score(scores_1d, theme_ids)
    th_ranks_1w = _rank_groups_by_score(scores_1w, theme_ids)
    th_ranks_3w = _rank_groups_by_score(scores_3w, theme_ids)
    th_ranks_6w = _rank_groups_by_score(scores_6w, theme_ids)

    all_ranks_0 = _rank_groups_by_score(scores_0, all_ids)
    all_ranks_1d = _rank_groups_by_score(scores_1d, all_ids)
    all_ranks_1w = _rank_groups_by_score(scores_1w, all_ids)
    all_ranks_3w = _rank_groups_by_score(scores_3w, all_ids)
    all_ranks_6w = _rank_groups_by_score(scores_6w, all_ids)

    idx_now = n_rows - 1
    bench_ret_3m_now = _safe_ret(bench_vals, idx_now, 63)

    processed_groups = []
    for g in ALL_GROUPS_DATA:
        item = dict(g)
        gid = g["id"]
        constituents = [s for s in g.get("constituents", []) if s in close_mat.columns]

        if not constituents:
            processed_groups.append(item)
            continue

        # Live returns per constituent
        rets_1d, rets_1w, rets_1m, rets_3m, rets_6m, rets_1y = [], [], [], [], [], []
        rs_now_list = []
        rs_1m_list = []
        adv_cnt = 0
        dec_cnt = 0
        above_50 = 0
        above_200 = 0
        stock_rs_pairs = []

        for sym in constituents:
            vals = close_mat[sym].values
            c_now = vals[idx_now]
            if np.isnan(c_now) or c_now <= 0:
                continue

            r1d = _safe_ret(vals, idx_now, 1)
            r1w = _safe_ret(vals, idx_now, 5)
            r1m = _safe_ret(vals, idx_now, 21)
            r3m = _safe_ret(vals, idx_now, 63)
            r6m = _safe_ret(vals, idx_now, 126)
            r1y = _safe_ret(vals, idx_now, 250)

            rets_1d.append(r1d)
            rets_1w.append(r1w)
            rets_1m.append(r1m)
            rets_3m.append(r3m)
            rets_6m.append(r6m)
            rets_1y.append(r1y)

            if r1d > 0:
                adv_cnt += 1
            else:
                dec_cnt += 1

            sma50 = float(np.nanmean(vals[max(0, idx_now - 49):idx_now + 1]))
            sma200 = float(np.nanmean(vals[max(0, idx_now - 199):idx_now + 1]))
            if c_now > sma50:
                above_50 += 1
            if c_now > sma200:
                above_200 += 1

            s_rs_now = rs_by_offset[0].get(sym, 50.0)
            s_rs_1m = rs_by_offset[21].get(sym, 50.0)
            rs_now_list.append(s_rs_now)
            rs_1m_list.append(s_rs_1m)
            stock_rs_pairs.append({"name": sym.replace(".NS", ""), "symbol": sym, "rs": int(round(s_rs_now))})

        valid_cnt = len(rs_now_list)
        if valid_cnt == 0:
            processed_groups.append(item)
            continue

        med_1d = round(float(np.median(rets_1d)), 1)
        med_1w = round(float(np.median(rets_1w)), 1)
        med_1m = round(float(np.median(rets_1m)), 1)
        med_3m = round(float(np.median(rets_3m)), 1)
        med_6m = round(float(np.median(rets_6m)), 1)
        med_1y = round(float(np.median(rets_1y)), 1)

        med_rs_now = round(float(np.median(rs_now_list)), 1)
        med_rs_1m = round(float(np.median(rs_1m_list)), 1)
        delta_rs = round(med_rs_now - med_rs_1m, 1)

        pct_50 = (above_50 / valid_cnt) * 100.0
        pct_200 = (above_200 / valid_cnt) * 100.0
        comp_score = int(round(0.60 * med_rs_now + 0.20 * pct_50 + 0.20 * pct_200))

        # RRG coordinates
        curr_x = round(med_3m - bench_ret_3m_now, 2)
        curr_y = round(delta_rs, 2)
        if curr_x >= 0 and curr_y >= 0:
            quad = "LEADING"
        elif curr_x < 0 and curr_y >= 0:
            quad = "IMPROVING"
        elif curr_x >= 0 and curr_y < 0:
            quad = "WEAKENING"
        else:
            quad = "LAGGING"

        # Historical live RRG trail
        tail = []
        for off in trail_offsets:
            t_idx = max(22, idx_now - off)
            t_date = dates_index[t_idx]
            if off == 0:
                tail.append({"date": t_date, "x": curr_x, "y": curr_y})
                continue

            b_ret_t = _safe_ret(bench_vals, t_idx, 63)
            g_rets_t = []
            g_rs_t = []
            g_rs_prev_t = []
            prev_t_idx = max(0, t_idx - 21)
            prev_off = min(n_rows - 23, off + 21)
            if prev_off not in rs_by_offset:
                rs_by_offset[prev_off] = _compute_rs_ratings_at_offset(close_mat, prev_off)

            for sym in constituents:
                vals = close_mat[sym].values
                if np.isnan(vals[t_idx]) or vals[t_idx] <= 0:
                    continue
                g_rets_t.append(_safe_ret(vals, t_idx, 63))
                g_rs_t.append(rs_by_offset[off].get(sym, 50.0))
                g_rs_prev_t.append(rs_by_offset[prev_off].get(sym, 50.0))

            if g_rets_t and g_rs_t:
                tx = round(float(np.median(g_rets_t)) - b_ret_t, 2)
                ty = round(float(np.median(g_rs_t)) - float(np.median(g_rs_prev_t)), 2)
            else:
                tx, ty = curr_x, curr_y
            tail.append({"date": t_date, "x": tx, "y": ty})

        # Real daily cumulative median sparklines for 1W (5d), 1M (21d), 3M (63d)
        sub_df = close_mat[constituents]

        def _make_sparkline(days: int) -> list:
            w = min(days, n_rows - 1)
            if w < 2:
                return [0.0, 0.0]
            window = sub_df.iloc[-(w + 1):]
            base = window.iloc[0].replace(0, np.nan)
            cum_ret = ((window.divide(base, axis=1)) - 1.0) * 100.0
            med_series = cum_ret.median(axis=1).fillna(0.0).values
            # Downsample 3M/1M slightly if needed or keep clean points
            if len(med_series) > 25:
                idxs = np.linspace(0, len(med_series) - 1, 25, dtype=int)
                med_series = med_series[idxs]
            return [round(float(v), 2) for v in med_series]

        spark_1w = _make_sparkline(5)
        spark_1m = _make_sparkline(21)
        spark_3m = _make_sparkline(63)

        # Top 4 constituent stocks sorted by live RS
        stock_rs_pairs.sort(key=lambda s: (-s["rs"], s["name"]))

        # Ranks (category-specific for cards, plus global for 'all')
        if g["type"] == "sector":
            r0, r1d, r1w, r3w, r6w = sec_ranks_0[gid], sec_ranks_1d[gid], sec_ranks_1w[gid], sec_ranks_3w[gid], sec_ranks_6w[gid]
        else:
            r0, r1d, r1w, r3w, r6w = th_ranks_0[gid], th_ranks_1d[gid], th_ranks_1w[gid], th_ranks_3w[gid], th_ranks_6w[gid]

        item.update({
            "x": curr_x,
            "y": curr_y,
            "current_x": curr_x,
            "current_y": curr_y,
            "quadrant": quad,
            "rs_rating": int(round(med_rs_now)),
            "median_rs": med_rs_now,
            "delta_rs": delta_rs,
            "score": comp_score,
            "adv_count": adv_cnt,
            "dec_count": dec_cnt,
            "total_count": valid_cnt,
            "ret_1d": med_1d,
            "ret_1w": med_1w,
            "ret_1m": med_1m,
            "ret_3m": med_3m,
            "ret_6m": med_6m,
            "ret_1y": med_1y,
            "top_stocks": stock_rs_pairs[:4],
            "tail": tail,
            "sparkline_1w": spark_1w,
            "sparkline_1m": spark_1m,
            "sparkline_3m": spark_3m,
            "rank": r0,
            "prev_rank": r3w,
            "rank_change": r3w - r0,
            "rank_1d": r1d,
            "rank_1w": r1w,
            "rank_3w": r3w,
            "rank_6w": r6w,
            "all_rank": all_ranks_0[gid],
            "all_rank_1d": all_ranks_1d[gid],
            "all_rank_1w": all_ranks_1w[gid],
            "all_rank_3w": all_ranks_3w[gid],
            "all_rank_6w": all_ranks_6w[gid],
        })
        processed_groups.append(item)

    sectors_list = sorted([g for g in processed_groups if g["type"] == "sector"], key=lambda s: s["rank"])
    themes_list = sorted([g for g in processed_groups if g["type"] == "theme"], key=lambda t: t["rank"])

    money_movement = {
        "1d": {
            "all": _build_movement_buckets(processed_groups, "all_rank", "all_rank_1d"),
            "sectors": _build_movement_buckets(sectors_list, "rank", "rank_1d"),
            "themes": _build_movement_buckets(themes_list, "rank", "rank_1d"),
        },
        "1w": {
            "all": _build_movement_buckets(processed_groups, "all_rank", "all_rank_1w"),
            "sectors": _build_movement_buckets(sectors_list, "rank", "rank_1w"),
            "themes": _build_movement_buckets(themes_list, "rank", "rank_1w"),
        },
        "3w": {
            "all": _build_movement_buckets(processed_groups, "all_rank", "all_rank_3w"),
            "sectors": _build_movement_buckets(sectors_list, "rank", "rank_3w"),
            "themes": _build_movement_buckets(themes_list, "rank", "rank_3w"),
        },
        "6w": {
            "all": _build_movement_buckets(processed_groups, "all_rank", "all_rank_6w"),
            "sectors": _build_movement_buckets(sectors_list, "rank", "rank_6w"),
            "themes": _build_movement_buckets(themes_list, "rank", "rank_6w"),
        },
    }

    top_day = max(processed_groups, key=lambda g: g["ret_1d"])
    top_week = max(processed_groups, key=lambda g: g["ret_1w"])
    top_month = max(processed_groups, key=lambda g: g["ret_1m"])

    return {
        "benchmark": used_benchmark,
        "timeframe": timeframe,
        "tail_length": tail_length,
        "data_mode": "LIVE",
        "stocks_loaded": len(series_dict),
        "as_of_date": dates_index[-1],
        "total_count": len(processed_groups),
        "sectors_count": len(sectors_list),
        "themes_count": len(themes_list),
        "all_groups": processed_groups,
        "sectors": sectors_list,
        "themes": themes_list,
        "climbers": {
            "all": money_movement["3w"]["all"]["climbers"],
            "sectors": money_movement["3w"]["sectors"]["climbers"],
            "themes": money_movement["3w"]["themes"]["climbers"],
        },
        "fallers": {
            "all": money_movement["3w"]["all"]["fallers"],
            "sectors": money_movement["3w"]["sectors"]["fallers"],
            "themes": money_movement["3w"]["themes"]["fallers"],
        },
        "money_movement": money_movement,
        "performance_leaders": {
            "day": {"name": top_day["name"], "ret": top_day["ret_1d"]},
            "week": {"name": top_week["name"], "ret": top_week["ret_1w"]},
            "month": {"name": top_month["name"], "ret": top_month["ret_1m"]},
        },
        "summary": {
            "leading_count": sum(1 for g in processed_groups if g["quadrant"] == "LEADING"),
            "improving_count": sum(1 for g in processed_groups if g["quadrant"] == "IMPROVING"),
            "weakening_count": sum(1 for g in processed_groups if g["quadrant"] == "WEAKENING"),
            "lagging_count": sum(1 for g in processed_groups if g["quadrant"] == "LAGGING"),
        },
        "scanned_at": datetime.now(IST).strftime("%H:%M:%S IST"),
    }


def _build_studio_payload(benchmark: str = "^NSEI", timeframe: str = "1wk", tail_length: int = 8):
    """
    Offline/fallback studio payload if live market data is unreachable.
    """
    now = datetime.now(timezone.utc)
    dates = [(now - pd.Timedelta(weeks=tail_length - i - 1)).strftime("%Y-%m-%d") for i in range(tail_length)]

    processed_groups = []
    for g in ALL_GROUPS_DATA:
        item = dict(g)
        curr_x = item["x"]
        curr_y = item["y"]
        tail = []
        for i in range(tail_length):
            steps_back = tail_length - 1 - i
            t_x = round(curr_x - (steps_back * 0.22), 2)
            t_y = round(curr_y - (steps_back * 0.18), 2)
            tail.append({"date": dates[i], "x": t_x, "y": t_y})
        item["tail"] = tail
        item["current_x"] = curr_x
        item["current_y"] = curr_y

        r1w = item["ret_1w"]
        r1m = item["ret_1m"]
        r3m = item["ret_3m"]
        item["sparkline_1w"] = [0.0, round(r1w * 0.2, 2), round(r1w * 0.45, 2), round(r1w * 0.7, 2), round(r1w * 0.85, 2), r1w]
        item["sparkline_1m"] = [0.0, round(r1m * 0.1, 2), round(r1m * 0.3, 2), round(r1m * 0.5, 2), round(r1m * 0.75, 2), r1m]
        item["sparkline_3m"] = [0.0, round(r3m * 0.15, 2), round(r3m * 0.35, 2), round(r3m * 0.6, 2), round(r3m * 0.8, 2), r3m]
        item["rank_change"] = item["prev_rank"] - item["rank"]
        processed_groups.append(item)

    sectors_list = sorted([g for g in processed_groups if g["type"] == "sector"], key=lambda s: s["rank"])
    themes_list = sorted([g for g in processed_groups if g["type"] == "theme"], key=lambda t: t["rank"])

    all_climbers = sorted([g for g in processed_groups if g["rank_change"] > 0], key=lambda g: g["rank_change"], reverse=True)
    all_fallers = sorted([g for g in processed_groups if g["rank_change"] < 0], key=lambda g: g["rank_change"])
    sector_climbers = sorted([g for g in sectors_list if g["rank_change"] > 0], key=lambda g: g["rank_change"], reverse=True)
    sector_fallers = sorted([g for g in sectors_list if g["rank_change"] < 0], key=lambda g: g["rank_change"])
    theme_climbers = sorted([g for g in themes_list if g["rank_change"] > 0], key=lambda g: g["rank_change"], reverse=True)
    theme_fallers = sorted([g for g in themes_list if g["rank_change"] < 0], key=lambda g: g["rank_change"])

    top_day = max(processed_groups, key=lambda g: g["ret_1d"])
    top_week = max(processed_groups, key=lambda g: g["ret_1w"])
    top_month = max(processed_groups, key=lambda g: g["ret_1m"])

    return {
        "benchmark": benchmark,
        "timeframe": timeframe,
        "tail_length": tail_length,
        "data_mode": "FALLBACK",
        "stocks_loaded": 0,
        "as_of_date": dates[-1],
        "total_count": len(processed_groups),
        "sectors_count": len(sectors_list),
        "themes_count": len(themes_list),
        "all_groups": processed_groups,
        "sectors": sectors_list,
        "themes": themes_list,
        "climbers": {"all": all_climbers[:8], "sectors": sector_climbers[:8], "themes": theme_climbers[:8]},
        "fallers": {"all": all_fallers[:8], "sectors": sector_fallers[:8], "themes": theme_fallers[:8]},
        "performance_leaders": {
            "day": {"name": top_day["name"], "ret": top_day["ret_1d"]},
            "week": {"name": top_week["name"], "ret": top_week["ret_1w"]},
            "month": {"name": top_month["name"], "ret": top_month["ret_1m"]},
        },
        "summary": {
            "leading_count": sum(1 for g in processed_groups if g["quadrant"] == "LEADING"),
            "improving_count": sum(1 for g in processed_groups if g["quadrant"] == "IMPROVING"),
            "weakening_count": sum(1 for g in processed_groups if g["quadrant"] == "WEAKENING"),
            "lagging_count": sum(1 for g in processed_groups if g["quadrant"] == "LAGGING"),
        },
        "scanned_at": datetime.now(IST).strftime("%H:%M:%S IST"),
    }


def get_sector_rotation_matrix(
    benchmark: str = "^CRSLDX",
    timeframe: str = "1wk",
    tail_length: int = 8,
    df_provider=None,
    force: bool = False,
):
    """
    Main entry point for Sector Rotation & Market Strength analysis.
    Computes live RS ratings, RRG coordinates, breadth, rank shifts, and sparklines
    from Yahoo Finance OHLCV via `df_provider`, with a 15-minute memory + disk cache.
    """
    global _RRG_CACHE
    cache_key = f"{benchmark}_{timeframe}_{tail_length}"
    now = time.time()

    if not force:
        with _RRG_CACHE_LOCK:
            if _RRG_CACHE["data"] and _RRG_CACHE["key"] == cache_key and (now - _RRG_CACHE["timestamp"]) < 900:
                return _RRG_CACHE["data"]

        # Check disk cache (valid for 15 minutes)
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    disk_obj = json.load(f)
                if (
                    disk_obj.get("key") == cache_key
                    and (now - disk_obj.get("timestamp", 0)) < 900
                    and disk_obj.get("data", {}).get("data_mode") == "LIVE"
                ):
                    with _RRG_CACHE_LOCK:
                        _RRG_CACHE["data"] = disk_obj["data"]
                        _RRG_CACHE["key"] = cache_key
                        _RRG_CACHE["timestamp"] = disk_obj["timestamp"]
                    return disk_obj["data"]
            except Exception:
                pass

    payload = None
    if df_provider is not None:
        try:
            payload = _compute_live_studio_payload(
                benchmark=benchmark,
                timeframe=timeframe,
                tail_length=tail_length,
                df_provider=df_provider,
            )
        except Exception:
            payload = None

    if payload is None:
        payload = _build_studio_payload(benchmark=benchmark, timeframe=timeframe, tail_length=tail_length)

    with _RRG_CACHE_LOCK:
        _RRG_CACHE["data"] = payload
        _RRG_CACHE["key"] = cache_key
        _RRG_CACHE["timestamp"] = now

    if payload.get("data_mode") == "LIVE":
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({"key": cache_key, "timestamp": now, "data": payload}, f)
        except Exception:
            pass

    return payload
