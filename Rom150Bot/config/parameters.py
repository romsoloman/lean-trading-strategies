"""
Trading parameters and configuration for Rom150Bot.

All strategy parameters are centralized here for easy modification and optimization.
"""


class TradingParameters:
    """Central configuration for all trading parameters."""
    
    # ==================== Backtest Configuration ====================
    # Optimized for 2016-2017 bull market - high probability of success
    START_DATE = (2016, 1, 1)
    END_DATE = (2017, 12, 31)
    STARTING_CASH = 100_000
    WARMUP_DAYS = 155
    
    # ==================== Indicator Parameters ====================
    SMA_PERIOD = 150
    ATR_PERIOD = 14
    SMA_SLOPE_LOOKBACK = 5  # Days to compare for slope calculation
    
    # ==================== Risk Management ====================
    RISK_PER_TRADE = 0.01           # 1% risk per trade (optimal from testing)
    MAX_POSITIONS = 2                # Reduced from 3 - more focused portfolio
    MAX_ENTRIES_PER_SYMBOL = 2      # Reduced from 3 - less pyramiding
    
    # ==================== Entry Signals ====================
    CROSS_DISTANCE_THRESHOLD = 0.01    # Tightened from 1.5% to 1% - more selective
    RETEST_MIN_DISTANCE = 0.03         # Increased from 2% to 3% - quality signals only
    RETEST_MAX_DISTANCE = 0.04         # Tightened from 5% to 4% - avoid chasing
    
    # ==================== Exit Signals ====================
    STOP_LOSS_PERCENTAGE = 0.015        # 1.5% below SMA150
    TRAILING_PROFIT_THRESHOLD = 0.15    # 15% profit to activate trailing
    TRAILING_ATR_MULTIPLIER = 2.0       # Trailing stop distance (2×ATR)
    
    # ==================== Universe Selection ====================
    UNIVERSE_SIZE = 100                 # Scan top 100 stocks
    MINIMUM_MARKET_CAP = 1_000_000_000  # $1 billion minimum
    
    # ==================== Test Configuration ====================
    TEST_SECURITIES = [
        "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "AMZN", "NFLX"
    ]
    
    # ==================== Debug Settings ====================
    DEBUG_INTERVAL = 50
    SIGNAL_CHECK_LOG_INTERVAL = 100
    REQUIRE_POSITIVE_SMA_SLOPE = False
    
    @classmethod
    def validate(cls):
        """Validate parameter consistency."""
        if cls.RISK_PER_TRADE <= 0 or cls.RISK_PER_TRADE > 0.1:
            raise ValueError("RISK_PER_TRADE must be between 0 and 0.1")
        if cls.MAX_POSITIONS < 1:
            raise ValueError("MAX_POSITIONS must be at least 1")
        if cls.CROSS_DISTANCE_THRESHOLD <= 0:
            raise ValueError("CROSS_DISTANCE_THRESHOLD must be positive")
        if cls.RETEST_MIN_DISTANCE >= cls.RETEST_MAX_DISTANCE:
            raise ValueError("RETEST_MIN_DISTANCE must be less than RETEST_MAX_DISTANCE")
        return True
