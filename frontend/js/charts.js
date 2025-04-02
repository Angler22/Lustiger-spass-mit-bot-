/**
 * Charts Utility Module for Crypto Trading Bot
 * Provides advanced charting functionality beyond basic dashboard charts
 */
class ChartManager {
    constructor() {
        // Chart type registry
        this.chartTypes = {
            candlestick: this.createCandlestickChart,
            marketDepth: this.createMarketDepthChart,
            correlation: this.createCorrelationHeatmap,
            performance: this.createPerformanceChart
        };
        
        // Color schemes
        this.colors = {
            // Base colors
            primary: '#2563eb',
            secondary: '#10b981',
            warning: '#f59e0b',
            danger: '#ef4444',
            dark: '#111827',
            gray: '#6b7280',
            light: '#f3f4f6',
            
            // Chart colors
            upColor: '#10b981',
            downColor: '#ef4444',
            volumeColor: 'rgba(107, 114, 128, 0.3)',
            gridColor: '#e5e7eb',
            
            // Gradient colors
            primaryGradient: ['#2563eb', '#60a5fa'],
            secondaryGradient: ['#10b981', '#34d399'],
            
            // Correlation heatmap colors
            correlationColors: [
                '#ef4444', // Strong negative (-1.0)
                '#fca5a5', // Weak negative (-0.5)
                '#f3f4f6', // No correlation (0)
                '#93c5fd', // Weak positive (0.5)
                '#2563eb'  // Strong positive (1.0)
            ]
        };
    }
    
    /**
     * Create an advanced chart
     * @param {string} type - Chart type
     * @param {string} containerId - Container element ID
     * @param {Object} data - Chart data
     * @param {Object} options - Chart options
     * @returns {Object} - Chart instance
     */
    createChart(type, containerId, data, options = {}) {
        const container = document.getElementById(containerId);
        
        if (!container) {
            console.error(`Container element not found: ${containerId}`);
            return null;
        }
        
        if (!this.chartTypes[type]) {
            console.error(`Unsupported chart type: ${type}`);
            return null;
        }
        
        return this.chartTypes[type].call(this, container, data, options);
    }
    
