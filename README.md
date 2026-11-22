# AI Price Action & TechnoFunda Charting Terminal

A self-hosted, TradingView-style interactive charting and batch-screening terminal built with **Python Flask**, **TradingView Lightweight Charts (v5.1.0)**, and **Yahoo Finance (`yfinance`)**. It automatically detects 14 classical chart patterns, Smart Money Concepts (`HH`, `HL`, `LH`, `LL`, `BOS`, `CHoCH`), dynamic viewport Support & Resistance levels, multi-touch trendlines, and runs batch screeners across the entire NSE equity universe—with **no broker API keys or paid subscriptions required**.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Project Folder Structure](#project-folder-structure)
3. [Complete Setup & Run Steps](#complete-setup--run-steps)
4. [Key Features](#key-features)
5. [User Guide: Charting Workspace](#user-guide-charting-workspace)
6. [User Guide: Built-In Market Scanners](#user-guide-built-in-market-scanners)
7. [Customizing Watchlists & Detection Logic](#customizing-watchlists--detection-logic)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before running this application, verify that your system meets the following requirements:

1. **Operating System:** Windows 10/11, macOS, or Linux.
2. **Python:** **Python 3.10 or higher** (Python 3.11, 3.12, or 3.13 recommended).
   * Check your installed version:
     ```bash
     python --version
     ```
   * *Windows Note:* When installing Python from [python.org](https://www.python.org/downloads/), check **"Add Python to PATH"**.
3. **pip (Python Package Installer):** Included with Python (`pip --version`).
4. **Internet Connection:** Required to load TradingView Lightweight Charts scripts in the browser, fetch historical/intraday OHLCV market data from Yahoo Finance, and download the official NSE equity and index constituent CSV files.
5. **Modern Web Browser:** Google Chrome, Microsoft Edge, Brave, Firefox, or Safari.
6. **Required Python Libraries:**
   * `flask` (Web server and REST API backend)
   * `yfinance` (Historical and intraday stock/index OHLCV data)
   * `pandas` (Dataframe normalization and timeframe resampling)
   * `numpy` (Numerical array operations)
   * `scipy` (Pivot extrema detection and linear regression)
   * `curl_cffi` (Browser-impersonated HTTP session to prevent Yahoo Finance / NSE rate limits)

---

## Project Folder Structure

Ensure your working directory is organized as follows before starting the server:

```text
Price Action/
├── app.py                     # Flask web server, caching, NSE CSV loader, REST API & batch scanners
├── pattern_detector.py        # Pivot detection, dynamic S&R, SMC, 14 chart patterns & scanner engines
├── requirements.txt           # Python package dependencies
├── README.md                  # Complete setup & user guide
├── nse_stocks_cache.json      # Auto-generated local cache of 2,200+ NSE symbols (created on first run)
├── nse_baskets_cache.json     # Auto-generated local cache of NSE index baskets (created on first run)
└── templates/
    └── index.html             # Single-page TradingView Lightweight Charts frontend & scanner modals