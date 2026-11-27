#!/usr/bin/env python3
"""
AI Price Action & TechnoFunda Terminal — Comprehensive Backtesting Engine
========================================================================
Performs rigorous historical backtesting across Indian equities (NSE) and global
assets for automated chart patterns, Cup & Handle cheats, Multi-Year Breakouts,
and Weekly Reversals with no lookahead bias.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timezone, timedelta
IST = timezone(timedelta(hours=5, minutes=30))
import numpy as np
import pandas as pd

# Import detection algorithms directly from pattern_detector
from pattern_detector import (
    find_pivots,
    detect_support_resistance,
    detect_smc_swings,
    detect_trendlines,
    detect_all_patterns,
    analyze_dataframe,
    evaluate_weekly_hl_ll,
    evaluate_multiyear_breakout,
    evaluate_swing_leader_3r,
    evaluate_pro_swing_setup,
)

# Import market data utilities and index baskets from app
try:
    from app import (
        fetch_ohlcv,
        _fetch_batch_ohlcv_map,
        _normalize_df,
        get_index_baskets,
        get_nifty_total_stocks,
    )
except ImportError:
    # Standalone fallback if app.py is not in path
    fetch_ohlcv = None
    _fetch_batch_ohlcv_map = None
    get_index_baskets = None


class Trade:
    """Represents a single backtest trade with lifecycle tracking."""
    def __init__(
        self,
        trade_id: int,
        symbol: str,
        strategy: str,
        pattern_name: str,
        direction: str,
        entry_idx: int,
        entry_time: int,
        entry_date: str,
        entry_price: float,
        stop_loss: float,
        target_1: float,
        target_2: float,
        target_3: float,
        shares: int,
        capital_allocated: float,
        risk_amount: float,
    ):
        self.trade_id = trade_id
        self.symbol = symbol
        self.strategy = strategy
        self.pattern_name = pattern_name
        self.direction = direction  # 'long' or 'short'
        self.entry_idx = entry_idx
        self.entry_time = entry_time
        self.entry_date = entry_date
        self.entry_price = round(entry_price, 2)
        self.initial_sl = round(stop_loss, 2)
        self.current_sl = round(stop_loss, 2)
        self.t1 = round(target_1, 2)
        self.t2 = round(target_2, 2)
        self.t3 = round(target_3, 2)
        self.shares = shares
        self.initial_shares = shares
        self.capital_allocated = round(capital_allocated, 2)
        self.risk_amount = round(risk_amount, 2)

        # Lifecycle tracking
        self.status = "OPEN"
        self.exit_idx = None
        self.exit_time = None
        self.exit_date = None
        self.exit_price = None
        self.exit_reason = None
        self.t1_hit = False
        self.t2_hit = False
        self.pnl = 0.0
        self.return_pct = 0.0
        self.r_multiple = 0.0
        self.holding_bars = 0
        self.realized_cash = 0.0

    def update_sl(self, new_sl: float):
        """Trailing Stop Loss update."""
        if self.direction == "long":
            self.current_sl = max(self.current_sl, round(new_sl, 2))
        else:
            self.current_sl = min(self.current_sl, round(new_sl, 2))

    def close(self, exit_idx: int, exit_time: int, exit_date: str, exit_price: float, reason: str, friction_pct: float = 0.0015):
        """Close trade with friction/brokerage/STT deduction."""
        self.exit_idx = exit_idx
        self.exit_time = exit_time
        self.exit_date = exit_date
        self.exit_reason = reason
        self.status = "CLOSED"
        self.holding_bars = exit_idx - self.entry_idx

        # Deduct friction (slippage + brokerage)
        friction_factor = (1.0 - friction_pct) if self.direction == "long" else (1.0 + friction_pct)
        eff_exit_price = round(exit_price * friction_factor, 2)
        self.exit_price = eff_exit_price

        if self.direction == "long":
            gross_pnl = (eff_exit_price - self.entry_price) * self.shares
        else:
            gross_pnl = (self.entry_price - eff_exit_price) * self.shares

        # Risk clamp: Max loss on a single trade cannot exceed 1.5x planned risk (gap-down/circuit)
        if self.risk_amount > 0:
            max_loss = self.risk_amount * 1.5
            if gross_pnl < -max_loss:
                gross_pnl = -max_loss
            # Max gain clamped to realistic 100% position return or 6x risk to protect against unadjusted stock splits
            max_gain = max(self.capital_allocated * 1.0, self.risk_amount * 6.0)
            if gross_pnl > max_gain:
                gross_pnl = max_gain

        self.pnl = round(gross_pnl + self.realized_cash, 2)
        self.return_pct = round((self.pnl / max(1.0, self.capital_allocated)) * 100.0, 2)
        
        # Risk R-Multiple
        if self.risk_amount > 0:
            self.r_multiple = round(self.pnl / self.risk_amount, 2)
        else:
            self.r_multiple = 0.0

    def partial_exit(self, exit_price: float, shares_to_exit: int, friction_pct: float = 0.0015):
        """Partial target exit (e.g. 50% at T1)."""
        shares_to_exit = min(self.shares, shares_to_exit)
        if shares_to_exit <= 0:
            return
        friction_factor = (1.0 - friction_pct) if self.direction == "long" else (1.0 + friction_pct)
        eff_price = exit_price * friction_factor
        if self.direction == "long":
            part_pnl = (eff_price - self.entry_price) * shares_to_exit
        else:
            part_pnl = (self.entry_price - eff_price) * shares_to_exit
        self.realized_cash += part_pnl
        self.shares -= shares_to_exit

    def to_dict(self):
        return {
            "Trade ID": self.trade_id,
            "Symbol": self.symbol,
            "Strategy": self.strategy,
            "Pattern": self.pattern_name,
            "Direction": self.direction.upper(),
            "Entry Date": self.entry_date,
            "Entry Price": self.entry_price,
            "Exit Date": self.exit_date,
            "Exit Price": self.exit_price,
            "Exit Reason": self.exit_reason,
            "Holding Bars": self.holding_bars,
            "Initial Shares": self.initial_shares,
            "Initial SL": self.initial_sl,
            "Target 1": self.t1,
            "Target 2": self.t2,
            "PnL (Rs)": self.pnl,
            "Return (%)": self.return_pct,
            "R-Multiple": self.r_multiple,
        }


class BacktestEngine:
    """Event-Driven Multi-Strategy Backtesting Engine."""
    def __init__(
        self,
        strategy: str = "cup_handle",
        initial_capital: float = 1000000.0,
        risk_per_trade_pct: float = 1.0,
        max_open_trades: int = 5,
        friction_pct: float = 0.0015,
        max_holding_bars: int = 35,
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_pct = risk_per_trade_pct / 100.0
        self.max_open_trades = max_open_trades
        self.friction_pct = friction_pct
        self.max_holding_bars = max_holding_bars

        self.trades = []
        self.open_trades = []
        self.trade_counter = 0
        self.equity_curve = []

    def _format_date(self, timestamp: int) -> str:
        return datetime.fromtimestamp(int(timestamp), tz=IST).strftime("%Y-%m-%d")

    def run_on_dataframe(self, symbol: str, df: pd.DataFrame, timeframe: str = "1d"):
        """
        Runs step-by-step forward rolling window evaluation.
        Evaluates signals on bar t, enters on bar t+1 open/trigger, manages positions bar-by-bar.
        """
        n = len(df)
        if n < 45:
            return

        times = df["time"].values
        opens = df["open"].values
        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values
        ema21_arr = df["close"].ewm(span=21, adjust=False).mean().values
        ema50_arr = df["close"].ewm(span=50, adjust=False).mean().values

        # Minimum warm-up period for indicators & pivot detection
        warmup = 35 if timeframe == "1d" else 52
        pending_order = None  # Trigger-entry stop-buy order (expires after 3 bars)

        for i in range(warmup, n - 1):
            curr_time = times[i]
            curr_date = self._format_date(curr_time)
            next_open = opens[i + 1]
            next_high = highs[i + 1]
            next_low = lows[i + 1]
            next_close = closes[i + 1]
            next_time = times[i + 1]
            next_date = self._format_date(next_time)

            # 0. Check Pending Trigger-Entry (STOP_BUY) Order on bar i+1
            if pending_order is not None and not any(t.symbol == symbol for t in self.open_trades) and len(self.open_trades) < self.max_open_trades:
                if next_low <= pending_order["stop_loss"] and next_open < pending_order["trigger_price"]:
                    pending_order = None  # Invalidated before triggering
                elif next_high >= pending_order["trigger_price"]:
                    fill_price = max(next_open, pending_order["trigger_price"])
                    stop_loss = pending_order["stop_loss"]
                    if fill_price >= 5.0 and stop_loss > 0 and fill_price > stop_loss:
                        min_sl_dist = fill_price * 0.015
                        max_sl_dist = fill_price * 0.08
                        actual_risk = max(min_sl_dist, min(max_sl_dist, fill_price - stop_loss))
                        stop_loss = round(fill_price - actual_risk, 2)
                        capital_risk = self.initial_capital * self.risk_pct
                        shares = max(1, int(capital_risk / max(0.25, actual_risk)))
                        max_shares = max(1, int((self.initial_capital * 0.15) / fill_price))
                        shares = max(1, min(shares, max_shares))
                        self.trade_counter += 1
                        new_trade = Trade(
                            trade_id=self.trade_counter,
                            symbol=symbol,
                            strategy=pending_order["strategy"],
                            pattern_name=pending_order["pattern_name"],
                            direction="long",
                            entry_idx=i + 1,
                            entry_time=next_time,
                            entry_date=next_date,
                            entry_price=fill_price * (1.0 + self.friction_pct),
                            stop_loss=stop_loss,
                            target_1=pending_order["target_1"],
                            target_2=pending_order["target_2"],
                            target_3=pending_order["target_2"] * 1.15,
                            shares=shares,
                            capital_allocated=shares * fill_price,
                            risk_amount=min(capital_risk, shares * actual_risk),
                        )
                        self.open_trades.append(new_trade)
                    pending_order = None
                else:
                    pending_order["ttl"] -= 1
                    if pending_order["ttl"] <= 0:
                        pending_order = None

            # 1. Manage Active Open Trades for this symbol
            active_for_symbol = [t for t in self.open_trades if t.symbol == symbol]
            for trade in active_for_symbol:
                bars_held = i - trade.entry_idx

                # Check Stop Loss breach
                if next_low <= trade.current_sl:
                    exit_price = min(next_open, trade.current_sl) if next_open < trade.current_sl else trade.current_sl
                    trade.close(i + 1, next_time, next_date, exit_price, "STOP_LOSS", self.friction_pct)
                    self.current_capital += trade.pnl
                    self.open_trades.remove(trade)
                    self.trades.append(trade)
                    continue

                # Check Target 1 hit
                if not trade.t1_hit and next_high >= trade.t1:
                    trade.t1_hit = True
                    # Book 50% partial profit
                    half_shares = trade.shares // 2
                    if half_shares > 0:
                        trade.partial_exit(trade.t1, half_shares, self.friction_pct)
                    # Move Trailing SL to Breakeven
                    trade.update_sl(trade.entry_price)

                # Check Target 2 hit
                if trade.t1_hit and not trade.t2_hit and next_high >= trade.t2:
                    trade.t2_hit = True
                    # Close remaining position at T2
                    trade.close(i + 1, next_time, next_date, trade.t2, "TARGET_2", self.friction_pct)
                    self.current_capital += trade.pnl
                    self.open_trades.remove(trade)
                    self.trades.append(trade)
                    continue

                # Check Max Holding Period reached (Time Stop)
                if bars_held >= self.max_holding_bars:
                    trade.close(i + 1, next_time, next_date, next_close, "TIME_STOP", self.friction_pct)
                    self.current_capital += trade.pnl
                    self.open_trades.remove(trade)
                    self.trades.append(trade)
                    continue

                # Dynamic Trailing SL: closing-basis 21/50 EMA for pro_swing, else intraday TSL
                if self.strategy == "pro_swing":
                    if trade.t1_hit and next_close < float(ema21_arr[i + 1]):
                        trade.close(i + 1, next_time, next_date, next_close, "EMA21_CLOSE_TSL", self.friction_pct)
                        self.current_capital += trade.pnl
                        self.open_trades.remove(trade)
                        self.trades.append(trade)
                        continue
                    if not trade.t1_hit and i > trade.entry_idx and next_close < float(ema50_arr[i + 1]):
                        trade.close(i + 1, next_time, next_date, next_close, "EMA50_CLOSE_TSL", self.friction_pct)
                        self.current_capital += trade.pnl
                        self.open_trades.remove(trade)
                        self.trades.append(trade)
                        continue
                else:
                    ema50_tsl = float(ema50_arr[i]) * 0.995
                    if ema50_tsl > trade.current_sl and next_close > float(ema50_arr[i]):
                        trade.update_sl(ema50_tsl)
                    if trade.t1_hit:
                        ema21_tsl = float(ema21_arr[i]) * 0.995
                        if ema21_tsl > trade.entry_price and next_close > float(ema21_arr[i]):
                            trade.update_sl(ema21_tsl)
                        if i >= 5:
                            recent_swing = np.min(lows[i - 4:i + 1])
                            if recent_swing > trade.entry_price and recent_swing * 0.995 < ema21_tsl:
                                trade.update_sl(recent_swing * 0.995)

            # 2. Check Signal Generation at bar i (strictly historical slice up to i)
            if len(self.open_trades) >= self.max_open_trades:
                continue
            if any(t.symbol == symbol for t in self.open_trades):
                continue  # Avoid duplicate entries in same symbol
            if pending_order is not None:
                continue

            slice_df = df.iloc[:i + 1].reset_index(drop=True)
            signal = self._detect_signal(symbol, slice_df, timeframe)
            if not signal:
                continue

            if signal.get("entry_type") == "STOP_BUY":
                pending_order = {
                    "strategy": signal["strategy"],
                    "pattern_name": signal["pattern_name"],
                    "trigger_price": signal["trigger_price"],
                    "stop_loss": signal["stop_loss"],
                    "target_1": signal["target_1"],
                    "target_2": signal["target_2"],
                    "ttl": 3,
                }
                continue

            # 3. Position Sizing & Order Placement for next bar (i + 1)
            entry_price = next_open if signal["entry_type"] == "MARKET" else signal["trigger_price"]
            stop_loss = signal["stop_loss"]

            # Filter penny stocks (< Rs. 5) or illiquid/corrupt data
            if entry_price < 5.0 or stop_loss <= 0 or entry_price <= stop_loss:
                continue

            # Enforce realistic risk distance: minimum 1.5%, maximum 7.5% per trade
            min_sl_dist = entry_price * 0.015
            max_sl_dist = entry_price * 0.075
            actual_risk = max(min_sl_dist, min(max_sl_dist, entry_price - stop_loss))
            stop_loss = round(entry_price - actual_risk, 2)

            # Robust position sizing: fixed fractional allocation against initial capital
            capital_risk = self.initial_capital * self.risk_pct
            shares = int(capital_risk / max(0.25, actual_risk))
            if shares <= 0:
                shares = 1

            # Cap position to max 15% of portfolio capital per stock
            max_trade_capital = self.initial_capital * 0.15
            max_shares = max(1, int(max_trade_capital / entry_price))
            shares = max(1, min(shares, max_shares))

            total_allocated = shares * entry_price
            effective_risk = min(capital_risk, shares * actual_risk)
            self.trade_counter += 1
            new_trade = Trade(
                trade_id=self.trade_counter,
                symbol=symbol,
                strategy=signal["strategy"],
                pattern_name=signal["pattern_name"],
                direction=signal.get("direction", "long"),
                entry_idx=i + 1,
                entry_time=next_time,
                entry_date=next_date,
                entry_price=entry_price * (1.0 + self.friction_pct),  # entry slippage
                stop_loss=stop_loss,
                target_1=signal["target_1"],
                target_2=signal["target_2"],
                target_3=signal.get("target_3", signal["target_2"] * 1.15),
                shares=shares,
                capital_allocated=total_allocated,
                risk_amount=effective_risk,
            )
            self.open_trades.append(new_trade)

        # 4. Close any trades left open at the end of the stock's historical data
        remaining_symbol_trades = [t for t in self.open_trades if t.symbol == symbol]
        if remaining_symbol_trades and n > 0:
            last_idx = n - 1
            last_time = times[last_idx]
            last_date = self._format_date(last_time)
            last_close = closes[last_idx]
            for trade in remaining_symbol_trades:
                trade.close(last_idx, last_time, last_date, last_close, "END_OF_DATA", self.friction_pct)
                self.current_capital += trade.pnl
                self.open_trades.remove(trade)
                self.trades.append(trade)

    def run_portfolio(self, df_map: dict, timeframe: str = "1d"):
        """
        True multi-asset portfolio simulation across all symbols in df_map.
        Evaluates signals and manages open positions step-by-step along a single unified timeline.
        Enforces max_open_trades globally across the whole portfolio at every step.
        """
        valid_map = {
            sym: df for sym, df in df_map.items()
            if df is not None and not df.empty and len(df) >= 35
        }
        if not valid_map:
            return

        if len(valid_map) == 1:
            sym, df = next(iter(valid_map.items()))
            return self.run_on_dataframe(sym, df, timeframe)

        # Build unified chronological timeline of all timestamps
        all_times = sorted(list(set(t for df in valid_map.values() for t in df["time"].values)))
        if len(all_times) < 40:
            return

        # Precompute lookup: sym -> dict of time -> row index, plus 21/50 EMA arrays for TSL
        sym_lookup = {}
        sym_emas = {}
        for sym, df in valid_map.items():
            sym_lookup[sym] = {
                t: idx for idx, t in enumerate(df["time"].values)
            }
            sym_emas[sym] = (
                df["close"].ewm(span=21, adjust=False).mean().values,
                df["close"].ewm(span=50, adjust=False).mean().values,
            )

        warmup = 35 if timeframe == "1d" else 52
        if len(all_times) <= warmup + 2:
            warmup = len(all_times) // 2

        pending_orders = {}  # sym -> trigger-entry STOP_BUY order (expires after 3 bars)

        # Step through unified calendar day-by-day
        for t_idx in range(warmup, len(all_times) - 1):
            curr_time = all_times[t_idx]
            next_time = all_times[t_idx + 1]
            curr_date = self._format_date(curr_time)
            next_date = self._format_date(next_time)

            # 0. Check Pending Trigger-Entry (STOP_BUY) Orders on bar t+1
            for sym in list(pending_orders.keys()):
                if len(self.open_trades) >= self.max_open_trades or any(t.symbol == sym for t in self.open_trades):
                    pending_orders.pop(sym, None)
                    continue
                order = pending_orders[sym]
                df = valid_map.get(sym)
                lookup = sym_lookup.get(sym, {})
                if df is None or next_time not in lookup:
                    continue
                bar_idx = lookup[next_time]
                next_open = float(df["open"].iloc[bar_idx])
                next_high = float(df["high"].iloc[bar_idx])
                next_low = float(df["low"].iloc[bar_idx])

                if next_low <= order["stop_loss"] and next_open < order["trigger_price"]:
                    pending_orders.pop(sym, None)
                    continue
                if next_high >= order["trigger_price"]:
                    fill_price = max(next_open, order["trigger_price"])
                    stop_loss = order["stop_loss"]
                    if fill_price >= 5.0 and stop_loss > 0 and fill_price > stop_loss and self.current_capital > (self.initial_capital * 0.08):
                        min_sl_dist = fill_price * 0.015
                        max_sl_dist = fill_price * 0.08
                        actual_risk = max(min_sl_dist, min(max_sl_dist, fill_price - stop_loss))
                        stop_loss = round(fill_price - actual_risk, 2)
                        per_slot_capital = min(self.current_capital, (self.initial_capital * (1.0 / max(1, self.max_open_trades))))
                        capital_risk = min(self.initial_capital * self.risk_pct, per_slot_capital * 0.05)
                        shares = max(1, int(capital_risk / max(0.25, actual_risk)))
                        total_allocated = shares * fill_price
                        if total_allocated > self.current_capital:
                            shares = int(self.current_capital / fill_price)
                            total_allocated = shares * fill_price
                        if shares > 0:
                            self.current_capital -= total_allocated
                            self.trade_counter += 1
                            new_trade = Trade(
                                trade_id=self.trade_counter,
                                symbol=sym,
                                strategy=order["strategy"],
                                pattern_name=order["pattern_name"],
                                direction="long",
                                entry_idx=bar_idx,
                                entry_time=next_time,
                                entry_date=next_date,
                                entry_price=fill_price * (1.0 + self.friction_pct),
                                stop_loss=stop_loss,
                                target_1=order["target_1"],
                                target_2=order["target_2"],
                                target_3=order["target_2"] * 1.15,
                                shares=shares,
                                capital_allocated=total_allocated,
                                risk_amount=min(capital_risk, shares * actual_risk),
                            )
                            new_trade.holding_bars = 0
                            self.open_trades.append(new_trade)
                    pending_orders.pop(sym, None)
                else:
                    order["ttl"] -= 1
                    if order["ttl"] <= 0:
                        pending_orders.pop(sym, None)

            # 1. Manage Active Open Trades across entire portfolio
            for trade in list(self.open_trades):
                sym = trade.symbol
                df = valid_map.get(sym)
                lookup = sym_lookup.get(sym, {})
                if next_time not in lookup or df is None:
                    continue

                bar_idx = lookup[next_time]
                next_open = float(df["open"].iloc[bar_idx])
                next_high = float(df["high"].iloc[bar_idx])
                next_low = float(df["low"].iloc[bar_idx])
                next_close = float(df["close"].iloc[bar_idx])

                trade.holding_bars += 1
                bars_held = trade.holding_bars

                # Check Stop Loss
                if next_low <= trade.current_sl:
                    exit_price = min(next_open, trade.current_sl) if next_open < trade.current_sl else trade.current_sl
                    trade.close(bar_idx, next_time, next_date, exit_price, "STOP_LOSS", self.friction_pct)
                    self.current_capital += (trade.capital_allocated + trade.pnl)
                    self.open_trades.remove(trade)
                    self.trades.append(trade)
                    continue

                # Check Target 1
                if not trade.t1_hit and next_high >= trade.t1:
                    trade.t1_hit = True
                    half_shares = trade.shares // 2
                    if half_shares > 0:
                        trade.partial_exit(trade.t1, half_shares, self.friction_pct)
                    trade.update_sl(trade.entry_price)

                # Check Target 2
                if trade.t1_hit and not trade.t2_hit and next_high >= trade.t2:
                    trade.t2_hit = True
                    trade.close(bar_idx, next_time, next_date, trade.t2, "TARGET_2", self.friction_pct)
                    self.current_capital += (trade.capital_allocated + trade.pnl)
                    self.open_trades.remove(trade)
                    self.trades.append(trade)
                    continue

                # Check Max Holding Bars (Time Stop)
                if bars_held >= self.max_holding_bars:
                    trade.close(bar_idx, next_time, next_date, next_close, "TIME_STOP", self.friction_pct)
                    self.current_capital += (trade.capital_allocated + trade.pnl)
                    self.open_trades.remove(trade)
                    self.trades.append(trade)
                    continue

                # Dynamic Trailing SL: closing-basis 21/50 EMA for pro_swing, else intraday TSL
                ema21_arr, ema50_arr = sym_emas[sym]
                if self.strategy == "pro_swing":
                    if trade.t1_hit and next_close < float(ema21_arr[bar_idx]):
                        trade.close(bar_idx, next_time, next_date, next_close, "EMA21_CLOSE_TSL", self.friction_pct)
                        self.current_capital += (trade.capital_allocated + trade.pnl)
                        self.open_trades.remove(trade)
                        self.trades.append(trade)
                        continue
                    if not trade.t1_hit and bars_held > 1 and next_close < float(ema50_arr[bar_idx]):
                        trade.close(bar_idx, next_time, next_date, next_close, "EMA50_CLOSE_TSL", self.friction_pct)
                        self.current_capital += (trade.capital_allocated + trade.pnl)
                        self.open_trades.remove(trade)
                        self.trades.append(trade)
                        continue
                else:
                    ema50_tsl = float(ema50_arr[bar_idx]) * 0.995
                    if ema50_tsl > trade.current_sl and next_close > float(ema50_arr[bar_idx]):
                        trade.update_sl(ema50_tsl)
                    if trade.t1_hit:
                        ema21_tsl = float(ema21_arr[bar_idx]) * 0.995
                        if ema21_tsl > trade.entry_price and next_close > float(ema21_arr[bar_idx]):
                            trade.update_sl(ema21_tsl)
                        if bar_idx >= 5:
                            recent_lows = df["low"].iloc[bar_idx - 4:bar_idx + 1].values
                            recent_swing = float(np.min(recent_lows))
                            if recent_swing > trade.entry_price and recent_swing * 0.995 < ema21_tsl:
                                trade.update_sl(recent_swing * 0.995)

            # 2. Check Signals if portfolio has open slots
            available_slots = self.max_open_trades - len(self.open_trades)
            if available_slots > 0 and self.current_capital > (self.initial_capital * 0.08):
                candidates = []
                held_symbols = {t.symbol for t in self.open_trades} | set(pending_orders.keys())

                for sym, df in valid_map.items():
                    if sym in held_symbols:
                        continue
                    lookup = sym_lookup.get(sym, {})
                    if curr_time not in lookup:
                        continue
                    curr_idx = lookup[curr_time]
                    if curr_idx < 30:
                        continue
                    if next_time not in lookup:
                        continue

                    slice_df = df.iloc[:curr_idx + 1].reset_index(drop=True)
                    sig = self._detect_signal(sym, slice_df, timeframe)
                    if sig:
                        next_bar_idx = lookup[next_time]
                        candidates.append((sym, sig, df, next_bar_idx))

                # Sort candidates by relative volume or breakout quality
                candidates.sort(key=lambda c: -c[1].get("relVol", 1.0) if "relVol" in c[1] else -c[1].get("trigger_price", 0))

                for sym, sig, df, next_bar_idx in candidates[:available_slots]:
                    if sig.get("entry_type") == "STOP_BUY":
                        pending_orders[sym] = {
                            "strategy": sig["strategy"],
                            "pattern_name": sig["pattern_name"],
                            "trigger_price": sig["trigger_price"],
                            "stop_loss": sig["stop_loss"],
                            "target_1": sig["target_1"],
                            "target_2": sig["target_2"],
                            "ttl": 3,
                        }
                        continue
                    next_open = float(df["open"].iloc[next_bar_idx])
                    entry_price = next_open if sig["entry_type"] == "MARKET" else sig["trigger_price"]
                    stop_loss = sig["stop_loss"]

                    if entry_price < 5.0 or stop_loss <= 0 or entry_price <= stop_loss:
                        continue

                    min_sl_dist = entry_price * 0.015
                    max_sl_dist = entry_price * 0.075
                    actual_risk = max(min_sl_dist, min(max_sl_dist, entry_price - stop_loss))
                    stop_loss = round(entry_price - actual_risk, 2)

                    # Dynamic allocation: up to 1/max_open_trades of portfolio equity, capped at current cash
                    per_slot_capital = min(self.current_capital, (self.initial_capital * (1.0 / max(1, self.max_open_trades))))
                    capital_risk = min(self.initial_capital * self.risk_pct, per_slot_capital * 0.05)
                    shares = int(capital_risk / max(0.25, actual_risk))
                    if shares <= 0:
                        shares = 1

                    total_allocated = shares * entry_price
                    if total_allocated > self.current_capital:
                        shares = int(self.current_capital / entry_price)
                        if shares <= 0:
                            continue
                        total_allocated = shares * entry_price

                    effective_risk = min(capital_risk, shares * actual_risk)
                    self.current_capital -= total_allocated
                    self.trade_counter += 1

                    new_trade = Trade(
                        trade_id=self.trade_counter,
                        symbol=sym,
                        strategy=sig["strategy"],
                        pattern_name=sig["pattern_name"],
                        direction=sig.get("direction", "long"),
                        entry_idx=next_bar_idx,
                        entry_time=next_time,
                        entry_date=next_date,
                        entry_price=entry_price * (1.0 + self.friction_pct),
                        stop_loss=stop_loss,
                        target_1=sig["target_1"],
                        target_2=sig["target_2"],
                        target_3=sig.get("target_3", sig["target_2"] * 1.15),
                        shares=shares,
                        capital_allocated=total_allocated,
                        risk_amount=effective_risk,
                    )
                    new_trade.holding_bars = 0
                    self.open_trades.append(new_trade)

        # 3. Close any positions still open at the end of the simulation timeline
        if self.open_trades and all_times:
            last_time = all_times[-1]
            last_date = self._format_date(last_time)
            for trade in list(self.open_trades):
                sym = trade.symbol
                df = valid_map.get(sym)
                lookup = sym_lookup.get(sym, {})
                last_bar_idx = lookup.get(last_time, len(df) - 1) if df is not None else 0
                last_close = float(df["close"].iloc[last_bar_idx]) if df is not None else trade.entry_price
                trade.close(last_bar_idx, last_time, last_date, last_close, "END_OF_DATA", self.friction_pct)
                self.current_capital += (trade.capital_allocated + trade.pnl)
                self.open_trades.remove(trade)
                self.trades.append(trade)

    def _detect_signal(self, symbol: str, slice_df: pd.DataFrame, timeframe: str) -> dict:
        """Evaluates entry triggers on historical bar slice without lookahead."""
        n = len(slice_df)
        last_close = float(slice_df["close"].iloc[-1])
        last_high = float(slice_df["high"].iloc[-1])
        last_low = float(slice_df["low"].iloc[-1])

        # --- A. Cup & Handle Strategy ---
        if self.strategy in ("cup_handle", "all"):
            pivots, high_idx, low_idx = find_pivots(slice_df, order=4)
            patterns = detect_all_patterns(slice_df, high_idx, low_idx)
            recent_cups = [
                p for p in patterns
                if p["name"] == "Cup and Handle" and abs(p["endIdx"] - (n - 1)) <= 3
            ]
            if recent_cups:
                cup = recent_cups[-1]
                meta = cup.get("meta", {})
                stage = meta.get("stage", "BREAKOUT (100%)")
                breakout_price = float(meta.get("breakout", last_close))
                low_cheat = float(meta.get("lowCheat", last_close * 0.95))
                mid_cheat = float(meta.get("midCheat", last_close * 0.98))
                handle_low = float(meta.get("handleLow", last_low * 0.95))

                trigger_price = breakout_price if "100%" in stage else (mid_cheat if "80%" in stage else low_cheat)

                # Ensure price is actually triggering (within 2% below up to 5% above trigger)
                if 0.98 * trigger_price <= last_close <= 1.05 * trigger_price:
                    # Invalidation stop loss: handle low or maximum 6.5% below entry
                    sl = max(handle_low, last_close * 0.935)
                    risk = max(last_close * 0.015, last_close - sl)
                    t1 = round(last_close + 1.5 * risk, 2)
                    t2 = round(last_close + 2.5 * risk, 2)

                    return {
                        "strategy": "Cup & Handle",
                        "pattern_name": f"Cup & Handle ({stage})",
                        "direction": "long",
                        "entry_type": "MARKET",
                        "trigger_price": last_close,
                        "stop_loss": round(sl, 2),
                        "target_1": t1,
                        "target_2": t2,
                    }

        # --- B. Multi-Year Breakout Strategy ---
        if self.strategy in ("myb", "all") and timeframe in ("1wk", "1d"):
            hit = evaluate_multiyear_breakout(symbol, slice_df, years=3)
            if hit and hit["status"] in ("BREAKOUT", "RETEST"):
                myb_lvl = hit["mybLevel"]
                sl = max(hit["stopLoss"], last_close * 0.935)
                risk = max(last_close * 0.015, last_close - sl)
                t1 = round(last_close + 1.5 * risk, 2)
                t2 = round(hit["target"], 2)
                return {
                    "strategy": "Multi-Year Breakout",
                    "pattern_name": f"MYB 3Y ({hit['status']})",
                    "direction": "long",
                    "entry_type": "MARKET",
                    "trigger_price": last_close,
                    "stop_loss": round(sl, 2),
                    "target_1": t1,
                    "target_2": t2,
                }

        # --- C. Weekly Reversal Strategy ---
        if self.strategy in ("weekly_reversal", "all"):
            rev = evaluate_weekly_hl_ll(symbol, slice_df)
            if rev and rev["forecast"] == "BULLISH REVERSAL":
                trigger = rev["triggerLevel"]
                sl = max(rev["stopLoss"], last_close * 0.935)
                if last_close >= trigger * 0.98:
                    risk = max(last_close * 0.015, last_close - sl)
                    return {
                        "strategy": "Weekly HL Reversal",
                        "pattern_name": "Weekly HL/LL Bullish Reversal",
                        "direction": "long",
                        "entry_type": "MARKET",
                        "trigger_price": last_close,
                        "stop_loss": round(sl, 2),
                        "target_1": round(last_close + 1.5 * risk, 2),
                        "target_2": round(last_close + 2.5 * risk, 2),
                    }

        # --- D. Classical 14 Patterns ---
        if self.strategy in ("patterns", "all"):
            pivots, high_idx, low_idx = find_pivots(slice_df, order=4)
            patterns = detect_all_patterns(slice_df, high_idx, low_idx)
            fresh_bullish = [
                p for p in patterns
                if p["direction"] == "bullish"
                and p["name"] in ("Bull Flag", "Ascending Triangle", "Falling Wedge", "Double Bottom", "Inverse Head and Shoulders")
                and abs(p["endIdx"] - (n - 1)) <= 1
            ]
            if fresh_bullish:
                pat = fresh_bullish[-1]
                recent_low = float(np.min(slice_df["low"].iloc[max(0, n - 8):]))
                sl = max(recent_low * 0.985, last_close * 0.935)
                risk = max(last_close * 0.015, last_close - sl)
                return {
                    "strategy": "Chart Patterns",
                    "pattern_name": pat["name"],
                    "direction": "long",
                    "entry_type": "MARKET",
                    "trigger_price": last_close,
                    "stop_loss": round(sl, 2),
                    "target_1": round(last_close + 1.5 * risk, 2),
                    "target_2": round(last_close + 2.5 * risk, 2),
                }

        # --- E. 4-6W Swing Leader (1:3 RR • C&H Cheat / Bull Flag + Stage 2) ---
        if self.strategy in ("swing_leader_3r", "all"):
            sl_hit = evaluate_swing_leader_3r(symbol, slice_df)
            if sl_hit:
                return {
                    "strategy": "4-6W Swing Leader (1:3 RR)",
                    "pattern_name": sl_hit["setupType"],
                    "direction": "long",
                    "entry_type": "MARKET",
                    "trigger_price": last_close,
                    "stop_loss": sl_hit["stopLoss"],
                    "target_1": sl_hit["target1"],
                    "target_2": sl_hit["target2"],
                    "relVol": sl_hit["relVol"],
                }

        # --- F. Pro Swing Setup (A: Trend Pullback + B: Bull Flag + D: Squeeze, Trigger Entry) ---
        if self.strategy in ("pro_swing",):
            recs = evaluate_pro_swing_setup(symbol, slice_df, rs_rating=80.0, sector_aligned=True, min_rs=70.0, min_turnover_cr=0.0)
            if recs:
                best = max(recs, key=lambda r: (r["status"] == "TRIGGERED", r["conviction"]))
                trig = float(best["trigger"])
                stop = float(best["stop"])
                risk = max(trig * 0.015, trig - stop)
                return {
                    "strategy": "Pro Swing (Pullback / Bull Flag)",
                    "pattern_name": best["setup"],
                    "direction": "long",
                    "entry_type": "STOP_BUY",
                    "trigger_price": trig,
                    "stop_loss": stop,
                    "target_1": round(trig + 1.5 * risk, 2),
                    "target_2": round(trig + 3.0 * risk, 2),
                    "relVol": best["relVol"],
                }

        return None

    def calculate_statistics(self) -> dict:
        """Calculates comprehensive institutional performance metrics."""
        if not self.trades:
            return {
                "Total Trades": 0,
                "Win Rate (%)": 0.0,
                "Net Profit (Rs)": 0.0,
                "Return on Capital (%)": 0.0,
            }

        pnls = [t.pnl for t in self.trades]
        returns = [t.return_pct for t in self.trades]
        r_mults = [t.r_multiple for t in self.trades]
        hold_bars = [t.holding_bars for t in self.trades]

        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        breakevens = [p for p in pnls if p == 0]

        total_trades = len(self.trades)
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = round((win_count / total_trades) * 100.0, 2)

        gross_profit = round(sum(wins), 2)
        gross_loss = round(abs(sum(losses)), 2)
        net_profit = round(gross_profit - gross_loss, 2)
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 99.99

        avg_trade_pnl = round(np.mean(pnls), 2)
        avg_win = round(np.mean(wins), 2) if wins else 0.0
        avg_loss = round(abs(np.mean(losses)), 2) if losses else 0.0
        win_loss_ratio = round(avg_win / avg_loss, 2) if avg_loss > 0 else 99.99

        # Expectancy & R-Multiple
        avg_r = round(float(np.mean(r_mults)), 2)
        expectancy = round(((win_rate / 100.0) * avg_win) - (((100.0 - win_rate) / 100.0) * avg_loss), 2)

        # Drawdown computation
        equity_series = [self.initial_capital]
        curr = self.initial_capital
        for p in pnls:
            curr += p
            equity_series.append(curr)

        peak = equity_series[0]
        max_dd_amount = 0.0
        max_dd_pct = 0.0
        for eq in equity_series:
            if eq > peak:
                peak = eq
            if peak > 0:
                dd_amt = max(0.0, peak - eq)
                dd_pct = (dd_amt / peak) * 100.0
                if dd_amt > max_dd_amount:
                    max_dd_amount = dd_amt
                if dd_pct > max_dd_pct:
                    max_dd_pct = dd_pct
        max_dd_pct = round(max(0.0, min(100.0, max_dd_pct)), 2)

        # Consecutive wins / losses
        max_consec_wins = 0
        max_consec_loss = 0
        c_w = 0
        c_l = 0
        for p in pnls:
            if p > 0:
                c_w += 1
                c_l = 0
                max_consec_wins = max(max_consec_wins, c_w)
            elif p < 0:
                c_l += 1
                c_w = 0
                max_consec_loss = max(max_consec_loss, c_l)

        # Sharpe / Sortino Ratios (per-trade approximation)
        std_returns = float(np.std(returns)) if len(returns) > 1 else 1.0
        downside_returns = [r for r in returns if r < 0]
        downside_std = float(np.std(downside_returns)) if len(downside_returns) > 1 else 1.0
        mean_ret = float(np.mean(returns)) if returns else 0.0

        sharpe_raw = (mean_ret / (std_returns + 1e-9)) * np.sqrt(min(252, total_trades))
        sortino_raw = (mean_ret / (downside_std + 1e-9)) * np.sqrt(min(252, total_trades))
        sharpe = round(float(sharpe_raw), 2) if not np.isnan(sharpe_raw) and not np.isinf(sharpe_raw) else 0.0
        sortino = round(float(sortino_raw), 2) if not np.isnan(sortino_raw) and not np.isinf(sortino_raw) else 0.0

        max_dd_amount = round(min(float(max_dd_amount), float(self.initial_capital)), 2)

        return {
            "Total Trades": total_trades,
            "Winning Trades": win_count,
            "Losing Trades": loss_count,
            "Breakeven Trades": len(breakevens),
            "Win Rate (%)": win_rate,
            "Profit Factor": profit_factor,
            "Net Profit (Rs)": net_profit,
            "Return on Capital (%)": round((net_profit / self.initial_capital) * 100.0, 2),
            "Final Equity (Rs)": round(self.initial_capital + net_profit, 2),
            "Gross Profit (Rs)": gross_profit,
            "Gross Loss (Rs)": gross_loss,
            "Average Trade PnL (Rs)": avg_trade_pnl,
            "Average Win (Rs)": avg_win,
            "Average Loss (Rs)": avg_loss,
            "Win/Loss Payoff Ratio": win_loss_ratio,
            "Average R-Multiple": avg_r,
            "Expectancy per Trade (Rs)": expectancy,
            "Max Drawdown (Rs)": round(max_dd_amount, 2),
            "Max Drawdown (%)": round(max_dd_pct, 2),
            "Max Consecutive Wins": max_consec_wins,
            "Max Consecutive Losses": max_consec_loss,
            "Sharpe Ratio": sharpe,
            "Sortino Ratio": sortino,
            "Average Holding Bars": round(float(np.mean(hold_bars)), 1) if hold_bars else 0,
        }

    def print_summary(self):
        """Displays a clean formatted ASCII performance report."""
        stats = self.calculate_statistics()
        print("\n" + "=" * 70)
        print(f"       AI PRICE ACTION TERMINAL — BACKTEST REPORT: [{self.strategy.upper()}]")
        print("=" * 70)
        print(f" Initial Capital:         Rs. {self.initial_capital:,.2f}")
        print(f" Final Portfolio Value:   Rs. {stats.get('Final Equity (Rs)', 0):,.2f}")
        print(f" Total Net Profit:        Rs. {stats.get('Net Profit (Rs)', 0):,.2f} ({stats.get('Return on Capital (%)', 0):+.2f}%)")
        print("-" * 70)
        print(f" Total Closed Trades:     {stats.get('Total Trades', 0)}")
        print(f" Winning Trades:          {stats.get('Winning Trades', 0)} ({stats.get('Win Rate (%)', 0)}%)")
        print(f" Losing Trades:           {stats.get('Losing Trades', 0)}")
        print(f" Profit Factor:           {stats.get('Profit Factor', 0)}")
        print(f" Win/Loss Payoff Ratio:   {stats.get('Win/Loss Payoff Ratio', 0)}x")
        print(f" Average R-Multiple:      {stats.get('Average R-Multiple', 0)}R")
        print(f" Trade Expectancy:        Rs. {stats.get('Expectancy per Trade (Rs)', 0):,.2f}")
        print("-" * 70)
        print(f" Max Drawdown (%):        {stats.get('Max Drawdown (%)', 0)}% (Rs. {stats.get('Max Drawdown (Rs)', 0):,.2f})")
        print(f" Max Consecutive Wins:    {stats.get('Max Consecutive Wins', 0)}")
        print(f" Max Consecutive Losses:  {stats.get('Max Consecutive Losses', 0)}")
        print(f" Sharpe Ratio:            {stats.get('Sharpe Ratio', 0)}")
        print(f" Sortino Ratio:           {stats.get('Sortino Ratio', 0)}")
        print(f" Avg Holding Duration:    {stats.get('Average Holding Bars', 0)} bars")
        print("=" * 70)

        # Breakdown by exit reason
        reasons = {}
        for t in self.trades:
            reasons[t.exit_reason] = reasons.get(t.exit_reason, 0) + 1
        if reasons:
            print(" Exit Reason Distribution:")
            for r, count in sorted(reasons.items(), key=lambda x: -x[1]):
                pct = round((count / len(self.trades)) * 100.0, 1)
                print(f"   • {r:<15}: {count:>3} trades ({pct}%)")
            print("=" * 70 + "\n")

    def export_csv(self, output_dir: str = "./backtest_results") -> str:
        """Exports detailed trade log to CSV."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trades_{self.strategy}_{timestamp}.csv"
        path = os.path.join(output_dir, filename)

        if not self.trades:
            print(f"[Backtester] No trades executed to export.")
            return ""

        trade_dicts = [t.to_dict() for t in self.trades]
        df_trades = pd.DataFrame(trade_dicts)
        df_trades.to_csv(path, index=False)
        print(f"[Backtester] Detailed trade log exported to: {path}")
        return path


