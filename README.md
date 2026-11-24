# AI Price Action & TechnoFunda Charting Terminal (Version 1.1)

A self-hosted, professional-grade, TradingView-style interactive charting and batch market screening terminal built with **Python Flask**, **TradingView Lightweight Charts (v5.1.0)**, and **Yahoo Finance (`yfinance`)**.

The terminal features automated detection of **14 classical & modern chart patterns**, **Smart Money Concepts (SMC)** market structure (`HH`, `HL`, `LH`, `LL`, `BOS`, `CHoCH`), **dynamic viewport Support & Resistance**, **multi-touch trendlines**, **algorithmic trade planning levels**, and **high-speed batch market screeners** across the entire National Stock Exchange (NSE) of India universe (2,200+ equities & official index baskets)—**100% free, requiring zero broker API keys or paid data subscriptions**.

> For the comprehensive documentation, technical architecture, and user guide, see [Readme Version 1.1.md](file:///d:/Personal/PriceAction/Readme%20Version%201.1.md).

---

## Quickstart

### 1. Prerequisites
* Python 3.10 or higher (Python 3.11, 3.12, or 3.13 recommended)
* Google Chrome, Microsoft Edge, Brave, or Firefox

### 2. Setup Virtual Environment & Dependencies
```bash
# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Terminal
```bash
python app.py
```
*The terminal will start and **automatically launch your default web browser** to `http://127.0.0.1:5000`.*

### 4. Interactive Backtesting (Web UI & CLI)
* **Web UI (Recommended):** Click **🧪 Backtest** in the top bar to configure strategies, index baskets, capital, and risk management directly in your browser with real-time KPI metrics, click-to-chart trade inspection, and Excel export.
* **CLI Engine (Optional):**
  ```bash
  # Backtest Cup & Handle breakouts across Nifty 50 over 3 years
  python backtester.py --strategy cup_handle --basket nifty50 --period 3y
  ```

---

## Table of Contents in [Readme Version 1.1.md](file:///d:/Personal/PriceAction/Readme%20Version%201.1.md)
1. Key Features & Capabilities
2. System & Software Prerequisites
3. Project Folder Structure
4. Step-by-Step Installation & Quickstart
5. Charting Workspace & User Interface
   - Top Navigation Bar
   - Preset View Modes
   - Left Manual Drawing Rail
   - Right Pattern Navigator
   - Interactive Legend & Trade Plan Overlay
   - Keyboard Shortcuts & Navigation
6. Built-In Market Scanners
   - Multi-Scale Cup & Handle Screener (60% Low Cheat, 80% Mid Cheat, 100% Breakout)
   - Multi-Year Breakout (MYB) Scanner (2Y, 3Y, 5Y, ATH)
   - Weekly HL / LL & Reversal Forecast Scanner
   - Dockable Scanner Panel & Excel Export
7. Supported Chart Patterns (14 Formations)
8. Historical Backtesting Engine (`backtester.py`)
9. Multi-Tier Market Data Pipeline & Architecture
10. Configuration & Customization
11. Troubleshooting & Frequently Asked Questions
