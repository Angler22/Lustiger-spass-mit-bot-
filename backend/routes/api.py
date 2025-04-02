"""
API routes for Crypto Trading Bot
"""
import os
from flask import Blueprint, request, jsonify, current_app, g

bp = Blueprint("api", __name__, url_prefix="/api")

@bp.route("/markets", methods=["GET"])
def get_markets():
    """Get top cryptocurrency markets"""
    try:
        limit = int(request.args.get("limit", 100))
        markets = current_app.api_service.get_top_markets(limit)
        return jsonify(markets)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/historical/<string:coin_id>", methods=["GET"])
def get_historical_data(coin_id):
    """Get historical price data for a cryptocurrency"""
    try:
        days = request.args.get("days", "30")
        data = current_app.api_service.get_historical_data(coin_id, days)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/coin/<string:coin_id>", methods=["GET"])
def get_coin_details(coin_id):
    """Get detailed information about a cryptocurrency"""
    try:
        data = current_app.api_service.get_coin_details(coin_id)
        if data:
            return jsonify(data)
        else:
            return jsonify({"error": "Coin not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/correlations/<string:base_coin>", methods=["GET"])
def get_correlations(base_coin):
    """Get correlations between a base coin and other coins"""
    try:
        correlations = current_app.api_service.get_correlations(base_coin)
        return jsonify(correlations)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/market/analyze/<string:symbol>", methods=["GET"])
def analyze_market(symbol):
    """Analyze market conditions and detect regime"""
    try:
        analysis = current_app.market_analyzer.analyze_market(symbol)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/market/technicals/<string:symbol>", methods=["GET"])
def analyze_technicals(symbol):
    """Perform technical analysis on a cryptocurrency"""
    try:
        analysis = current_app.market_analyzer.analyze_technicals(symbol)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/strategy/optimal/<string:symbol>", methods=["GET"])
async def get_optimal_strategy(symbol):
    """Get optimal strategy based on market regime"""
    try:
        strategy = await current_app.strategy_manager.get_optimal_strategy(symbol)
        return jsonify(strategy)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/strategy/activate", methods=["POST"])
def activate_strategy():
    """Create and activate a strategy"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ["name", "type", "parameters", "symbols"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        success = current_app.strategy_manager.activate_strategy(
            data["name"],
            data["type"],
            data["parameters"],
            data["symbols"]
        )
        
        if success:
            return jsonify({"success": True, "message": "Strategy activated"})
        else:
            return jsonify({"success": False, "message": "Failed to activate strategy"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/strategy/deactivate", methods=["POST"])
def deactivate_strategy():
    """Deactivate a strategy for specific symbols"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ["type", "symbols"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        success = current_app.strategy_manager.deactivate_strategy(
            data["type"],
            data["symbols"]
        )
        
        if success:
            return jsonify({"success": True, "message": "Strategy deactivated"})
        else:
            return jsonify({"success": False, "message": "Failed to deactivate strategy"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/strategy/performance/<string:type_str>/<string:symbol>", methods=["GET"])
def get_strategy_performance(type_str, symbol):
    """Get strategy performance metrics"""
    try:
        performance = current_app.strategy_manager.get_performance(type_str, symbol)
        if performance:
            return jsonify(performance)
        else:
            return jsonify({"error": "Performance data not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/strategy/risk", methods=["POST"])
def update_risk_settings():
    """Update risk management settings"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        current_app.strategy_manager.update_risk_settings(data)
        return jsonify({"success": True, "message": "Risk settings updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/trade/signal/<string:symbol>", methods=["GET"])
async def get_trade_signal(symbol):
    """Get trading signal for a symbol"""
    try:
        price = float(request.args.get("price", 0))
        if price <= 0:
            # Get current price if not provided
            coin_details = current_app.api_service.get_coin_details(symbol)
            if coin_details and "market_data" in coin_details and "current_price" in coin_details["market_data"]:
                price = coin_details["market_data"]["current_price"]["usd"]
            else:
                return jsonify({"error": "Invalid price and could not get current price"}), 400
        
        signal = await current_app.strategy_manager.get_signal(symbol, price)
        if signal:
            return jsonify(signal)
        else:
            return jsonify({"message": "No signal at this time"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/trade/execute", methods=["POST"])
async def execute_trade():
    """Execute a trade"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ["symbol", "action", "quantity"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Check if we're in simulation mode
        simulation = current_app.config.get("SIMULATION_MODE", True)
        if "simulation" in data:
            simulation = data["simulation"]
        
        # Execute the trade
        result = await current_app.strategy_manager.execute_signal(data, simulation)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/backtest", methods=["POST"])
async def run_backtest():
    """Run a backtest"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ["type", "parameters", "symbol", "start_date", "end_date", "initial_capital"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        result = await current_app.strategy_manager.backtest(
            data["type"],
            data["parameters"],
            data["symbol"],
            data["start_date"],
            data["end_date"],
            data["initial_capital"]
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/portfolio", methods=["GET"])
def get_portfolio():
    """Get portfolio data"""
    try:
        # In a real system, this would fetch data from a database
        # For now, we'll just return dummy data
        import random
        from datetime import datetime, timedelta
        
        # Generate portfolio history
        history = []
        value = 10000
        now = datetime.now()
        
        for i in range(100):
            time = (now - timedelta(hours=100-i)).isoformat()
            value = value * (1 + (random.random() * 0.02 - 0.01))  # ±1% change
            history.append({"time": time, "value": value})
        
        # Generate asset allocation
        assets = [
            {"symbol": "BTC", "name": "Bitcoin", "percentage": 40, "value": value * 0.4},
            {"symbol": "ETH", "name": "Ethereum", "percentage": 30, "value": value * 0.3},
            {"symbol": "USDT", "name": "Tether", "percentage": 20, "value": value * 0.2},
            {"symbol": "SOL", "name": "Solana", "percentage": 10, "value": value * 0.1}
        ]
        
        return jsonify({
            "portfolio_value": value,
            "portfolio_history": history,
            "assets": assets
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/trades", methods=["GET"])
def get_trades():
    """Get trade history"""
    try:
        # Get trades from strategy manager
        trades = current_app.strategy_manager.trades
        return jsonify(trades)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/exchange/config", methods=["POST"])
def configure_exchange():
    """Configure exchange API keys"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ["exchange", "api_key", "api_secret"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        success = current_app.api_service.set_exchange_keys(
            data["exchange"],
            data["api_key"],
            data["api_secret"]
        )
        
        if success:
            # Set as active exchange
            current_app.api_service.set_active_exchange(data["exchange"])
            return jsonify({"success": True, "message": "Exchange configured"})
        else:
            return jsonify({"success": False, "message": "Failed to configure exchange"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/exchange/active", methods=["GET"])
def get_active_exchange():
    """Get active exchange"""
    try:
        exchange = current_app.api_service.active_exchange
        return jsonify({"active_exchange": exchange})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/exchange/active", methods=["POST"])
def set_active_exchange():
    """Set active exchange"""
    try:
        data = request.json
        if not data or "exchange" not in data:
            return jsonify({"error": "Exchange not specified"}), 400
        
        success = current_app.api_service.set_active_exchange(data["exchange"])
        if success:
            return jsonify({"success": True, "message": f"Active exchange set to {data['exchange']}"})
        else:
            return jsonify({"success": False, "message": "Failed to set active exchange"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
