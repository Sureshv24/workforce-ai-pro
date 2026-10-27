import { useCallback, useEffect, useState } from "react";
import { Database, Upload, RefreshCw, FileCheck2, AlertCircle } from "lucide-react";
import api from "../api/client";

const formatBytes = (bytes = 0) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

const getError = (error) => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message) {
    return `${detail.message}${detail.missing?.length ? ` Missing: ${detail.missing.join(", ")}` : ""}`;
  }
  return error?.message || "Something went wrong. Please try again.";
};

export default function DatasetManagement({ currentUser }) {
  const [datasets, setDatasets] = useState([]);
  const [file, setFile] = useState(null);
  const [validation, setValidation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const role = String(currentUser?.role || "").toUpperCase();
  const canManage = ["ADMIN", "HR"].includes(role);

  const loadDatasets = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await api.get("/datasets/");
      setDatasets(response.data?.items || []);
    } catch (err) {
      setError(getError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (canManage) loadDatasets();
    else setLoading(false);
  }, [canManage, loadDatasets]);

  const [trainingId, setTrainingId] = useState("");
  const [trainingResult, setTrainingResult] = useState(null);

  const trainDataset = async (dataset) => {
    const confirmed = window.confirm(
      `Train and activate the attrition model using ${dataset.name}? This replaces the model used for future predictions if training succeeds.`
    );
    if (!confirmed) return;

    setTrainingId(dataset.id);
    setTrainingResult(null);
    setError("");
    setNotice("");

    try {
      const response = await api.post(
        `/datasets/${encodeURIComponent(dataset.id)}/train`
      );
      setTrainingResult(response.data);
      setNotice(response.data.message || "Model training completed.");
    } catch (err) {
      setError(getError(err));
    } finally {
      setTrainingId("");
    }
  };
  const chooseFile = (event) => {
    const selected = event.target.files?.[0] || null;
    setFile(selected);
    setValidation(null);
    setError("");
    setNotice("");
  };

  const validateFile = async () => {
    if (!file) {
      setError("Choose a CSV file first.");
      return;
    }

    setValidating(true);
    setError("");
    setNotice("");
    setValidation(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await api.post("/datasets/validate", formData);
      setValidation(response.data);
      if (response.data.valid) {
        setNotice("Dataset validation completed successfully.");
      } else {
        setError("Please fix the dataset issues listed below before uploading.");
      }
    } catch (err) {
      setError(getError(err));
    } finally {
      setValidating(false);
    }
  };

  const uploadFile = async () => {
    if (!file) {
      setError("Choose a CSV file first.");
      return;
    }

    if (!validation?.valid) {
      setError("Validate the selected CSV successfully before uploading.");
      return;
    }

    setUploading(true);
    setError("");
    setNotice("");

    try {
      const formData = new FormData();
      formData.append("file", file);
      await api.post("/datasets/", formData);
      setNotice("Dataset uploaded successfully.");
      setFile(null);
      setValidation(null);
      const input = document.getElementById("dataset-csv-input");
      if (input) input.value = "";
      await loadDatasets();
    } catch (err) {
      setError(getError(err));
    } finally {
      setUploading(false);
    }
  };

  if (!canManage) {
    return (
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-800">
        <AlertCircle className="mb-2 h-6 w-6" />
        Dataset management is available to Admin and HR users only.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Dataset Management</h2>
          <p className="mt-1 text-sm text-slate-500">
            Manage employee attrition datasets used by the AI prediction platform.
          </p>
        </div>
        <button
          type="button"
          onClick={loadDatasets}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}
      {notice && (
        <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
          {notice}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <Database className="mb-3 h-6 w-6 text-indigo-600" />
          <p className="text-sm text-slate-500">Available datasets</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">{datasets.length}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <FileCheck2 className="mb-3 h-6 w-6 text-emerald-600" />
          <p className="text-sm text-slate-500">Valid datasets</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">
            {datasets.filter((item) => item.valid).length}
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <Database className="mb-3 h-6 w-6 text-violet-600" />
          <p className="text-sm text-slate-500">Total dataset rows</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">
            {datasets.reduce((total, item) => total + (item.rows || 0), 0).toLocaleString()}
          </p>
        </div>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
        <h3 className="text-lg font-bold text-slate-900">Upload employee dataset</h3>
        <p className="mt-1 text-sm text-slate-500">
          CSV only, maximum 10 MB. Required columns must match the current attrition model.
        </p>

        <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center">
          <input
            id="dataset-csv-input"
            type="file"
            accept=".csv,text/csv"
            onChange={chooseFile}
            className="block w-full rounded-xl border border-slate-200 p-2.5 text-sm text-slate-700 file:mr-3 file:rounded-lg file:border-0 file:bg-indigo-50 file:px-3 file:py-2 file:font-semibold file:text-indigo-700"
          />
          <button
            type="button"
            onClick={validateFile}
            disabled={!file || validating || uploading}
            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl border border-indigo-200 px-4 py-2.5 text-sm font-semibold text-indigo-700 hover:bg-indigo-50 disabled:opacity-50"
          >
            <FileCheck2 className="h-4 w-4" />
            {validating ? "Validating..." : "Validate CSV"}
          </button>
          <button
            type="button"
            onClick={uploadFile}
            disabled={!file || !validation?.valid || uploading || validating}
            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Upload className="h-4 w-4" />
            {uploading ? "Uploading..." : "Upload"}
          </button>
        </div>

        {file && (
          <p className="mt-3 text-sm text-slate-500">
            Selected: <span className="font-medium text-slate-700">{file.name}</span>
            {" · "}{formatBytes(file.size)}
          </p>
        )}

        {validation && (
          <div className={`mt-4 rounded-xl border p-4 ${validation.valid ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50"}`}>
            <p className="font-semibold text-slate-800">
              {validation.valid ? "CSV validation passed" : "CSV needs attention"}
            </p>
            <p className="mt-1 text-sm text-slate-600">
              {validation.rows} rows · {validation.columns} columns
            </p>
            {validation.issues?.length > 0 && (
              <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-amber-800">
                {validation.issues.map((issue, index) => <li key={index}>{issue}</li>)}
              </ul>
            )}
            {validation.missing_required_columns?.length > 0 && (
              <p className="mt-2 text-sm text-red-700">
                Missing columns: {validation.missing_required_columns.join(", ")}
              </p>
            )}
          </div>
        )}
      </section>

      {trainingResult && (
        <section className="rounded-2xl border border-indigo-200 bg-indigo-50 p-5">
          <h3 className="font-bold text-slate-900">Latest training result</h3>
          <p className="mt-2 text-sm text-slate-700">{trainingResult.message}</p>
          <div className="mt-3 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-white p-3">
              <p className="text-xs text-slate-500">Training rows</p>
              <p className="text-lg font-bold">{trainingResult.training_rows}</p>
            </div>
            <div className="rounded-xl bg-white p-3">
              <p className="text-xs text-slate-500">Evaluation rows</p>
              <p className="text-lg font-bold">{trainingResult.evaluation_rows}</p>
            </div>
            <div className="rounded-xl bg-white p-3">
              <p className="text-xs text-slate-500">Evaluation accuracy</p>
              <p className="text-lg font-bold">
                {typeof trainingResult.accuracy === "number"
                  ? `${(trainingResult.accuracy * 100).toFixed(1)}%`
                  : "N/A"}
              </p>
            </div>
          </div>
          <p className="mt-3 text-xs text-slate-600">
            Evaluation metrics are based on a held-out split of the selected dataset and do not guarantee real-world performance.
          </p>
        </section>
      )}
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-5 py-4">
          <h3 className="font-bold text-slate-900">Available datasets</h3>
        </div>
        {loading ? (
          <p className="p-6 text-sm text-slate-500">Loading datasets...</p>
        ) : datasets.length === 0 ? (
          <p className="p-6 text-sm text-slate-500">No datasets found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-5 py-3">Dataset</th>
                  <th className="px-5 py-3">Rows</th>
                  <th className="px-5 py-3">Columns</th>
                  <th className="px-5 py-3">File size</th>
                  <th className="px-5 py-3">Validation</th>
                  <th className="px-5 py-3">Type</th>
                  <th className="px-5 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {datasets.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50">
                    <td className="px-5 py-4">
                      <p className="font-semibold text-slate-800">{item.name}</p>
                      {item.uploaded_at && (
                        <p className="mt-1 text-xs text-slate-400">
                          Uploaded {new Date(item.uploaded_at).toLocaleString()}
                        </p>
                      )}
                    </td>
                    <td className="px-5 py-4 text-slate-600">{item.rows.toLocaleString()}</td>
                    <td className="px-5 py-4 text-slate-600">{item.columns}</td>
                    <td className="px-5 py-4 text-slate-600">{formatBytes(item.size_bytes)}</td>
                    <td className="px-5 py-4">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${item.valid ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>
                        {item.valid ? "Valid columns" : "Needs review"}
                      </span>
                      {item.missing_required_columns?.length > 0 && (
                        <p className="mt-1 max-w-xs text-xs text-red-600">
                          Missing: {item.missing_required_columns.join(", ")}
                        </p>
                      )}
                    </td>
                    <td className="px-5 py-4 text-slate-600">
                      {item.is_sample ? "Sample" : "Uploaded"}
                    </td>
                    <td className="px-5 py-4">
                      <button
                        type="button"
                        onClick={() => trainDataset(item)}
                        disabled={!item.valid || Boolean(trainingId)}
                        className="rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {trainingId === item.id ? "Training..." : "Train Model"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

