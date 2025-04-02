/**
 * API Client for Crypto Trading Bot
 * Handles communication with the backend API
 */
class ApiClient {
    constructor() {
        // Base API URL - can be configured based on environment
        this.baseUrl = 'http://localhost:5000/api';
        this.authUrl = 'http://localhost:5000/auth';
        
        // Authentication token
        this.token = localStorage.getItem('auth_token');
    }
    
    /**
     * Set authentication token
     * @param {string} token - JWT token
     */
    setToken(token) {
        this.token = token;
        localStorage.setItem('auth_token', token);
    }
    
    /**
     * Clear authentication token
     */
    clearToken() {
        this.token = null;
        localStorage.removeItem('auth_token');
    }
    
    /**
     * Get request headers including auth token if available
     * @returns {Object} - Request headers
     */
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        return headers;
    }
    
    /**
     * Make API request
     * @param {string} method - HTTP method
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Request data
     * @param {boolean} auth - Whether authentication is required
     * @returns {Promise<Object>} - API response
     */
    async request(method, endpoint, data = null, auth = true) {
        const url = endpoint.startsWith('/auth') 
            ? `${this.authUrl}${endpoint.substring(5)}` 
            : `${this.baseUrl}${endpoint}`;
        
        const options = {
            method,
            headers: this.getHeaders()
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url, options);
            const responseData = await response.json();
            
            if (!response.ok) {
                throw new Error(responseData.error || 'API request failed');
            }
            
            return responseData;
        } catch (error) {
            console.error(`API Error (${method} ${endpoint}):`, error);
            throw error;
        }
    }
    
    /**
     * Register a new user
     * @param {Object} userData - User registration data
     * @returns {Promise<Object>} - Registration response
     */
    async register(userData) {
        return this.request('POST', '/auth/register', userData, false);
    }
    
    /**
     * Login user
     * @param {Object} credentials - Login credentials
     * @returns {Promise<Object>} - Login response with token
     */
    async login(credentials) {
        const response = await this.request('POST', '/auth/login', credentials, false);
        if (response && response.token) {
            this.setToken(response.token);
        }
        return response;
    }
    
    /**
     * Logout user
     */
    async logout() {
        try {
            await this.request('POST', '/auth/logout');
        } catch (error) {
            // Ignore errors on logout
            console.log('Logout error:', error);
        }
        
        this.clearToken();
    }
    
    /**
     * Get user profile
     * @returns {Promise<Object>} - User profile data
     */
    async getProfile() {
        return this.request('GET', '/auth/profile');
    }
    
    /**
     * Get top cryptocurrency markets
     * @param {number} limit - Number of markets to fetch
     * @returns {Promise<Array>} - Array of market data
     */
    async getMarkets(limit = 100) {
        return this.request('GET', `/markets?limit=${limit}`);
    }
    
    /**
     * Get historical price data for a cryptocurrency
     * @param {string} coinId - Coin ID (e.g., bitcoin, ethereum)
     * @param {string} days - Number of days (1, 7, 30, 90, 365, max)
     * @returns {Promise<Object>} - Historical price data
     */
    async getHistoricalData(coinId, days = '30') {
        return this.request('GET', `/historical/${coinId}?days=${days}`);
    }
    
    /**
     * Get detailed information about a cryptocurrency
     * @param {string} coinId - Coin ID (e.g., bitcoin, ethereum)
     * @returns {Promise<Object>} - Detailed coin information
     */
    async getCoinDetails(coinId) {
        return this.request('GET', `/coin/${coinId}`);
    }
    
    /**
     * Get correlations between a base coin and other coins
     * @param {string} baseCoin - Base coin ID (e.g., bitcoin)
     * @returns {Promise<Array>} - Array of correlated cryptocurrencies
     */
    async getCorrelations(baseCoin) {
        return this.request('GET', `/correlations/${baseCoin}`);
    }
    
    /**
     * Analyze market conditions and detect regime
     * @param {string} symbol - Cryptocurrency symbol
     * @returns {Promise<Object>} - Market analysis results
     */
    async analyzeMarket(symbol) {
        return this.request('GET', `/market/analyze/${symbol}`);
    }
    
    /**
     * Perform technical analysis on a cryptocurrency
     * @param {string} symbol - Cryptocurrency symbol
     * @returns {Promise<Object>} - Technical analysis results
     */
    async analyzeTechnicals(symbol) {
        return this.request('GET', `/market/technicals/${symbol}`);
    }
    
    /**
     * Get optimal strategy based on market regime
     * @param {string} symbol - Cryptocurrency symbol
     * @returns {Promise<Object>} - Recommended strategy info
     */
    async getOptimalStrategy(symbol) {
        return this.request('GET', `/strategy/optimal/${symbol}`);
    }
    
    /**
     * Create and activate a strategy
     * @param {string} name - Strategy name
     * @param {string} type - Strategy type (trend, mean_reversion, market_making, arbitrage)
     * @param {Object} parameters - Strategy parameters
     * @param {Array<string>} symbols - Trading pairs for the strategy
     * @returns {Promise<Object>} - Activation response
     */
    async activateStrategy(name, type, parameters, symbols) {
        return this.request('POST', '/strategy/activate', {
            name,
            type,
            parameters,
            symbols
        });
    }
    
    /**
     * Deactivate a strategy for specific symbols
     * @param {string} type - Strategy type
     * @param {Array<string>} symbols - Trading pairs to deactivate
     * @returns {Promise<Object>} - Deactivation response
     */
    async deactivateStrategy(type, symbols) {
        return this.request('POST', '/strategy/deactivate', {
            type,
            symbols
        });
    }
    
    /**
     * Get strategy performance metrics
     * @param {string} type - Strategy type
     * @param {string} symbol - Cryptocurrency symbol
     * @returns {Promise<Object>} - Performance metrics
     */
    async getStrategyPerformance(type, symbol) {
        return this.request('GET', `/strategy/performance/${type}/${symbol}`);
    }
    
    /**
     * Update risk management settings
     * @param {Object} settings - Risk management settings
     * @returns {Promise<Object>} - Update response
     */
    async updateRiskSettings(settings) {
        return this.request('POST', '/strategy/risk', settings);
    }
    
    /**
     * Get trading signal for a symbol
     * @param {string} symbol - Cryptocurrency symbol
     * @param {number} price - Current price (optional)
     * @returns {Promise<Object>} - Trading signal
     */
    async getTradeSignal(symbol, price = null) {
        let endpoint = `/trade/signal/${symbol}`;
        if (price !== null) {
            endpoint += `?price=${price}`;
        }
        return this.request('GET', endpoint);
    }
    
    /**
     * Execute a trade
     * @param {string} symbol - Cryptocurrency symbol
     * @param {string} action - Trade action (buy, sell)
     * @param {number} quantity - Trade quantity
     * @param {boolean} simulation - Whether to simulate the trade
     * @returns {Promise<Object>} - Trade execution result
     */
    async executeTrade(symbol, action, quantity, simulation = true) {
        return this.request('POST', '/trade/execute', {
            symbol,
            action,
            quantity,
            simulation
        });
    }
    
    /**
     * Run a backtest
     * @param {string} type - Strategy type
     * @param {Object} parameters - Strategy parameters
     * @param {string} symbol - Cryptocurrency symbol
     * @param {string} startDate - Start date (ISO format)
     * @param {string} endDate - End date (ISO format)
     * @param {number} initialCapital - Initial capital
     * @returns {Promise<Object>} - Backtest results
     */
    async runBacktest(type, parameters, symbol, startDate, endDate, initialCapital) {
        return this.request('POST', '/backtest', {
            type,
            parameters,
            symbol,
            start_date: startDate,
            end_date: endDate,
            initial_capital: initialCapital
        });
    }
    
    /**
     * Get portfolio data
     * @returns {Promise<Object>} - Portfolio data
     */
    async getPortfolio() {
        return this.request('GET', '/portfolio');
    }
    
    /**
     * Get trade history
     * @returns {Promise<Array>} - Trade history
     */
    async getTrades() {
        return this.request('GET', '/trades');
    }
    
    /**
     * Configure exchange API keys
     * @param {string} exchange - Exchange name (binance, coinbase, kraken)
     * @param {string} apiKey - API key
     * @param {string} apiSecret - API secret
     * @returns {Promise<Object>} - Configuration response
     */
    async configureExchange(exchange, apiKey, apiSecret) {
        return this.request('POST', '/exchange/config', {
            exchange,
            api_key: apiKey,
            api_secret: apiSecret
        });
    }
    
    /**
     * Get active exchange
     * @returns {Promise<Object>} - Active exchange info
     */
    async getActiveExchange() {
        return this.request('GET', '/exchange/active');
    }
    
    /**
     * Set active exchange
     * @param {string} exchange - Exchange name
     * @returns {Promise<Object>} - Update response
     */
    async setActiveExchange(exchange) {
        return this.request('POST', '/exchange/active', {
            exchange
        });
    }
}

// Create a singleton instance
const apiClient = new ApiClient();

// Export the instance
window.apiClient = apiClient;