    /**
     * Create a candlestick chart
     * @param {HTMLElement} container - Container element
     * @param {Object} data - Chart data
     * @param {Object} options - Chart options
     * @returns {Object} - Chart instance
     */
    createCandlestickChart(container, data, options = {}) {
        // Format data for candlestick chart
        const ohlcData = this.formatOHLCData(data);
        
        // Set default options
        const defaultOptions = {
            title: 'Price Chart',
            showVolume: true,
            timeUnit: 'day',
            indicators: ['sma20', 'sma50', 'bollinger']
        };
        
        // Merge options
        const chartOptions = { ...defaultOptions, ...options };
        
        // Create Chart.js chart with financial plugin
        // Note: In a real app, we would use a library like trading-vue-js or Lightweight Charts
        // For this demo, we'll simulate a candlestick chart with regular Chart.js
        
        // Define datasets
        const datasets = [
            {
                label: 'Price',
                data: ohlcData.map(candle => ({
                    x: new Date(candle.time),
                    o: candle.open,
                    h: candle.high,
                    l: candle.low,
                    c: candle.close
                })),
                borderColor: context => {
                    const index = context.dataIndex;
                    const candle = ohlcData[index];
                    return candle.close >= candle.open ? this.colors.upColor : this.colors.downColor;
                },
                backgroundColor: context => {
                    const index = context.dataIndex;
                    const candle = ohlcData[index];
                    return candle.close >= candle.open ? 
                        `${this.colors.upColor}40` : 
                        `${this.colors.downColor}40`;
                },
                type: 'bar',
                barPercentage: 0.4
            }
        ];
        
        // Add volume if enabled
        if (chartOptions.showVolume) {
            datasets.push({
                label: 'Volume',
                data: ohlcData.map(candle => ({
                    x: new Date(candle.time),
                    y: candle.volume
                })),
                backgroundColor: this.colors.volumeColor,
                type: 'bar',
                yAxisID: 'volume'
            });
        }
        
        // Create chart instance
        const chart = new Chart(container, {
            type: 'bar',
            data: {
                datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: chartOptions.title
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                const dataPoint = context.raw;
                                
                                if (dataPoint.o !== undefined) {
                                    return [
                                        `Open: $${dataPoint.o.toLocaleString()}`,
                                        `High: $${dataPoint.h.toLocaleString()}`,
                                        `Low: $${dataPoint.l.toLocaleString()}`,
                                        `Close: $${dataPoint.c.toLocaleString()}`
                                    ];
                                } else if (context.dataset.label === 'Volume') {
                                    return `Volume: $${dataPoint.y.toLocaleString()}`;
                                }
                                
                                return context.dataset.label + ': ' + dataPoint.y;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: chartOptions.timeUnit
                        }
                    },
                    y: {
                        grid: {
                            color: this.colors.gridColor
                        },
                        position: 'right',
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    },
                    volume: {
                        position: 'left',
                        grid: {
                            drawOnChartArea: false
                        },
                        ticks: {
                            callback: function(value) {
                                return this.getLabelForValue(value).substring(0, 3) + 'M';
                            }
                        },
                        display: chartOptions.showVolume
                    }
                }
            }
        });
        
        return chart;
    }
    
    /**
     * Create a market depth chart
     * @param {HTMLElement} container - Container element
     * @param {Object} data - Chart data
     * @param {Object} options - Chart options
     * @returns {Object} - Chart instance
     */
    createMarketDepthChart(container, data, options = {}) {
        // Format data for market depth chart
        const { bids, asks } = this.formatMarketDepthData(data);
        
        // Set default options
        const defaultOptions = {
            title: 'Market Depth',
            maxDepth: 100000 // Maximum depth to show
        };
        
        // Merge options
        const chartOptions = { ...defaultOptions, ...options };
        
        // Create chart
        const chart = new Chart(container, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'Bids',
                        data: bids,
                        borderColor: this.colors.secondary,
                        backgroundColor: `${this.colors.secondary}20`,
                        borderWidth: 2,
                        fill: true,
                        stepped: true
                    },
                    {
                        label: 'Asks',
                        data: asks,
                        borderColor: this.colors.danger,
                        backgroundColor: `${this.colors.danger}20`,
                        borderWidth: 2,
                        fill: true,
                        stepped: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: chartOptions.title
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.raw.y;
                                return `${label}: ${value.toLocaleString()} @ $${context.raw.x.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        title: {
                            display: true,
                            text: 'Price (USD)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Cumulative Size'
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
        
        return chart;
    }
    
    /**
     * Create a correlation heatmap
     * @param {HTMLElement} container - Container element
     * @param {Object} data - Chart data
     * @param {Object} options - Chart options
     * @returns {Object} - Chart instance
     */
    createCorrelationHeatmap(container, data, options = {}) {
        // Format data for correlation heatmap
        const { labels, values } = this.formatCorrelationData(data);
        
        // Set default options
        const defaultOptions = {
            title: 'Cryptocurrency Correlation Heatmap'
        };
        
        // Merge options
        const chartOptions = { ...defaultOptions, ...options };
        
        // Create datasets for heatmap
        const datasets = [];
        
        // Create a dataset for each row of the correlation matrix
        for (let i = 0; i < values.length; i++) {
            const rowData = [];
            
            // For each column in this row
            for (let j = 0; j < values[i].length; j++) {
                rowData.push({
                    x: labels[j],
                    y: labels[i],
                    v: values[i][j]
                });
            }
            
            datasets.push({
                label: labels[i],
                data: rowData
            });
        }
        
        // Create chart
        const chart = new Chart(container, {
            type: 'matrix',
            data: {
                datasets: [
                    {
                        label: 'Correlation',
                        data: this.flattenCorrelationMatrix(labels, values),
                        backgroundColor: context => this.getCorrelationColor(context.dataset.data[context.dataIndex].v),
                        borderColor: '#ffffff',
                        borderWidth: 1,
                        width: ({ chart }) => (chart.chartArea || {}).width / labels.length - 1,
                        height: ({ chart }) => (chart.chartArea || {}).height / labels.length - 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: chartOptions.title
                    },
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                return `${context[0].raw.x} vs ${context[0].raw.y}`;
                            },
                            label: function(context) {
                                const value = context.raw.v;
                                return `Correlation: ${value.toFixed(2)}`;
                            }
                        }
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        labels: labels,
                        ticks: {
                            autoSkip: false,
                            maxRotation: 90,
                            minRotation: 45
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        type: 'category',
                        labels: labels,
                        offset: true,
                        ticks: {
                            autoSkip: false
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
        
        return chart;
    }
    
    /**
     * Create a performance comparison chart
     * @param {HTMLElement} container - Container element
     * @param {Object} data - Chart data
     * @param {Object} options - Chart options
     * @returns {Object} - Chart instance
     */
    createPerformanceChart(container, data, options = {}) {
        // Format data for performance chart
        const { labels, datasets } = this.formatPerformanceData(data);
        
        // Set default options
        const defaultOptions = {
            title: 'Strategy Performance Comparison',
            timeUnit: 'day',
            showBaseline: true,
            baseline: 'S&P 500'
        };
        
        // Merge options
        const chartOptions = { ...defaultOptions, ...options };
        
        // Add baseline if enabled
        if (chartOptions.showBaseline && data.baseline) {
            datasets.push({
                label: chartOptions.baseline,
                data: data.baseline.map(item => ({
                    x: new Date(item.time),
                    y: item.value
                })),
                borderColor: this.colors.gray,
                backgroundColor: 'transparent',
                borderWidth: 2,
                borderDash: [5, 5],
                fill: false
            });
        }
        
        // Create chart
        const chart = new Chart(container, {
            type: 'line',
            data: {
                labels,
                datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: chartOptions.title
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: chartOptions.timeUnit
                        },
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Return (%)'
                        },
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
        
        return chart;
    }
    
    /**
     * Format OHLC data for candlestick chart
     * @param {Array} data - Raw OHLC data
     * @returns {Array} - Formatted OHLC data
     */
    formatOHLCData(data) {
        // If data is already in the right format, return it
        if (data && data.length > 0 && data[0].open !== undefined) {
            return data;
        }
        
        // If we have price data, convert it to OHLC format
        if (data && data.prices && data.prices.length > 0) {
            const ohlcData = [];
            const volumeData = data.total_volumes || [];
            
            let currentDay = null;
            let candle = null;
            
            // Group by day and create daily candles
            data.prices.forEach((price, index) => {
                const time = new Date(price.time);
                const day = time.toISOString().split('T')[0];
                const value = price.value;
                
                if (day !== currentDay) {
                    // Start a new candle
                    if (candle) {
                        ohlcData.push(candle);
                    }
                    
                    // Find the volume for this time
                    let volume = 0;
                    if (volumeData[index]) {
                        volume = volumeData[index].value;
                    }
                    
                    currentDay = day;
                    candle = {
                        time: time.toISOString(),
                        open: value,
                        high: value,
                        low: value,
                        close: value,
                        volume
                    };
                } else {
                    // Update existing candle
                    candle.high = Math.max(candle.high, value);
                    candle.low = Math.min(candle.low, value);
                    candle.close = value;
                    
                    // Add volume if available
                    if (volumeData[index]) {
                        candle.volume += volumeData[index].value;
                    }
                }
            });
            
            // Add the last candle
            if (candle) {
                ohlcData.push(candle);
            }
            
            return ohlcData;
        }
        
        // Default empty data
        return [];
    }
    
    /**
     * Format market depth data
     * @param {Object} data - Raw market depth data
     * @returns {Object} - Formatted market depth data
     */
    formatMarketDepthData(data) {
        const bids = [];
        const asks = [];
        
        if (!data || !data.bids || !data.asks) {
            return { bids, asks };
        }
        
        // Process bids
        let bidVolume = 0;
        for (const [price, volume] of data.bids) {
            bidVolume += volume;
            bids.push({ x: parseFloat(price), y: bidVolume });
        }
        
        // Sort bids by price (descending)
        bids.sort((a, b) => b.x - a.x);
        
        // Process asks
        let askVolume = 0;
        for (const [price, volume] of data.asks) {
            askVolume += volume;
            asks.push({ x: parseFloat(price), y: askVolume });
        }
        
        // Sort asks by price (ascending)
        asks.sort((a, b) => a.x - b.x);
        
        return { bids, asks };
    }
    
    /**
     * Format correlation data
     * @param {Object} data - Raw correlation data
     * @returns {Object} - Formatted correlation data
     */
    formatCorrelationData(data) {
        const labels = [];
        const values = [];
        
        if (!data || !data.length) {
            return { labels, values };
        }
        
        // Extract unique symbols
        data.forEach(item => {
            if (!labels.includes(item.symbol)) {
                labels.push(item.symbol);
            }
        });
        
        // Initialize correlation matrix with 1's on diagonal
        for (let i = 0; i < labels.length; i++) {
            values[i] = new Array(labels.length).fill(0);
            values[i][i] = 1; // Perfect correlation with self
        }
        
        // Fill correlation values
        data.forEach(item => {
            const sourceIndex = labels.indexOf(item.symbol);
            
            // Skip if symbol not found
            if (sourceIndex === -1) return;
            
            // Fill correlation with target coins
            item.correlations.forEach(corr => {
                const targetIndex = labels.indexOf(corr.symbol);
                
                if (targetIndex !== -1) {
                    values[sourceIndex][targetIndex] = corr.correlation_score;
                    values[targetIndex][sourceIndex] = corr.correlation_score; // Symmetrical
                }
            });
        });
        
        return { labels, values };
    }
    
    /**
     * Format performance data
     * @param {Object} data - Raw performance data
     * @returns {Object} - Formatted performance data
     */
    formatPerformanceData(data) {
        const labels = [];
        const datasets = [];
        
        if (!data || !data.strategies) {
            return { labels, datasets };
        }
        
        // Process each strategy
        Object.entries(data.strategies).forEach(([name, strategy], index) => {
            if (!strategy.returns || !strategy.returns.length) return;
            
            // Convert returns to percentage points
            const returns = strategy.returns.map((item, i) => {
                const time = new Date(item.time);
                if (i === 0) time.setHours(0, 0, 0, 0);
                
                // Add time to labels if not already present
                const timeStr = time.toISOString();
                if (!labels.includes(timeStr)) {
                    labels.push(timeStr);
                }
                
                return {
                    x: time,
                    y: item.value
                };
            });
            
            // Create dataset for this strategy
            datasets.push({
                label: name,
                data: returns,
                borderColor: this.getColorFromIndex(index),
                backgroundColor: 'transparent',
                borderWidth: 2,
                fill: false
            });
        });
        
        // Sort labels chronologically
        labels.sort();
        
        return { labels, datasets };
    }
    
    /**
     * Flatten correlation matrix for Chart.js matrix chart
     * @param {Array} labels - Labels for matrix
     * @param {Array} values - Correlation matrix values
     * @returns {Array} - Flattened data points
     */
    flattenCorrelationMatrix(labels, values) {
        const data = [];
        
        for (let i = 0; i < labels.length; i++) {
            for (let j = 0; j < labels.length; j++) {
                data.push({
                    x: labels[j],
                    y: labels[i],
                    v: values[i][j]
                });
            }
        }
        
        return data;
    }
    
    /**
     * Get color for correlation value
     * @param {number} correlation - Correlation value (-1 to 1)
     * @returns {string} - Color string
     */
    getCorrelationColor(correlation) {
        // Map correlation from -1...1 to 0...4 (index in colors array)
        const index = Math.round((correlation + 1) * 2);
        return this.colors.correlationColors[index] || this.colors.correlationColors[2];
    }
    
    /**
     * Get color from index
     * @param {number} index - Color index
     * @returns {string} - Color string
     */
    getColorFromIndex(index) {
        const colors = [
            this.colors.primary,
            this.colors.secondary,
            this.colors.warning,
            this.colors.danger,
            '#8b5cf6', // Purple
            '#ec4899', // Pink
            '#14b8a6', // Teal
            '#f97316', // Orange
            '#84cc16', // Lime
            '#0ea5e9'  // Sky blue
        ];
        
        return colors[index % colors.length];
    }
    
    /**
     * Create a gradient color
     * @param {CanvasRenderingContext2D} ctx - Canvas context
     * @param {Array} colors - Array of colors
     * @returns {CanvasGradient} - Canvas gradient
     */
    createGradient(ctx, colors) {
        const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
        
        colors.forEach((color, index) => {
            gradient.addColorStop(index / (colors.length - 1), color);
        });
        
        return gradient;
    }
}

// Create a singleton instance
const chartManager = new ChartManager();

// Export the instance
window.chartManager = chartManager;
