"""
Flask TWS Real-time Market Data Application

This application connects to Interactive Brokers TWS API to fetch real-time market data
and displays it with a stock chart, logger output, and space for future calculations.

Requirements:
pip install flask flask-socketio ibapi plotly pandas

Before running:
1. Make sure TWS or IB Gateway is running
2. Enable API connections in TWS (File -> Global Configuration -> API -> Settings)
3. Set the Socket port (default 7497 for TWS, 4002 for IB Gateway)
4. Enable "Enable ActiveX and Socket Clients"
"""
import logging

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import time
from log import logger_config, Logger
from datetime import datetime
import json
from collections import deque
import pandas as pd

# IB API imports
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.ticktype import TickType

from ib import IBClient, IBWrapper
from ib import TWSConnection



app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")
logger = Logger(__name__, socketio)

# Global variables
price_data = deque(maxlen=500)  # Store last 500 price points
log_messages = deque(maxlen=100)  # Store last 100 log messages
current_symbol = "AAPL"

# Global TWS connection
tws = TWSConnection(logger, log_messages, socketio, price_data)

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', symbol=current_symbol)

@app.route('/connect', methods=['POST'])
def connect_tws():
    """Connect to TWS API"""
    data = request.json
    host = data.get('host', '127.0.0.1')
    port = data.get('port', 4002)

    success = tws.start_connect(host, port)
    return jsonify({'success': success, 'connected': tws.connected})

@app.route('/disconnect', methods=['POST'])
def disconnect_tws():
    """Disconnect from TWS API"""
    tws.start_disconnect()
    return jsonify({'success': True, 'connected': tws.connected})

@app.route('/subscribe', methods=['POST'])
def subscribe_symbol():
    """Subscribe to market data for a symbol"""
    global current_symbol
    data = request.json
    symbol = data.get('symbol', 'AAPL').upper()

    if tws.connected:
        # Cancel previous subscription
        tws.cancel_market_data()
        time.sleep(0.5)

        # Clear previous data
        price_data.clear()

        # Subscribe to new symbol
        current_symbol = symbol
        success = tws.request_market_data(symbol)
        return jsonify({'success': success, 'symbol': current_symbol})
    else:
        return jsonify({'success': False, 'error': 'Not connected to TWS'})

@app.route('/status')
def status():
    """Get connection status"""
    return jsonify({
        'connected': tws.connected,
        'symbol': current_symbol,
        'data_points': len(price_data)
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('log_update', list(log_messages))
    if price_data:
        emit('price_update', {
            'symbol': current_symbol,
            'price': price_data[-1]['price'] if price_data else 0,
            'timestamp': price_data[-1]['timestamp'] if price_data else '',
            'data': list(price_data)
        })

if __name__ == '__main__':
    # Add some initial log messages
    logger.info("Flask TWS application started")

    # Start the Flask-SocketIO server with proper configuration
    try:
        # Try with eventlet first
        socketio.run(app, debug=True, host='127.0.0.1', port=8000, allow_unsafe_werkzeug=True)
    except Exception as e:
        print(f"Failed to start with eventlet: {e}")
        print("Trying with threading...")
        # Fallback to threading
        socketio.run(app, debug=True, host='127.0.0.1', port=8000, allow_unsafe_werkzeug=True, async_mode='threading')