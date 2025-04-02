/**
 * Main Application Script for Crypto Trading Bot
 * Initializes components and handles user interactions
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize application
    initApp();
});

/**
 * Initialize application
 */
async function initApp() {
    try {
        // Check if dependencies are loaded
        if (!window.apiClient || !window.authManager || !window.dashboard) {
            console.error('Required dependencies not loaded');
            setTimeout(initApp, 500); // Retry after 500ms
            return;
        }
        
        // Initialize dashboard
        if (typeof window.dashboard.init === 'function') {
            await window.dashboard.init();
        }
        
        // Setup tab navigation
        setupTabs();
        
        // Setup timeframe controls
        setupTimeframeControls();
        
        // Setup correlation coin selection
        setupCoinSelection();
        
        // Setup market search
        setupMarketSearch();
        
        // Setup modals
        setupModals();
        
        // Setup trading mode toggle
        setupTradingModeToggle();
        
        // Setup backtest form
        setupBacktestForm();
        
        // Setup settings forms
        setupSettingsForms();
        
        // Check API key configuration
        checkApiKeys();
        
        console.log('Crypto Trading Bot initialized');
    } catch (error) {
        console.error('Failed to initialize application:', error);
    }
}

/**
 * Setup tab navigation
 */
function setupTabs() {
    const sidebarItems = document.querySelectorAll('.sidebar li');
    const tabContents = document.querySelectorAll('.tab-content');
    
    sidebarItems.forEach(item => {
        item.addEventListener('click', () => {
            // Get tab name
            const tab = item.getAttribute('data-tab');
            
            // Update active tab in sidebar
            sidebarItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            
            // Show selected tab content
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === tab) {
                    content.classList.add('active');
                    
                    // Refresh content when switching to tab
                    refreshTabContent(tab);
                }
            });
        });
    });
}

/**
 * Refresh content when switching tabs
 * @param {string} tab - Tab name
 */
async function refreshTabContent(tab) {
    try {
        switch (tab) {
            case 'dashboard':
                // Update portfolio data
                const portfolioData = await apiClient.getPortfolio();
                window.dashboard.updatePortfolioData(portfolioData);
                break;
                
            case 'markets':
                // Update market data
                const marketData = await apiClient.getMarkets();
                window.dashboard.updateMarketTable(marketData);
                break;
                
            case 'correlations':
                // Update correlations for active coin
                const activeCoin = document.querySelector('.coins-filter .coin-btn.active');
                if (activeCoin) {
                    const coin = activeCoin.getAttribute('data-coin');
                    const correlationData = await apiClient.getCorrelations(coin);
                    window.dashboard.updateCorrelationTable(correlationData);
                }
                break;
                
            case 'strategies':
                // Get active strategies (could extend API for this)
                break;
                
            case 'backtesting':
                // Set default dates
                setDefaultBacktestDates();
                break;
                
            case 'settings':
                // Get active exchange
                const exchangeInfo = await apiClient.getActiveExchange();
                if (exchangeInfo && exchangeInfo.active_exchange) {
                    const select = document.getElementById('exchange-select');
                    if (select) {
                        select.value = exchangeInfo.active_exchange;
                    }
                }
                break;
        }
    } catch (error) {
        console.error(`Failed to refresh ${tab} tab:`, error);
        authManager.showNotification(`Failed to load ${tab} data`, 'error');
    }
}

/**
 * Setup timeframe controls
 */
function setupTimeframeControls() {
    const timeButtons = document.querySelectorAll('.time-btn');
    
    timeButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Update active button
            timeButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Update selected timeframe
            const timeframe = button.getAttribute('data-time');
            window.dashboard.updateTimeframe(timeframe);
        });
    });
}

/**
 * Setup correlation coin selection
 */
