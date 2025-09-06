from datetime import datetime
from flask_socketio import SocketIO, emit
# IB API imports
from ibapi.wrapper import EWrapper
from ibapi.ticktype import TickType, TickTypeEnum

current_symbol = "AAPL"

class IBWrapper(EWrapper):
    """IB API Wrapper to handle incoming data"""

    def __init__(self, logger, log_messages, socketio, price_data):
        EWrapper.__init__(self)
        self.price_data = {}
        self.logger = logger
        self.log_messages = log_messages
        self.socketio = socketio
        self.price_data = price_data


    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        """Handle errors from IB API"""
        error_msg = f"Error {errorCode}: {errorString}"
        self.logger.error(error_msg)
        self.log_messages.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'level': 'ERROR',
            'message': error_msg
        })
        self.socketio.emit('log_update', list(self.log_messages))

    def tickPrice(self, reqId, tickType, price, attrib):
        """Handle real-time price updates"""
        if TickTypeEnum(tickType) == TickTypeEnum.LAST:
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

            log_msg = f"Price update for {current_symbol}: ${price:.2f}"
            self.log_messages.append({
                'timestamp': timestamp.strftime('%H:%M:%S'),
                'level': 'INFO',
                'message': log_msg
            })
            self.socketio.emit('log_update', list(self.log_messages))

    def tickSize(self, reqId, tickType, size):
        """Handle volume updates"""
        if TickTypeEnum(tickType) == TickTypeEnum.VOLUME:
            log_msg = f"Volume update: {size}"
            self.log_messages.append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'level': 'INFO',
                'message': log_msg
            })
            self.socketio.emit('log_update', list(self.log_messages))

