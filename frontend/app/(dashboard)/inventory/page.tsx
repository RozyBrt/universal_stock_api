"use client";

import { useEffect, useState } from "react";
import { fetchJson } from "../../lib/apiClient";
import { useWebSocket } from "../../context/WebSocketContext";

export default function InventoryPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionModal, setActionModal] = useState<{
    isOpen: boolean;
    type: "in" | "out" | null;
    item: any | null;
    quantity: number;
    reference_number: string;
    notes: string;
    error: string | null;
  }>({ isOpen: false, type: null, item: null, quantity: 1, reference_number: "", notes: "", error: null });

  const [newItemModalOpen, setNewItemModalOpen] = useState(false);
  const [newItemForm, setNewItemForm] = useState({
    name: "",
    sku: "",
    category_id: 1,
    unit_price: 0,
    quantity_in_stock: 0,
    reorder_level: 5,
    description: "",
    error: null as string | null,
  });

  const [categories, setCategories] = useState<any[]>([]);
  const [createCategoryModalOpen, setCreateCategoryModalOpen] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState("");
  const [newCategoryDesc, setNewCategoryDesc] = useState("");
  const [categoryError, setCategoryError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string>("all");

  const [editItemModalOpen, setEditItemModalOpen] = useState(false);
  const [editItemId, setEditItemId] = useState<number | null>(null);
  const [editItemForm, setEditItemForm] = useState({
    name: "", sku: "", category_id: 1, unit_price: 0, reorder_level: 5, description: "", error: null as string | null
  });

  const [itemToDelete, setItemToDelete] = useState<any | null>(null);

  const [historyModalOpen, setHistoryModalOpen] = useState(false);
  const [historyItem, setHistoryItem] = useState<any | null>(null);
  const [historyData, setHistoryData] = useState<any[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const openHistoryModal = async (item: any) => {
    setHistoryItem(item);
    setHistoryModalOpen(true);
    setHistoryLoading(true);
    try {
      const res = await fetchJson<any>(`/transactions/item/${item.id}`);
      setHistoryData(Array.isArray(res) ? res : (res.data || []));
    } catch (e: any) {
      alert("Failed to load history: " + e.message);
    } finally {
      setHistoryLoading(false);
    }
  };

  const loadItems = async () => {
    setLoading(true);
    try {
      const response = await fetchJson<any>("/items?limit=500");
      setItems(response.data || []);
    } catch (error) {
      console.error("Failed to load items", error);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      // Backend returns list directly, not inside .data based on standard FastAPI response_model=list[...]
      const response = await fetchJson<any>("/categories?limit=100");
      setCategories(Array.isArray(response) ? response : (response.data || []));
      
      // Auto-select first category if available
      if (Array.isArray(response) && response.length > 0) {
        setNewItemForm(prev => ({ ...prev, category_id: response[0].id }));
      } else if (response.data && response.data.length > 0) {
        setNewItemForm(prev => ({ ...prev, category_id: response.data[0].id }));
      }
    } catch (error) {
      console.error("Failed to load categories", error);
    }
  };

  useEffect(() => {
    loadItems();
    loadCategories();
  }, []);

  const { subscribe } = useWebSocket();

  useEffect(() => {
    // Listen to stock updates
    const unsubscribeStock = subscribe("STOCK_UPDATE", (data: any) => {
      setItems((prevItems) => {
        const exists = prevItems.some((item) => item.id === data.item_id);
        if (!exists) return prevItems;

        return prevItems.map((item) =>
          item.id === data.item_id
            ? {
                ...item,
                quantity_in_stock: data.quantity_in_stock,
                reorder_level: data.reorder_level,
                flashType: data.action, // "IN" or "OUT"
              }
            : item
        );
      });

      // Remove flash effect after 1.5 seconds
      setTimeout(() => {
        setItems((prevItems) =>
          prevItems.map((item) =>
            item.id === data.item_id ? { ...item, flashType: null } : item
          )
        );
      }, 1500);
    });

    // Listen to item alterations (create, update, delete)
    const unsubscribeItems = subscribe("ITEM_CHANGED", (data: any) => {
      loadItems();
    });

    return () => {
      unsubscribeStock();
      unsubscribeItems();
    };
  }, [subscribe]);

  const openModal = (item: any, type: "in" | "out") => {
    setActionModal({ isOpen: true, type, item, quantity: 1, reference_number: "", notes: "", error: null });
  };

  const closeModal = () => {
    setActionModal({ isOpen: false, type: null, item: null, quantity: 1, reference_number: "", notes: "", error: null });
  };

  const handleStockAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionModal.item || !actionModal.type) return;

    try {
      const endpoint = actionModal.type === "in" ? "add-stock" : "remove-stock";
      await fetchJson(`/items/${actionModal.item.id}/${endpoint}`, {
        method: "POST",
        body: JSON.stringify({
          quantity: actionModal.quantity,
          reference_number: actionModal.reference_number || undefined,
          notes: actionModal.notes || undefined,
        }),
      });
      
      closeModal();
      loadItems(); // Refresh items
    } catch (error: any) {
      setActionModal(prev => ({ ...prev, error: error.message || String(error) }));
    }
  };

  const handleCreateItem = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetchJson("/items", {
        method: "POST",
        body: JSON.stringify(newItemForm),
      });
      setNewItemModalOpen(false);
      setNewItemForm({ name: "", sku: "", category_id: categories.length > 0 ? categories[0].id : 1, unit_price: 0, quantity_in_stock: 0, reorder_level: 5, description: "", error: null });
      loadItems(); // Refresh items
    } catch (error: any) {
      setNewItemForm(prev => ({ ...prev, error: error.message || String(error) }));
    }
  };

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetchJson<any>("/categories", {
        method: "POST",
        body: JSON.stringify({ name: newCategoryName, description: newCategoryDesc || undefined }),
      });
      setNewCategoryName("");
      setNewCategoryDesc("");
      setCreateCategoryModalOpen(false);
      await loadCategories();
      
      // Select the newly created category
      if (response && response.id) {
        setNewItemForm(prev => ({...prev, category_id: response.id}));
      }
    } catch (error: any) {
      setCategoryError(error.message || String(error));
    }
  };

  const openEditModal = (item: any) => {
    setEditItemId(item.id);
    setEditItemForm({
      name: item.name,
      sku: item.sku,
      category_id: item.category_id || (categories.length > 0 ? categories[0].id : 1),
      unit_price: item.unit_price,
      reorder_level: item.reorder_level || 5,
      description: item.description || "",
      error: null
    });
    setEditItemModalOpen(true);
  };

  const handleEditItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editItemId) return;
    try {
      await fetchJson(`/items/${editItemId}`, {
        method: "PATCH",
        body: JSON.stringify(editItemForm),
      });
      setEditItemModalOpen(false);
      loadItems();
    } catch (error: any) {
      setEditItemForm(prev => ({ ...prev, error: error.message || String(error) }));
    }
  };

  const confirmDelete = async () => {
    if (!itemToDelete) return;
    try {
      await fetchJson(`/items/${itemToDelete.id}`, { method: "DELETE" });
      setItemToDelete(null);
      loadItems();
    } catch (error: any) {
      alert("Failed to delete item: " + error.message);
    }
  };

  const filteredItems = items.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          item.sku.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategoryFilter === "all" || item.category_id?.toString() === selectedCategoryFilter;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1>Inventory Management</h1>
        <button className="btn btn-primary" onClick={() => setNewItemModalOpen(true)}>+ New Item</button>
      </div>

      <div className="glass-panel table-container">
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', padding: '0 0.5rem' }}>
          <input 
            type="text" 
            className="form-control" 
            placeholder="Search by Item Name or SKU..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ flex: 1, background: "rgba(0,0,0,0.2)", border: "1px solid rgba(255,255,255,0.1)" }}
          />
          <select 
            className="form-control" 
            value={selectedCategoryFilter}
            onChange={(e) => setSelectedCategoryFilter(e.target.value)}
            style={{ width: '200px', appearance: "auto", background: "rgba(0,0,0,0.2)", border: "1px solid rgba(255,255,255,0.1)" }}
          >
            <option value="all" style={{ color: "#000" }}>All Categories</option>
            {categories.map(c => <option key={c.id} value={c.id.toString()} style={{ color: "#000" }}>{c.name}</option>)}
          </select>
        </div>

        {loading ? (
          <div className="loading-state">Loading inventory...</div>
        ) : (
          <table className="inventory-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Name</th>
                <th>Category</th>
                <th>Stock</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((item) => (
                <tr key={item.id} className={item.flashType ? `flash-${item.flashType.toLowerCase()}` : ""}>
                  <td className="font-mono">{item.sku}</td>
                  <td className="font-medium">{item.name}</td>
                  <td>{item.category?.name || "-"}</td>
                  <td>
                    <span className={`stock-badge ${item.quantity_in_stock <= (item.reorder_level || 0) ? "low" : "good"}`}>
                      {item.quantity_in_stock}
                    </span>
                  </td>
                  <td>
                    <span className={`status-dot ${item.is_active ? "active" : "inactive"}`}></span>
                    {item.is_active ? "Active" : "Inactive"}
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button 
                        className="action-btn btn-in" 
                        title="Add Stock (In)"
                        onClick={() => openModal(item, "in")}
                      >
                        + In
                      </button>
                      <button 
                        className="action-btn btn-out" 
                        title="Remove Stock (Out)"
                        onClick={() => openModal(item, "out")}
                      >
                        - Out
                      </button>
                      <button 
                        className="action-btn" 
                        title="View History"
                        onClick={() => openHistoryModal(item)}
                        style={{ background: "rgba(0, 240, 255, 0.05)", border: "1px solid rgba(0, 240, 255, 0.2)", color: "var(--primary)" }}
                      >
                        🕒
                      </button>
                      <button 
                        className="action-btn" 
                        title="Edit Item"
                        onClick={() => openEditModal(item)}
                        style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "var(--text-main)" }}
                      >
                        ✏️
                      </button>
                      <button 
                        className="action-btn" 
                        title="Delete Item"
                        onClick={() => setItemToDelete(item)}
                        style={{ background: "rgba(255,51,102,0.05)", border: "1px solid rgba(255,51,102,0.2)", color: "var(--danger)" }}
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filteredItems.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center empty-state">No items found in inventory.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Modal for Stock Actions */}
      {actionModal.isOpen && actionModal.item && (
        <div className="modal-overlay">
          <div className="modal-content animate-fade-in">
            <h2>
              {actionModal.type === "in" ? "Add Stock" : "Remove Stock"} - {actionModal.item.name}
            </h2>
            {actionModal.error && (
              <div style={{ marginBottom: "1rem", padding: "0.75rem", background: "rgba(255, 51, 102, 0.1)", border: "1px solid rgba(255, 51, 102, 0.3)", borderRadius: "8px", color: "var(--danger)", fontSize: "0.9rem" }}>
                {actionModal.error}
              </div>
            )}
            <form onSubmit={handleStockAction}>
              <div className="form-group">
                <label className="form-label">Quantity</label>
                <input 
                  type="number" 
                  className="form-control" 
                  min="1" 
                  value={actionModal.quantity} 
                  onChange={(e) => setActionModal(prev => ({...prev, quantity: e.target.value === "" ? ("" as any) : parseInt(e.target.value)}))}
                  required 
                />
              </div>
              <div className="form-group">
                <label className="form-label">Reference Number (Optional)</label>
                <input 
                  type="text" 
                  className="form-control" 
                  placeholder={actionModal.type === "in" ? "e.g. PO-2024-001" : "e.g. SO-2024-001"}
                  value={actionModal.reference_number} 
                  onChange={(e) => setActionModal(prev => ({...prev, reference_number: e.target.value}))} 
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Notes (Optional)</label>
                <textarea 
                  className="form-control" 
                  rows={2} 
                  value={actionModal.notes} 
                  onChange={(e) => setActionModal(prev => ({...prev, notes: e.target.value}))}
                ></textarea>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-outline" onClick={closeModal}>Cancel</button>
                <button type="submit" className={`btn ${actionModal.type === "in" ? "btn-primary" : "btn-danger"}`}>
                  Confirm {actionModal.type === "in" ? "In" : "Out"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal for New Item */}
      {newItemModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content animate-fade-in" style={{ maxWidth: "600px" }}>
            <h2>Create New Item</h2>
            {newItemForm.error && (
              <div style={{ marginBottom: "1rem", padding: "0.75rem", background: "rgba(255, 51, 102, 0.1)", border: "1px solid rgba(255, 51, 102, 0.3)", borderRadius: "8px", color: "var(--danger)", fontSize: "0.9rem" }}>
                {newItemForm.error}
              </div>
            )}
            <form onSubmit={handleCreateItem}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Name</label>
                  <input type="text" className="form-control" required value={newItemForm.name} onChange={e => setNewItemForm({...newItemForm, name: e.target.value})} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">SKU</label>
                  <input type="text" className="form-control" required value={newItemForm.sku} onChange={e => setNewItemForm({...newItemForm, sku: e.target.value})} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Unit Price (Rp)</label>
                  <input type="number" className="form-control" min="0" required value={newItemForm.unit_price} onChange={e => setNewItemForm({...newItemForm, unit_price: e.target.value === "" ? ("" as any) : parseInt(e.target.value)})} />
                </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                      <label className="form-label">Category</label>
                      <a href="#" onClick={(e) => { e.preventDefault(); setCreateCategoryModalOpen(true); }} style={{ color: "var(--primary)", fontSize: "0.85rem", textDecoration: "none" }}>+ New</a>
                    </div>
                    <select className="form-control" required value={newItemForm.category_id} onChange={e => setNewItemForm({...newItemForm, category_id: parseInt(e.target.value)})} style={{ appearance: "auto" }}>
                      {categories.length === 0 && <option value="" disabled>Loading...</option>}
                      {categories.map(c => (
                        <option key={c.id} value={c.id} style={{ color: "#000" }}>{c.name}</option>
                      ))}
                    </select>
                  </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Initial Stock</label>
                  <input type="number" className="form-control" min="0" required value={newItemForm.quantity_in_stock} onChange={e => setNewItemForm({...newItemForm, quantity_in_stock: e.target.value === "" ? ("" as any) : parseInt(e.target.value)})} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Reorder Level</label>
                  <input type="number" className="form-control" min="0" required value={newItemForm.reorder_level} onChange={e => setNewItemForm({...newItemForm, reorder_level: e.target.value === "" ? ("" as any) : parseInt(e.target.value)})} />
                </div>
              </div>
              <div className="form-group" style={{ marginTop: "1.5rem", marginBottom: 0 }}>
                <label className="form-label">Description (Optional)</label>
                <textarea className="form-control" rows={3} value={newItemForm.description} onChange={e => setNewItemForm({...newItemForm, description: e.target.value})}></textarea>
              </div>
              <div className="modal-actions" style={{ marginTop: "2rem" }}>
                <button type="button" className="btn btn-outline" onClick={() => setNewItemModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Item</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal for Edit Item */}
      {editItemModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content animate-fade-in" style={{ maxWidth: "600px" }}>
            <h2>Edit Item</h2>
            {editItemForm.error && (
              <div style={{ marginBottom: "1rem", padding: "0.75rem", background: "rgba(255, 51, 102, 0.1)", border: "1px solid rgba(255, 51, 102, 0.3)", borderRadius: "8px", color: "var(--danger)", fontSize: "0.9rem" }}>
                {editItemForm.error}
              </div>
            )}
            <form onSubmit={handleEditItem}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Name</label>
                  <input type="text" className="form-control" required value={editItemForm.name} onChange={e => setEditItemForm({...editItemForm, name: e.target.value})} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">SKU</label>
                  <input type="text" className="form-control" required value={editItemForm.sku} onChange={e => setEditItemForm({...editItemForm, sku: e.target.value})} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Unit Price (Rp)</label>
                  <input type="number" className="form-control" min="0" required value={editItemForm.unit_price} onChange={e => setEditItemForm({...editItemForm, unit_price: e.target.value === "" ? ("" as any) : parseInt(e.target.value)})} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                    <label className="form-label">Category</label>
                  </div>
                  <select className="form-control" required value={editItemForm.category_id} onChange={e => setEditItemForm({...editItemForm, category_id: parseInt(e.target.value)})} style={{ appearance: "auto" }}>
                    {categories.map(c => (
                      <option key={c.id} value={c.id} style={{ color: "#000" }}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Reorder Level</label>
                  <input type="number" className="form-control" min="0" required value={editItemForm.reorder_level} onChange={e => setEditItemForm({...editItemForm, reorder_level: e.target.value === "" ? ("" as any) : parseInt(e.target.value)})} />
                </div>
                {/* Notice: Stock quantity cannot be edited directly here, must use +In / -Out */}
              </div>
              <div className="form-group" style={{ marginTop: "1.5rem", marginBottom: 0 }}>
                <label className="form-label">Description (Optional)</label>
                <textarea className="form-control" rows={3} value={editItemForm.description} onChange={e => setEditItemForm({...editItemForm, description: e.target.value})}></textarea>
              </div>
              <div className="modal-actions" style={{ marginTop: "2rem" }}>
                <button type="button" className="btn btn-outline" onClick={() => setEditItemModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal for Create Category */}
      {createCategoryModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content animate-fade-in">
            <h2 style={{ marginBottom: "1.5rem", fontSize: "1.2rem" }}>Create New Category</h2>
            {categoryError && (
              <div style={{ marginBottom: "1rem", padding: "0.75rem", background: "rgba(255, 51, 102, 0.1)", border: "1px solid rgba(255, 51, 102, 0.3)", borderRadius: "8px", color: "var(--danger)", fontSize: "0.9rem" }}>
                {categoryError}
              </div>
            )}
            <form onSubmit={handleCreateCategory}>
              <div className="form-group">
                <label className="form-label">Category Name</label>
                <input type="text" className="form-control" required value={newCategoryName} onChange={e => setNewCategoryName(e.target.value)} autoFocus />
              </div>
              <div className="form-group">
                <label className="form-label">Description (Optional)</label>
                <textarea className="form-control" rows={2} value={newCategoryDesc} onChange={e => setNewCategoryDesc(e.target.value)}></textarea>
              </div>
              <div className="modal-actions" style={{ marginTop: "1.5rem" }}>
                <button type="button" className="btn btn-outline" onClick={() => setCreateCategoryModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal for Delete Confirmation */}
      {itemToDelete && (
        <div className="modal-overlay">
          <div className="modal-content animate-fade-in" style={{ maxWidth: "400px", textAlign: "center" }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🗑️</div>
            <h2 style={{ marginBottom: "1rem", color: "var(--danger)" }}>Hapus Barang?</h2>
            <p style={{ color: "var(--text-muted)", marginBottom: "2rem", lineHeight: "1.5" }}>
              Apakah Anda yakin ingin menghapus <strong>{itemToDelete.name} ({itemToDelete.sku})</strong>? 
              <br/><br/>
              Tindakan ini akan menonaktifkan barang tersebut dari peredaran.
            </p>
            <div className="modal-actions" style={{ justifyContent: "center", marginTop: 0 }}>
              <button type="button" className="btn btn-outline" onClick={() => setItemToDelete(null)}>Batal</button>
              <button type="button" className="btn btn-danger" onClick={confirmDelete}>Ya, Hapus</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal for Item History */}
      {historyModalOpen && (
        <div className="modal-overlay" onClick={() => setHistoryModalOpen(false)}>
          <div className="modal-content animate-fade-in" onClick={e => e.stopPropagation()} style={{ maxWidth: "800px" }}>
            <h2 style={{ marginBottom: "1.5rem" }}>History - {historyItem?.name}</h2>
            <div className="glass-panel" style={{ maxHeight: "400px", overflowY: "auto", padding: 0 }}>
              {historyLoading ? (
                <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>Loading history...</div>
              ) : (
                <table className="inventory-table" style={{ width: "100%", textAlign: "left", borderCollapse: "collapse" }}>
                  <thead style={{ position: "sticky", top: 0, background: "#151823" }}>
                    <tr>
                      <th style={{ padding: "1rem", borderBottom: "1px solid rgba(255,255,255,0.1)" }}>Date</th>
                      <th style={{ padding: "1rem", borderBottom: "1px solid rgba(255,255,255,0.1)" }}>Type</th>
                      <th style={{ padding: "1rem", borderBottom: "1px solid rgba(255,255,255,0.1)" }}>Qty</th>
                      <th style={{ padding: "1rem", borderBottom: "1px solid rgba(255,255,255,0.1)" }}>Ref #</th>
                      <th style={{ padding: "1rem", borderBottom: "1px solid rgba(255,255,255,0.1)" }}>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historyData.length === 0 ? (
                      <tr>
                        <td colSpan={5} style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>No transactions found for this item.</td>
                      </tr>
                    ) : (
                      historyData.map((tx: any) => (
                        <tr key={tx.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.02)" }}>
                          <td style={{ padding: "1rem", color: "var(--text-muted)" }}>{new Date(tx.created_at).toLocaleString()}</td>
                          <td style={{ padding: "1rem" }}>
                            <span className={`stock-badge ${tx.transaction_type === "IN" ? "good" : "low"}`} style={{ animation: "none" }}>
                              {tx.transaction_type}
                            </span>
                          </td>
                          <td style={{ padding: "1rem", fontWeight: "bold" }}>{tx.quantity}</td>
                          <td style={{ padding: "1rem", color: "var(--text-muted)" }}>{tx.reference_number || "-"}</td>
                          <td style={{ padding: "1rem", color: "var(--text-muted)" }}>{tx.notes || "-"}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              )}
            </div>
            <div className="modal-actions" style={{ marginTop: "1.5rem" }}>
              <button type="button" className="btn btn-outline" onClick={() => setHistoryModalOpen(false)}>Close</button>
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

        .inventory-table tbody tr.flash-in {
          animation: flashGreen 1.5s ease;
        }

        .inventory-table tbody tr.flash-out {
          animation: flashRed 1.5s ease;
        }

        @keyframes flashGreen {
          0% { background: rgba(0, 255, 157, 0.2); }
          100% { background: transparent; }
        }

        @keyframes flashRed {
          0% { background: rgba(255, 51, 102, 0.2); }
          100% { background: transparent; }
        }

        .font-mono {
          font-family: monospace;
          color: var(--primary);
        }

        .font-medium {
          font-weight: 500;
        }

        .stock-badge {
          display: inline-block;
          padding: 0.25rem 0.75rem;
          border-radius: 12px;
          font-weight: 600;
          font-size: 0.9rem;
        }

        .stock-badge.good {
          background: rgba(0, 255, 157, 0.1);
          color: var(--success);
        }

        .stock-badge.low {
          background: rgba(255, 51, 102, 0.1);
          color: var(--danger);
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0% { box-shadow: 0 0 0 0 rgba(255, 51, 102, 0.4); }
          70% { box-shadow: 0 0 0 6px rgba(255, 51, 102, 0); }
          100% { box-shadow: 0 0 0 0 rgba(255, 51, 102, 0); }
        }

        .status-dot {
          display: inline-block;
          width: 8px;
          height: 8px;
          border-radius: 50%;
          margin-right: 0.5rem;
        }

        .status-dot.active { background: var(--success); }
        .status-dot.inactive { background: var(--text-muted); }

        .action-buttons {
          display: flex;
          gap: 0.5rem;
        }

        .action-btn {
          padding: 0.4rem 0.8rem;
          border-radius: 6px;
          font-size: 0.85rem;
          font-weight: 600;
          cursor: pointer;
          border: 1px solid transparent;
          transition: all 0.2s;
        }

        .btn-in {
          background: rgba(0, 240, 255, 0.1);
          color: var(--primary);
          border-color: rgba(0, 240, 255, 0.2);
        }
        .btn-in:hover {
          background: var(--primary);
          color: #000;
        }

        .btn-out {
          background: rgba(255, 51, 102, 0.1);
          color: var(--danger);
          border-color: rgba(255, 51, 102, 0.2);
        }
        .btn-out:hover {
          background: var(--danger);
          color: #fff;
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

        .modal-content h2 {
          margin-bottom: 1.5rem;
          font-size: 1.5rem;
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
