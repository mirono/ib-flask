# TWS Real-time Market Data Flask Application

## Requirements

Create a `requirements.txt` file with the following dependencies:

```
flask==2.3.3
flask-socketio==5.3.6
ibapi==9.81.1.post1
plotly==5.17.0
pandas==2.1.3
python-socketio==5.9.0
eventlet==0.33.3
python-engineio==4.7.1
```

## Project Structure

```
tws_flask_app/
├── app.py                 # Main Flask application
├── templates/
│   └── index.html         # Frontend template
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Setup Instructions

### 1. Interactive Brokers Setup

1. **Install TWS or IB Gateway:**
   - Download from [Interactive Brokers](https://www.interactivebrokers.com/en/trading/tws.php)
   - Install and create a paper trading account if you don't have a live account

2. **Configure TWS for API Access:**
   - Open TWS and log in
   - Go to `File` → `Global Configuration` → `API` → `Settings`
   - Check "Enable ActiveX and Socket Clients"
   - Set Socket port to `7497` (TWS) or `4002` (IB Gateway)
   - Add `127.0.0.1` to trusted IPs if needed
   - Uncheck "Read-Only API" if you plan to place orders later

### 2. Python Environment Setup

1. **Create virtual environment:**
   ```bash
   python -m venv tws_env
   source tws_env/bin/activate  # On Windows: tws_env\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### 3. Run the Application

1. **Start TWS or IB Gateway** and make sure it's connected

2. **Run the Flask application:**
   ```bash
   python app.py
   ```

3. **Access the application:**
   - Open your browser and go to `http://localhost:5000`
   - The application will start with a disconnected status

## Usage Guide

### Connection Process

1. **Connect to TWS:**
   - Enter Host: `127.0.0.1` (default)
   - Enter Port: `7497` for TWS or `4002` for IB Gateway
   - Click "Connect" button
   - Status indicator should turn green when connected

2. **Subscribe to Market Data:**
   - Enter a stock symbol (e.g., AAPL, MSFT, GOOGL)
   - Click "Subscribe" button
   - Real-time data will start flowing

### Interface Layout

- **Top Left:** Real-time stock price chart with interactive controls
- **Bottom Left:** Logger output showing connection status and data updates
- **Right Half:** Real-time calculations including:
  - Current price display
  - Number of data points received
  - Average price (last 50 points)
  - Price change from first received price
  - Simple volatility calculation

### Features

- **Real-time Price Updates:** Live streaming of last price data
- **Interactive Chart:** Plotly-based chart with zoom and pan capabilities
- **WebSocket Communication:** Real-time updates without page refresh
- **Connection Management:** Easy connect/disconnect functionality
- **Multi-symbol Support:** Switch between different stocks dynamically
- **Calculation Engine:** Ready-to-extend calculation framework

## Troubleshooting

### Common Issues

1. **Connection Failed:**
   - Ensure TWS/IB Gateway is running
   - Check API settings in TWS are enabled
   - Verify port number (7497 for TWS, 4002 for IB Gateway)
   - Make sure no firewall is blocking the connection

2. **No Data Received:**
   - Check if you have market data subscriptions in your IB account
   - Verify the symbol exists and is tradeable
   - Some symbols may require specific exchanges (try adding exchange info)

3. **Port Already in Use:**
   - Change the Flask port by modifying the last line in app.py:
     ```python
     socketio.run(app, debug=True, host='0.0.0.0', port=5001)
     ```

### Market Data Permissions

- **Paper Trading:** Usually includes delayed data for major exchanges
- **Live Account:** Requires market data subscriptions for real-time data
- **Outside Market Hours:** Limited or no data available

## Extending the Application

### Adding New Calculations

The right panel is designed for custom calculations. Add new metrics in the `updateCalculations()` function in the HTML template:

```javascript
// Example: Add RSI calculation
function calculateRSI(prices, period = 14) {
    // Your RSI calculation logic here
}
```

### Database Integration

To store historical data, add database connections:

```python
# Add to app.py
from sqlalchemy import create_engine
import sqlite3

# Store price data
def store_price_data(symbol, price, timestamp):
    # Your database storage logic
    pass
```

### Additional Market Data

The IB API supports many data types:
- Level 2 data (market depth)
- Options chains
- Futures data
- Forex rates
- Market scanners

### Order Placement

The TWS connection can be extended to place orders:

```python
def place_order(contract, order):
    if tws.connected:
        tws.client.placeOrder(tws.next_order_id, contract, order)
        tws.next_order_id += 1
```

## Security Notes

- This application runs locally and connects to your TWS instance
- No sensitive data is transmitted over the internet
- For production use, add proper authentication and HTTPS
- Consider rate limiting for API calls

## License

This project is for educational purposes. Make sure to comply with Interactive Brokers' API terms of service.