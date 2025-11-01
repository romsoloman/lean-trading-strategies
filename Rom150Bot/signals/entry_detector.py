"""
Entry signal detection for Rom150Bot.

Identifies cross and retest patterns on the SMA150.
"""


class EntrySignalDetector:
    """
    Detects entry signals based on SMA150 patterns.
    
    Two types of signals:
    1. Cross: Price crosses above SMA150 (within threshold)
    2. Retest: Price pulls back to retest SMA150 (within range)
    """
    
    def __init__(self, cross_threshold, retest_min, retest_max):
        """Initialize the entry signal detector."""
        self.cross_threshold = cross_threshold
        self.retest_min = retest_min
        self.retest_max = retest_max
        self.previous_prices = {}
    
    def detect_signal(self, symbol, current_price, sma_value):
        """Detect if there's a valid entry signal."""
        distance_pct = ((current_price - sma_value) / sma_value)
        
        # Check for cross pattern
        if 0 < distance_pct <= self.cross_threshold:
            if symbol in self.previous_prices:
                prev_price = self.previous_prices[symbol]
                if prev_price < sma_value:
                    return "cross"
            return "cross"
        
        # Check for retest pattern
        if self.retest_min <= distance_pct <= self.retest_max:
            return "retest"
        
        return None
    
    def update_price_history(self, symbol, price):
        """Update price history for cross detection."""
        self.previous_prices[symbol] = price
    
    def clear_history(self, symbol):
        """Clear price history for a symbol."""
        if symbol in self.previous_prices:
            del self.previous_prices[symbol]
