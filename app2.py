import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import threading
import time
from datetime import datetime
import queue
import logging
from io import StringIO
import sys

# TWS API imports
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum


class StreamlitLogHandler(logging.Handler):
    """Custom log handler to capture logs for Streamlit display"""

    def __init__(self):
        super().__init__()
        self.log_queue = queue.Queue()

    def emit(self, record):
        log_entry = self.format(record)
        self.log_queue.put(log_entry)

    def get_logs(self):
        logs = []
        while not self.log_queue.empty():
            try:
                logs.append(self.log_queue.get_nowait())
            except queue.Empty:
                break
        return logs


class TWSApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.price_data = queue.Queue()
        self.logger = logging.getLogger('TWS')
        self.logger.setLevel(logging.INFO)

        # Create custom handler for Streamlit
        self.log_handler = StreamlitLogHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        self.logger.addHandler(self.log_handler)

        self.req_id = 1000
        self.connected = False

    def error(self, reqId, errorCode, errorString, advancedOrderReject=""):
        self.logger.error(f"Error {errorCode}: {errorString}")

    def connectAck(self):
        self.logger.info("Connected to TWS")
        self.connected = True

    def connectionClosed(self):
        self.logger.info("Connection closed")
        self.connected = False

    def tickPrice(self, reqId, tickType, price, attrib):
        tick_name = TickTypeEnum.to_str(tickType)
        timestamp = datetime.now()

        # Only process BID, ASK, and LAST prices
        if tickType in [1, 2, 4]:  # BID=1, ASK=2, LAST=4
            price_update = {
                'timestamp': timestamp,
                'type': tick_name,
                'price': price,
                'reqId': reqId
            }
            self.price_data.put(price_update)
            self.logger.info(f"{tick_name}: ${price:.2f}")

    def tickSize(self, reqId, tickType, size):
        tick_name = TickTypeEnum.to_str(tickType)
        if tickType in [0, 3, 8]:  # BID_SIZE=0, ASK_SIZE=3, VOLUME=8
            self.logger.info(f"{tick_name}: {size}")

    def get_price_updates(self):
        updates = []
        while not self.price_data.empty():
            try:
                updates.append(self.price_data.get_nowait())
            except queue.Empty:
                break
        return updates

    def get_logs(self):
        return self.log_handler.get_logs()


def create_contract(symbol, exchange="SMART", currency="USD"):
    """Create a stock contract"""
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = exchange
    contract.currency = currency
    return contract


def run_tws_app(app):
    """Run the TWS app in a separate thread"""
    app.run()


