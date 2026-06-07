"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [username, setUsername] = useState<string | null>(null);

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
    <div className="sidebar animate-fade-in">
      <div className="sidebar-header">
        <h2 className="brand">
          <span className="brand-icon">⚡</span> U-Stock
        </h2>
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
        }

        .sidebar-header {
          padding: 2rem 1.5rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
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
  );
}
