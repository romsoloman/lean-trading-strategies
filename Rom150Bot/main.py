# region imports
from AlgorithmImports import *

# Configuration
from config import TradingParameters as Params

# Components
from indicators import IndicatorManager
from signals import EntrySignalDetector, ExitSignalDetector
from risk import PositionSizer, StopLossManager, TrailingStopManager
from universe import UniverseSelector
from portfolio import PortfolioManager
# endregion


class Rom150BotModular(QCAlgorithm):
    """
    Rom150Bot - Modular Implementation
    
    A systematic trading algorithm based on the 150-period Simple Moving Average strategy.
    
    Architecture:
    - Clean separation of concerns
    - Small, focused modules
    - Easy to test and maintain
    - Professional structure
    """
    
    def initialize(self):
        """Initialize the algorithm with modular components."""
        
        # ==================== Basic Configuration ====================
        self.set_start_date(*Params.START_DATE)
        self.set_end_date(*Params.END_DATE)
        self.set_cash(Params.STARTING_CASH)
        self.set_warmup(Params.WARMUP_DAYS, Resolution.DAILY)
        
        # Validate parameters
        Params.validate()
        
        # ==================== SPY Market Filter ====================
        self.spy = self.add_equity("SPY", Resolution.DAILY).symbol
        self.set_benchmark(self.spy)
        self.spy_sma = self.sma(self.spy, Params.SMA_PERIOD, Resolution.DAILY)
        
        # ==================== Initialize Components ====================
        
        # Indicator management
        self.indicator_manager = IndicatorManager(
            self,
            Params.SMA_PERIOD,
            Params.ATR_PERIOD,
            Params.SMA_SLOPE_LOOKBACK
        )
        
        # Risk management
        self.position_sizer = PositionSizer(Params.RISK_PER_TRADE)
        self.stop_loss_manager = StopLossManager(Params.STOP_LOSS_PERCENTAGE)
        self.trailing_stop_manager = TrailingStopManager(
            Params.TRAILING_PROFIT_THRESHOLD,
            Params.TRAILING_ATR_MULTIPLIER
        )
        
        # Signal detection
        self.entry_detector = EntrySignalDetector(
            Params.CROSS_DISTANCE_THRESHOLD,
            Params.RETEST_MIN_DISTANCE,
            Params.RETEST_MAX_DISTANCE
        )
        self.exit_detector = ExitSignalDetector(
            self.stop_loss_manager,
            self.trailing_stop_manager
        )
        
        # Portfolio management
        self.portfolio_manager = PortfolioManager(
            Params.MAX_POSITIONS,
            Params.MAX_ENTRIES_PER_SYMBOL
        )
        
        # ==================== Universe Selection (Dynamic Stock Scanning) ====================
        self.universe_selector = UniverseSelector(
            self,
            Params.UNIVERSE_SIZE,
            Params.MINIMUM_MARKET_CAP
        )
        self.add_universe(self.universe_selector.coarse_selection_function)
        
        # ==================== Debug Tracking ====================
        self.debug_counter = 0
        self.spy_filter_count = 0
        self.signal_check_count = 0
        
        self.debug("Rom150BotModular initialized successfully")
        self.debug(f"Backtest: {Params.START_DATE} to {Params.END_DATE}")
        self.debug(f"Max positions: {Params.MAX_POSITIONS}, Risk: {Params.RISK_PER_TRADE * 100}%")
    
    def on_securities_changed(self, changes):
        """Handle securities being added or removed from universe."""
        # Add indicators for new securities
        for security in changes.added_securities:
            symbol = security.symbol
            if symbol == self.spy:
                continue
            self.indicator_manager.add_indicators(symbol)
            self.portfolio_manager.initialize_symbol(symbol)
        
        # Remove indicators for removed securities
        for security in changes.removed_securities:
            symbol = security.symbol
            if symbol == self.spy:
                continue
            self.indicator_manager.remove_indicators(symbol)
            self.portfolio_manager.remove_symbol(symbol)
        
        if len(changes.added_securities) > 0:
            self.debug(
                f"Universe: +{len(changes.added_securities)} -{len(changes.removed_securities)}"
            )
    
    def on_data(self, data):
        """Main algorithm logic executed on each data slice."""
        # Skip during warmup
        if self.is_warming_up:
            return
        
        # Check SPY market filter
        if not self._is_spy_bullish():
            self.spy_filter_count += 1
            return
        
        # Debug logging
        self._log_debug_info()
        
        # Process exit signals first
        self._process_exits(data)
        
        # Process entry signals
        self._process_entries(data)
        
        # Update price history for cross detection
        self._update_price_history(data)
    
    def _is_spy_bullish(self):
        """Check if SPY is above its SMA150 (market filter)."""
        if not self.spy_sma.is_ready:
            return False
        
        spy_price = self.securities[self.spy].price
        spy_sma_value = self.spy_sma.current.value
        is_bullish = spy_price > spy_sma_value
        
        # Log first bullish signal
        if is_bullish and not hasattr(self, '_spy_bullish_logged'):
            self.debug(f"SPY bullish @ ${spy_price:.2f} (SMA: ${spy_sma_value:.2f})")
            self._spy_bullish_logged = True
        
        return is_bullish
    
    def _process_exits(self, data):
        """Check and process exit signals for all open positions."""
        invested_symbols = [
            symbol for symbol in self.portfolio.keys()
            if self.portfolio[symbol].invested
        ]
        
        for symbol in invested_symbols:
            if symbol not in data.bars:
                continue
            
            current_price = data.bars[symbol].close
            holding = self.portfolio[symbol]
            
            if holding.quantity <= 0:
                continue
            
            # Get indicator values
            sma_value = self.indicator_manager.get_sma_value(symbol)
            atr_value = self.indicator_manager.get_atr_value(symbol)
            
            # Check exit conditions
            should_exit, reason = self.exit_detector.check_exit_conditions(
                symbol,
                current_price,
                holding.average_price,
                sma_value,
                atr_value
            )
            
            if should_exit:
                self._execute_exit(symbol, holding.quantity, current_price, reason)
    
    def _process_entries(self, data):
        """Check and process entry signals for potential new positions."""
        current_position_count = sum(
            1 for holding in self.portfolio.values() if holding.invested
        )
        
        if not self.portfolio_manager.can_open_new_position(current_position_count):
            return
        
        # Check each symbol in our universe
        for symbol in self.indicator_manager.get_all_symbols():
            if symbol not in data.bars or symbol == self.spy:
                continue
            
            # Check if we can enter this symbol
            if self.portfolio[symbol].invested:
                if not self.portfolio_manager.can_add_to_position(symbol):
                    continue
            else:
                if not self.portfolio_manager.can_open_new_position(current_position_count):
                    continue
            
            # Check if indicators are ready
            if not self.indicator_manager.are_indicators_ready(symbol):
                continue
            
            # Get current data
            current_price = data.bars[symbol].close
            sma_value = self.indicator_manager.get_sma_value(symbol)
            
            if sma_value is None or sma_value <= 0:
                continue
            
            # Check entry conditions
            if self._check_entry_conditions(symbol, current_price, sma_value):
                self._execute_entry(symbol, current_price, sma_value)
                current_position_count += 1
                
                if not self.portfolio_manager.can_open_new_position(current_position_count):
                    break
    
    def _check_entry_conditions(self, symbol, current_price, sma_value):
        """Check if all entry conditions are met."""
        # Condition 1: SMA slope must be positive (optional for synthetic data)
        if Params.REQUIRE_POSITIVE_SMA_SLOPE:
            if not self.indicator_manager.is_sma_slope_positive(symbol):
                return False
        
        # Condition 2: Detect entry signal (cross or retest)
        signal_type = self.entry_detector.detect_signal(symbol, current_price, sma_value)
        
        if signal_type:
            self.debug(f"✅ {symbol}: {signal_type.upper()} signal @ ${current_price:.2f} (SMA: ${sma_value:.2f})")
            return True
        
        return False
    
    def _execute_entry(self, symbol, current_price, sma_value):
        """Execute an entry order with proper risk management."""
        # Calculate stop price
        stop_price = self.stop_loss_manager.calculate_stop_price(sma_value)
        
        # Calculate position size
        portfolio_value = self.portfolio.total_portfolio_value
        shares = self.position_sizer.calculate_shares(
            current_price,
            stop_price,
            portfolio_value
        )
        
        if shares <= 0:
            return
        
        # Check buying power
        order_value = shares * current_price
        if order_value > self.portfolio.cash:
            shares = int(self.portfolio.cash / current_price * 0.95)
        
        if shares <= 0:
            return
        
        # Execute order
        self.market_order(symbol, shares)
        
        # Track entry
        self.portfolio_manager.record_entry(symbol, current_price)
        self.stop_loss_manager.update_stop_price(symbol, sma_value)
        
        # Log
        entry_num = self.portfolio_manager.get_entry_count(symbol)
        risk = (current_price - stop_price) * shares
        self.debug(f"ENTRY: {symbol} {shares} shares @ ${current_price:.2f} (#{entry_num}, Risk: ${risk:.2f})")
    
    def _execute_exit(self, symbol, quantity, current_price, reason):
        """Execute an exit order and clean up tracking."""
        # Execute order
        self.market_order(symbol, -quantity)
        
        # Calculate P&L
        entry_price = self.portfolio[symbol].average_price
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        profit_amount = (current_price - entry_price) * quantity
        
        self.debug(f"EXIT: {symbol} {quantity} shares @ ${current_price:.2f}")
        self.debug(f"  {reason}, P&L: ${profit_amount:.2f} ({profit_pct:.2f}%)")
        
        # Clean up tracking
        self.portfolio_manager.clear_position(symbol)
        self.exit_detector.cleanup_symbol(symbol)
    
    def _update_price_history(self, data):
        """Update price history for cross detection."""
        for symbol in data.bars.keys():
            if symbol in self.indicator_manager.get_all_symbols():
                self.entry_detector.update_price_history(symbol, data.bars[symbol].close)
    
    def _log_debug_info(self):
        """Log periodic debug information."""
        self.debug_counter += 1
        if self.debug_counter % Params.DEBUG_INTERVAL == 0:
            invested = sum(1 for h in self.portfolio.values() if h.invested)
            self.debug(
                f"{self.time.date()}: Positions {invested}/{Params.MAX_POSITIONS}, "
                f"Days blocked: {self.spy_filter_count}"
            )