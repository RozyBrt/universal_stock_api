"use client";

import React, { createContext, useContext, useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  timestamp: string;
  isRead: boolean;
  item_id?: number;
  quantity_in_stock?: number;
  reorder_level?: number;
}

interface ToastMessage {
  id: string;
  title: string;
  message: string;
  type: "info" | "warning" | "error" | "success";
}

interface WebSocketContextType {
  isConnected: boolean;
  notifications: Notification[];
  toasts: ToastMessage[];
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearNotifications: () => void;
  subscribe: (type: string, callback: (data: any) => void) => () => void;
  addToast: (title: string, message: string, type: ToastMessage["type"]) => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [currentUserId, setCurrentUserId] = useState<string>("guest");
  
  const listenersRef = useRef<{ [key: string]: Array<(data: any) => void> }>({});
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectDelayRef = useRef(1000);
  const maxReconnectDelay = 30000;
  const router = useRouter();

  // Helper untuk mengambil user ID dari token JWT di localStorage
  const getUserIdFromToken = useCallback((): string => {
    if (typeof window === "undefined") return "guest";
    const token = localStorage.getItem("access_token");
    if (!token) return "guest";
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.sub ? String(payload.sub) : "guest";
    } catch (e) {
      return "guest";
    }
  }, []);

  // Update currentUserId saat status koneksi berubah (misal login/logout)
  useEffect(() => {
    setCurrentUserId(getUserIdFromToken());
  }, [isConnected, getUserIdFromToken]);

  // Load notifications dari localStorage berdasarkan User ID saat user berganti
  useEffect(() => {
    if (currentUserId !== "guest") {
      const saved = localStorage.getItem(`ustock_notifications_${currentUserId}`);
      if (saved) {
        try {
          setNotifications(JSON.parse(saved));
        } catch (e) {
          console.warn("Failed to load notifications", e);
          setNotifications([]);
        }
      } else {
        setNotifications([]);
      }
    } else {
      setNotifications([]);
    }
  }, [currentUserId]);

  // Simpan ke localStorage saat notifications berubah
  const saveNotifications = (newNotifications: Notification[]) => {
    setNotifications(newNotifications);
    const userId = getUserIdFromToken();
    if (userId !== "guest") {
      localStorage.setItem(`ustock_notifications_${userId}`, JSON.stringify(newNotifications));
    }
  };

  // Tambah toast melayang
  const addToast = useCallback((title: string, message: string, type: ToastMessage["type"]) => {
    const id = Math.random().toString(36).substring(7);
    setToasts((prev) => [...prev, { id, title, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  // Mark single as read
  const markAsRead = (id: string) => {
    const updated = notifications.map((n) => (n.id === id ? { ...n, isRead: true } : n));
    saveNotifications(updated);
  };

  // Mark all as read
  const markAllAsRead = () => {
    const updated = notifications.map((n) => ({ ...n, isRead: true }));
    saveNotifications(updated);
    addToast("Sukses", "Semua notifikasi ditandai sebagai dibaca", "success");
  };

  // Hapus semua riwayat
  const clearNotifications = () => {
    saveNotifications([]);
    addToast("Sukses", "Riwayat notifikasi berhasil dibersihkan", "success");
  };

  // Subscribe ke event WebSocket tertentu
  const subscribe = useCallback((type: string, callback: (data: any) => void) => {
    if (!listenersRef.current[type]) {
      listenersRef.current[type] = [];
    }
    listenersRef.current[type].push(callback);

    // Kembalikan fungsi unsubscribe
    return () => {
      if (listenersRef.current[type]) {
        listenersRef.current[type] = listenersRef.current[type].filter((cb) => cb !== callback);
      }
    };
  }, []);

  // Hubungkan ke WebSocket Server
  const connect = useCallback(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setIsConnected(false);
      return;
    }

    if (socketRef.current) {
      socketRef.current.close();
    }

    // Tentukan URL WebSocket secara dinamis berdasarkan NEXT_PUBLIC_API_URL
    let wsUrl = `ws://localhost:8000/api/v1/ws?token=${token}`;
    const apiEnvUrl = process.env.NEXT_PUBLIC_API_URL;
    if (apiEnvUrl) {
      const baseWsUrl = apiEnvUrl
        .replace(/^https:\/\//i, "wss://")
        .replace(/^http:\/\//i, "ws://");
      wsUrl = `${baseWsUrl}/ws?token=${token}`;
    }
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      reconnectDelayRef.current = 1000; // Reset delay on success
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      // Coba hubungkan kembali jika token masih ada
      if (localStorage.getItem("access_token")) {
        const delay = reconnectDelayRef.current;
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectDelayRef.current = Math.min(delay * 2, maxReconnectDelay);
          connect();
        }, delay);
      }
    };

    ws.onerror = (error) => {
      console.warn("WebSocket error (normal during disconnect/reconnect):", error);
      ws.close();
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        const { type, ...data } = message;

        // Distribusikan ke event listeners
        if (listenersRef.current[type]) {
          listenersRef.current[type].forEach((cb) => cb(data));
        }

        // Tangani notifikasi stok kritis secara global
        if (type === "LOW_STOCK_ALERT") {
          const newNotification: Notification = {
            id: Math.random().toString(36).substring(7),
            type: "low_stock",
            title: `Stok Kritis: ${data.name}`,
            message: `Barang ${data.name} (${data.sku}) tersisa ${data.quantity_in_stock} unit (Batas minimum: ${data.reorder_level}).`,
            timestamp: data.timestamp || new Date().toISOString(),
            isRead: false,
            item_id: data.item_id,
            quantity_in_stock: data.quantity_in_stock,
            reorder_level: data.reorder_level,
          };

          // Simpan notifikasi ke list spesifik user
          setNotifications((prev) => {
            const updated = [newNotification, ...prev];
            const userId = getUserIdFromToken();
            if (userId !== "guest") {
              localStorage.setItem(`ustock_notifications_${userId}`, JSON.stringify(updated));
            }
            return updated;
          });

          // Tampilkan toast warning
          addToast(
            `Stok Kritis: ${data.name}`,
            `Tersisa ${data.quantity_in_stock} unit. Batas: ${data.reorder_level} unit.`,
            "warning"
          );
        }

        // Tampilkan toast info untuk perubahan status item
        if (type === "ITEM_CHANGED") {
          if (data.action === "CREATE") {
            addToast("Item Baru", `Barang "${data.name}" baru saja ditambahkan.`, "info");
          } else if (data.action === "DELETE") {
            addToast("Item Dihapus", `Item ID ${data.item_id} telah dinonaktifkan.`, "info");
          }
        }
      } catch (e) {
        console.warn("Gagal membaca pesan WebSocket:", e);
      }
    };
  }, [addToast]);

  // Pantau perubahan login/token
  useEffect(() => {
    connect();

    // Dengarkan event storage untuk memantau perubahan login/logout antar tab
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "access_token") {
        if (e.newValue) {
          connect();
        } else {
          setIsConnected(false);
          if (socketRef.current) {
            socketRef.current.close();
          }
        }
      }
    };

    window.addEventListener("storage", handleStorageChange);

    return () => {
      window.removeEventListener("storage", handleStorageChange);
      if (socketRef.current) {
        socketRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  return (
    <WebSocketContext.Provider
      value={{
        isConnected,
        notifications,
        toasts,
        markAsRead,
        markAllAsRead,
        clearNotifications,
        subscribe,
        addToast,
      }}
    >
      {children}

      {/* Floating Glassmorphic Toast Notifications Container */}
      <div className="toast-container">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast-${t.type} glass-panel`}>
            <div className="toast-header">
              <span className="toast-icon">
                {t.type === "warning" ? "⚠️" : t.type === "success" ? "✅" : t.type === "error" ? "❌" : "ℹ️"}
              </span>
              <strong className="toast-title">{t.title}</strong>
              <button
                className="toast-close"
                onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}
              >
                ×
              </button>
            </div>
            <div className="toast-body">{t.message}</div>
          </div>
        ))}
      </div>

      <style jsx>{`
        .toast-container {
          position: fixed;
          top: 20px;
          right: 20px;
          z-index: 9999;
          display: flex;
          flex-direction: column;
          gap: 10px;
          max-width: 350px;
          pointer-events: none;
        }

        :global(.toast) {
          pointer-events: auto !important;
          padding: 1rem;
          border-radius: 12px;
          background: rgba(25, 28, 41, 0.85) !important;
          border: 1px solid var(--glass-border) !important;
          box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
          animation: slideIn 0.3s ease-out forwards;
        }

        :global(.toast-warning) {
          border-left: 4px solid var(--danger) !important;
        }

        :global(.toast-success) {
          border-left: 4px solid var(--success) !important;
        }

        :global(.toast-info) {
          border-left: 4px solid var(--primary) !important;
        }

        .toast-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 0.25rem;
        }

        .toast-icon {
          font-size: 1.1rem;
        }

        .toast-title {
          flex: 1;
          font-weight: 600;
          color: #fff;
        }

        .toast-close {
          background: none;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          font-size: 1.2rem;
          line-height: 1;
          padding: 0;
        }

        .toast-close:hover {
          color: #fff;
        }

        .toast-body {
          font-size: 0.85rem;
          color: var(--text-muted);
          line-height: 1.4;
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(100px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
      `}</style>
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error("useWebSocket must be used within a WebSocketProvider");
  }
  return context;
}
