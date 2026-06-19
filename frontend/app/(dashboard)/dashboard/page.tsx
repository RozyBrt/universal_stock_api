"use client";

import { useEffect, useState } from "react";
import { fetchJson } from "../../lib/apiClient";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState({
    totalItems: 0,
    totalStock: 0,
    totalAssetValue: 0,
    lowStockRatio: 0,
    stockTurnover: 0,
  });
  const [transactionTrends, setTransactionTrends] = useState<any[]>([]);
  const [topMovingItems, setTopMovingItems] = useState<any[]>([]);
  const [lowStockItems, setLowStockItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const [analyticsRes, alertsRes] = await Promise.all([
          fetchJson<any>("/items/analytics"),
          fetchJson<any>("/items/alerts/low-stock?limit=500")
        ]);

        setMetrics({
          totalItems: analyticsRes.total_items || 0,
          totalStock: analyticsRes.total_stock_volume || 0,
          totalAssetValue: analyticsRes.total_asset_value || 0,
          lowStockRatio: analyticsRes.low_stock_ratio || 0,
          stockTurnover: analyticsRes.stock_turnover || 0,
        });
        setTransactionTrends(analyticsRes.transaction_trends || []);
        setTopMovingItems(analyticsRes.top_moving_items || []);
        setLowStockItems(alertsRes.data || []);
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
        {/* Total Items */}
        <div className="glass-panel metric-card">
          <div className="metric-icon" style={{ boxShadow: "0 0 15px rgba(0, 240, 255, 0.15)", color: "var(--primary)" }}>📦</div>
          <div className="metric-info" style={{ flex: 1 }}>
            <h3>Total Items</h3>
            {loading ? (
              <div className="skeleton" style={{ width: "80px", height: "2.5rem", marginTop: "0.25rem" }}></div>
            ) : (
              <p className="metric-value">{metrics.totalItems}</p>
            )}
          </div>
        </div>

        {/* Total Stock Volume */}
        <div className="glass-panel metric-card">
          <div className="metric-icon" style={{ boxShadow: "0 0 15px rgba(0, 255, 157, 0.15)", color: "var(--success)" }}>📈</div>
          <div className="metric-info" style={{ flex: 1 }}>
            <h3>Total Stock</h3>
            {loading ? (
              <div className="skeleton" style={{ width: "100px", height: "2.5rem", marginTop: "0.25rem" }}></div>
            ) : (
              <p className="metric-value">{metrics.totalStock}</p>
            )}
          </div>
        </div>

        {/* Total Asset Value */}
        <div className="glass-panel metric-card">
          <div className="metric-icon" style={{ boxShadow: "0 0 15px rgba(255, 235, 59, 0.15)", color: "#ffeb3b" }}>💰</div>
          <div className="metric-info" style={{ flex: 1 }}>
            <h3>Asset Value</h3>
            {loading ? (
              <div className="skeleton" style={{ width: "120px", height: "2.5rem", marginTop: "0.25rem" }}></div>
            ) : (
              <p className="metric-value" style={{ fontSize: "1.6rem" }}>
                {new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(metrics.totalAssetValue)}
              </p>
            )}
          </div>
        </div>

        {/* Low Stock Ratio */}
        <div className="glass-panel metric-card">
          <div className="metric-icon" style={{ boxShadow: "0 0 15px rgba(255, 51, 102, 0.15)", color: "var(--danger)" }}>⚠️</div>
          <div className="metric-info" style={{ flex: 1 }}>
            <h3>Low Stock Rate</h3>
            {loading ? (
              <div className="skeleton" style={{ width: "70px", height: "2.5rem", marginTop: "0.25rem" }}></div>
            ) : (
              <p className="metric-value" style={{ color: metrics.lowStockRatio > 0.2 ? "var(--danger)" : "var(--text-main)" }}>
                {(metrics.lowStockRatio * 100).toFixed(1)}%
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Analytics Section Grid */}
      <div className="analytics-grid" style={{ marginBottom: "2.5rem" }}>
        {/* Weekly Stock Movement Trends SVG Chart */}
        <div className="glass-panel chart-container">
          <h2>Weekly Stock Movement Trends</h2>
          {loading ? (
            <div style={{ height: "220px", display: "flex", flexDirection: "column", gap: "1rem", justifyContent: "center" }}>
              <div className="skeleton" style={{ width: "100%", height: "180px" }}></div>
            </div>
          ) : transactionTrends.length === 0 ? (
            <div className="empty-state-chart" style={{ height: "220px", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)" }}>
              No transactions recorded in the last 7 days.
            </div>
          ) : (
            <div style={{ position: "relative", width: "100%", height: "220px", marginTop: "0.5rem" }}>
              {/* Native SVG Chart */}
              <svg viewBox="0 0 600 200" width="100%" height="100%" style={{ overflow: "visible" }}>
                {/* Horizontal Grid lines */}
                {[0, 1, 2, 3, 4].map((g) => (
                  <line 
                    key={g} 
                    x1="40" 
                    y1={30 + g * 30} 
                    x2="580" 
                    y2={30 + g * 30} 
                    stroke="rgba(255, 255, 255, 0.05)" 
                    strokeWidth="1" 
                  />
                ))}

                {/* Render Bars */}
                {(() => {
                  // Find max value to scale chart y-axis
                  const maxVal = Math.max(
                    ...transactionTrends.map(t => Math.max(t.total_in, t.total_out)),
                    10 // default min height scale
                  );

                  return transactionTrends.map((t, idx) => {
                    const xBase = 60 + idx * 72;
                    const inHeight = (t.total_in / maxVal) * 120;
                    const outHeight = (t.total_out / maxVal) * 120;
                    
                    const dateObj = new Date(t.date);
                    const formattedDate = dateObj.toLocaleDateString('en-US', { day: 'numeric', month: 'short' });

                    return (
                      <g key={t.date}>
                        {/* IN Bar (Cyan) */}
                        <rect
                          x={xBase}
                          y={150 - inHeight}
                          width="18"
                          height={inHeight}
                          fill="var(--primary)"
                          rx="3"
                          style={{ transition: "all 0.5s ease", filter: "drop-shadow(0 0 4px var(--primary-glow))" }}
                          className="chart-bar"
                        >
                          <title>{`IN: ${t.total_in} items`}</title>
                        </rect>

                        {/* OUT Bar (Red/Pink) */}
                        <rect
                          x={xBase + 22}
                          y={150 - outHeight}
                          width="18"
                          height={outHeight}
                          fill="var(--danger)"
                          rx="3"
                          style={{ transition: "all 0.5s ease", filter: "drop-shadow(0 0 4px var(--danger-glow))" }}
                          className="chart-bar"
                        >
                          <title>{`OUT: ${t.total_out} items`}</title>
                        </rect>

                        {/* Date Label */}
                        <text
                          x={xBase + 20}
                          y="172"
                          textAnchor="middle"
                          fill="var(--text-muted)"
                          fontSize="9"
                          fontFamily="inherit"
                        >
                          {formattedDate}
                        </text>
                      </g>
                    );
                  });
                })()}

                {/* Y-axis indicator */}
                <line x1="40" y1="30" x2="40" y2="150" stroke="rgba(255, 255, 255, 0.1)" strokeWidth="1" />
                <line x1="40" y1="150" x2="580" y2="150" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1" />
              </svg>
              
              {/* Legend */}
              <div style={{ display: "flex", gap: "1.5rem", justifyContent: "flex-end", marginTop: "0.25rem", fontSize: "0.8rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  <div style={{ width: "10px", height: "10px", background: "var(--primary)", borderRadius: "3px", boxShadow: "0 0 8px var(--primary-glow)" }}></div>
                  <span style={{ color: "var(--text-muted)" }}>Stock IN</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  <div style={{ width: "10px", height: "10px", background: "var(--danger)", borderRadius: "3px", boxShadow: "0 0 8px var(--danger-glow)" }}></div>
                  <span style={{ color: "var(--text-muted)" }}>Stock OUT</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Top Moving Items Panel */}
        <div className="glass-panel top-items-container">
          <h2>Top Moving Items (30 Days)</h2>
          {loading ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "1.2rem" }}>
              {[1, 2, 3, 4, 5].map(n => (
                <div key={n} style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <div className="skeleton" style={{ width: "140px", height: "0.9rem" }}></div>
                    <div className="skeleton" style={{ width: "40px", height: "0.9rem" }}></div>
                  </div>
                  <div className="skeleton" style={{ width: "100%", height: "6px" }}></div>
                </div>
              ))}
            </div>
          ) : topMovingItems.length === 0 ? (
            <div className="empty-state-list" style={{ height: "220px", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)", fontSize: "0.9rem" }}>
              No transactions recorded in the last 30 days.
            </div>
          ) : (
            <div className="top-items-list" style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "1.2rem" }}>
              {(() => {
                const maxOut = Math.max(...topMovingItems.map(item => item.total_out), 1);
                return topMovingItems.map((item, idx) => {
                  const percentage = (item.total_out / maxOut) * 100;
                  return (
                    <div key={item.id} className="top-item-row" style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                        <span style={{ fontWeight: 500, fontSize: "0.9rem", maxWidth: "70%", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {idx + 1}. {item.name} <span style={{ color: "var(--text-muted)", fontSize: "0.75rem", fontFamily: "monospace" }}>({item.sku})</span>
                        </span>
                        <span style={{ fontWeight: 600, color: "var(--primary)", fontSize: "0.85rem" }}>{item.total_out} OUT</span>
                      </div>
                      <div className="progress-bar-bg" style={{ width: "100%", height: "5px", background: "rgba(255, 255, 255, 0.05)", borderRadius: "3px", overflow: "hidden" }}>
                        <div 
                          className="progress-bar-fill" 
                          style={{ 
                            width: `${percentage}%`, 
                            height: "100%", 
                            background: "linear-gradient(to right, var(--secondary), var(--primary))", 
                            borderRadius: "3px",
                            boxShadow: "0 0 8px var(--primary-glow)",
                            transition: "width 1s cubic-bezier(0.4, 0, 0.2, 1)"
                          }}
                        ></div>
                      </div>
                    </div>
                  );
                });
              })()}
            </div>
          )}
        </div>
      </div>

      <div className="alerts-section">
        <h2>Critical Alerts</h2>
        {loading ? (
          <div className="grid-cards">
            {[1, 2, 3].map((n) => (
              <div key={n} className="glass-panel alert-card danger" style={{ borderLeftColor: "rgba(255, 255, 255, 0.1)" }}>
                <div className="skeleton" style={{ width: "24px", height: "24px", borderRadius: "50%", marginRight: "0.5rem" }}></div>
                <div className="alert-content" style={{ flex: 1 }}>
                  <div className="skeleton" style={{ width: "50%", height: "1.2rem", marginBottom: "0.5rem" }}></div>
                  <div className="skeleton" style={{ width: "30%", height: "0.9rem", marginBottom: "1rem" }}></div>
                  <div style={{ display: "flex", gap: "1rem" }}>
                    <div className="skeleton" style={{ width: "80px", height: "1.5rem" }}></div>
                    <div className="skeleton" style={{ width: "100px", height: "1.5rem" }}></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
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

        .analytics-grid {
          display: grid;
          grid-template-columns: 1.6fr 1fr;
          gap: 1.5rem;
        }

        @media (max-width: 900px) {
          .analytics-grid {
            grid-template-columns: 1fr;
          }
        }

        .chart-container, .top-items-container {
          padding: 1.75rem;
          min-height: 320px;
        }

        .chart-container h2, .top-items-container h2 {
          font-size: 1.15rem;
          color: var(--text-main);
          margin-bottom: 0.5rem;
          font-weight: 600;
        }

        .chart-bar:hover {
          opacity: 0.8;
          cursor: pointer;
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
