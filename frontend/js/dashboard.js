/**
 * Dashboard Module for Crypto Trading Bot
 * Handles UI updates and data visualization
 */
class Dashboard {
    constructor() {
        // Chart instances
        this.charts = {
            portfolio: null,
            allocation: null,
            marketDetail: null,
            backtestResults: null
        };
        
        // Data storage
        this.data = {
            portfolioHistory: [],
            assets: [],
            markets: [],
            correlations: {},
            trades: []
        };
        
        // Current settings
        this.settings = {
            timeframe: '1d',
            activeCoin: 'bitcoin',
            theme: 'light'
        };
        
        // Chart colors
        this.colors = {
            primary: '#2563eb',
            secondary: '#10b981',
            danger: '#ef4444',
            warning: '#f59e0b',
            gray: '#6b7280',
            chartColors: [
                '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
                '#ec4899', '#f43f5e', '#06b6d4', '#84cc16', '#6366f1'
            ]
        };
    }
    
    /**
     * Initialize dashboard
     */
    async init() {
        try {
            // Initialize charts
            this.initCharts();
            
            // Fetch initial data
            await Promise.all([
                this.fetchPortfolioData(),
                this.fetchMarketData(),
                this.fetchCorrelationData(this.settings.activeCoin)
            ]);
            
            // Initialize event listeners
            this.setupEventListeners();
            
            console.log('Dashboard initialized');
        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
        }
    }
    
    /**
     * Initialize charts
     */
    initCharts() {
        // Portfolio chart
        const portfolioCanvas = document.getElementById('portfolioChart');
        if (portfolioCanvas) {
            this.charts.portfolio = new Chart(portfolioCanvas, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Portfolio Value',
                        data: [],
                        borderColor: this.colors.primary,
                        backgroundColor: `${this.colors.primary}20`,
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            callbacks: {
                                label: function(context) {
                                    return `Portfolio Value: $${context.raw.toLocaleString('en-US', { maximumFractionDigits: 2 })}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            beginAtZero: false,
                            grid: {
                                color: '#e5e7eb'
                            },
                            ticks: {
                                callback: function(value) {
                                    return `$${value.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Asset allocation chart
        const allocationCanvas = document.getElementById('allocationChart');
        if (allocationCanvas) {
            this.charts.allocation = new Chart(allocationCanvas, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: this.colors.chartColors,
                        borderWidth: 1,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                boxWidth: 12,
                                padding: 10
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.raw || 0;
                                    const percentage = context.parsed || 0;
                                    return `${label}: ${percentage}% ($${value.toLocaleString('en-US', { maximumFractionDigits: 2 })})`;
                                }
                            }
                        }
                    },
                    cutout: '70%'
                }
            });
        }
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Market table row click
        const marketTableBody = document.getElementById('marketTableBody');
        if (marketTableBody) {
            marketTableBody.addEventListener('click', (e) => {
                const viewBtn = e.target.closest('.view-btn');
                const tradeBtn = e.target.closest('.trade-btn');
                
                if (viewBtn) {
                    const coinId = viewBtn.getAttribute('data-id');
                    if (coinId) {
                        this.showMarketDetail(coinId);
                    }
                } else if (tradeBtn) {
                    const coinId = tradeBtn.getAttribute('data-id');
                    if (coinId) {
                        // Show trade modal or UI
                        console.log(`Trading ${coinId}`);
                    }
                }
            });
        }
        
        // Correlation table row click
        const correlationTableBody = document.getElementById('correlationTableBody');
        if (correlationTableBody) {
            correlationTableBody.addEventListener('click', (e) => {
                const tradeBtn = e.target.closest('.trade-btn');
                const analyzeBtn = e.target.closest('.analyze-btn');
                
                if (tradeBtn) {
                    const symbol = tradeBtn.getAttribute('data-symbol');
                    if (symbol) {
                        // Show trade modal or UI
                        console.log(`Trading ${symbol}`);
                    }
                } else if (analyzeBtn) {
                    const coinId = analyzeBtn.getAttribute('data-id');
                    if (coinId) {
                        this.showMarketDetail(coinId);
                    }
                }
            });
        }
        
