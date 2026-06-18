"use client";

import { useEffect, useState } from "react";
import { fetchJson } from "../../lib/apiClient";

export default function CategoriesPage() {
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // New Category State
  const [newModalOpen, setNewModalOpen] = useState(false);
  const [newForm, setNewForm] = useState({ name: "", description: "" });

  // Edit Category State
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({ name: "", description: "" });

  // Delete State
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [deleteName, setDeleteName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadCategories = async () => {
    setLoading(true);
    try {
      const response = await fetchJson<any>("/categories");
      setCategories(Array.isArray(response) ? response : (response.data || []));
    } catch (error) {
      console.error("Failed to load categories", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCategories();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await fetchJson("/categories", {
        method: "POST",
        body: JSON.stringify({
          name: newForm.name,
          description: newForm.description || undefined
        }),
      });
      setNewModalOpen(false);
      setNewForm({ name: "", description: "" });
      loadCategories();
    } catch (error: any) {
      alert("Failed to create category: " + error.message);
    } finally {
      setSubmitting(false);
    }
  };

  const openEditModal = (category: any) => {
    setEditId(category.id);
    setEditForm({ name: category.name, description: category.description || "" });
    setEditModalOpen(true);
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editId) return;
    setSubmitting(true);
    try {
      await fetchJson(`/categories/${editId}`, {
        method: "PATCH",
        body: JSON.stringify({
          name: editForm.name,
          description: editForm.description || undefined
        }),
      });
      setEditModalOpen(false);
      loadCategories();
    } catch (error: any) {
      alert("Failed to update category: " + error.message);
    } finally {
      setSubmitting(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteId) return;
    setSubmitting(true);
    try {
      await fetchJson(`/categories/${deleteId}`, { method: "DELETE" });
      setDeleteId(null);
      loadCategories();
    } catch (error: any) {
      alert("Failed to delete category: " + error.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1>Category Management</h1>
        <button className="btn btn-primary" onClick={() => setNewModalOpen(true)}>+ New Category</button>
      </div>

      <div className="glass-panel table-container">
        <table className="category-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Category Name</th>
              <th>Description</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              [1, 2, 3, 4].map((n) => (
                <tr key={n}>
                  <td className="font-mono">
                    <div className="skeleton" style={{ width: "40px", height: "1.2rem" }}></div>
                  </td>
                  <td className="font-medium">
                    <div className="skeleton" style={{ width: "120px", height: "1.2rem" }}></div>
                  </td>
                  <td>
                    <div className="skeleton" style={{ width: "200px", height: "1.2rem" }}></div>
                  </td>
                  <td>
                    <div className="skeleton" style={{ width: "60px", height: "1.2rem" }}></div>
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <div className="skeleton" style={{ width: "60px", height: "1.8rem", borderRadius: "6px" }}></div>
                      <div className="skeleton" style={{ width: "70px", height: "1.8rem", borderRadius: "6px" }}></div>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              categories.map((c) => (
                <tr key={c.id}>
                  <td className="font-mono">#{c.id}</td>
                  <td className="font-medium">{c.name}</td>
                  <td style={{ color: "var(--text-muted)", maxWidth: "300px" }}>{c.description || "-"}</td>
                  <td>
                    <span className={`status-dot ${c.is_active ? "active" : "inactive"}`}></span>
                    {c.is_active ? "Active" : "Inactive"}
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button 
                        className="action-btn" 
                        title="Edit Category"
                        onClick={() => openEditModal(c)}
                        style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "var(--text-main)" }}
                      >
                        ✏️ Edit
                      </button>
                      <button 
                        className="action-btn" 
                        title="Delete Category"
                        onClick={() => { setDeleteId(c.id); setDeleteName(c.name); }}
                        style={{ background: "rgba(255,51,102,0.05)", border: "1px solid rgba(255,51,102,0.2)", color: "var(--danger)" }}
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
            {!loading && categories.length === 0 && (
              <tr>
                <td colSpan={5} className="text-center empty-state">No categories found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* New Category Modal */}
      {newModalOpen && (
        <div className="modal-overlay" onClick={() => setNewModalOpen(false)}>
          <div className="modal-content animate-fade-in" onClick={e => e.stopPropagation()}>
            <h2 style={{ marginBottom: "1.5rem" }}>Create New Category</h2>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label className="form-label">Category Name</label>
                <input type="text" className="form-control" required autoFocus value={newForm.name} onChange={e => setNewForm({...newForm, name: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Description (Optional)</label>
                <textarea className="form-control" rows={3} value={newForm.description} onChange={e => setNewForm({...newForm, description: e.target.value})}></textarea>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-outline" onClick={() => setNewModalOpen(false)} disabled={submitting}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? "Creating..." : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Category Modal */}
      {editModalOpen && (
        <div className="modal-overlay" onClick={() => setEditModalOpen(false)}>
          <div className="modal-content animate-fade-in" onClick={e => e.stopPropagation()}>
            <h2 style={{ marginBottom: "1.5rem" }}>Edit Category</h2>
            <form onSubmit={handleEdit}>
              <div className="form-group">
                <label className="form-label">Category Name</label>
                <input type="text" className="form-control" required autoFocus value={editForm.name} onChange={e => setEditForm({...editForm, name: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Description (Optional)</label>
                <textarea className="form-control" rows={3} value={editForm.description} onChange={e => setEditForm({...editForm, description: e.target.value})}></textarea>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-outline" onClick={() => setEditModalOpen(false)} disabled={submitting}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteId && (
        <div className="modal-overlay" onClick={() => setDeleteId(null)}>
          <div className="modal-content animate-fade-in" onClick={e => e.stopPropagation()} style={{ maxWidth: "400px", textAlign: "center" }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🗑️</div>
            <h2 style={{ marginBottom: "1rem", color: "var(--danger)" }}>Delete Category?</h2>
            <p style={{ color: "var(--text-muted)", marginBottom: "2rem", lineHeight: "1.5" }}>
              Are you sure you want to delete <strong>{deleteName}</strong>? 
              <br/><br/>
              This will only work if there are no items attached to this category.
            </p>
            <div className="modal-actions" style={{ justifyContent: "center", marginTop: 0 }}>
              <button type="button" className="btn btn-outline" onClick={() => setDeleteId(null)} disabled={submitting}>Cancel</button>
              <button type="button" className="btn btn-danger" onClick={confirmDelete} disabled={submitting}>
                {submitting ? "Deleting..." : "Yes, Delete"}
              </button>
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

        .category-table {
          width: 100%;
          border-collapse: collapse;
          text-align: left;
        }

        .category-table th {
          padding: 1rem;
          color: var(--text-muted);
          font-weight: 500;
          border-bottom: 1px solid var(--glass-border);
        }

        .category-table td {
          padding: 1rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.02);
          color: var(--text-main);
          vertical-align: middle;
        }

        .category-table tbody tr:hover {
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
