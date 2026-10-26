import { useCallback, useEffect, useState } from "react";
import { getPredictionHistory } from "../api/predictionHistory";
import { RefreshCw, Search, AlertCircle } from "lucide-react";

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export default function PredictionHistory() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [riskLevel, setRiskLevel] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const pageSize = 10;

  const loadHistory = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const params = { page, page_size: pageSize };
      if (riskLevel) params.risk_level = riskLevel;
      if (employeeId.trim()) params.employee_id = Number(employeeId);

      const response = await getPredictionHistory(params);
      setItems(response.data.items || []);
      setTotal(response.data.total || 0);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Could not load prediction history. Check your login and backend."
      );
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, riskLevel, employeeId]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  function applyFilters() {
    setPage(1);
    // The effect loads the updated page and filters.
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <section className="panel page-panel">
      <div className="panel-heading">
        <div>
          <h2>Prediction History</h2>
          <p>Saved attrition predictions returned by the backend.</p>
        </div>
        <button className="subtle-button" onClick={loadHistory} disabled={loading}>
          <RefreshCw size={15} /> Refresh
        </button>
      </div>

      <div className="table-actions" style={{ marginBottom: 16, flexWrap: "wrap" }}>
        <label>
          <span>Employee ID</span>
          <input
            type="number"
            min="1"
            placeholder="All employees"
            value={employeeId}
            onChange={(event) => {
              setEmployeeId(event.target.value);
              setPage(1);
            }}
          />
        </label>

        <label>
          <span>Risk level</span>
          <select
            value={riskLevel}
            onChange={(event) => {
              setRiskLevel(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All risk levels</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </label>
      </div>

      {error && (
        <div className="error-box" role="alert">
          <AlertCircle size={17} /> {error}
        </div>
      )}

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Prediction ID</th>
              <th>Employee ID</th>
              <th>Predicted Attrition</th>
              <th>Risk Level</th>
              <th>Risk Score</th>
              <th>Created At</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{item.id}</td>
                <td>{item.employee_id ?? "—"}</td>
                <td>{item.predicted_attrition ? "Yes" : "No"}</td>
                <td>
                  <span className={`risk-pill risk-${String(item.risk_level || "low").toLowerCase()}`}>
                    <i /> {item.risk_level || "Unknown"}
                  </span>
                </td>
                <td>{item.risk_score == null ? "—" : `${item.risk_score}%`}</td>
                <td>{formatDate(item.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {!loading && !error && items.length === 0 && (
          <div className="empty-state">No saved predictions found yet.</div>
        )}
        {loading && <div className="empty-state">Loading prediction history...</div>}
      </div>

      <div className="table-bottom">
        <span>{total} saved prediction(s)</span>
        <div className="table-actions">
          <button
            className="subtle-button"
            disabled={page <= 1 || loading}
            onClick={() => setPage((current) => current - 1)}
          >
            Previous
          </button>
          <span>Page {page} of {totalPages}</span>
          <button
            className="subtle-button"
            disabled={page >= totalPages || loading}
            onClick={() => setPage((current) => current + 1)}
          >
            Next
          </button>
        </div>
      </div>
    </section>
  );
}
