"use client";

import { useEffect, useState } from "react";
import { fetchJson } from "../../lib/apiClient";

export default function ApiKeysPage() {
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Generate State
  const [generateModalOpen, setGenerateModalOpen] = useState(false);
  const [keyName, setKeyName] = useState("");
  const [newlyGeneratedKey, setNewlyGeneratedKey] = useState<string | null>(null);

  // Revoke State
  const [revokeId, setRevokeId] = useState<number | null>(null);
  const [revokeName, setRevokeName] = useState("");

  const loadApiKeys = async () => {
    setLoading(true);
    try {
      const response = await fetchJson<any>("/auth/api-key");
      setApiKeys(Array.isArray(response) ? response : (response.data || []));
    } catch (error) {
      console.error("Failed to load API keys", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApiKeys();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetchJson(`/auth/api-key/generate?name=${encodeURIComponent(keyName)}`, {
        method: "POST"
      });
      setNewlyGeneratedKey(res.api_key);
      setKeyName("");
      loadApiKeys();
    } catch (error: any) {
      alert("Failed to generate API Key: " + error.message);
    }
  };

  const confirmRevoke = async () => {
    if (!revokeId) return;
    try {
      // Endpoint returns 204 No Content, our fetchJson is updated to handle it safely and return null
      await fetchJson(`/auth/api-key/${revokeId}`, { method: "DELETE" });
      setRevokeId(null);
      loadApiKeys();
    } catch (error: any) {
      alert("Failed to revoke API key: " + error.message);
    }
  };

  const closeGenerateModal = () => {
    setGenerateModalOpen(false);
    setNewlyGeneratedKey(null);
  };

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <div>
          <h1>API Keys</h1>
          <p style={{ color: "var(--text-muted)", marginTop: "0.5rem" }}>
            Manage integration keys for 3rd party apps or POS systems.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setGenerateModalOpen(true)}>+ Generate New Key</button>
      </div>

      <div className="glass-panel table-container">
        {loading ? (
          <div className="loading-state">Loading keys...</div>
        ) : (
          <table className="keys-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Created At</th>
                <th>Last Used At</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {apiKeys.map((k) => (
                <tr key={k.id}>
                  <td className="font-mono">#{k.id}</td>
                  <td className="font-medium">{k.name}</td>
                  <td style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
                    {new Date(k.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
                    {k.last_used_at ? new Date(k.last_used_at).toLocaleString() : "Never used"}
                  </td>
                  <td>
                    <span className={`status-badge ${k.is_active ? "active" : "inactive"}`}>
                      {k.is_active ? "Active" : "Revoked"}
                    </span>
                  </td>
                  <td>
                    {k.is_active && (
                      <button 
                        className="action-btn" 
                        title="Revoke Key"
                        onClick={() => { setRevokeId(k.id); setRevokeName(k.name); }}
                        style={{ background: "rgba(255,51,102,0.05)", border: "1px solid rgba(255,51,102,0.2)", color: "var(--danger)" }}
                      >
                        🚫 Revoke
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {apiKeys.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center empty-state">No API keys found.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Generate Key Modal */}
      {generateModalOpen && (
        <div className="modal-overlay" onClick={newlyGeneratedKey ? undefined : closeGenerateModal}>
          <div className="modal-content animate-fade-in" onClick={e => e.stopPropagation()}>
            {newlyGeneratedKey ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🔑</div>
                <h2 style={{ marginBottom: "1rem", color: "var(--success)" }}>Key Generated Successfully!</h2>
                <p style={{ color: "var(--text-muted)", marginBottom: "1rem" }}>
                  Please copy this key and store it somewhere safe. For security reasons, <strong>you will not be able to see it again!</strong>
                </p>
                <div style={{ background: "rgba(0,0,0,0.5)", padding: "1.5rem", borderRadius: "8px", border: "1px solid rgba(0, 255, 157, 0.3)", marginBottom: "2rem", wordBreak: "break-all", fontFamily: "monospace", color: "#fff", fontSize: "1.1rem" }}>
                  {newlyGeneratedKey}
                </div>
                <button type="button" className="btn btn-primary" onClick={closeGenerateModal} style={{ width: "100%" }}>
                  I have copied the key
                </button>
              </div>
            ) : (
              <>
                <h2 style={{ marginBottom: "1.5rem" }}>Generate API Key</h2>
                <form onSubmit={handleGenerate}>
                  <div className="form-group">
                    <label className="form-label">Key Name</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      placeholder="e.g. Android POS App" 
                      required 
                      autoFocus 
                      value={keyName} 
                      onChange={e => setKeyName(e.target.value)} 
                    />
                    <small style={{ color: "var(--text-muted)", marginTop: "0.5rem", display: "block" }}>
                      Give it a descriptive name so you know which app is using it.
                    </small>
                  </div>
                  <div className="modal-actions">
                    <button type="button" className="btn btn-outline" onClick={closeGenerateModal}>Cancel</button>
                    <button type="submit" className="btn btn-primary">Generate</button>
                  </div>
                </form>
              </>
            )}
          </div>
        </div>
      )}

      {/* Revoke Confirmation Modal */}
      {revokeId && (
        <div className="modal-overlay" onClick={() => setRevokeId(null)}>
          <div className="modal-content animate-fade-in" onClick={e => e.stopPropagation()} style={{ maxWidth: "400px", textAlign: "center" }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🚫</div>
            <h2 style={{ marginBottom: "1rem", color: "var(--danger)" }}>Revoke Key?</h2>
            <p style={{ color: "var(--text-muted)", marginBottom: "2rem", lineHeight: "1.5" }}>
              Are you sure you want to revoke <strong>{revokeName}</strong>? 
              <br/><br/>
              Any application currently using this key will lose access immediately. This action cannot be undone.
            </p>
            <div className="modal-actions" style={{ justifyContent: "center", marginTop: 0 }}>
              <button type="button" className="btn btn-outline" onClick={() => setRevokeId(null)}>Cancel</button>
              <button type="button" className="btn btn-danger" onClick={confirmRevoke}>Yes, Revoke</button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 2rem;
        }

        .table-container {
          overflow-x: auto;
          padding: 1rem;
        }

        .keys-table {
          width: 100%;
          border-collapse: collapse;
          text-align: left;
        }

        .keys-table th {
          padding: 1rem;
          color: var(--text-muted);
          font-weight: 500;
          border-bottom: 1px solid var(--glass-border);
        }

        .keys-table td {
          padding: 1rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.02);
          color: var(--text-main);
          vertical-align: middle;
        }

        .keys-table tbody tr:hover {
          background: rgba(255, 255, 255, 0.03);
        }

        .font-mono {
          font-family: monospace;
          color: var(--text-muted);
        }

        .font-medium {
          font-weight: 500;
          font-size: 1.05rem;
        }

        .status-badge {
          display: inline-block;
          padding: 0.25rem 0.6rem;
          border-radius: 6px;
          font-weight: 600;
          font-size: 0.8rem;
        }

        .status-badge.active {
          background: rgba(0, 255, 157, 0.1);
          color: var(--success);
          border: 1px solid rgba(0, 255, 157, 0.2);
        }

        .status-badge.inactive {
          background: rgba(255, 255, 255, 0.05);
          color: var(--text-muted);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .action-btn {
          padding: 0.4rem 0.8rem;
          border-radius: 6px;
          font-size: 0.85rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .action-btn:hover {
          filter: brightness(1.2);
        }

        .loading-state, .empty-state {
          padding: 3rem;
          text-align: center;
          color: var(--text-muted);
        }

        /* Modal Styles */
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          backdrop-filter: blur(5px);
          display: flex;
          align-items: flex-start;
          justify-content: center;
          z-index: 1000;
          padding: 3rem 1rem;
          overflow-y: auto;
        }

        .modal-content {
          width: 100%;
          max-width: 450px;
          padding: 2.5rem;
          margin: auto;
          background: #151823;
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 16px;
          box-shadow: 0 10px 40px rgba(0,0,0, 0.5);
        }

        .modal-actions {
          display: flex;
          justify-content: flex-end;
          gap: 1rem;
          margin-top: 2rem;
        }
      `}</style>
    </div>
  );
}
