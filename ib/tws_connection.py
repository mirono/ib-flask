from datetime import datetime
from ibapi.contract import Contract
from ibapi.utils import iswrapper

# from .ib_wrapper import IBWrapper
# from .ib_client import IBClient
import threading
import time

# IB API imports
from ibapi.client import EClient
#from ibapi.wrapper import EWrapper
from ib import IBClient, IBWrapper

from ib import IBWrapper


class TWSConnection(EClient):
    """Manages TWS connection and data requests"""

    def __init__(self, logger, log_messages, socketio, price_data):
        self.logger = logger
        self.log_messages = log_messages
        self.wrapper = IBWrapper(logger, log_messages, socketio, price_data)
        # self.client = IBClient(self.wrapper)
        EClient.__init__(self, self.wrapper)
        # EWrapper.__init__(self)
        # EClient.__init__(self, self)
        self.connected = False
        self.request_id = 1
        self.socketio = socketio

    def start_connect(self, host='127.0.0.1', port=4002, client_id=1):
        """Connect to TWS"""
        try:
            self.connect(host, port, client_id)

            # Start the socket in a separate thread
            api_thread = threading.Thread(target=self.run_loop, daemon=True)
            api_thread.start()

            # Wait for connection
            time.sleep(2)

            if self.isConnected():
                self.connected = True
                self.log_messages.append({
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'level': 'INFO',
                    'message': f'Connected to TWS at {host}:{port}'
                })
                return True
            else:
                raise Exception("Failed to connect to TWS")

        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            self.logger.error(error_msg)
            self.log_messages.append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'level': 'ERROR',
                'message': error_msg
            })
            return False

    def run_loop(self):
        """Run the IB API message loop"""
        self.run()

    def start_disconnect(self):
        """Disconnect from TWS"""
        if self.connected:
            self.disconnect()
            self.connected = False
            self.log_messages.append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'level': 'INFO',
                'message': 'Disconnected from TWS'
            })

    @iswrapper
    def connectAck(self):
        self.logger.info(f"{time.time()} Connected")

    # @iswrapper
    # def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
    #     """Handle errors from IB API"""
    #     error_msg = f"Error {errorCode}: {errorString}"
    #     self.logger.error(error_msg)
    #     self.log_messages.append({
    #         'timestamp': datetime.now().strftime('%H:%M:%S'),
    #         'level': 'ERROR',
    #         'message': error_msg
    #     })
    #     self.socketio.emit('log_update', list(self.log_messages))
    #
    #
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

        self.log_messages.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'level': 'INFO',
            'message': f'Requesting market data for {symbol}'
        })

        return True

    def cancel_market_data(self, req_id=1):
        """Cancel market data request"""
        if self.connected:
            self.cancelMktData(req_id)
            self.log_messages.append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'level': 'INFO',
                'message': 'Cancelled market data request'
            })
