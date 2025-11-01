# 🚀 LEAN Trading Strategies

**QuantConnect LEAN algorithmic trading workspace with offline backtesting capabilities**

A professional, modular Python trading bot implementing the SMA150 trend-following strategy.

## Features

- ✅ **Modular Architecture** - Clean, testable, maintainable code
- ✅ **Offline Backtesting** - No QuantConnect credentials needed
- ✅ **Docker-based** - Consistent execution environment
- ✅ **Production-ready** - Professional risk management
- ✅ **Sample Data Included** - 66+ equities ready to test

## Quick Start

```bash
# Install LEAN CLI
pip install lean

# Pull Docker image
docker pull quantconnect/lean:latest

# Run backtest
lean backtest Rom150Bot --no-update
```

## Repository Structure

```
lean-trading-strategies/
├── Rom150Bot/           # Main trading algorithm
│   ├── main.py         # Algorithm orchestrator
│   ├── config/         # Trading parameters
│   ├── indicators/     # Technical indicators
│   ├── signals/        # Entry/Exit detection
│   ├── risk/           # Risk management
│   ├── universe/       # Stock selection
│   └── portfolio/      # Position tracking
├── data/               # Market data
└── lean.json          # LEAN configuration
```

## Documentation

See full documentation coming soon!

---

**Last Updated:** November 1, 2025
