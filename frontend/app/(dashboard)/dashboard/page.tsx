"use client";

import { useEffect, useState } from "react";
import { fetchJson } from "../../lib/apiClient";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState({ totalItems: 0, totalStock: 0 });
  const [lowStockItems, setLowStockItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        // Fetch all items to calculate basic metrics (max limit is 500)
        const response = await fetchJson<any>("/items?limit=500");
        const items = response.data || [];
        const totalStock = items.reduce((sum: number, item: any) => sum + item.quantity_in_stock, 0);
        setMetrics({ totalItems: items.length, totalStock });

        // Fetch low stock alerts
        const alertsResponse = await fetchJson<any>("/items/alerts/low-stock?limit=500");
        setLowStockItems(alertsResponse.data || []);
      } catch (error) {
        console.error("Failed to load dashboard data", error);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  return (
    <div className="animate-fade-in">
      <h1>Dashboard Overview</h1>
      
      <div className="grid-cards" style={{ marginBottom: "2rem" }}>
        <div className="glass-panel metric-card">
          <div className="metric-icon">📦</div>
          <div className="metric-info">
            <h3>Total Items</h3>
            <p className="metric-value">{loading ? "..." : metrics.totalItems}</p>
          </div>
        </div>

        <div className="glass-panel metric-card">
          <div className="metric-icon">📈</div>
          <div className="metric-info">
            <h3>Total Stock Volume</h3>
            <p className="metric-value">{loading ? "..." : metrics.totalStock}</p>
          </div>
        </div>
      </div>

      <div className="alerts-section">
        <h2>Critical Alerts</h2>
        {loading ? (
          <p>Loading alerts...</p>
        ) : lowStockItems.length === 0 ? (
          <div className="glass-panel alert-card success">
            <div className="alert-icon">✅</div>
            <div>
              <h4>All Good!</h4>
              <p>No items are currently running low on stock.</p>
            </div>
          </div>
        ) : (
          <div className="grid-cards">
            {lowStockItems.map((item) => (
              <div key={item.id} className="glass-panel alert-card danger animate-fade-in">
                <div className="alert-icon">⚠️</div>
                <div className="alert-content">
                  <h4>{item.name}</h4>
                  <p>SKU: {item.sku}</p>
                  <div className="stock-level">
                    <span className="current-stock">Stock: {item.quantity_in_stock}</span>
                    <span className="reorder-level">Threshold: {item.reorder_level}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <style jsx>{`
        .metric-card {
          padding: 1.5rem;
          display: flex;
          align-items: center;
          gap: 1.5rem;
        }

        .metric-icon {
          font-size: 2.5rem;
          background: rgba(255, 255, 255, 0.05);
          width: 70px;
          height: 70px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 16px;
        }

        .metric-info h3 {
          color: var(--text-muted);
          font-size: 1rem;
          font-weight: 500;
          margin-bottom: 0.5rem;
        }

        .metric-value {
          font-size: 2rem;
          font-weight: 700;
          color: var(--text-main);
          margin: 0;
        }

        .alerts-section h2 {
          margin-bottom: 1.5rem;
        }

        .alert-card {
          padding: 1.5rem;
          display: flex;
          align-items: flex-start;
          gap: 1rem;
          border-left: 4px solid transparent;
        }

        .alert-card.success {
          border-left-color: var(--success);
          background: rgba(0, 255, 157, 0.05);
        }

        .alert-card.danger {
          border-left-color: var(--danger);
          background: rgba(255, 51, 102, 0.05);
        }

        .alert-icon {
          font-size: 1.5rem;
          margin-top: 0.2rem;
        }

        .alert-content h4 {
          margin: 0 0 0.2rem 0;
          font-size: 1.1rem;
        }

        .alert-content p {
          color: var(--text-muted);
          margin: 0 0 1rem 0;
          font-size: 0.9rem;
        }

        .stock-level {
          display: flex;
          gap: 1rem;
          font-size: 0.9rem;
        }

        .current-stock {
          color: var(--danger);
          font-weight: 600;
          background: rgba(255, 51, 102, 0.1);
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
        }

        .reorder-level {
          color: var(--text-muted);
          background: rgba(255, 255, 255, 0.05);
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
        }
      `}</style>
    </div>
  );
}
