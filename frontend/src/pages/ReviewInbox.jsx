import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';
import { formatCurrency, formatDate } from '../utils/formatters';
import { Inbox, CheckCircle2, XCircle, Sparkles, ShieldCheck, ArrowRight, RefreshCw, Bookmark } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const ReviewInbox = () => {
  const { user } = useAuth();
  const [pendingTx, setPendingTx] = useState([]);
  const [categories, setCategories] = useState([]);
  const [learnedMaps, setLearnedMaps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCatMap, setSelectedCatMap] = useState({});
  const [actionLoading, setActionLoading] = useState({});

  const currency = user?.currency || 'INR';

  const fetchData = async () => {
    try {
      const [pendingRes, catRes, mapsRes] = await Promise.all([
        api.get('/bank-transactions/?status=NEEDS_REVIEW'),
        api.get('/categories/'),
        api.get('/merchant-category-map/')
      ]);
      setPendingTx(pendingRes.data);
      setCategories(catRes.data);
      setLearnedMaps(mapsRes.data);

      const initialSelected = {};
      pendingRes.data.forEach(item => {
        if (item.matched_category) {
          initialSelected[item.id] = item.matched_category;
        } else if (catRes.data.length > 0) {
          initialSelected[item.id] = catRes.data[0].id;
        }
      });
      setSelectedCatMap(initialSelected);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleConfirmOrReassign = async (item) => {
    const chosenCatId = selectedCatMap[item.id];
    if (!chosenCatId) return;

    setActionLoading(prev => ({ ...prev, [item.id]: true }));

    // Optimistic UI Removal
    const previousPending = [...pendingTx];
    setPendingTx(prev => prev.filter(t => t.id !== item.id));

    try {
      await api.post(`/bank-transactions/${item.id}/confirm/`, {
        matched_category: chosenCatId
      });
      // Refresh learned maps in background
      const mapsRes = await api.get('/merchant-category-map/');
      setLearnedMaps(mapsRes.data);
    } catch (e) {
      console.error('Failed to confirm transaction', e);
      // Rollback on error
      setPendingTx(previousPending);
    } finally {
      setActionLoading(prev => ({ ...prev, [item.id]: false }));
    }
  };

  const handleIgnore = async (id) => {
    setActionLoading(prev => ({ ...prev, [id]: true }));
    const previousPending = [...pendingTx];
    setPendingTx(prev => prev.filter(t => t.id !== id));

    try {
      await api.post(`/bank-transactions/${id}/ignore/`);
    } catch (e) {
      console.error('Failed to ignore transaction', e);
      setPendingTx(previousPending);
    } finally {
      setActionLoading(prev => ({ ...prev, [id]: false }));
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400 text-sm">Loading Review Inbox...</div>;
  }

  return (
    <div className="space-y-6 animate-in fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Inbox className="h-6 w-6 text-indigo-400" /> Auto-Detected Review Inbox
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Confirm or reassign auto-detected bank transactions. FundFlow learns from your choices to auto-confirm future transactions.
          </p>
        </div>

        <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-bold text-xs">
          <Sparkles className="h-4 w-4 text-indigo-400" />
          <span>{pendingTx.length} Transactions Need Review</span>
        </div>
      </div>

      {/* Review Inbox List */}
      <div className="space-y-4">
        {pendingTx.length === 0 ? (
          <div className="glass-card rounded-2xl p-12 text-center border border-slate-800">
            <div className="h-12 w-12 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto mb-3 border border-emerald-500/20">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <h3 className="text-base font-bold text-white mb-1">Review Inbox is All Clear!</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              All auto-detected bank expenses have been confirmed or auto-matched via learned merchant patterns.
            </p>
          </div>
        ) : (
          <AnimatePresence>
            {pendingTx.map((item) => {
              const confidencePct = Math.round((item.confidence_score || 0) * 100);
              return (
                <motion.div
                  key={item.id}
                  layout
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="glass-card rounded-2xl p-5 border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-sm">{item.normalized_merchant}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        confidencePct > 70
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                          : 'bg-slate-800 text-slate-400'
                      }`}>
                        {confidencePct > 0 ? `${confidencePct}% Confidence Guess` : 'New Unmatched Merchant'}
                      </span>
                    </div>

                    <p className="text-xs text-slate-400 font-mono truncate max-w-lg">
                      {item.raw_narration}
                    </p>
                    <span className="text-[11px] text-slate-500 block">{formatDate(item.date)}</span>
                  </div>

                  <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                    <div className="text-right sm:text-right font-extrabold text-white text-base">
                      {formatCurrency(item.amount, currency)}
                    </div>

                    {/* Category Dropdown */}
                    <div className="w-full sm:w-52">
                      <select
                        value={selectedCatMap[item.id] || ''}
                        onChange={(e) => setSelectedCatMap({ ...selectedCatMap, [item.id]: e.target.value })}
                        className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-slate-100 font-medium focus:outline-none focus:border-indigo-500"
                      >
                        {categories.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleConfirmOrReassign(item)}
                        disabled={actionLoading[item.id]}
                        className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-bold text-xs shadow-md shadow-emerald-500/20 flex items-center gap-1.5 transition-all"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5" /> Confirm & Learn
                      </button>

                      <button
                        onClick={() => handleIgnore(item.id)}
                        disabled={actionLoading[item.id]}
                        className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 transition-colors"
                        title="Ignore Transaction"
                      >
                        <XCircle className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>

      {/* Learned Merchant Patterns Table */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800">
        <h3 className="font-bold text-sm text-white mb-4 flex items-center gap-2">
          <Bookmark className="h-4 w-4 text-indigo-400" /> Learned Merchant & Category Memory ({learnedMaps.length})
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3">Merchant Key</th>
                <th className="p-3">Assigned Category</th>
                <th className="p-3">Match Count</th>
                <th className="p-3">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {learnedMaps.length === 0 ? (
                <tr>
                  <td colSpan={4} className="p-4 text-center text-slate-400">
                    No merchant patterns learned yet. Confirm transactions above to train the matcher.
                  </td>
                </tr>
              ) : (
                learnedMaps.map((map) => (
                  <tr key={map.id} className="hover:bg-slate-900/40">
                    <td className="p-3 font-bold text-white">{map.merchant_pattern}</td>
                    <td className="p-3 font-semibold text-emerald-400">{map.category_name}</td>
                    <td className="p-3 font-semibold text-indigo-300">{map.match_count} times</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        {map.source}
                      </span>
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
