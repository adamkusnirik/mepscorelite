/**
 * API client for the scoring system
 */

class ScoringAPI {
    constructor(baseUrl = `${window.location.protocol}//${window.location.host}:5001`) {
        this.baseUrl = baseUrl;
    }
    
    /**
     * Get MEP scores with optional custom weights
     */
    async getScores(term = 10, axisWeights = null, metricWeights = null) {
        try {
            const url = `${this.baseUrl}/api/score?term=${term}`;
            
            const options = {
                method: axisWeights || metricWeights ? 'POST' : 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            };
            
            if (axisWeights || metricWeights) {
                options.body = JSON.stringify({
                    axis_weights: axisWeights,
                    metric_weights: metricWeights
                });
            }
            
            const response = await fetch(url, options);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'API request failed');
            }
            
            return data;
            
        } catch (error) {
            console.error('Error fetching scores:', error);
            throw error;
        }
    }
    
    /**
     * Get current scoring configuration
     */
    async getScoringConfig() {
        try {
            const response = await fetch(`${this.baseUrl}/api/scoring-config`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Error fetching scoring config:', error);
            throw error;
        }
    }
    
    /**
     * Update scoring configuration
     */
    async updateScoringConfig(axisWeights = null, metricWeights = null) {
        try {
            const response = await fetch(`${this.baseUrl}/api/scoring-config`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    axis_weights: axisWeights,
                    metric_weights: metricWeights
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'API request failed');
            }
            
            return data;
            
        } catch (error) {
            console.error('Error updating scoring config:', error);
            throw error;
        }
    }
    
    /**
     * Check if scoring API is available
     */
    async checkHealth() {
        try {
            const response = await fetch(`${this.baseUrl}/api/scoring-config`, {
                method: 'GET',
                timeout: 3000
            });
            
            return response.ok;
            
        } catch (error) {
            return false;
        }
    }
}

// Create singleton instance
const scoringAPI = new ScoringAPI();

// Make available globally
window.ScoringAPI = ScoringAPI;
window.scoringAPI = scoringAPI;

export default scoringAPI;