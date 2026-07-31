import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';
import { formatCurrency, formatDate } from '../utils/formatters';
import { PieChart, RefreshCw, Plus, Edit2, Save, Trash2, CheckCircle2, History, AlertCircle } from 'lucide-react';

export const Categories = () => {
  const { user } = useAuth();
  const [categories, setCategories] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [allocating, setAllocating] = useState(false);
  const [message, setMessage] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', allocation_type: 'PERCENTAGE', allocation_value: 0, color: '#6366f1' });

  const currency = user?.currency || 'INR';

  const fetchData = async () => {
    try {
      const [catRes, histRes] = await Promise.all([
        api.get('/categories/'),
        api.get('/categories/allocation-history/')
      ]);
      setCategories(catRes.data);
      setHistory(histRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const totalPercentage = categories
    .filter(c => c.allocation_type === 'PERCENTAGE')
    .reduce((sum, c) => sum + parseFloat(c.allocation_value || 0), 0);

  const startEdit = (cat) => {
    setEditingId(cat.id);
    setEditForm({
      name: cat.name,
      allocation_type: cat.allocation_type,
      allocation_value: cat.allocation_value,
      color: cat.color
    });
  };

  const handleSaveEdit = async (id) => {
    setSaving(true);
    try {
      await api.put(`/categories/${id}/`, editForm);
      setEditingId(null);
      await fetchData();
      setMessage('Category updated successfully');
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const handleRunAllocation = async () => {
    setAllocating(true);
    setMessage('');
    try {
      const res = await api.post('/categories/run-allocation/');
      setMessage('Salary allocation executed successfully!');
      await fetchData();
    } catch (e) {
      console.error(e);
    } finally {
      setAllocating(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400 text-sm">Loading Salary & Category Engine...</div>;
  }

  return (
    <div className="space-y-6 animate-in fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <PieChart className="h-6 w-6 text-indigo-400" /> Salary Allocation Engine
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Configure percentage or fixed-amount distribution rules for your monthly salary ({formatCurrency(user?.monthly_salary, currency)})
          </p>
        </div>

        <button
          onClick={handleRunAllocation}
          disabled={allocating}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-bold text-xs shadow-lg shadow-emerald-500/20 transition-all"
        >
          <RefreshCw className={`h-4 w-4 ${allocating ? 'animate-spin' : ''}`} />
          <span>{allocating ? 'Processing Allocation...' : 'Run Salary Allocation Now'}</span>
        </button>
      </div>

      {message && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4" /> {message}
        </div>
      )}

      {/* Percentage Total Indicator */}
      <div className="glass-card rounded-2xl p-5 border border-slate-800 flex items-center justify-between">
        <div>
          <span className="text-xs text-slate-400 block font-medium">Percentage Category Sum</span>
          <span className="text-lg font-bold text-white">{totalPercentage.toFixed(1)}% of Salary</span>
        </div>

        <div className={`px-3 py-1.5 rounded-xl text-xs font-bold border ${
          Math.round(totalPercentage) === 100
            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
            : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
        }`}>
          {Math.round(totalPercentage) === 100 ? 'Valid 100% Allocation' : 'Adjustment Needed'}
        </div>
      </div>

      {/* Categories Manager Table */}
      <div className="glass-card rounded-2xl overflow-hidden border border-slate-800">
        <div className="p-5 border-b border-slate-800">
          <h3 className="font-bold text-sm text-white">Active Categories ({categories.length})</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="p-4">Category</th>
                <th className="p-4">Allocation Type</th>
                <th className="p-4">Value</th>
                <th className="p-4">Monthly Allocation</th>
                <th className="p-4">Current Balance</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {categories.map((cat) => (
                <tr key={cat.id} className="hover:bg-slate-900/40 transition-colors">
                  <td className="p-4">
                    {editingId === cat.id ? (
                      <input
                        type="text"
                        value={editForm.name}
                        onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                        className="px-2 py-1 rounded bg-slate-950 border border-slate-700 text-white"
                      />
                    ) : (
                      <span className="font-bold text-white flex items-center gap-2">
                        <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: cat.color }} />
                        {cat.name}
                        {cat.is_savings_category && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-semibold">
                            Buffer
                          </span>
                        )}
                      </span>
                    )}
                  </td>
                  <td className="p-4">
                    {editingId === cat.id ? (
                      <select
                        value={editForm.allocation_type}
                        onChange={(e) => setEditForm({ ...editForm, allocation_type: e.target.value })}
                        className="px-2 py-1 rounded bg-slate-950 border border-slate-700 text-white"
                      >
                        <option value="PERCENTAGE">Percentage</option>
                        <option value="FIXED">Fixed Amount</option>
                      </select>
                    ) : (
                      <span className="font-medium text-slate-400">{cat.allocation_type}</span>
                    )}
                  </td>
                  <td className="p-4 font-bold text-white">
                    {editingId === cat.id ? (
                      <input
                        type="number"
                        step="0.1"
                        value={editForm.allocation_value}
                        onChange={(e) => setEditForm({ ...editForm, allocation_value: parseFloat(e.target.value) || 0 })}
                        className="w-20 px-2 py-1 rounded bg-slate-950 border border-slate-700 text-white"
                      />
                    ) : (
                      `${cat.allocation_value}${cat.allocation_type === 'PERCENTAGE' ? '%' : ' ' + currency}`
                    )}
                  </td>
                  <td className="p-4 font-semibold text-emerald-400">
                    {formatCurrency(cat.allocated_monthly_amount, currency)}
                  </td>
                  <td className="p-4 font-semibold text-slate-200">
                    {formatCurrency(cat.current_balance, currency)}
                  </td>
                  <td className="p-4 text-right">
                    {editingId === cat.id ? (
                      <button
                        onClick={() => handleSaveEdit(cat.id)}
                        disabled={saving}
                        className="p-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white"
                      >
                        <Save className="h-4 w-4" />
                      </button>
                    ) : (
                      <button
                        onClick={() => startEdit(cat)}
                        className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Allocation History Log */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800">
        <h3 className="font-bold text-sm text-white mb-4 flex items-center gap-2">
          <History className="h-4 w-4 text-indigo-400" /> Salary Credit & Allocation Run History
        </h3>

        <div className="space-y-3">
          {history.length === 0 ? (
            <p className="text-xs text-slate-400 py-4 text-center">No allocation runs logged yet</p>
          ) : (
            history.map((run) => (
              <div key={run.id} className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
                <div>
                  <span className="font-bold text-white block">Monthly Salary Distribution Run #{run.id}</span>
                  <span className="text-[11px] text-slate-400">{formatDate(run.run_date)}</span>
                </div>
                <div className="text-right">
                  <span className="font-bold text-emerald-400 block">{formatCurrency(run.salary_amount, currency)}</span>
                  <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400">
                    {run.status}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