        // Market detail back button
        const backButton = document.querySelector('.market-detail .back-button');
        if (backButton) {
            backButton.addEventListener('click', () => {
                this.hideMarketDetail();
            });
        }
        
        // Trading buttons
        const buyBtn = document.querySelector('.market-trading .buy-btn');
        const sellBtn = document.querySelector('.market-trading .sell-btn');
        
        if (buyBtn) {
            buyBtn.addEventListener('click', () => {
                const symbol = document.querySelector('.market-detail-title').textContent;
                this.executeTrade(symbol, 'buy');
            });
        }
        
        if (sellBtn) {
            sellBtn.addEventListener('click', () => {
                const symbol = document.querySelector('.market-detail-title').textContent;
                this.executeTrade(symbol, 'sell');
            });
        }
    }
    
    /**
     * Update timeframe for portfolio chart
     * @param {string} timeframe - Timeframe (1d, 1w, 1m, 3m, 1y, all)
     */
    updateTimeframe(timeframe) {
        this.settings.timeframe = timeframe;
        this.updatePortfolioChart();
    }
    
    /**
     * Fetch portfolio data from API
     */
    async fetchPortfolioData() {
        try {
            const data = await apiClient.getPortfolio();
            
            if (data) {
                this.data.portfolioHistory = data.portfolio_history || [];
                this.data.assets = data.assets || [];
                
                // Update UI
                this.updatePortfolioData(data);
            }
        } catch (error) {
            console.error('Failed to fetch portfolio data:', error);
        }
    }
    
    /**
     * Update portfolio data in the UI
     * @param {Object} data - Portfolio data
     */
    updatePortfolioData(data) {
        if (!data) return;
        
        // Update portfolio history
        if (data.portfolio_history) {
            this.data.portfolioHistory = data.portfolio_history;
        }
        
        // Update asset allocation
        if (data.assets) {
            this.data.assets = data.assets;
        }
        
        // Update portfolio chart
        this.updatePortfolioChart();
        
        // Update allocation chart
        this.updateAllocationChart();
        
        // Update portfolio value
        this.updatePortfolioValue(data.portfolio_value);
    }
    
    /**
     * Update portfolio chart with current data
     */
    updatePortfolioChart() {
        if (!this.charts.portfolio || !this.data.portfolioHistory.length) return;
        
        // Filter data by timeframe
        const filteredData = this.filterByTimeframe(this.data.portfolioHistory, this.settings.timeframe);
        
        // Update chart data
        this.charts.portfolio.data.labels = filteredData.map(item => this.formatDate(new Date(item.time), this.settings.timeframe));
        this.charts.portfolio.data.datasets[0].data = filteredData.map(item => item.value);
        
        // Update chart
        this.charts.portfolio.update();
    }
    
    /**
     * Update allocation chart with current data
     */
    updateAllocationChart() {
        if (!this.charts.allocation || !this.data.assets.length) return;
        
        // Update chart data
        this.charts.allocation.data.labels = this.data.assets.map(asset => asset.symbol);
        this.charts.allocation.data.datasets[0].data = this.data.assets.map(asset => asset.percentage);
        
        // Update chart
        this.charts.allocation.update();
    }
    
    /**
     * Update portfolio value display
     * @param {number} currentValue - Current portfolio value
     */
    updatePortfolioValue(currentValue) {
        if (!currentValue) return;
        
        const valueElement = document.querySelector('.portfolio-value .value');
        const changeElement = document.querySelector('.portfolio-value .change');
        
        if (valueElement) {
            valueElement.textContent = `$${currentValue.toLocaleString('en-US', { maximumFractionDigits: 2 })}`;
        }
        
        // Calculate 24h change
        if (changeElement && this.data.portfolioHistory.length >= 2) {
            // Get value from 24h ago
            const now = new Date();
            const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
            
            // Find the closest data point to 24h ago
            const previousPoint = this.findClosestDataPoint(this.data.portfolioHistory, oneDayAgo);
            const previousValue = previousPoint ? previousPoint.value : currentValue;
            
            // Calculate percentage change
            const changePercent = ((currentValue - previousValue) / previousValue) * 100;
            
            // Update display
            changeElement.textContent = `${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%`;
            changeElement.className = `change ${changePercent >= 0 ? 'up' : 'down'}`;
        }
    }
    
    /**
     * Fetch market data from API
     */
    async fetchMarketData() {
        try {
            const data = await apiClient.getMarkets();
            
            if (data) {
                this.data.markets = data;
                
                // Update market table
                this.updateMarketTable(data);
            }
        } catch (error) {
            console.error('Failed to fetch market data:', error);
        }
    }
    
    /**
     * Update market table with current data
     * @param {Array} markets - Market data
     */
    updateMarketTable(markets) {
        if (!markets || !markets.length) return;
        
        const tableBody = document.getElementById('marketTableBody');
        if (!tableBody) return;
        
        // Clear table
        tableBody.innerHTML = '';
        
        // Add rows
        markets.forEach(market => {
            const row = document.createElement('tr');
            
            // Determine price change class
            const priceChangeClass = market.price_change_percentage_24h >= 0 ? 'up' : 'down';
            
            // Determine regime class
            const regimeColor = market.regime === 'trending' ? this.colors.primary : 
                               market.regime === 'sideways' ? this.colors.warning : 
                               this.colors.danger;
            
            row.innerHTML = `
                <td>
                    <div class="coin-info">
                        <img src="${market.image}" alt="${market.name}" width="24" height="24">
                        <div>
                            <div class="coin-symbol">${market.symbol.toUpperCase()}</div>
                            <div class="coin-name">${market.name}</div>
                        </div>
                    </div>
                </td>
                <td>$${market.current_price.toLocaleString('en-US', { maximumFractionDigits: 8 })}</td>
                <td class="${priceChangeClass}">${market.price_change_percentage_24h >= 0 ? '+' : ''}${market.price_change_percentage_24h.toFixed(2)}%</td>
                <td>$${market.total_volume.toLocaleString('en-US', { maximumFractionDigits: 0 })}</td>
                <td>$${market.market_cap.toLocaleString('en-US', { maximumFractionDigits: 0 })}</td>
                <td>
                    <div class="regime" style="color: ${regimeColor}">
                        <span class="regime-dot" style="background-color: ${regimeColor}"></span>
                        ${market.regime.charAt(0).toUpperCase() + market.regime.slice(1)}
                    </div>
                </td>
                <td>
                    <button class="view-btn" data-id="${market.id}">View</button>
                    <button class="trade-btn" data-id="${market.id}">Trade</button>
                </td>
            `;
            
            tableBody.appendChild(row);
        });
    }
    
    /**
     * Fetch correlation data from API
     * @param {string} baseCoin - Base coin ID
     */
    async fetchCorrelationData(baseCoin) {
        try {
            const data = await apiClient.getCorrelations(baseCoin);
            
            if (data) {
                this.data.correlations[baseCoin] = data;
                
                // Update correlation table
                this.updateCorrelationTable(data);
            }
        } catch (error) {
            console.error(`Failed to fetch correlation data for ${baseCoin}:`, error);
        }
    }
    
    /**
     * Update correlation table with current data
     * @param {Array} correlations - Correlation data
     */
    updateCorrelationTable(correlations) {
        if (!correlations || !correlations.length) return;
        
        const tableBody = document.getElementById('correlationTableBody');
        if (!tableBody) return;
        
        // Clear table
        tableBody.innerHTML = '';
        
        // Update statistics
        this.updateCorrelationStats(correlations);
        
        // Add rows
        correlations.forEach((correlation, index) => {
            const row = document.createElement('tr');
            
            // Determine performance delta class
            const deltaClass = correlation.performance_delta >= 0 ? 'positive' : 'negative';
            
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>
                    <div class="coin-info">
                        <div class="coin-symbol">${correlation.symbol.toUpperCase()}</div>
                        <div class="coin-name">${correlation.name}</div>
                    </div>
                </td>
                <td>
                    <div class="correlation-bar">
                        <div class="bar" style="width: ${correlation.correlation_score * 100}%"></div>
                    </div>
                    <div class="correlation-value">${correlation.correlation_score.toFixed(3)}</div>
                </td>
                <td class="${deltaClass}">
                    <div class="performance-bar">
                        <div class="bar" style="width: ${Math.min(Math.abs(correlation.performance_delta), 100)}%"></div>
                    </div>
                    <div class="performance-value">${correlation.performance_delta >= 0 ? '+' : ''}${correlation.performance_delta.toFixed(2)}%</div>
                </td>
                <td>$${correlation.current_price.toLocaleString('en-US', { maximumFractionDigits: 8 })}</td>
                <td>$${(correlation.volume / 1000000).toFixed(2)}M</td>
                <td>
                    <button class="trade-btn" data-symbol="${correlation.symbol}">Trade</button>
                    <button class="analyze-btn" data-id="${correlation.id}">Analyze</button>
                </td>
            `;
            
            tableBody.appendChild(row);
        });
    }
    
    /**
     * Update correlation statistics
     * @param {Array} correlations - Correlation data
     */
    updateCorrelationStats(correlations) {
        if (!correlations || !correlations.length) return;
        
        // Calculate statistics
        const totalCorrelated = correlations.length;
        const highCorrelations = correlations.filter(c => c.correlation_score > 0.8).length;
        const outperforming = correlations.filter(c => c.performance_delta > 0).length;
        const underperforming = totalCorrelated - outperforming;
        
        // Update UI
        const totalElement = document.querySelector('.correlation-stats .stat-card:nth-child(1) .stat-value');
        const highElement = document.querySelector('.correlation-stats .stat-card:nth-child(2) .stat-value');
        const outElement = document.querySelector('.correlation-stats .stat-card:nth-child(3) .stat-value');
        const underElement = document.querySelector('.correlation-stats .stat-card:nth-child(4) .stat-value');
        
        if (totalElement) totalElement.textContent = totalCorrelated;
        if (highElement) highElement.textContent = highCorrelations;
        if (outElement) outElement.textContent = outperforming;
        if (underElement) underElement.textContent = underperforming;
    }
    
    /**
     * Show detailed market view
     * @param {string} coinId - Cryptocurrency ID
     */
    async showMarketDetail(coinId) {
        try {
            // Get market list and detail containers
            const marketList = document.querySelector('.markets-table-container');
            const marketDetail = document.getElementById('marketDetail');
            
            if (!marketList || !marketDetail) return;
            
            // Hide market list and show detail view
            marketList.style.display = 'none';
            marketDetail.classList.remove('hidden');
            
            // Fetch coin details
            const coinDetails = await apiClient.getCoinDetails(coinId);
            
            if (!coinDetails) {
                throw new Error('Failed to fetch coin details');
            }
            
            // Update title
            const titleElement = document.querySelector('.market-detail-title');
            if (titleElement) {
                titleElement.textContent = `${coinDetails.name} (${coinDetails.symbol.toUpperCase()})`;
            }
            
            // Fetch historical data
            const historicalData = await apiClient.getHistoricalData(coinId, '30');
            
            if (!historicalData || !historicalData.prices || !historicalData.prices.length) {
                throw new Error('Failed to fetch historical data');
            }
            
            // Initialize detail chart
            this.initMarketDetailChart(historicalData);
            
            // Fetch technical analysis
            const technicalAnalysis = await apiClient.analyzeTechnicals(coinId);
            
            if (!technicalAnalysis) {
                throw new Error('Failed to fetch technical analysis');
            }
            
            // Update technical indicators
            this.updateTechnicalIndicators(technicalAnalysis);
            
            // Fetch market analysis
            const marketAnalysis = await apiClient.analyzeMarket(coinId);
            
            if (!marketAnalysis) {
                throw new Error('Failed to fetch market analysis');
            }
            
            // Update market regime
            this.updateMarketRegime(marketAnalysis, technicalAnalysis.price);
            
        } catch (error) {
            console.error(`Failed to show market detail for ${coinId}:`, error);
            this.hideMarketDetail();
            authManager.showNotification(`Failed to load data for ${coinId}`, 'error');
        }
    }
    
    /**
     * Hide market detail view
     */
    hideMarketDetail() {
        const marketList = document.querySelector('.markets-table-container');
        const marketDetail = document.getElementById('marketDetail');
        
        if (!marketList || !marketDetail) return;
        
        // Show market list and hide detail view
        marketList.style.display = 'block';
        marketDetail.classList.add('hidden');
        
        // Destroy chart to free memory
        if (this.charts.marketDetail) {
            this.charts.marketDetail.destroy();
            this.charts.marketDetail = null;
        }
    }
    
    /**
     * Initialize market detail chart
     * @param {Object} historicalData - Historical price data
     */
    initMarketDetailChart(historicalData) {
        const chartContainer = document.getElementById('marketDetailChart');
        
        if (!chartContainer) return;
        
        // Extract data
        const prices = historicalData.prices || [];
        const volumes = historicalData.total_volumes || [];
        
        if (!prices.length) return;
        
        // Format data for chart
        const labels = prices.map(item => this.formatDate(new Date(item.time), '1m'));
        const priceData = prices.map(item => item.value);
        
        // Calculate SMA lines
        const sma20 = this.calculateSMA(priceData, 20);
        const sma50 = this.calculateSMA(priceData, 50);
        
        // Prepare volume data
        const volumeData = volumes.map(item => item.value);
        const maxVolume = Math.max(...volumeData);
        const minPrice = Math.min(...priceData);
        
        // Normalize volumes to fit on the same scale
        const normalizedVolumes = volumeData.map(volume => {
            return (volume / maxVolume) * (minPrice * 0.3);
        });
        
        // Destroy existing chart
        if (this.charts.marketDetail) {
            this.charts.marketDetail.destroy();
        }
        
        // Create new chart
        this.charts.marketDetail = new Chart(chartContainer, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Price',
                        data: priceData,
                        borderColor: this.colors.primary,
                        backgroundColor: `${this.colors.primary}20`,
                        borderWidth: 2,
                        fill: false,
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'SMA 20',
                        data: sma20,
                        borderColor: this.colors.secondary,
                        borderWidth: 1.5,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'SMA 50',
                        data: sma50,
                        borderColor: this.colors.warning,
                        borderWidth: 1.5,
                        borderDash: [2, 2],
                        fill: false,
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Volume',
                        data: normalizedVolumes,
                        backgroundColor: `${this.colors.gray}40`,
                        borderColor: `${this.colors.gray}00`,
                        borderWidth: 0,
                        type: 'bar',
                        yAxisID: 'y'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                
                                if (label === 'Volume') {
                                    const volumeIndex = context.dataIndex;
                                    const actualVolume = volumeData[volumeIndex];
                                    return `Volume: $${actualVolume.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
                                }
                                
                                return `${label}: $${context.raw.toLocaleString('en-US', { maximumFractionDigits: 2 })}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        position: 'right',
                        grid: {
                            color: '#e5e7eb'
                        },
                        ticks: {
                            callback: function(value) {
                                return `$${value.toLocaleString('en-US', { maximumFractionDigits: 2 })}`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Update technical indicators display
     * @param {Object} technicals - Technical analysis data
     */
    updateTechnicalIndicators(technicals) {
        const indicatorGrid = document.querySelector('.indicator-grid');
        
        if (!indicatorGrid || !technicals) return;
        
        // Clear existing indicators
        indicatorGrid.innerHTML = '';
        
        // Create indicator elements
        const indicators = [
            { name: 'Price', value: `$${technicals.price.toLocaleString('en-US', { maximumFractionDigits: 8 })}` },
            { name: 'EMA (9)', value: `$${technicals.ema.short.toLocaleString('en-US', { maximumFractionDigits: 2 })}` },
            { name: 'EMA (21)', value: `$${technicals.ema.medium.toLocaleString('en-US', { maximumFractionDigits: 2 })}` },
            { name: 'RSI', value: technicals.rsi.toFixed(2) },
            { name: 'MACD', value: technicals.macd.value.toFixed(2) },
            { name: 'Signal', value: technicals.signal.toUpperCase(), class: technicals.signal === 'buy' ? 'buy' : (technicals.signal === 'sell' ? 'sell' : '') }
        ];
        
        // Add indicators to grid
        indicators.forEach(indicator => {
            const indicatorElement = document.createElement('div');
            indicatorElement.className = 'indicator';
            
            indicatorElement.innerHTML = `
                <div class="indicator-name">${indicator.name}</div>
                <div class="indicator-value ${indicator.class || ''}">${indicator.value}</div>
            `;
            
            indicatorGrid.appendChild(indicatorElement);
        });
    }
    
    /**
     * Update market regime display
     * @param {Object} analysis - Market analysis data
     * @param {number} price - Current price
     */
    updateMarketRegime(analysis, price) {
        if (!analysis) return;
        
        // Update regime dot in dashboard
        const regimeDot = document.querySelector('.regime-dot');
        const regimeText = document.querySelector('.regime-text');
        const volatilityValue = document.querySelector('.volatility-value');
        const confidenceValue = document.querySelector('.confidence-value');
        const strategyName = document.querySelector('.strategy-name');
        
        if (regimeDot) {
            regimeDot.setAttribute('data-regime', analysis.regime);
        }
        
        if (regimeText) {
            regimeText.textContent = analysis.regime.charAt(0).toUpperCase() + analysis.regime.slice(1);
        }
        
        if (volatilityValue) {
            volatilityValue.textContent = `${(analysis.volatility * 100).toFixed(2)}%`;
        }
        
        if (confidenceValue) {
            confidenceValue.textContent = `${Math.round(analysis.confidence)}%`;
        }
        
        // Update strategy selection in market detail
        const strategySelect = document.getElementById('marketStrategy');
        if (strategySelect) {
            // Set appropriate strategy based on regime
            switch (analysis.regime) {
                case 'trending':
                    strategySelect.value = 'trend';
                    if (strategyName) strategyName.textContent = 'Trend Following';
                    break;
                case 'sideways':
                    strategySelect.value = 'mean_reversion';
                    if (strategyName) strategyName.textContent = 'Mean Reversion';
                    break;
                case 'volatile':
                    strategySelect.value = 'market_making';
                    if (strategyName) strategyName.textContent = 'Market Making';
                    break;
                default:
                    strategySelect.value = 'trend';
                    if (strategyName) strategyName.textContent = 'Trend Following';
            }
        }
    }
    
    /**
     * Execute a trade
     * @param {string} symbol - Trading pair symbol
     * @param {string} action - Trade action (buy, sell)
     */
    async executeTrade(symbol, action) {
        try {
            // Get simulation mode status
            const simulationMode = !document.getElementById('tradingModeToggle')?.checked;
            
            // Confirm trade
            const confirmMessage = `${action.toUpperCase()} ${symbol} ${simulationMode ? '(Simulation)' : '(LIVE TRADE)'}\n\nAre you sure you want to proceed?`;
            const confirmed = window.confirm(confirmMessage);
            
            if (!confirmed) return;
            
            // Execute trade
            const result = await apiClient.executeTrade(symbol, action, 1, simulationMode);
            
            if (result && result.success) {
                // Show success notification
                const message = `${action.toUpperCase()} order placed successfully ${simulationMode ? '(Simulation)' : ''}`;
                authManager.showNotification(message, 'success');
                
                // Refresh portfolio data
                this.fetchPortfolioData();
            } else {
                throw new Error(result?.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Trade execution failed:', error);
            authManager.showNotification(`Trade failed: ${error.message}`, 'error');
        }
    }
    
    /**
     * Display backtest results
     * @param {Object} results - Backtest results
     */
    displayBacktestResults(results) {
        if (!results) return;
        
        // Show results container
        const resultsContainer = document.getElementById('backtestResults');
        if (resultsContainer) {
            resultsContainer.classList.remove('hidden');
        }
        
        // Update summary cards
        this.updateBacktestSummary(results);
        
        // Update results chart
        this.initBacktestChart(results.equity_curve);
        
        // Update trades table
        this.updateBacktestTrades(results.trades);
    }
    
    /**
     * Update backtest summary cards
     * @param {Object} results - Backtest results
     */
    updateBacktestSummary(results) {
        // Update final capital
        const finalCapitalValue = document.querySelector('.summary-card:nth-child(1) .value');
        const finalCapitalChange = document.querySelector('.summary-card:nth-child(1) .change');
        
        if (finalCapitalValue) {
            finalCapitalValue.textContent = `$${results.final_capital.toLocaleString('en-US', { maximumFractionDigits: 2 })}`;
        }
        
        if (finalCapitalChange) {
            finalCapitalChange.textContent = `${results.total_return >= 0 ? '+' : ''}${results.total_return.toFixed(2)}%`;
            finalCapitalChange.className = `change ${results.total_return >= 0 ? 'positive' : 'negative'}`;
        }
        
        // Update other metrics
        const metricsMap = [
            { selector: '.summary-card:nth-child(2) .value', value: results.metrics.trades },
            { selector: '.summary-card:nth-child(3) .value', value: `${results.metrics.win_rate.toFixed(2)}%` },
            { selector: '.summary-card:nth-child(4) .value', value: results.metrics.profit_factor.toFixed(2) },
            { selector: '.summary-card:nth-child(5) .value', value: `${results.metrics.max_drawdown.toFixed(2)}%`, class: 'negative' },
            { selector: '.summary-card:nth-child(6) .value', value: (results.total_return / (results.metrics.max_drawdown || 1)).toFixed(2) }
        ];
        
        metricsMap.forEach(metric => {
            const element = document.querySelector(metric.selector);
            if (element) {
                element.textContent = metric.value;
                if (metric.class) {
                    element.className = `value ${metric.class}`;
                }
            }
        });
    }
    
    /**
     * Initialize backtest results chart
     * @param {Array} equityCurve - Equity curve data
     */
    initBacktestChart(equityCurve) {
        const chartContainer = document.getElementById('backtestResultsChart');
        
        if (!chartContainer || !equityCurve || !equityCurve.length) return;
        
        // Format data for chart
        const labels = equityCurve.map(item => this.formatDate(new Date(item.time), '1m'));
        const data = equityCurve.map(item => item.value);
        
        // Destroy existing chart
        if (this.charts.backtestResults) {
            this.charts.backtestResults.destroy();
        }
        
        // Create new chart
        this.charts.backtestResults = new Chart(chartContainer, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Equity',
                    data,
                    borderColor: this.colors.primary,
                    backgroundColor: `${this.colors.primary}20`,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Equity: $${context.raw.toLocaleString('en-US', { maximumFractionDigits: 2 })}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        grid: {
                            color: '#e5e7eb'
                        },
                        ticks: {
                            callback: function(value) {
                                return `$${value.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
                            }
                        },
                        beginAtZero: false
                    }
                }
            }
        });
    }
    
    /**
     * Update backtest trades table
     * @param {Array} trades - Trade history
     */
    updateBacktestTrades(trades) {
        const tableBody = document.getElementById('backtestTradesBody');
        
        if (!tableBody || !trades || !trades.length) return;
        
        // Clear table
        tableBody.innerHTML = '';
        
        // Add rows for each trade
        trades.forEach((trade, index) => {
            const row = document.createElement('tr');
            
            // Determine profit/loss class
            const plClass = trade.profit_loss > 0 ? 'positive' : (trade.profit_loss < 0 ? 'negative' : '');
            
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${this.formatDate(new Date(trade.time), 'datetime')}</td>
                <td class="${trade.action === 'buy' ? 'buy' : 'sell'}">${trade.action.toUpperCase()}</td>
                <td>$${trade.price.toLocaleString('en-US', { maximumFractionDigits: 8 })}</td>
                <td>${trade.quantity.toFixed(8)}</td>
                <td>$${trade.value.toLocaleString('en-US', { maximumFractionDigits: 2 })}</td>
                <td class="${plClass}">${trade.profit_loss ? `${trade.profit_loss > 0 ? '+' : ''}$${trade.profit_loss.toLocaleString('en-US', { maximumFractionDigits: 2 })}` : '-'}</td>
            `;
            
            tableBody.appendChild(row);
        });
    }
    
    /**
     * Filter data by timeframe
     * @param {Array} data - Data array with time property
     * @param {string} timeframe - Timeframe (1d, 1w, 1m, 3m, 1y, all)
     * @returns {Array} - Filtered data
     */
    filterByTimeframe(data, timeframe) {
        if (!data || !data.length) return [];
        
        const now = new Date();
        
        // Determine cutoff date based on timeframe
        let cutoffDate;
        switch (timeframe) {
            case '1d': cutoffDate = new Date(now.getTime() - 24 * 60 * 60 * 1000); break;
            case '1w': cutoffDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000); break;
            case '1m': cutoffDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000); break;
            case '3m': cutoffDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000); break;
            case '1y': cutoffDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000); break;
            default: return data; // 'all' timeframe or unknown
        }
        
        // Filter data by date
        return data.filter(item => new Date(item.time) >= cutoffDate);
    }
    
    /**
     * Find closest data point to a given date
     * @param {Array} data - Data array with time property
     * @param {Date} targetDate - Target date
     * @returns {Object|null} - Closest data point or null
     */
    findClosestDataPoint(data, targetDate) {
        if (!data || !data.length) return null;
        
        const targetTime = targetDate.getTime();
        
        // Find closest point by time difference
        return data.reduce((closest, current) => {
            const currentTime = new Date(current.time).getTime();
            const closestTime = closest ? new Date(closest.time).getTime() : Infinity;
            
            const currentDiff = Math.abs(currentTime - targetTime);
            const closestDiff = Math.abs(closestTime - targetTime);
            
            return currentDiff < closestDiff ? current : closest;
        }, null);
    }
    
    /**
     * Calculate Simple Moving Average
     * @param {Array} data - Data array
     * @param {number} period - SMA period
     * @returns {Array} - SMA values (with nulls for the first period-1 points)
     */
    calculateSMA(data, period) {
        const result = new Array(data.length).fill(null);
        
        if (data.length < period) return result;
        
        // Calculate SMA for each point starting from index (period-1)
        for (let i = period - 1; i < data.length; i++) {
            const slice = data.slice(i - period + 1, i + 1);
            const sum = slice.reduce((total, value) => total + value, 0);
            result[i] = sum / period;
        }
        
        return result;
    }
    
    /**
     * Format date based on timeframe
     * @param {Date} date - Date to format
     * @param {string} timeframe - Timeframe or format type
     * @returns {string} - Formatted date string
     */
    formatDate(date, timeframe) {
        if (!date) return '';
        
        switch (timeframe) {
            case '1d':
                return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            case '1w':
                return date.toLocaleDateString([], { weekday: 'short', hour: '2-digit', minute: '2-digit' });
            case '1m':
            case '3m':
                return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
            case '1y':
            case 'all':
                return date.toLocaleDateString([], { year: 'numeric', month: 'short' });
            case 'datetime':
                return date.toLocaleString([], { year: '2-digit', month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
            default:
                return date.toLocaleDateString();
        }
    }
}

// Create a singleton instance
const dashboard = new Dashboard();

// Export the instance
window.dashboard = dashboard;