function setupCoinSelection() {
    const coinButtons = document.querySelectorAll('.coins-filter .coin-btn');
    
    coinButtons.forEach(button => {
        button.addEventListener('click', async () => {
            // Update active button
            coinButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Update correlations
            const coin = button.getAttribute('data-coin');
            try {
                const correlationData = await apiClient.getCorrelations(coin);
                window.dashboard.updateCorrelationTable(correlationData);
            } catch (error) {
                console.error('Failed to fetch correlations:', error);
                authManager.showNotification('Failed to load correlation data', 'error');
            }
        });
    });
}

/**
 * Setup market search
 */
function setupMarketSearch() {
    const searchInput = document.getElementById('marketSearch');
    
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            const query = searchInput.value.toLowerCase().trim();
            
            // Filter market table rows
            const rows = document.querySelectorAll('#marketTableBody tr');
            
            rows.forEach(row => {
                const symbol = row.querySelector('.coin-symbol')?.textContent.toLowerCase() || '';
                const name = row.querySelector('.coin-name')?.textContent.toLowerCase() || '';
                
                if (symbol.includes(query) || name.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
}

/**
 * Setup modals
 */
function setupModals() {
    // API Key Modal
    setupModal('apiKeyModal', 'settingsBtn');
    
    // Strategy Modal
    setupModal('strategyModal', 'newStrategyBtn');
    
    // Add strategy card
    const addStrategyCard = document.querySelector('.add-strategy');
    if (addStrategyCard) {
        addStrategyCard.addEventListener('click', () => {
            document.getElementById('strategyModal').classList.add('active');
        });
    }
    
    // Strategy type change
    const strategyType = document.getElementById('strategy-type');
    if (strategyType) {
        strategyType.addEventListener('change', () => {
            updateStrategyParameters(strategyType.value);
        });
    }
}

/**
 * Setup modal functionality
 * @param {string} modalId - Modal ID
 * @param {string} openBtnId - Open button ID
 */
function setupModal(modalId, openBtnId) {
    const modal = document.getElementById(modalId);
    const openBtn = document.getElementById(openBtnId);
    const closeButtons = modal?.querySelectorAll('.close-modal, .cancel-btn');
    
    // Open modal
    if (openBtn && modal) {
        openBtn.addEventListener('click', () => {
            modal.classList.add('active');
        });
    }
    
    // Close modal
    if (closeButtons) {
        closeButtons.forEach(button => {
            button.addEventListener('click', () => {
                modal.classList.remove('active');
            });
        });
    }
    
    // Handle specific modal save actions
    const saveBtn = modal?.querySelector('.save-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            if (modalId === 'apiKeyModal') {
                saveApiKeys(modal);
            } else if (modalId === 'strategyModal') {
                saveStrategy(modal);
            }
        });
    }
}

/**
 * Save API keys from modal
 * @param {HTMLElement} modal - Modal element
 */
async function saveApiKeys(modal) {
    const exchange = modal.querySelector('#modal-exchange-select').value;
    const apiKey = modal.querySelector('#modal-api-key').value;
    const apiSecret = modal.querySelector('#modal-api-secret').value;
    
    if (!exchange || !apiKey || !apiSecret) {
        authManager.showNotification('Please fill in all fields', 'error');
        return;
    }
    
    try {
        // Save API keys
        await apiClient.configureExchange(exchange, apiKey, apiSecret);
        
        // Set as active exchange
        await apiClient.setActiveExchange(exchange);
        
        // Update settings tab
        const settingsExchange = document.getElementById('exchange-select');
        const settingsApiKey = document.getElementById('api-key');
        const settingsApiSecret = document.getElementById('api-secret');
        
        if (settingsExchange) settingsExchange.value = exchange;
        if (settingsApiKey) settingsApiKey.value = apiKey;
        if (settingsApiSecret) settingsApiSecret.value = '••••••••••••••••';
        
        // Hide modal
        modal.classList.remove('active');
        
        // Show success notification
        authManager.showNotification('API keys saved successfully', 'success');
    } catch (error) {
        console.error('Failed to save API keys:', error);
        authManager.showNotification('Failed to save API keys', 'error');
    }
}

/**
 * Save strategy from modal
 * @param {HTMLElement} modal - Modal element
 */
