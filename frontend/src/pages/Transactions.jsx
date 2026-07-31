import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import api from '../api/axios';
import { formatCurrency, formatDate } from '../utils/formatters';
import { Receipt, Search, Filter, Trash2, ShieldCheck, Inbox } from 'lucide-react';

export const Transactions = () => {
  const { user } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedType, setSelectedType] = useState('');

  const currency = user?.currency || 'INR';

  const fetchData = async () => {
    try {
      const [txRes, catRes] = await Promise.all([
        api.get('/transactions/'),
        api.get('/categories/')
      ]);
      setTransactions(txRes.data);
      setCategories(catRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this transaction record? Category balance will be re-adjusted.')) return;
    try {
      await api.delete(`/transactions/${id}/`);
      await fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  const filteredTransactions = transactions.filter((tx) => {
    const matchesSearch =
      tx.merchant?.toLowerCase().includes(search.toLowerCase()) ||
      tx.note?.toLowerCase().includes(search.toLowerCase()) ||
      tx.category_name?.toLowerCase().includes(search.toLowerCase());

    const matchesCat = !selectedCategory || tx.category?.toString() === selectedCategory;
    const matchesType = !selectedType || tx.type === selectedType;

    return matchesSearch && matchesCat && matchesType;
  });

  if (loading) {
    return <div className="p-8 text-center text-slate-400 text-sm">Loading Transaction Ledger...</div>;
  }

  return (
    <div className="space-y-6 animate-in fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Receipt className="h-6 w-6 text-indigo-400" /> Transaction Ledger
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Audit log of auto-detected bank expenses, monthly allocations, and Smart Cover transfers.
          </p>
        </div>

        <Link
          to="/review-inbox"
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-md shadow-amber-500/20 transition-all"
        >
          <Inbox className="h-4 w-4" /> Review Inbox
        </Link>
      </div>

      {/* Filter Bar */}
      <div className="glass-card rounded-2xl p-4 border border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="relative">
          <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search merchant, note..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Transaction Types</option>
            <option value="EXPENSE">Expenses Only</option>
            <option value="ALLOCATION">Allocations Only</option>
            <option value="AUTO_TRANSFER">Smart Cover Transfers</option>
          </select>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="glass-card rounded-2xl overflow-hidden border border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="p-4">Date</th>
                <th className="p-4">Merchant / Detail</th>
                <th className="p-4">Category</th>
                <th className="p-4">Type</th>
                <th className="p-4">Amount</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredTransactions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400">
                    No transactions match your search filters
                  </td>
                </tr>
              ) : (
                filteredTransactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="p-4 text-slate-400 font-medium">{formatDate(tx.date)}</td>
                    <td className="p-4">
                      <span className="font-bold text-white block">{tx.merchant || 'N/A'}</span>
                      {tx.note && <span className="text-[11px] text-slate-400 block">{tx.note}</span>}
                    </td>
                    <td className="p-4 font-semibold text-slate-200">
                      {tx.category_name || 'N/A'}
                    </td>
                    <td className="p-4">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${
                        tx.type === 'EXPENSE'
                          ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                          : tx.type === 'AUTO_TRANSFER'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                      }`}>
                        {tx.type}
                      </span>
                    </td>
                    <td className={`p-4 font-extrabold ${tx.type === 'EXPENSE' ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {tx.type === 'EXPENSE' ? '-' : '+'}{formatCurrency(tx.amount, currency)}
                    </td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => handleDelete(tx.id)}
                        className="p-1.5 rounded-lg bg-slate-900 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 border border-slate-800 transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