def load_universe_symbols(basket: str = "nifty50", custom_symbols: list = None) -> list:
    """Resolves target stock symbols from cache or basket names."""
    if custom_symbols:
        out = []
        for s in custom_symbols:
            s = s.strip().upper()
            if not s:
                continue
            if not s.startswith("^") and "." not in s and "-" not in s:
                s = f"{s}.NS"
            out.append(s)
        return out

    # Check local baskets cache
    base_dir = os.path.dirname(os.path.abspath(__file__))
    baskets_file = os.path.join(base_dir, "nse_baskets_cache.json")
    if os.path.exists(baskets_file):
        try:
            with open(baskets_file, "r", encoding="utf-8") as f:
                baskets = json.load(f)
            b_key = basket.lower().replace(" ", "").replace("-", "")
            if b_key in baskets and baskets[b_key]:
                return baskets[b_key]
            # Match aliases
            aliases = {
                "nifty50": "nifty50",
                "nifty100": "nifty100",
                "niftymidcap": "nifty_midcap",
                "niftysmallcap": "nifty_smallcap",
                "nifty500": "nifty500",
                "nifty750": "nifty750",
                "all": "all"
            }
            if b_key in aliases and aliases[b_key] in baskets:
                return baskets[aliases[b_key]]
        except Exception:
            pass

    # Default fallback liquid basket
    return [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "BHARTIARTL.NS", "SBIN.NS", "ITC.NS", "HINDUNILVR.NS", "LT.NS",
        "BAJFINANCE.NS", "TATAMOTORS.NS", "SUNPHARMA.NS", "M&M.NS", "MARUTI.NS",
        "KOTAKBANK.NS", "AXISBANK.NS", "TITAN.NS", "NTPC.NS", "ONGC.NS"
    ]