async function saveStrategy(modal) {
    const name = modal.querySelector('#strategy-name').value;
    const type = modal.querySelector('#strategy-type').value;
    const symbols = modal.querySelector('#strategy-symbols').value.split(',').map(s => s.trim());
    const positionSize = parseFloat(modal.querySelector('#position-size').value);
    
    // Get parameters based on strategy type
    let parameters = {};
    
    switch (type) {
        case 'trend':
            parameters = {
                short_ema: parseInt(modal.querySelector('#short-ema').value),
                long_ema: parseInt(modal.querySelector('#long-ema').value)
            };
            break;
        case 'mean_reversion':
            parameters = {
                width: parseFloat(modal.querySelector('#grid-width').value),
                levels: parseInt(modal.querySelector('#grid-levels').value)
            };
            break;
        case 'market_making':
            parameters = {
                spread: parseFloat(modal.querySelector('#spread').value),
                order_size: parseFloat(modal.querySelector('#order-size').value)
            };
            break;
    }
    
    // Validate inputs
    if (!name || symbols.length === 0 || isNaN(positionSize)) {
        authManager.showNotification('Please fill in all required fields', 'error');
        return;
    }
    
    try {
        // Update risk settings
        await apiClient.updateRiskSettings({
            max_position_size: positionSize
        });
        
        // Activate strategy
        await apiClient.activateStrategy(name, type, parameters, symbols);
        
        // Hide modal
        modal.classList.remove('active');
        
        // Show success notification
        authManager.showNotification('Strategy saved and activated', 'success');
        
        // Refresh strategies tab
        const strategiesTab = document.querySelector('.sidebar li[data-tab="strategies"]');
        if (strategiesTab) {
            strategiesTab.click();
        }
    } catch (error) {
        console.error('Failed to activate strategy:', error);
        authManager.showNotification('Failed to activate strategy', 'error');
    }
}

/**
 * Update strategy parameters inputs based on type
 * @param {string} type - Strategy type
 */
function updateStrategyParameters(type) {
    const paramGroup = document.querySelector('.dynamic-parameters');
    
    if (!paramGroup) return;
    
    // Clear existing parameters
    paramGroup.innerHTML = '';
    
    // Add parameters based on strategy type
    switch (type) {
        case 'trend':
            paramGroup.innerHTML = `
                <div class="parameter-group" id="trendParams">
                    <div class="form-group">
                        <label for="short-ema">Short EMA Period</label>
                        <input type="number" id="short-ema" min="2" max="50" value="9">
                    </div>
                    <div class="form-group">
                        <label for="long-ema">Long EMA Period</label>
                        <input type="number" id="long-ema" min="5" max="200" value="21">
                    </div>
                </div>
            `;
            break;
        case 'mean_reversion':
            paramGroup.innerHTML = `
                <div class="parameter-group" id="meanReversionParams">
                    <div class="form-group">
                        <label for="grid-width">Grid Width (%)</label>
                        <input type="number" id="grid-width" min="0.1" max="10" step="0.1" value="2.0">
                    </div>
                    <div class="form-group">
                        <label for="grid-levels">Grid Levels</label>
                        <input type="number" id="grid-levels" min="2" max="20" value="10">
                    </div>
                </div>
            `;
            break;
        case 'market_making':
            paramGroup.innerHTML = `
                <div class="parameter-group" id="marketMakingParams">
                    <div class="form-group">
                        <label for="spread">Spread (%)</label>
                        <input type="number" id="spread" min="0.1" max="5" step="0.1" value="0.5">
                    </div>
                    <div class="form-group">
                        <label for="order-size">Order Size (% of capital)</label>
                        <input type="number" id="order-size" min="1" max="50" value="5">
                    </div>
                </div>
            `;
            break;
        case 'custom':
            paramGroup.innerHTML = `
                <div class="parameter-group" id="customParams">
                    <div class="form-group">
                        <label for="custom-params">Custom Parameters (JSON)</label>
                        <textarea id="custom-params" rows="4" placeholder="{}">{}</textarea>
                    </div>
                </div>
            `;
            break;
    }
}

