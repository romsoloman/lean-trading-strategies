"""
Exit signal detection for Rom150Bot.

Monitors stop loss and trailing stop conditions.
"""


class ExitSignalDetector:
    """
    Detects exit signals based on stop loss conditions.
    
    Two types of exits:
    1. Static stop loss: Price below SMA150 threshold
    2. Trailing stop: Price hits trailing stop after profit threshold
    """
    
    def __init__(self, stop_loss_manager, trailing_stop_manager):
        """Initialize the exit signal detector."""
        self.stop_loss_manager = stop_loss_manager
        self.trailing_stop_manager = trailing_stop_manager
    
    def check_exit_conditions(self, symbol, current_price, entry_price, sma_value, atr_value):
        """Evaluate all exit conditions for a position."""
        if sma_value is None:
            return False, None
        
        # Check static stop loss
        stop_price = self.stop_loss_manager.get_stop_price(symbol)
        if stop_price is not None and current_price < stop_price:
            return True, f"Stop Loss (${stop_price:.2f})"
        
        # Update stop loss if SMA has moved up
        self.stop_loss_manager.update_stop_price(symbol, sma_value)
        
        # Check trailing stop
        if atr_value is not None and atr_value > 0:
            trailing_stop = self.trailing_stop_manager.update(
                symbol, current_price, entry_price, atr_value
            )
            if trailing_stop is not None and current_price < trailing_stop:
                return True, f"Trailing Stop (${trailing_stop:.2f})"
        
        return False, None
    
    def cleanup_symbol(self, symbol):
        """Clean up tracking for a symbol after exit."""
        self.stop_loss_manager.remove_stop(symbol)
        self.trailing_stop_manager.remove_trailing_stop(symbol)
