"use client";

import { useEffect, useState } from "react";
import { fetchJson } from "../../lib/apiClient";

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewNotesModal, setViewNotesModal] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"all" | "me">("all");

  const loadTransactions = async (bypassCache = false) => {
    setLoading(true);
    try {
      const endpoint = viewMode === "me" ? "/transactions/me?limit=100" : "/transactions?limit=100";
      const response = await fetchJson<any>(endpoint, bypassCache ? { cache: "no-store" } : undefined);
      setTransactions(Array.isArray(response) ? response : (response.data || []));
    } catch (error) {
      console.error("Failed to load transactions", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, [viewMode]);

  return (
    <>
      <div className="animate-fade-in">
        <div className="page-header" style={{ flexDirection: "column", alignItems: "flex-start", gap: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", width: "100%", alignItems: "center" }}>
            <h1>Transaction History</h1>
            <button className="btn btn-outline" onClick={() => loadTransactions(true)}>
              Refresh 🔄
            </button>
          </div>
          
          <div className="tabs">
            <button 
              className={`tab-btn ${viewMode === "all" ? "active" : ""}`}
              onClick={() => setViewMode("all")}
            >
              All Transactions
            </button>
            <button 
              className={`tab-btn ${viewMode === "me" ? "active" : ""}`}
              onClick={() => setViewMode("me")}
            >
              My Transactions
            </button>
          </div>
        </div>

      <div className="glass-panel table-container">
        {loading ? (
          <div className="loading-state">Loading transactions...</div>
        ) : transactions.length === 0 ? (
          <div className="empty-state">No transactions recorded yet.</div>
        ) : (
          <table className="inventory-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Item ID</th>
                <th>Quantity</th>
                <th>Reference No.</th>
                <th>Notes</th>
                <th>User ID</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((trx) => (
                <tr key={trx.id}>
                  <td style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
                    {new Date(trx.created_at).toLocaleString()}
                  </td>
                  <td>
                    <span className={`type-badge ${trx.transaction_type.toLowerCase()}`}>
                      {trx.transaction_type}
                    </span>
                  </td>
                  <td className="font-mono">#{trx.item_id}</td>
                  <td style={{ fontWeight: 600 }}>
                    {trx.transaction_type === "IN" ? "+" : "-"}{trx.quantity}
                  </td>
                  <td className="font-mono">{trx.reference_number || "-"}</td>
                  <td 
                    style={{ maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", cursor: trx.notes ? "pointer" : "default" }}
                    title={trx.notes ? "Click to view full notes" : ""}
                    onClick={() => {
                      if (trx.notes) setViewNotesModal(trx.notes);
                    }}
                  >
                    {trx.notes || "-"}
                  </td>
                  <td>{trx.performed_by}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      </div>

      {viewNotesModal && (
        <div className="modal-overlay" onClick={() => setViewNotesModal(null)}>
          <div className="modal-content animate-fade-in" onClick={e => e.stopPropagation()}>
            <h2 style={{ marginBottom: "1.5rem", fontSize: "1.2rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              Transaction Notes
              <button 
                onClick={() => setViewNotesModal(null)}
                style={{ background: "transparent", border: "none", color: "var(--text-muted)", fontSize: "1.2rem", cursor: "pointer" }}
              >
                ✕
              </button>
            </h2>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "1.5rem", borderRadius: "8px", maxHeight: "50vh", overflowY: "auto", whiteSpace: "pre-wrap", color: "var(--text-main)", lineHeight: "1.6", border: "1px solid rgba(255,255,255,0.05)" }}>
              {viewNotesModal}
            </div>
            <div className="modal-actions" style={{ marginTop: "2rem", display: "flex", justifyContent: "flex-end" }}>
              <button className="btn btn-primary" onClick={() => setViewNotesModal(null)}>Close</button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .page-header {
          display: flex;
          margin-bottom: 2rem;
        }

        .tabs {
          display: flex;
          gap: 1rem;
          border-bottom: 1px solid var(--glass-border);
          width: 100%;
          padding-bottom: 0.5rem;
        }

        .tab-btn {
          background: transparent;
          border: none;
          color: var(--text-muted);
          font-size: 1rem;
          font-weight: 500;
          cursor: pointer;
          padding: 0.5rem 1rem;
          border-radius: 8px;
          transition: all 0.3s;
        }

        .tab-btn:hover {
          color: var(--text-main);
          background: rgba(255,255,255,0.05);
        }

        .tab-btn.active {
          color: var(--primary);
          background: rgba(0, 240, 255, 0.1);
          border: 1px solid rgba(0, 240, 255, 0.2);
        }

        .table-container {
          overflow-x: auto;
          padding: 1rem;
        }

        .inventory-table {
          width: 100%;
          border-collapse: collapse;
          text-align: left;
        }

        .inventory-table th {
          padding: 1rem;
          color: var(--text-muted);
          font-weight: 500;
          border-bottom: 1px solid var(--glass-border);
        }

        .inventory-table td {
          padding: 1rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.02);
          color: var(--text-main);
          vertical-align: middle;
        }

        .inventory-table tbody tr:hover {
          background: rgba(255, 255, 255, 0.03);
        }

        .font-mono {
          font-family: monospace;
          color: var(--primary);
        }

        .type-badge {
          display: inline-block;
          padding: 0.25rem 0.6rem;
          border-radius: 6px;
          font-weight: 600;
          font-size: 0.8rem;
        }

        .type-badge.in {
          background: rgba(0, 240, 255, 0.1);
          color: var(--primary);
          border: 1px solid rgba(0, 240, 255, 0.2);
        }

        .type-badge.out {
          background: rgba(255, 51, 102, 0.1);
          color: var(--danger);
          border: 1px solid rgba(255, 51, 102, 0.2);
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
          background: rgba(0, 0, 0, 0.75);
          backdrop-filter: blur(8px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 1.5rem;
          overflow-y: auto;
        }

        .modal-content {
          width: 100%;
          max-width: 500px;
          padding: 2.5rem;
          margin: auto;
          background: #151823;
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 16px;
          box-shadow: 0 10px 40px rgba(0,0,0, 0.5);
        }
      `}</style>
    </>
  );
}