/**
 * Setup trading mode toggle
 */
function setupTradingModeToggle() {
    const toggle = document.getElementById('tradingModeToggle');
    
    if (toggle) {
        toggle.addEventListener('change', () => {
            const isLiveTrading = toggle.checked;
            
            if (isLiveTrading) {
                // Check if API keys are configured
                apiClient.getActiveExchange().then(info => {
                    if (!info || !info.active_exchange) {
                        authManager.showNotification('Please configure API keys before enabling live trading', 'error');
                        toggle.checked = false;
                        return;
                    }
                    
                    // Confirm live trading mode
                    const confirm = window.confirm('Are you sure you want to enable live trading? This will use real funds to execute trades.');
                    
                    if (!confirm) {
                        toggle.checked = false;
                        return;
                    }
                    
                    authManager.showNotification('Live trading mode enabled', 'warning');
                }).catch(error => {
                    console.error('Failed to check exchange configuration:', error);
                    authManager.showNotification('Error checking exchange configuration', 'error');
                    toggle.checked = false;
                });
            } else {
                authManager.showNotification('Simulation mode enabled', 'success');
            }
        });
    }
}

/**
 * Setup backtest form
 */
function setupBacktestForm() {
    const runButton = document.getElementById('runBacktestBtn');
    
    if (runButton) {
        runButton.addEventListener('click', async () => {
            // Get form values
            const symbol = document.getElementById('backtest-symbol')?.value.trim() || 'bitcoin';
            const strategy = document.getElementById('backtest-strategy')?.value || 'trend';
            const startDate = document.getElementById('backtest-start')?.value || getDefaultStartDate();
            const endDate = document.getElementById('backtest-end')?.value || getDefaultEndDate();
            const initialCapital = parseFloat(document.getElementById('backtest-capital')?.value) || 10000;
            
            // Validate inputs
            if (!symbol || !strategy || !startDate || !endDate || isNaN(initialCapital)) {
                authManager.showNotification('Please fill in all required fields', 'error');
                return;
            }
            
            try {
                // Show loading state
                runButton.disabled = true;
                runButton.textContent = 'Running...';
                document.getElementById('backtestResults')?.classList.add('hidden');
                
                // Get strategy parameters based on type
                let parameters = {};
                
                switch (strategy) {
                    case 'trend':
                        parameters = {
                            short_ema: 9,
                            long_ema: 21
                        };
                        break;
                    case 'mean_reversion':
                        parameters = {
                            width: 2.0,
                            levels: 10
                        };
                        break;
                    case 'market_making':
                        parameters = {
                            spread: 0.5,
                            order_size: 5
                        };
                        break;
                    case 'optimized':
                        // Get optimal parameters for the current market regime
                        const analysis = await apiClient.analyzeMarket(symbol);
                        const optimalStrategy = await apiClient.getOptimalStrategy(symbol);
                        
                        // Use optimal strategy type and parameters
                        parameters = optimalStrategy.parameters;
                        break;
                }
                
                // Run backtest
                const results = await apiClient.runBacktest(
                    strategy,
                    parameters,
                    symbol,
                    startDate,
                    endDate,
                    initialCapital
                );
                
                // Display results
                window.dashboard.displayBacktestResults(results);
                
                // Reset button
                runButton.disabled = false;
                runButton.textContent = 'Run Backtest';
                
                // Show success notification
                authManager.showNotification('Backtest completed successfully', 'success');
            } catch (error) {
                console.error('Backtest failed:', error);
                authManager.showNotification('Backtest failed: ' + (error.message || 'Unknown error'), 'error');
                
                // Reset button
                runButton.disabled = false;
                runButton.textContent = 'Run Backtest';
            }
        });
    }
    
    // Set default dates
    setDefaultBacktestDates();
}

/**
 * Set default backtest dates
 */
function setDefaultBacktestDates() {
    const startDateInput = document.getElementById('backtest-start');
    const endDateInput = document.getElementById('backtest-end');
    
    if (startDateInput && !startDateInput.value) {
        startDateInput.value = getDefaultStartDate();
    }
    
    if (endDateInput && !endDateInput.value) {
        endDateInput.value = getDefaultEndDate();
    }
}

