import './index.css';
import { useEffect, useState } from 'react';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';

import { getPredict, getPredictionExplanation } from '../../api/predict';

function PredictSummary() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [asOfParam, setAsOf] = useState('');
  const [gridIdParam, setGridId] = useState(1);
  const [error, setError] = useState(null);

  const [explanationModalOpen, setExplanationModalOpen] = useState(false);
  const [explanationLoading, setExplanationLoading] = useState(false);
  const [explanationResult, setExplanationResult] = useState(null);
  const [explanationError, setExplanationError] = useState(null);

  const fetchSummary = async (gridId, asOf = null) => {
    setLoading(true);
    setError(null);

    try {
      const data = await getPredict(gridId, asOf || null);

      if (data?.error) {
        setError(data.message || 'Failed to load prediction summary.');
        setSummary(null);
      } else {
        setSummary(data);
      }
    } catch (err) {
      setError(err?.message || 'Failed to load prediction summary.');
      setSummary(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary(gridIdParam, asOfParam);
  }, [asOfParam, gridIdParam]);

  // Handler for the "Explain Prediction" AI Route
  const handleExplainPrediction = async () => {
    if (!summary) return;

    setExplanationModalOpen(true);
    setExplanationLoading(true);
    setExplanationError(null);
    setExplanationResult(null);

    try {
      const payload = {
        grid_id: gridIdParam,
        as_of: asOfParam || new Date().toISOString(),
        risk_score: summary.risk_score,
        risk_level: summary.risk_level,
        model_version: summary.model_version,
        explanation_note: summary.explanation_note,
      };

      const result = await getPredictionExplanation(payload);
      setExplanationResult(result);
    } catch (err) {
      setExplanationError(err.message || 'Unable to retrieve explanation.');
    } finally {
      setExplanationLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="progress-wrapper">
          <CircularProgressbar
            value={75}
            text="Loading"
            styles={buildStyles({
              rotation: 0.25,
              strokeLinecap: 'round',
              textSize: '12px',
              pathTransitionDuration: 1.5,
              pathColor: 'currentColor',
              textColor: 'currentColor',
              trailColor: '#e5e7eb',
            })}
          />
        </div>
        <p className="loading-text">Loading prediction summary...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <div className="error-icon">!</div>
        <h2>Unable to load network summary</h2>
        <p>{error}</p>
        <button
          className="retry-button"
          onClick={() => fetchSummary(gridIdParam, asOfParam)}
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="error-container">
        <h2>No data available</h2>
        <button
          className="retry-button"
          onClick={() => fetchSummary(gridIdParam, asOfParam)}
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="network-summary">
      <div className="summary-header">
        <div>
          <h1>Prediction Summary</h1>
          <p>Overview of Grid #{gridIdParam} Prediction</p>
        </div>

        <div className="filter-controls">
          <div className="as-of-section">
            <label htmlFor="grid_id">Grid ID</label>
            <input
              id="grid_id"
              type="number"
              min="1"
              value={gridIdParam}
              onChange={(e) => setGridId(Number(e.target.value) || 1)}
            />
          </div>

          <div className="as-of-section">
            <label htmlFor="as-of">As of</label>
            <input
              id="as-of"
              type="datetime-local"
              value={asOfParam}
              onChange={(e) => setAsOf(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="summary-grid">
        <div className="summary-card">
          <div className="card-title">Risk Score</div>
          <div className="card-value">{summary.risk_score ?? 'N/A'}</div>
          <div className="card-description">Risk score for current grid</div>
        </div>

        <div className="summary-card">
          <div className="card-title">Risk Level</div>
          <div className={`card-value risk-badge ${summary.risk_level?.toLowerCase()}`}>
            {summary.risk_level ?? 'N/A'}
          </div>
          <div className="card-description">Risk level for current grid</div>
        </div>

        <div className="summary-card">
          <div className="card-title">Model Version</div>
          <div className="card-value">{summary.model_version ?? 'N/A'}</div>
          <div className="card-description">ML Model Version</div>
        </div>

        <div className="summary-card">
          <div className="card-title">Explanation Note</div>
          <div className="card-value text-sm">{summary.explanation_note || 'None provided'}</div>
          <div className="card-description">Raw model notes</div>
        </div>
      </div>

      {/* Primary Action Button to trigger AI Explanation */}
      <div className="actions-bar">
        <button className="explain-btn" onClick={handleExplainPrediction}>
          ✨ Explain This Prediction
        </button>
      </div>

      {/* AI Explanation Drawer / Modal */}
      {explanationModalOpen && (
        <div className="modal-overlay" onClick={() => setExplanationModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>🤖 AI Prediction Analysis</h2>
              <button className="close-btn" onClick={() => setExplanationModalOpen(false)}>
                &times;
              </button>
            </div>

            <div className="modal-body">
              {explanationLoading && (
                <div className="modal-loading">
                  <span className="spinner"></span>
                  <p>Analyzing risk prediction for Grid #{gridIdParam}...</p>
                </div>
              )}

              {explanationError && (
                <div className="modal-error">
                  <p>⚠️ {explanationError}</p>
                </div>
              )}

              {explanationResult && (
                <div className="explanation-details">
                  <div className="explanation-meta">
                    <span><strong>Grid ID:</strong> #{explanationResult.grid_id}</span>
                    <span><strong>Risk:</strong> {explanationResult.risk_level?.toUpperCase()}</span>
                  </div>
                  <div className="explanation-text">
                    <h3>Operational Assessment:</h3>
                    <p>{explanationResult.explanation}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default PredictSummary;