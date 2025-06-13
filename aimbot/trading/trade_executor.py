

class TradeExecutor:
    """Executes trades based on generated signals."""
    
    def __init__(self, broker="paper", api_key=None, api_secret=None, max_capital_per_trade=1000, 
                 use_stop_loss=True, stop_loss_pct=0.05):
        """
        Initialize the trade executor with broker credentials and risk parameters.
        
        Args:
            broker (str): Broker name ('paper', 'alpaca', etc.)
            api_key (str): API key for broker
            api_secret (str): API secret for broker
            max_capital_per_trade (float): Maximum capital to use per trade
            use_stop_loss (bool): Whether to use stop loss orders
            stop_loss_pct (float): Stop loss percentage (e.g., 0.05 for 5%)
        """
        self.broker = broker
        self.api_key = api_key
        self.api_secret = api_secret
        self.max_capital_per_trade = max_capital_per_trade
        self.use_stop_loss = use_stop_loss
        self.stop_loss_pct = stop_loss_pct
        self.client = None
        
        logger.info(f"Initializing Trade Executor with {broker} broker")
        self._connect_to_broker()
    
    def _connect_to_broker(self):
        """Establish connection to the broker API."""
        try:
            if self.broker == "paper":
                logger.info("Using paper trading mode (no actual broker connection)")
                return
            
            elif self.broker == "alpaca":
                try:
                    # Import Alpaca SDK
                    import alpaca_trade_api as tradeapi
                    
                    # Connect to Alpaca API
                    self.client = tradeapi.REST(
                        self.api_key,
                        self.api_secret,
                        base_url='https://paper-api.alpaca.markets' # Use paper trading endpoint by default
                    )
                    
                    # Test connection
                    account = self.client.get_account()
                    logger.info(f"Connected to Alpaca. Account status: {account.status}")
                    
                except ImportError:
                    logger.error("Alpaca SDK not installed. Run: pip install alpaca-trade-api")
                except Exception as e:
                    logger.error(f"Failed to connect to Alpaca: {str(e)}")
            
            # Add support for other brokers here
            else:
                logger.warning(f"Broker {self.broker} not supported")
                
        except Exception as e:
            logger.error(f"Error connecting to broker: {str(e)}")
    
    def execute_trade(self, signal, order_type="market", limit_price=None, quantity=None):
        """
        Execute a trade based on the given signal.
        
        Args:
            signal (dict): The trading signal to execute
            order_type (str): Type of order ('market' or 'limit')
            limit_price (float): Price for limit orders
            quantity (int): Number of shares to trade, if None will be calculated
            
        Returns:
            dict: Information about the executed trade
        """
        ticker = signal['ticker']
        action = signal['action']
        confidence = signal['confidence']
        
        if action not in ["BUY", "SELL"]:
            logger.info(f"No trade to execute for {ticker} (action: {action})")
            return {"status": "no_trade", "order_id": None}
        
        # Log the execution
        logger.info(f"Executing {action} for {ticker} with {confidence} confidence")
        
        try:
            # Paper trading mode
            if self.broker == "paper":
                logger.info(f"Paper trading: {action} {ticker}")
                return {
                    "status": "success", 
                    "order_id": f"paper-{datetime.now().timestamp()}",
                    "ticker": ticker,
                    "action": action,
                    "quantity": quantity or 10,  # Default for paper trading
                    "price": None,  # Would be filled in real execution
                    "timestamp": datetime.now().isoformat()
                }
            
            # Calculate position size if not provided
            if quantity is None:
                quantity = self._calculate_position_size(ticker, confidence)
                
            # Execute with Alpaca
            if self.broker == "alpaca" and self.client:
                side = "buy" if action == "BUY" else "sell"
                
                if order_type == "market":
                    # Market order
                    order = self.client.submit_order(
                        symbol=ticker,
                        qty=quantity,
                        side=side,
                        type='market',
                        time_in_force='gtc'
                    )
                    
                elif order_type == "limit" and limit_price:
                    # Limit order
                    order = self.client.submit_order(
                        symbol=ticker,
                        qty=quantity,
                        side=side,
                        type='limit',
                        time_in_force='gtc',
                        limit_price=limit_price
                    )
                
                # Add stop loss if enabled
                if self.use_stop_loss and action == "BUY":
                    current_price = float(self.client.get_latest_trade(ticker).price)
                    stop_price = current_price * (1 - self.stop_loss_pct)
                    
                    self.client.submit_order(
                        symbol=ticker,
                        qty=quantity,
                        side="sell",
                        type='stop',
                        time_in_force='gtc',
                        stop_price=stop_price
                    )
                    logger.info(f"Set stop loss for {ticker} at {stop_price}")
                
                return {
                    "status": "success",
                    "order_id": order.id,
                    "ticker": ticker,
                    "action": action,
                    "quantity": quantity,
                    "price": limit_price if order_type == "limit" else None,
                    "timestamp": datetime.now().isoformat()
                }
                
            else:
                logger.error(f"Cannot execute trade: broker {self.broker} not connected")
                return {"status": "error", "order_id": None, "message": "Broker not connected"}
                
        except Exception as e:
            logger.error(f"Error executing trade for {ticker}: {str(e)}")
            return {"status": "error", "order_id": None, "message": str(e)}
    
    def _calculate_position_size(self, ticker, confidence):
        """Calculate the position size based on risk parameters and confidence."""
        # Simple position sizing based on confidence and max capital
        base_quantity = int(self.max_capital_per_trade * confidence / 100)  # Assuming $100 per share
        return max(1, base_quantity)  # Ensure at least 1 share
    
    def check_order_status(self, order_id):
        """
        Check the status of an order.
        
        Args:
            order_id (str): ID of the order to check
            
        Returns:
            dict: Order status information
        """
        if self.broker == "paper":
            # For paper trading, simulate a filled order
            return {"status": "filled", "filled_qty": 10, "filled_price": 100.0}
            
        elif self.broker == "alpaca" and self.client:
            try:
                order = self.client.get_order(order_id)
                return {
                    "status": order.status,
                    "filled_qty": order.filled_qty,
                    "filled_price": order.filled_avg_price,
                    "symbol": order.symbol
                }
            except Exception as e:
                logger.error(f"Error checking order status: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        return {"status": "unknown"}