def main():
    st.set_page_config(
        page_title="Real-time Market Data",
        page_icon="📈",
        layout="wide"
    )

    st.title("📈 Real-time Market Data with TWS API")

    # Initialize session state
    if 'tws_app' not in st.session_state:
        st.session_state.tws_app = TWSApp()
        st.session_state.price_history = pd.DataFrame(columns=['timestamp', 'bid', 'ask', 'last'])
        st.session_state.connected = False
        st.session_state.logs = []

    # Top control panel
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

    with col1:
        symbol = st.text_input("Symbol", value="AAPL", key="symbol_input")

    with col2:
        exchange = st.selectbox("Exchange", ["SMART", "NYSE", "NASDAQ"], key="exchange_select")

    with col3:
        host = st.text_input("TWS Host", value="127.0.0.1", key="host_input")

    with col4:
        port = st.number_input("TWS Port", value=7497, key="port_input")

    # Connection controls
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("Connect", type="primary"):
            try:
                st.session_state.tws_app.connect(host, int(port), 1)
                # Start the TWS app in a separate thread
                threading.Thread(target=run_tws_app, args=(st.session_state.tws_app,), daemon=True).start()
                time.sleep(1)  # Give it time to connect
                st.success("Connecting to TWS...")
            except Exception as e:
                st.error(f"Connection failed: {e}")

    with col2:
        if st.button("Request Data"):
            if st.session_state.tws_app.connected:
                contract = create_contract(symbol, exchange)
                st.session_state.tws_app.reqMktData(st.session_state.tws_app.req_id, contract, "", False, False, [])
                st.success(f"Requesting data for {symbol}")
            else:
                st.error("Not connected to TWS")

    # Main layout: Left column (2/3) and Right column (1/3)
    left_col, right_col = st.columns([2, 1])

    with left_col:
        # Top left: Stock graph
        st.subheader(f"📊 {symbol} Price Chart")
        chart_container = st.container()

        # Bottom left: Logger output
        st.subheader("📝 Log Output")
        log_container = st.container()

        with log_container:
            log_placeholder = st.empty()

    with right_col:
        st.subheader("🔬 Real-time Calculations")
        st.info("This space is reserved for future real-time calculations such as:")
        st.write("• Technical indicators")
        st.write("• Risk metrics")
        st.write("• Portfolio analytics")
        st.write("• Custom calculations")

        # Current price display
        current_price_placeholder = st.empty()
        bid_ask_placeholder = st.empty()

    # Auto-refresh data
    placeholder = st.empty()

    # Main update loop
    while True:
        # Get new price updates
        updates = st.session_state.tws_app.get_price_updates()

        if updates:
            # Process price updates
            for update in updates:
                timestamp = update['timestamp']
                price_type = update['type']
                price = update['price']

                # Update price history
                if len(st.session_state.price_history) == 0:
                    new_row = pd.DataFrame({
                        'timestamp': [timestamp],
                        'bid': [price if price_type == 'BID' else None],
                        'ask': [price if price_type == 'ASK' else None],
                        'last': [price if price_type == 'LAST' else None]
                    })
                    st.session_state.price_history = new_row
                else:
                    # Update the last row or add new row
                    last_time = st.session_state.price_history.iloc[-1]['timestamp']
                    if (timestamp - last_time).total_seconds() < 1:  # Same second, update
                        if price_type == 'BID':
                            st.session_state.price_history.iloc[
                                -1, st.session_state.price_history.columns.get_loc('bid')] = price
                        elif price_type == 'ASK':
                            st.session_state.price_history.iloc[
                                -1, st.session_state.price_history.columns.get_loc('ask')] = price
                        elif price_type == 'LAST':
                            st.session_state.price_history.iloc[
                                -1, st.session_state.price_history.columns.get_loc('last')] = price
                    else:  # New second, add new row
                        new_row = pd.DataFrame({
                            'timestamp': [timestamp],
                            'bid': [price if price_type == 'BID' else st.session_state.price_history.iloc[-1]['bid']],
                            'ask': [price if price_type == 'ASK' else st.session_state.price_history.iloc[-1]['ask']],
                            'last': [price if price_type == 'LAST' else st.session_state.price_history.iloc[-1]['last']]
                        })
                        st.session_state.price_history = pd.concat([st.session_state.price_history, new_row],
                                                                   ignore_index=True)

            # Keep only last 100 data points
            if len(st.session_state.price_history) > 100:
                st.session_state.price_history = st.session_state.price_history.tail(100).reset_index(drop=True)

        # Update chart
        with chart_container:
            if len(st.session_state.price_history) > 0:
                fig = make_subplots(specs=[[{"secondary_y": False}]])

                df = st.session_state.price_history.dropna()
                if len(df) > 0:
                    # Plot lines
                    if 'last' in df.columns and df['last'].notna().any():
                        fig.add_trace(
                            go.Scatter(x=df['timestamp'], y=df['last'],
                                       mode='lines', name='Last Price',
                                       line=dict(color='blue', width=2))
                        )

                    if 'bid' in df.columns and df['bid'].notna().any():
                        fig.add_trace(
                            go.Scatter(x=df['timestamp'], y=df['bid'],
                                       mode='lines', name='Bid',
                                       line=dict(color='green', width=1))
                        )

                    if 'ask' in df.columns and df['ask'].notna().any():
                        fig.add_trace(
                            go.Scatter(x=df['timestamp'], y=df['ask'],
                                       mode='lines', name='Ask',
                                       line=dict(color='red', width=1))
                        )

                fig.update_layout(
                    height=400,
                    xaxis_title="Time",
                    yaxis_title="Price ($)",
                    showlegend=True,
                    margin=dict(l=0, r=0, t=0, b=0)
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No price data available yet. Connect to TWS and request market data.")

        # Update current price display
        with current_price_placeholder:
            if len(st.session_state.price_history) > 0:
                latest = st.session_state.price_history.iloc[-1]
                if pd.notna(latest['last']):
                    st.metric("Last Price", f"${latest['last']:.2f}")

        with bid_ask_placeholder:
            if len(st.session_state.price_history) > 0:
                latest = st.session_state.price_history.iloc[-1]
                col1, col2 = st.columns(2)
                with col1:
                    if pd.notna(latest['bid']):
                        st.metric("Bid", f"${latest['bid']:.2f}")
                with col2:
                    if pd.notna(latest['ask']):
                        st.metric("Ask", f"${latest['ask']:.2f}")

        # Update logs
        new_logs = st.session_state.tws_app.get_logs()
        if new_logs:
            st.session_state.logs.extend(new_logs)
            # Keep only last 50 log entries
            if len(st.session_state.logs) > 50:
                st.session_state.logs = st.session_state.logs[-50:]

        with log_placeholder:
            if st.session_state.logs:
                log_text = "\n".join(st.session_state.logs[-10:])  # Show last 10 logs
                st.text_area("Recent Logs", value=log_text, height=200, key=f"logs_{time.time()}")
            else:
                st.text_area("Recent Logs", value="No logs yet...", height=200, key=f"logs_empty_{time.time()}")

        # Update connection status
        if st.session_state.tws_app.connected != st.session_state.connected:
            st.session_state.connected = st.session_state.tws_app.connected
            if st.session_state.connected:
                st.success("✅ Connected to TWS")
            else:
                st.error("❌ Disconnected from TWS")

        # Sleep briefly before next update
        time.sleep(0.5)


if __name__ == "__main__":
    main()