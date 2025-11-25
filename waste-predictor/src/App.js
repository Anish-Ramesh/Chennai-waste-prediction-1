import React, { useState, useEffect } from "react";
import "@fortawesome/fontawesome-free/css/all.css";
import "./App.css";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";

// Determine API base URL so it works both locally and when deployed.
// - When running with React dev server (port 3000), talk to Flask on http://127.0.0.1:5000
// - When served through Flask itself (port 5000, including Vercel), always use same-origin calls ("" base URL)
//   so requests hit the same host that served index.html.
const getApiBaseUrl = () => {
  const { port } = window.location;

  // React dev server
  if (process.env.NODE_ENV === 'development' || port === '3000') {
    return "http://127.0.0.1:5000";
  }

  // Served by Flask (local run or Vercel): use same origin
  return "";
};

const API_BASE_URL = getApiBaseUrl();
console.log("Using API base URL:", API_BASE_URL); // Debug log

const PIE_COLORS = [
  "#047857",
  "#0ea5e9",
  "#f97316",
  "#6366f1",
  "#22c55e",
  "#eab308",
  "#ec4899",
  "#14b8a6",
  "#a855f7",
  "#f59e0b"
];

function App() {
  const [totalHouseholds, setTotalHouseholds] = useState("");
  const [coveredHouseholds, setCoveredHouseholds] = useState("");
  const [zoneName, setZoneName] = useState("Thiruvotriyur");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);
  const [isLoadingDashboard, setIsLoadingDashboard] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/dashboard`);
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.error || "Failed to load dashboard data");
        }
        setDashboardData(data);
      } catch (err) {
        console.error("Dashboard load error", err);
      } finally {
        setIsLoadingDashboard(false);
      }
    };

    fetchDashboard();
  }, []);

  const handlePredict = async () => {
    setError('');
    setResult(null);
    setIsLoading(true);

    try {
      // Convert inputs to numbers and validate
      const total = Number(totalHouseholds);
      const covered = Number(coveredHouseholds);
      
      if (isNaN(total) || isNaN(covered) || total <= 0 || covered < 0 || covered > total) {
        throw new Error('Please enter valid household numbers');
      }

      const response = await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          total_households: total,
          covered_households: covered,
          zone_name: zoneName
        })
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Prediction failed');
      }
      
      setResult(data.prediction);
    } catch (err) {
      setError(err.message || 'An error occurred. Please try again.');
      console.error('Prediction error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <div className="app-container">
        <header className="app-header">
          <div className="app-header-accent" />
          <div className="app-header-inner">
            <div className="app-header-text">
              <div className="app-pill">
                <span className="app-pill-dot" />
                Smart Waste Management
              </div>
              <h1 className="app-title">
                Greater Chennai Corporation
              </h1>
              <p className="app-subtitle">
                Live intelligence dashboard for household coverage and source segregation across city zones.
              </p>
            </div>
            {dashboardData?.city_totals && (
              <div className="city-snapshot">
                <div className="city-snapshot-header">
                  <span className="city-snapshot-title">City-wide snapshot</span>
                  <span className="city-snapshot-pill">
                    <i className="fas fa-leaf" />
                    Updated
                  </span>
                </div>
                <div className="city-snapshot-stat">
                  <p className="label">Total Households</p>
                  <p className="value">
                    {dashboardData.city_totals.Total_Households.toLocaleString()}
                  </p>
                </div>
                <div className="city-snapshot-stat">
                  <p className="label">Covered</p>
                  <p className="value accent">
                    {dashboardData.city_totals.Covered_Households.toLocaleString()}
                  </p>
                </div>
                <div className="city-snapshot-stat">
                  <p className="label">Segregated</p>
                  <p className="value accent-soft">
                    {dashboardData.city_totals.HH_Source_Segregation.toLocaleString()}
                  </p>
                </div>
                <div className="city-snapshot-stat">
                  <p className="label">Segregation Rate</p>
                  <p className="value accent-strong">
                    {dashboardData.city_totals.Segregation_Rate}%
                  </p>
                </div>
              </div>
            )}
          </div>
        </header>

        <div className="main-grid">
          {/* Prediction Panel */}
          <div className="panel panel-prediction">
            <h2 className="panel-title">
              <span className="panel-icon">
                <i className="fas fa-chart-line" />
              </span>
              <span>Zone-level Prediction</span>
            </h2>

            <p className="panel-description">
              Enter current household coverage for a zone to estimate segregation performance and projected participating households.
            </p>

            <div className="panel-form">
              <div>
                <label className="field-label">
                  Total Households
                </label>
                <input
                  type="number"
                  value={totalHouseholds}
                  onChange={(e) => setTotalHouseholds(e.target.value)}
                  placeholder="e.g., 1000"
                  className="field-input"
                />
              </div>

              <div>
                <label className="field-label">
                  Covered Households
                </label>
                <input
                  type="number"
                  value={coveredHouseholds}
                  onChange={(e) => setCoveredHouseholds(e.target.value)}
                  placeholder="e.g., 800"
                  className="field-input"
                />
              </div>

              <div>
                <label className="field-label">
                  Zone
                </label>
                <select
                  value={zoneName}
                  onChange={(e) => setZoneName(e.target.value)}
                  className="field-select"
                >
                  <option value="Adyar">Adyar</option>
                  <option value="Alandur">Alandur</option>
                  <option value="Ambattur">Ambattur</option>
                  <option value="Anna Nagar">Anna Nagar</option>
                  <option value="Ayanavaram">Ayanavaram</option>
                  <option value="Besant Nagar">Besant Nagar</option>
                  <option value="Choolaimedu">Choolaimedu</option>
                  <option value="Egmore">Egmore</option>
                  <option value="Guindy">Guindy</option>
                  <option value="Kodambakkam">Kodambakkam</option>
                  <option value="Madhavaram">Madhavaram</option>
                  <option value="Manali">Manali</option>
                  <option value="Perungudi">Perungudi</option>
                  <option value="Royapuram">Royapuram</option>
                  <option value="Sholinganallur">Sholinganallur</option>
                  <option value="Teynampet">Teynampet</option>
                  <option value="Thiru Vi Ka Nagar">Thiru Vi Ka Nagar</option>
                  <option value="Thiruvikanagar">Thiruvikanagar</option>
                  <option value="Thiruvotriyur">Thiruvotriyur</option>
                  <option value="Tondiarpet">Tondiarpet</option>
                  <option value="Valasaravakkam">Valasaravakkam</option>
                  <option value="Velachery">Velachery</option>
                </select>
              </div>

              <button
                onClick={handlePredict}
                disabled={isLoading}
                className={`primary-button ${isLoading ? "primary-button-disabled" : ""}`}
              >
                <i className="fas fa-magic" />
                <span>{isLoading ? "Predicting..." : "Run Prediction"}</span>
              </button>

              {error && (
                <div className="error-box">
                  {error}
                </div>
              )}

              {result && (
                <div className="result-box">
                  <h3 className="result-title">
                    <i className="fas fa-seedling" />
                    Prediction Results
                  </h3>
                  <div className="result-body">
                    <div className="result-row">
                      <span className="label">Segregation Rate</span>
                      <span className="value accent">{result.segregation_rate}%</span>
                    </div>
                    <div className="result-row">
                      <span className="label">Predicted Households</span>
                      <span className="value">{result.predicted_households}</span>
                    </div>
                    <div className="result-footer">
                      Model used: <span className="mono">{result.model_used}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Dashboard charts */}
          <div className="panel panel-dashboard">
            <h2 className="panel-title">
              <span className="panel-icon">
                <i className="fas fa-chart-pie" />
              </span>
              <span>Zone-wise Segregation Overview</span>
            </h2>
            <p className="panel-description panel-description-muted">
              Explore how different zones contribute to overall household source segregation across the city.
            </p>

            {isLoadingDashboard && (
              <p className="panel-loading">Loading dashboard data...</p>
            )}

            {!isLoadingDashboard && dashboardData?.zones && (
              <div className="chart-wrapper">
                <ResponsiveContainer>
                  <PieChart>
                    <Pie
                      data={dashboardData.zones}
                      dataKey="HH_Source_Segregation"
                      nameKey="Zone_Name"
                      cx="50%"
                      cy="50%"
                      outerRadius={90}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {dashboardData.zones.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={PIE_COLORS[index % PIE_COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => value.toLocaleString()} />
                    <Legend verticalAlign="bottom" height={36} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}

            {!isLoadingDashboard && !dashboardData?.zones && (
              <p className="panel-error">Dashboard data not available.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