/**
 * Get default start date (3 months ago)
 * @returns {string} - Default start date (YYYY-MM-DD)
 */
function getDefaultStartDate() {
    const date = new Date();
    date.setMonth(date.getMonth() - 3);
    return date.toISOString().split('T')[0];
}

/**
 * Get default end date (today)
 * @returns {string} - Default end date (YYYY-MM-DD)
 */
function getDefaultEndDate() {
    return new Date().toISOString().split('T')[0];
}

/**
 * Setup settings forms
 */
function setupSettingsForms() {
    // API keys form
    const saveApiBtn = document.querySelector('.save-api-btn');
    if (saveApiBtn) {
        saveApiBtn.addEventListener('click', async () => {
            const exchange = document.getElementById('exchange-select').value;
            const apiKey = document.getElementById('api-key').value;
            const apiSecret = document.getElementById('api-secret').value;
            
            if (!exchange || !apiKey || !apiSecret) {
                authManager.showNotification('Please fill in all API key fields', 'error');
                return;
            }
            
            try {
                // Save API keys
                await apiClient.configureExchange(exchange, apiKey, apiSecret);
                
                // Set as active exchange
                await apiClient.setActiveExchange(exchange);
                
                // Show success notification
                authManager.showNotification('API keys saved successfully', 'success');
            } catch (error) {
                console.error('Failed to save API keys:', error);
                authManager.showNotification('Failed to save API keys', 'error');
            }
        });
    }
    
    // Risk management form
    const saveRiskBtn = document.querySelector('.save-risk-btn');
    if (saveRiskBtn) {
        saveRiskBtn.addEventListener('click', async () => {
            const maxPosition = parseFloat(document.getElementById('max-position').value);
            const stopLoss = parseFloat(document.getElementById('stop-loss').value);
            const takeProfit = parseFloat(document.getElementById('take-profit').value);
            const maxTrades = parseInt(document.getElementById('max-trades').value);
            const emergencyStop = parseFloat(document.getElementById('emergency-stop').value);
            
            if (isNaN(maxPosition) || isNaN(stopLoss) || isNaN(takeProfit) || isNaN(maxTrades) || isNaN(emergencyStop)) {
                authManager.showNotification('Please fill in all risk management fields with valid numbers', 'error');
                return;
            }
            
            try {
                // Update risk settings
                await apiClient.updateRiskSettings({
                    max_position_size: maxPosition,
                    stop_loss: stopLoss,
                    take_profit: takeProfit,
                    max_concurrent_trades: maxTrades,
                    emergency_stop_threshold: emergencyStop
                });
                
                // Show success notification
                authManager.showNotification('Risk settings saved successfully', 'success');
            } catch (error) {
                console.error('Failed to save risk settings:', error);
                authManager.showNotification('Failed to save risk settings', 'error');
            }
        });
    }
    
    // Notification settings form
    const saveNotifBtn = document.querySelector('.save-notif-btn');
    if (saveNotifBtn) {
        saveNotifBtn.addEventListener('click', () => {
            // In a real application, this would save notification preferences
            // For this demo, we'll just show a confirmation
            authManager.showNotification('Notification settings saved successfully', 'success');
        });
    }
}

/**
 * Check if API keys are configured
 */
function checkApiKeys() {
    setTimeout(async () => {
        try {
            // Check if any exchange is configured
            const info = await apiClient.getActiveExchange();
            
            if (!info || !info.active_exchange) {
                // Show API key modal on first load
                const apiKeyModal = document.getElementById('apiKeyModal');
                if (apiKeyModal) {
                    apiKeyModal.classList.add('active');
                }
            }
        } catch (error) {
            console.error('Failed to check exchange configuration:', error);
            // Show API key modal on error
            const apiKeyModal = document.getElementById('apiKeyModal');
            if (apiKeyModal) {
                apiKeyModal.classList.add('active');
            }
        }
    }, 1000);
}
