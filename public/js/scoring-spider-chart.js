/**
 * Interactive Spider/Radar Chart for EP Scoring Weights
 */

class ScoringSpiderChart {
    constructor(canvasId, containerId) {
        this.canvas = document.getElementById(canvasId);
        this.container = document.getElementById(containerId);
        this.chart = null;
        
        // Default weights from scoring system
        this.axisWeights = {
            "legislative_production": 0.40,
            "control_transparency": 0.15,
            "engagement_presence": 0.25,
            "institutional_roles": 0.20
        };
        
        this.axisLabels = {
            "legislative_production": "Legislative Production",
            "control_transparency": "Control & Transparency",
            "engagement_presence": "Engagement & Presence",
            "institutional_roles": "Institutional Roles"
        };
        
        // Callbacks
        this.onWeightChange = null;
        
        this.initChart();
        this.createControls();
    }
    
    initChart() {
        const ctx = this.canvas.getContext('2d');
        
        this.chart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: Object.values(this.axisLabels),
                datasets: [{
                    label: 'Current Weights',
                    data: Object.values(this.axisWeights),
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    borderColor: 'rgba(59, 130, 246, 0.8)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(59, 130, 246, 1)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
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
                                const label = context.label;
                                const value = (context.raw * 100).toFixed(1);
                                return `${label}: ${value}%`;
                            }
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 1.0,
                        min: 0,
                        ticks: {
                            stepSize: 0.2,
                            callback: function(value) {
                                return (value * 100) + '%';
                            },
                            font: {
                                size: 10
                            }
                        },
                        pointLabels: {
                            font: {
                                size: 11,
                                weight: 'bold'
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                interaction: {
                    intersect: true
                }
            }
        });
    }
    
