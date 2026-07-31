import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';
import { formatCurrency, formatDate } from '../utils/formatters';
import { CalendarClock, Plus, CheckCircle2, AlertCircle, Clock, Trash2 } from 'lucide-react';

export const Bills = () => {
  const { user } = useAuth();
  const [bills, setBills] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [form, setForm] = useState({
    name: '',
    amount: '',
    due_date: new Date().toISOString().split('T')[0],
    recurrence: 'MONTHLY',
    reminder_days_before: 3,
    category: ''
  });

  const currency = user?.currency || 'INR';

  const fetchData = async () => {
    try {
      const [bRes, cRes] = await Promise.all([
        api.get('/bills/'),
        api.get('/categories/')
      ]);
      setBills(bRes.data);
      setCategories(cRes.data);
      if (cRes.data.length > 0) {
        setForm(f => ({ ...f, category: cRes.data[0].id }));
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

  const handleMarkPaid = async (id) => {
    try {
      await api.post(`/bills/${id}/mark-paid/`);
      await fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this bill reminder?')) return;
    try {
      await api.delete(`/bills/${id}/`);
      await fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddBill = async (e) => {
    e.preventDefault();
    try {
      await api.post('/bills/', form);
      setShowAddModal(false);
      await fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400 text-sm">Loading Bills & Reminders...</div>;
  }

  return (
    <div className="space-y-6 animate-in fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <CalendarClock className="h-6 w-6 text-amber-400" /> Bills & EMI Reminders
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Track upcoming recurring obligations & auto-log expenses when marked as paid.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-white font-semibold text-xs shadow-md shadow-amber-500/20 transition-all"
        >
          <Plus className="h-4 w-4" /> Add Bill / EMI Reminder
        </button>
      </div>

      {/* Bills Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {bills.map((bill) => (
          <div key={bill.id} className="glass-card rounded-2xl p-5 border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="font-bold text-sm text-white">{bill.name}</span>
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                  bill.is_paid
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                }`}>
                  {bill.is_paid ? 'Paid' : 'Pending'}
                </span>
              </div>

              <div className="text-xl font-extrabold text-amber-400 mb-2">
                {formatCurrency(bill.amount, currency)}
              </div>

              <div className="space-y-1 text-xs text-slate-400 mb-4">
                <div className="flex items-center justify-between">
                  <span>Due Date:</span>
                  <span className="font-semibold text-slate-200">{formatDate(bill.due_date)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Recurrence:</span>
                  <span className="font-semibold text-slate-200">{bill.recurrence}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Linked Category:</span>
                  <span className="font-semibold text-indigo-300">{bill.category_name || 'None'}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-800">
              <button
                onClick={() => handleDelete(bill.id)}
                className="text-xs text-slate-500 hover:text-rose-400"
              >
                <Trash2 className="h-4 w-4" />
              </button>

              {!bill.is_paid && (
                <button
                  onClick={() => handleMarkPaid(bill.id)}
                  className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 text-white font-bold text-xs shadow-md shadow-emerald-500/20 flex items-center gap-1.5"
                >
                  <CheckCircle2 className="h-3.5 w-3.5" /> Mark as Paid
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="glass-card w-full max-w-md rounded-2xl p-6 border border-slate-700">
            <h3 className="text-base font-bold text-white mb-4">Add Bill / EMI Reminder</h3>

            <form onSubmit={handleAddBill} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Bill Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Wi-Fi Broadband, Car EMI"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Amount</label>
                  <input
                    type="number"
                    required
                    placeholder="0.00"
                    value={form.amount}
                    onChange={(e) => setForm({ ...form, amount: e.target.value })}
                    className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Due Date</label>
                  <input
                    type="date"
                    required
                    value={form.due_date}
                    onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                    className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Linked Category</label>
                <select
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-xs"
                >
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
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
                  className="flex-1 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs"
                >
                  Save Bill
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
