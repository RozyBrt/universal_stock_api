"use client";

import { useState } from "react";
import Sidebar from "../components/Sidebar";
import { WebSocketProvider } from "../context/WebSocketContext";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <WebSocketProvider>
      <div className="dashboard-wrapper">
        {/* Mobile Header Bar */}
        <header className="mobile-header">
          <button className="hamburger-btn" onClick={() => setSidebarOpen(true)} title="Open Menu">
            ☰
          </button>
          <h2 className="mobile-brand">⚡ U-Stock</h2>
          <div style={{ width: "32px" }}></div> {/* Balance placeholder */}
        </header>

        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        
        <main className="main-content">
          <div className="page-container">
            {children}
          </div>
        </main>
      </div>

      <style jsx>{`
        .dashboard-wrapper {
          display: flex;
          min-height: 100vh;
        }

        .main-content {
          flex: 1;
          margin-left: 260px; /* Sidebar width */
          width: calc(100% - 260px);
          transition: all 0.3s ease;
        }

        .mobile-header {
          display: none;
        }

        @media (max-width: 768px) {
          .main-content {
            margin-left: 0;
            width: 100%;
            padding-top: 60px; /* Make space for mobile header */
          }

          .mobile-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: rgba(15, 17, 26, 0.8);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--glass-border);
            z-index: 90;
            padding: 0 1.25rem;
          }

          .hamburger-btn {
            background: none;
            border: none;
            color: var(--primary);
            font-size: 1.6rem;
            cursor: pointer;
            padding: 0.25rem 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: color 0.2s;
          }

          .hamburger-btn:hover {
            color: #fff;
          }

          .mobile-brand {
            font-size: 1.25rem;
            margin: 0;
            font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(to right, #fff, var(--primary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
          }
        }
      `}</style>
    </WebSocketProvider>
  );
}

