import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';
import { formatCurrency, formatDate } from '../utils/formatters';
import { ShieldCheck, Plus, ToggleLeft, ToggleRight, ArrowRight, ShieldAlert, History, Trash2 } from 'lucide-react';

export const SmartCover = () => {
  const { user } = useAuth();
  const [rules, setRules] = useState([]);
  const [logs, setLogs] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [form, setForm] = useState({
    category: '',
    source_category: '',
    trigger_threshold: 0,
    transfer_type: 'COVER_DEFICIT',
    transfer_amount: 1000,
    priority: 1,
    is_active: true
  });

  const currency = user?.currency || 'INR';

  const fetchData = async () => {
    try {
      const [rulesRes, logsRes, catRes] = await Promise.all([
        api.get('/transactions/overflow-rules/'),
        api.get('/transactions/auto-transfer-logs/'),
        api.get('/categories/')
      ]);
      setRules(rulesRes.data);
      setLogs(logsRes.data);
      setCategories(catRes.data);

      const savingsCat = catRes.data.find(c => c.is_savings_category);
      const otherCat = catRes.data.find(c => !c.is_savings_category);
      if (savingsCat && otherCat) {
        setForm(f => ({ ...f, source_category: savingsCat.id, category: otherCat.id }));
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleToggleActive = async (rule) => {
    try {
      await api.put(`/transactions/overflow-rules/${rule.id}/`, {
        ...rule,
        is_active: !rule.is_active
      });
      await fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteRule = async (id) => {
    if (!window.confirm('Delete this Smart Cover rule?')) return;
    try {
      await api.delete(`/transactions/overflow-rules/${id}/`);
      await fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddRule = async (e) => {
    e.preventDefault();
    try {
      await api.post('/transactions/overflow-rules/', form);
      setShowAddModal(false);
      await fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400 text-sm">Loading Smart Cover Engine...</div>;
  }

  return (
    <div className="space-y-6 animate-in fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-emerald-400" /> Smart Cover (Overflow Rules)
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Automated overflow rules that auto-transfer funds from Savings when spending categories deplete.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-semibold text-xs shadow-md shadow-emerald-500/20 transition-all"
        >
          <Plus className="h-4 w-4" /> Create Smart Cover Rule
        </button>
      </div>

      {/* Rules Grid */}
      <div className="space-y-4">
        <h3 className="font-bold text-sm text-white">Active Smart Cover Rules ({rules.length})</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {rules.map((rule) => (
            <div key={rule.id} className="glass-card rounded-2xl p-5 border border-slate-800 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2 text-xs font-bold text-white">
                    <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                      Priority {rule.priority}
                    </span>
                    <span>{rule.category_name}</span>
                  </div>

                  <button
                    onClick={() => handleToggleActive(rule)}
                    className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-white"
                  >
                    {rule.is_active ? (
                      <span className="text-emerald-400 flex items-center gap-1">Active <ToggleRight className="h-5 w-5" /></span>
                    ) : (
                      <span className="text-slate-500 flex items-center gap-1">Paused <ToggleLeft className="h-5 w-5" /></span>
                    )}
                  </button>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs space-y-2 mb-3">
                  <div className="flex items-center justify-between text-slate-300">
                    <span>Source Buffer:</span>
                    <span className="font-bold text-emerald-400">{rule.source_category_name}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-300">
                    <span>Trigger Threshold:</span>
                    <span className="font-bold text-slate-100">Balance &lt; {formatCurrency(rule.trigger_threshold, currency)}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-300">
                    <span>Transfer Type:</span>
                    <span className="font-bold text-indigo-300">{rule.transfer_type === 'COVER_DEFICIT' ? 'Cover Full Deficit' : `Fixed ${formatCurrency(rule.transfer_amount, currency)}`}</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  onClick={() => handleDeleteRule(rule.id)}
                  className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1 font-semibold"
                >
                  <Trash2 className="h-3.5 w-3.5" /> Remove Rule
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Auto Transfer Audit Trail */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800">
        <h3 className="font-bold text-sm text-white mb-4 flex items-center gap-2">
          <History className="h-4 w-4 text-emerald-400" /> Auto-Transfer Audit Log
        </h3>

        <div className="space-y-3">
          {logs.length === 0 ? (
            <p className="text-xs text-slate-400 py-6 text-center">No auto-transfers executed yet</p>
          ) : (
            logs.map((log) => (
              <div key={log.id} className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <ShieldAlert className="h-4 w-4 text-emerald-400 shrink-0" />
                  <div>
                    <span className="font-bold text-white block">
                      {log.from_category_name} &rarr; {log.to_category_name}
                    </span>
                    <span className="text-[11px] text-slate-400">{log.reason} &bull; {formatDate(log.created_at)}</span>
                  </div>
                </div>
                <div className="font-extrabold text-emerald-400 text-sm">
                  +{formatCurrency(log.amount, currency)}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Add Rule Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="glass-card w-full max-w-md rounded-2xl p-6 border border-slate-700">
            <h3 className="text-base font-bold text-white mb-4">Create Smart Cover Overflow Rule</h3>

            <form onSubmit={handleAddRule} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Protected Category</label>
                <select
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-xs"
                >
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Source Buffer Category (Savings)</label>
                <select
                  value={form.source_category}
                  onChange={(e) => setForm({ ...form, source_category: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-xs"
                >
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Transfer Mode</label>
                <select
                  value={form.transfer_type}
                  onChange={(e) => setForm({ ...form, transfer_type: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-xs"
                >
                  <option value="COVER_DEFICIT">Cover Exact Shortfall / Deficit</option>
                  <option value="FIXED_AMOUNT">Fixed Transfer Amount</option>
                </select>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-2.5 rounded-xl bg-slate-900 text-slate-300 font-semibold text-xs border border-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs"
                >
                  Save Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
