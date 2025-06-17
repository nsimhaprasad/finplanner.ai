import React from 'react';
import './PortfolioAnalysis.css';

interface AnalysisData {
  asset_allocation: Record<string, number>;
  sector_concentration: Record<string, number>;
  recommendations: string[];
}

interface PortfolioAnalysisProps {
  analysis: AnalysisData;
}

const PortfolioAnalysis: React.FC<PortfolioAnalysisProps> = ({ analysis }) => {
  const renderChart = (data: Record<string, number> | undefined, title: string) => {
    // Handle undefined/null data
    if (!data || Object.keys(data).length === 0) {
      return (
        <div className="chart-container">
          <h4>{title}</h4>
          <div className="chart">
            <p>No data available</p>
          </div>
        </div>
      );
    }

    const total = Object.values(data).reduce((sum, value) => sum + value, 0);
    
    return (
      <div className="chart-container">
        <h4>{title}</h4>
        <div className="chart">
          {Object.entries(data).map(([key, value]) => {
            const percentage = total > 0 ? (value / total) * 100 : 0;
            return (
              <div key={key} className="chart-item">
                <div className="chart-label">
                  <span className="label-text">{key}</span>
                  <span className="label-value">{value.toFixed(1)}%</span>
                </div>
                <div className="chart-bar">
                  <div 
                    className="chart-fill" 
                    style={{ width: `${percentage}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="portfolio-analysis">
      <h2>Portfolio Analysis</h2>
      
      <div className="analysis-grid">
        <div className="analysis-section">
          {renderChart(analysis.asset_allocation, "Asset Allocation")}
        </div>
        
        <div className="analysis-section">
          {renderChart(analysis.sector_concentration, "Sector Concentration")}
        </div>
      </div>

      <div className="recommendations-section">
        <h3>Recommendations</h3>
        <ul className="recommendations-list">
          {analysis.recommendations && analysis.recommendations.length > 0 ? (
            analysis.recommendations.map((recommendation, index) => (
              <li key={index} className="recommendation-item">
                <span className="recommendation-icon">💡</span>
                {recommendation}
              </li>
            ))
          ) : (
            <li className="recommendation-item">
              <span className="recommendation-icon">ℹ️</span>
              No recommendations available
            </li>
          )}
        </ul>
      </div>
    </div>
  );
};

export default PortfolioAnalysis;