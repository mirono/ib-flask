from datetime import datetime
from ibapi.contract import Contract
from ibapi.utils import iswrapper

# from .ib_wrapper import IBWrapper
# from .ib_client import IBClient
import threading
import time

# IB API imports
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.ticktype import TickType, TickTypeEnum

current_symbol = "AAPL"


class TWSConnection(EClient, EWrapper):
    """Manages TWS connection and data requests"""

    def __init__(self, logger, log_messages, socketio, price_data):
        self.logger = logger
        self.log_messages = log_messages
        EWrapper.__init__(self)
        EClient.__init__(self, self)
        self.connected = False
        self.request_id = 1
        self.socketio = socketio
        self.price_data = price_data

    def start_connect(self, host='127.0.0.1', port=4002, client_id=1):
        """Connect to TWS"""
        self.logger.info(f"Connecting to TWS at {host}:{port} ...")
        try:
            self.connect(host, port, client_id)
            # Start the socket in a separate thread
            api_thread = threading.Thread(target=self.run_loop, daemon=True)
            api_thread.start()

        except Exception as e:
            self.logger.error(f"Connection error: {str(e)}")
            return False

    def run_loop(self):
        """Run the IB API message loop"""
        self.run()

    def start_disconnect(self):
        """Disconnect from TWS"""
        if self.connected:
            self.disconnect()
            self.connected = False
            self.logger.info("Disconnected from TWS")

    @iswrapper
    def connectAck(self):
        self.connected = True
        self.logger.info("Connected to TWS")
        self.socketio.emit('connection_status', {'status': 'connected'})

    @iswrapper
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        """Handle errors from IB API"""
        self.logger.error(f"Error {errorCode}: {errorString}")

    @iswrapper
    def nextValidId(self, order_id: int):
        self.logger.info(f"Next valid request id: {order_id}")
        self.request_id = order_id

    def next_request_id(self):
        self.request_id += 1
        return self.request_id

    def request_market_data(self, symbol):
        """Request real-time market data for a symbol"""
        if not self.connected:
            return False

        # Create contract
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        # Request market data
        request_id = self.next_request_id()
        self.reqMktData(request_id, contract, "", False, False, [])

        self.logger.info(f"Requested market data for {symbol}")
        return True

    def cancel_market_data(self, req_id=1):
        """Cancel market data request"""
        if self.connected:
            self.cancelMktData(req_id)
            self.logger.info(f"Cancelled market data request for {current_symbol}")

    @iswrapper
    def tickPrice(self, reqId, tickType, price, attrib):
        """Handle real-time price updates"""
        # if TickTypeEnum(tickType) == TickTypeEnum.LAST:
        if tickType == 4: # TickTypeEnum.LAST
            timestamp = datetime.now()
            price_point = {
                'timestamp': timestamp.strftime('%H:%M:%S'),
                'price': price,
                'datetime': timestamp.isoformat()
            }
            self.price_data.append(price_point)

            # Emit real-time data to frontend
            self.socketio.emit('price_update', {
                'symbol': current_symbol,
                'price': price,
                'timestamp': price_point['timestamp'],
                'data': list(self.price_data)[-50:]  # Send last 50 points
            })

            self.logger.info(f"Price update for {current_symbol}: ${price:.2f}")

    @iswrapper
    def tickSize(self, reqId, tickType, size):
        """Handle volume updates"""
        # if TickTypeEnum.  (tickType) == TickTypeEnum.VOLUME:
        if tickType == 8: # TickTypeEnum.VOLUME
            self.logger.info(f"Volume update: {size}")