def main():
    parser = argparse.ArgumentParser(
        description="AI Price Action Terminal — Historical Backtester",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default="cup_handle",
        choices=["cup_handle", "myb", "weekly_reversal", "patterns", "swing_leader_3r", "pro_swing", "all"],
        help="Strategy module to backtest.",
    )
    parser.add_argument(
        "--basket",
        type=str,
        default="nifty50",
        help="Index basket (nifty50, nifty100, nifty_midcap, nifty500, all) or 'custom'.",
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default="",
        help="Comma-separated custom tickers (e.g., 'RELIANCE,TCS,TATAMOTORS'). Overrides --basket.",
    )
    parser.add_argument(
        "--period",
        type=str,
        default="3y",
        choices=["1y", "2y", "3y", "5y", "max"],
        help="Historical lookback period.",
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        default="1d",
        choices=["1d", "1wk"],
        help="Chart candle timeframe.",
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=1000000.0,
        help="Initial portfolio capital in INR (Rs).",
    )
    parser.add_argument(
        "--risk",
        type=float,
        default=1.0,
        help="Risk per trade as percentage of portfolio equity (e.g. 1.0 for 1%%).",
    )
    parser.add_argument(
        "--max-trades",
        type=int,
        default=5,
        help="Maximum simultaneous open positions.",
    )
    parser.add_argument(
        "--friction",
        type=float,
        default=0.15,
        help="Total friction/slippage + taxes per trade in %% (0.15 = 0.15%%).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./backtest_results",
        help="Directory to save exported trade logs.",
    )

    args = parser.parse_args()

    custom_list = [s.strip() for s in args.symbols.split(",") if s.strip()] if args.symbols else None
    symbols = load_universe_symbols(args.basket, custom_list)

    print("\n" + "=" * 70)
    print(f" STARTING BACKTEST: Strategy={args.strategy.upper()} | Universe={len(symbols)} stocks")
    print(f" Timeframe: {args.timeframe} | Period: {args.period} | Capital: Rs. {args.capital:,.0f} | Risk/Trade: {args.risk}%")
    print("=" * 70)

    engine = BacktestEngine(
        strategy=args.strategy,
        initial_capital=args.capital,
        risk_per_trade_pct=args.risk,
        max_open_trades=args.max_trades,
        friction_pct=args.friction / 100.0,
        max_holding_bars=35 if args.timeframe == "1d" else 15,
    )

    # Fetch batch data
    print(f"[Data] Downloading historical OHLCV data for {len(symbols)} tickers...")
    try:
        import yfinance as yf
        batch_df = yf.download(
            tickers=symbols,
            period=args.period,
            interval=args.timeframe,
            group_by="ticker",
            auto_adjust=True,
            threads=True,
            progress=True,
        )
    except Exception as e:
        print(f"[Error] Batch download failed: {e}")
        return

    processed = 0
    for sym in symbols:
        try:
            if len(symbols) == 1:
                sub_df = batch_df
            elif isinstance(batch_df.columns, pd.MultiIndex) and sym in batch_df.columns.get_level_values(0):
                sub_df = batch_df[sym]
            else:
                continue

            if sub_df is None or sub_df.empty:
                continue

            sub_df = sub_df.reset_index()
            date_col = "Datetime" if "Datetime" in sub_df.columns else "Date"
            if date_col not in sub_df.columns:
                continue

            sub_df["dt"] = pd.to_datetime(sub_df[date_col], utc=True)
            sub_df = sub_df.rename(columns={
                "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"
            })
            required = ["dt", "open", "high", "low", "close", "volume"]
            if not all(c in sub_df.columns for c in required):
                continue

            clean_df = sub_df[required].dropna().sort_values("dt").reset_index(drop=True)
            clean_df["time"] = (clean_df["dt"].astype("int64") // 10**9).astype(int)

            engine.run_on_dataframe(sym, clean_df, args.timeframe)
            processed += 1
        except Exception as e:
            continue

    print(f"\n[Completed] Backtest processed across {processed} symbols.")
    engine.print_summary()
    engine.export_csv(args.output)


if __name__ == "__main__":
    main()
