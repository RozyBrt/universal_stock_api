"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useWebSocket } from "../context/WebSocketContext";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [username, setUsername] = useState<string | null>(null);
  const [showNotifications, setShowNotifications] = useState(false);
  const { isConnected, notifications, markAsRead, markAllAsRead, clearNotifications } = useWebSocket();
  const unreadCount = notifications.filter((n) => !n.isRead).length;

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
    } else {
      // Decode token payload simply to get username (if present) or just set a placeholder
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUsername(payload.sub ? `Admin ID: ${payload.sub}` : "User");
      } catch (e) {
        setUsername("User");
      }
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    router.push("/login");
  };

  const navItems = [
    { name: "Dashboard", path: "/dashboard", icon: "📊" },
    { name: "Inventory", path: "/inventory", icon: "📦" },
    { name: "Categories", path: "/categories", icon: "📁" },
    { name: "Transactions", path: "/transactions", icon: "📝" },
    { name: "API Keys", path: "/api-keys", icon: "🔑" },
  ];

  return (
    <>
      {/* Sidebar overlay backdrop on mobile */}
      <div className={`sidebar-overlay ${isOpen ? "visible" : ""}`} onClick={onClose}></div>

      <div className={`sidebar ${isOpen ? "open" : ""} animate-fade-in`}>
        <div className="sidebar-header">
          <div className="header-top">
            <h2 className="brand">
              <span className="brand-icon">⚡</span> U-Stock
            </h2>
            <div className="bell-container">
              <button className="btn-bell" onClick={() => setShowNotifications(!showNotifications)}>
                🔔 {unreadCount > 0 && <span className="bell-badge">{unreadCount}</span>}
              </button>
              <span
                className={`status-indicator ${isConnected ? "online" : "offline"}`}
                title={isConnected ? "Terhubung ke Live Server" : "Terputus dari Live Server"}
              ></span>
              <button className="btn-close-sidebar" onClick={onClose} title="Close Menu">
                ✕
              </button>
            </div>
          </div>

        {showNotifications && (
          <div className="notifications-dropdown glass-panel">
            <div className="dropdown-header">
              <h3>Notifikasi</h3>
              <div className="dropdown-actions">
                {notifications.length > 0 && (
                  <>
                    <button onClick={markAllAsRead}>Centang Semua</button>
                    <button onClick={clearNotifications}>Bersihkan</button>
                  </>
                )}
              </div>
            </div>
            <div className="notifications-list">
              {notifications.length === 0 ? (
                <div className="empty-notifications">Tidak ada notifikasi baru</div>
              ) : (
                notifications.map((n) => (
                  <div
                    key={n.id}
                    className={`notification-item ${n.isRead ? "read" : "unread"}`}
                    onClick={() => markAsRead(n.id)}
                  >
                    <div className="notification-item-header">
                      <span className="notification-bullet"></span>
                      <span className="notification-time">
                        {new Date(n.timestamp).toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <div className="notification-title">{n.title}</div>
                    <div className="notification-message">{n.message}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      <div className="nav-links">
        {navItems.map((item) => {
          const isActive = pathname === item.path || pathname.startsWith(`${item.path}/`);
          return (
            <Link key={item.path} href={item.path} className={`nav-item ${isActive ? 'active' : ''}`}>
              <span className="nav-icon">{item.icon}</span>
              {item.name}
            </Link>
          );
        })}
      </div>

      <div className="sidebar-footer">
        <div className="user-info">
          <div className="avatar">👤</div>
          <span>{username || "Loading..."}</span>
        </div>
        <button onClick={handleLogout} className="btn-logout">
          Logout 🚪
        </button>
      </div>

      <style jsx>{`
        .sidebar {
          width: 260px;
          height: 100vh;
          background: var(--bg-card);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border-right: 1px solid var(--glass-border);
          display: flex;
          flex-direction: column;
          position: fixed;
          left: 0;
          top: 0;
          z-index: 100;
          transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .sidebar-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          backdrop-filter: blur(4px);
          z-index: 95;
          opacity: 0;
          pointer-events: none;
          transition: opacity 0.3s ease;
        }

        .sidebar-overlay.visible {
          opacity: 1;
          pointer-events: auto;
        }

        .btn-close-sidebar {
          display: none;
        }

        @media (max-width: 768px) {
          .sidebar {
            transform: translateX(-100%);
            z-index: 100;
          }

          .sidebar.open {
            transform: translateX(0);
            box-shadow: 10px 0 40px rgba(0, 0, 0, 0.5);
          }

          .btn-close-sidebar {
            display: flex;
            align-items: center;
            justify-content: center;
            background: none;
            border: none;
            color: var(--text-muted);
            font-size: 1.3rem;
            cursor: pointer;
            padding: 0.25rem;
            margin-left: 0.5rem;
            transition: color 0.2s;
          }

          .btn-close-sidebar:hover {
            color: var(--danger);
          }
        }

        .sidebar-header {
          padding: 1.5rem 1.25rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          position: relative;
        }

        .header-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
          width: 100%;
        }

        .bell-container {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .btn-bell {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid var(--glass-border);
          color: #fff;
          border-radius: 8px;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          position: relative;
          transition: all 0.3s ease;
          font-size: 1rem;
          padding: 0;
        }

        .btn-bell:hover {
          background: rgba(255, 255, 255, 0.1);
          border-color: var(--primary);
          box-shadow: 0 0 10px var(--primary-glow);
        }

        .bell-badge {
          position: absolute;
          top: -4px;
          right: -4px;
          background: var(--danger);
          color: #fff;
          font-size: 0.65rem;
          font-weight: 700;
          border-radius: 50%;
          width: 16px;
          height: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px solid var(--bg-dark);
        }

        .status-indicator {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .status-indicator.online {
          background: var(--success);
          box-shadow: 0 0 8px var(--success-glow);
        }

        .status-indicator.offline {
          background: var(--danger);
          box-shadow: 0 0 8px var(--danger-glow);
        }

        .notifications-dropdown {
          position: absolute;
          top: 60px;
          left: 10px;
          right: 10px;
          background: rgba(20, 24, 38, 0.95) !important;
          border: 1px solid var(--glass-border) !important;
          border-radius: 12px;
          box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.5);
          z-index: 1000;
          max-height: 350px;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          animation: slideDown 0.3s ease-out;
        }

        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .dropdown-header {
          padding: 0.75rem 1rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .dropdown-header h3 {
          font-size: 0.85rem;
          margin: 0;
          color: #fff;
        }

        .dropdown-actions {
          display: flex;
          gap: 0.5rem;
        }

        .dropdown-actions button {
          background: none;
          border: none;
          color: var(--primary);
          font-size: 0.7rem;
          cursor: pointer;
          font-family: inherit;
        }

        .dropdown-actions button:hover {
          text-decoration: underline;
        }

        .notifications-list {
          overflow-y: auto;
          flex: 1;
          max-height: 250px;
        }

        .empty-notifications {
          padding: 1.5rem 1rem;
          text-align: center;
          color: var(--text-muted);
          font-size: 0.8rem;
        }

        .notification-item {
          padding: 0.75rem 1rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.03);
          cursor: pointer;
          transition: all 0.2s ease;
          text-align: left;
        }

        .notification-item:hover {
          background: rgba(255, 255, 255, 0.02);
        }

        .notification-item.unread {
          background: rgba(0, 240, 255, 0.02);
        }

        .notification-item-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.2rem;
        }

        .notification-bullet {
          width: 6px;
          height: 6px;
          border-radius: 50%;
        }

        .unread .notification-bullet {
          background: var(--danger);
        }

        .read .notification-bullet {
          background: transparent;
        }

        .notification-time {
          font-size: 0.7rem;
          color: var(--text-muted);
        }

        .notification-title {
          font-size: 0.8rem;
          font-weight: 600;
          color: #fff;
          margin-bottom: 0.1rem;
        }

        .notification-message {
          font-size: 0.75rem;
          color: var(--text-muted);
          line-height: 1.3;
        }

        .brand {
          font-size: 1.5rem;
          margin: 0;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          background: linear-gradient(to right, #fff, var(--primary));
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .brand-icon {
          -webkit-text-fill-color: initial;
        }

        .nav-links {
          padding: 1.5rem 1rem;
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 1rem;
          border-radius: 12px;
          color: var(--text-muted);
          transition: all 0.3s ease;
          font-weight: 500;
        }

        .nav-item:hover {
          background: rgba(255, 255, 255, 0.05);
          color: #fff;
          transform: translateX(4px);
        }

        .nav-item.active {
          background: rgba(0, 240, 255, 0.1);
          color: var(--primary);
          border: 1px solid rgba(0, 240, 255, 0.2);
          box-shadow: 0 0 15px rgba(0, 240, 255, 0.1);
        }

        .sidebar-footer {
          padding: 1.5rem;
          border-top: 1px solid rgba(255, 255, 255, 0.05);
        }

        .user-info {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 1rem;
          color: var(--text-main);
          font-weight: 500;
        }

        .avatar {
          width: 36px;
          height: 36px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .btn-logout {
          width: 100%;
          padding: 0.75rem;
          background: transparent;
          border: 1px solid var(--danger);
          color: var(--danger);
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.3s ease;
          font-family: inherit;
          font-weight: 500;
        }

        .btn-logout:hover {
          background: var(--danger);
          color: #fff;
          box-shadow: 0 0 15px var(--danger-glow);
        }
      `}</style>
    </div>
    </>
  );
}
