"use client";

import Sidebar from "../components/Sidebar";
import { WebSocketProvider } from "../context/WebSocketContext";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <WebSocketProvider>
      <div className="dashboard-wrapper">
        <Sidebar />
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
        }
      `}</style>
    </WebSocketProvider>
  );
}
