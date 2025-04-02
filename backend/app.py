"""
Crypto Trading Bot - Backend Application
Main Flask application file
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from routes import api, auth
from services.api_service import ApiService
from services.market_analyzer import MarketAnalyzer
from services.strategy_manager import StrategyManager

# Load environment variables
load_dotenv()

def create_app(test_config=None):
    """Create and configure the Flask application"""
    app = Flask(__name__, static_folder="../frontend", static_url_path="/")
    
    # Enable CORS for all routes
    CORS(app)
    
    # Set configuration from environment variables or defaults
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev_key_change_in_production"),
        DATABASE_URL=os.environ.get("DATABASE_URL", "sqlite:///crypto_bot.db"),
        SIMULATION_MODE=(os.environ.get("SIMULATION_MODE", "true").lower() == "true")
    )
    
    if test_config:
        # Override configuration with test config if provided
        app.config.update(test_config)
    
    # Initialize services
    api_service = ApiService()
    market_analyzer = MarketAnalyzer()
    strategy_manager = StrategyManager(api_service, market_analyzer)
    
    # Register blueprints for routes
    app.register_blueprint(api.bp)
    app.register_blueprint(auth.bp)
    
    # Register services with app context
    with app.app_context():
        app.api_service = api_service
        app.market_analyzer = market_analyzer
        app.strategy_manager = strategy_manager
    
    # Basic health check route
    @app.route("/health")
    def health_check():
        """Health check endpoint"""
        return jsonify({"status": "healthy", "simulation_mode": app.config["SIMULATION_MODE"]})
    
    # Serve frontend index page from root
    @app.route("/")
    def index():
        """Serve the frontend index page"""
        return app.send_static_file("index.html")
    
    # Error handler for 404
    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 not found errors"""
        if request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found"}), 404
        return app.send_static_file("index.html")
    
    # Error handler for 500
    @app.errorhandler(500)
    def server_error(e):
        """Handle 500 server errors"""
        return jsonify({"error": "Server error", "message": str(e)}), 500
    
    return app

if __name__ == "__main__":
    # Run app when script is executed directly
    from flask import request  # Import here to avoid circular import
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