    createControls() {
        const controlsHtml = `
            <div class="spider-controls mt-4">
                <h4 class="text-sm font-semibold text-gray-700 mb-3">Adjust Axis Weights</h4>
                <div class="space-y-3">
                    ${Object.entries(this.axisWeights).map(([key, value]) => `
                        <div class="weight-control">
                            <label class="flex items-center justify-between text-sm">
                                <span class="text-gray-600">${this.axisLabels[key]}</span>
                                <span class="weight-value font-mono text-gray-700" data-axis="${key}">
                                    ${(value * 100).toFixed(1)}%
                                </span>
                            </label>
                            <input 
                                type="range" 
                                min="0" 
                                max="1" 
                                step="0.01" 
                                value="${value}"
                                data-axis="${key}"
                                class="weight-slider w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer mt-1"
                            >
                        </div>
                    `).join('')}
                </div>
                <div class="mt-4 pt-3 border-t border-gray-200">
                    <div class="flex items-center justify-between text-sm">
                        <span class="text-gray-600">Total Weight:</span>
                        <span id="total-weight" class="font-mono font-semibold">100.0%</span>
                    </div>
                    <div class="mt-2 flex gap-2">
                        <button id="normalize-weights" class="px-3 py-1 bg-gray-100 text-gray-700 text-xs rounded hover:bg-gray-200 transition-colors">
                            Normalize to 100%
                        </button>
                        <button id="reset-weights" class="px-3 py-1 bg-gray-100 text-gray-700 text-xs rounded hover:bg-gray-200 transition-colors">
                            Reset to Default
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        this.container.insertAdjacentHTML('beforeend', controlsHtml);
        this.bindControlEvents();
    }
    
    bindControlEvents() {
        // Weight sliders
        const sliders = this.container.querySelectorAll('.weight-slider');
        sliders.forEach(slider => {
            slider.addEventListener('input', (e) => {
                const axis = e.target.dataset.axis;
                const value = parseFloat(e.target.value);
                this.updateWeight(axis, value);
            });
        });
        
        // Normalize button
        const normalizeBtn = this.container.querySelector('#normalize-weights');
        normalizeBtn.addEventListener('click', () => {
            this.normalizeWeights();
        });
        
        // Reset button
        const resetBtn = this.container.querySelector('#reset-weights');
        resetBtn.addEventListener('click', () => {
            this.resetWeights();
        });
    }
    
    updateWeight(axis, value) {
        this.axisWeights[axis] = value;
        
        // Update display
        const valueSpan = this.container.querySelector(`[data-axis="${axis}"].weight-value`);
        valueSpan.textContent = `${(value * 100).toFixed(1)}%`;
        
        // Update chart
        this.chart.data.datasets[0].data = Object.values(this.axisWeights);
        this.chart.update('none');
        
        // Update total weight display
        this.updateTotalWeight();
        
        // Trigger callback
        if (this.onWeightChange) {
            this.onWeightChange(this.axisWeights);
        }
    }
    
    updateTotalWeight() {
        const total = Object.values(this.axisWeights).reduce((sum, val) => sum + val, 0);
        const totalSpan = this.container.querySelector('#total-weight');
        totalSpan.textContent = `${(total * 100).toFixed(1)}%`;
        
        // Color coding based on how close to 100%
        if (Math.abs(total - 1.0) < 0.01) {
            totalSpan.className = 'font-mono font-semibold text-gray-800';
        } else if (Math.abs(total - 1.0) < 0.1) {
            totalSpan.className = 'font-mono font-semibold text-gray-700';
        } else {
            totalSpan.className = 'font-mono font-semibold text-gray-600';
        }
    }
    
    normalizeWeights() {
        const total = Object.values(this.axisWeights).reduce((sum, val) => sum + val, 0);
        
        if (total === 0) return;
        
        // Normalize all weights to sum to 1
        Object.keys(this.axisWeights).forEach(axis => {
            this.axisWeights[axis] = this.axisWeights[axis] / total;
            
            // Update sliders and displays
            const slider = this.container.querySelector(`[data-axis="${axis}"].weight-slider`);
            const valueSpan = this.container.querySelector(`[data-axis="${axis}"].weight-value`);
            
            slider.value = this.axisWeights[axis];
            valueSpan.textContent = `${(this.axisWeights[axis] * 100).toFixed(1)}%`;
        });
        
        // Update chart
        this.chart.data.datasets[0].data = Object.values(this.axisWeights);
        this.chart.update();
        
        this.updateTotalWeight();
        
        if (this.onWeightChange) {
            this.onWeightChange(this.axisWeights);
        }
    }
    
    resetWeights() {
        const defaultWeights = {
            "legislative_production": 0.40,
            "control_transparency": 0.15,
            "engagement_presence": 0.25,
            "institutional_roles": 0.20
        };
        
        Object.keys(defaultWeights).forEach(axis => {
            this.axisWeights[axis] = defaultWeights[axis];
            
            // Update sliders and displays
            const slider = this.container.querySelector(`[data-axis="${axis}"].weight-slider`);
            const valueSpan = this.container.querySelector(`[data-axis="${axis}"].weight-value`);
            
            slider.value = this.axisWeights[axis];
            valueSpan.textContent = `${(this.axisWeights[axis] * 100).toFixed(1)}%`;
        });
        
        // Update chart
        this.chart.data.datasets[0].data = Object.values(this.axisWeights);
        this.chart.update();
        
        this.updateTotalWeight();
        
        if (this.onWeightChange) {
            this.onWeightChange(this.axisWeights);
        }
    }
    
    setWeights(newWeights) {
        Object.keys(newWeights).forEach(axis => {
            if (axis in this.axisWeights) {
                this.axisWeights[axis] = newWeights[axis];
                
                // Update sliders and displays
                const slider = this.container.querySelector(`[data-axis="${axis}"].weight-slider`);
                const valueSpan = this.container.querySelector(`[data-axis="${axis}"].weight-value`);
                
                if (slider && valueSpan) {
                    slider.value = this.axisWeights[axis];
                    valueSpan.textContent = `${(this.axisWeights[axis] * 100).toFixed(1)}%`;
                }
            }
        });
        
        // Update chart
        this.chart.data.datasets[0].data = Object.values(this.axisWeights);
        this.chart.update();
        
        this.updateTotalWeight();
    }
    
    getWeights() {
        return { ...this.axisWeights };
    }
    
    destroy() {
        if (this.chart) {
            this.chart.destroy();
        }
    }
}

// CSS for custom slider styling
const sliderStyles = `
<style>
.weight-slider {
    background: linear-gradient(to right, #e2e8f0 0%, #e2e8f0 100%);
}

.weight-slider::-webkit-slider-thumb {
    appearance: none;
    height: 20px;
    width: 20px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
    border: 2px solid #ffffff;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.weight-slider::-moz-range-thumb {
    height: 20px;
    width: 20px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
    border: 2px solid #ffffff;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
</style>
`;

// Inject styles
document.head.insertAdjacentHTML('beforeend', sliderStyles);

// Make available globally for non-module scripts
window.ScoringSpiderChart = ScoringSpiderChart;

export default ScoringSpiderChart;