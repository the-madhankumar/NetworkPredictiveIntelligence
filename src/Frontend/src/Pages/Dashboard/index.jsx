import { useState } from "react";
import NetworkSummary from "../../components/NetworkSummary";
import GridActivity from "../../components/NetworkGrid"; 

import './index.css';
import HotspotsAndAlerts from "../../components/HotspotAndGrid";
import PredictSummary from "../../components/Predict";

function Dashboard() {
  const [selectedGridId, setSelectedGridId] = useState(1);
  const [activeTab, setActiveTab] = useState("summary");

  return (
    <div className="dashboard-container" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <nav className="dashboard-nav">
        <div>Telecom Dashboard</div>
        <button
          className={`nav-tab ${activeTab === "summary" ? "active" : ""}`}
          onClick={() => setActiveTab("summary")}
        >
          Network Summary
        </button>
        <button
          className={`nav-tab ${activeTab === "grid" ? "active" : ""}`}
          onClick={() => setActiveTab("grid")}
        >
          Grid Activity
        </button>

        <button
          className={`nav-tab ${activeTab === "hotspot" ? "active" : ""}`}
          onClick={() => setActiveTab("hotspot")}
        >
          Hotspot And Alerts
        </button>

        <button
          className={`nav-tab ${activeTab === "predict" ? "active" : ""}`}
          onClick={() => setActiveTab("predict")}
        >
          Prediction
        </button>
      </nav>

      <div className="dashboard-content">
        {activeTab === "summary" && <NetworkSummary />}
        {activeTab === "grid" && (
          <GridActivity initialGridId={selectedGridId} />
        )}
        {activeTab === "hotspot" && (
          <HotspotsAndAlerts />
        )}
        {activeTab === "predict" && (
          <PredictSummary />
        )}
      </div>
    </div>
  );
}

export default Dashboard;