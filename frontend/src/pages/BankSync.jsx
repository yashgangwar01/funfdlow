import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';
import { formatDate } from '../utils/formatters';
import { Landmark, ShieldCheck, RefreshCw, ExternalLink, CheckCircle2, Clock, AlertTriangle, ArrowRight } from 'lucide-react';

export const BankSync = () => {
  const { user } = useAuth();
  const [consents, setConsents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState('');

  const fetchConsents = async () => {
    try {
      const res = await api.get('/bank-sync/consents/');
      setConsents(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConsents();
  }, []);

  const handleLinkBank = async () => {
    setConnecting(true);
    setMessage('');
    try {
      const res = await api.post('/bank-sync/consent/', {});
      const redirectUrl = res.data.redirect_url;
      setMessage('Redirecting to Setu AA Consent Screen...');
      if (redirectUrl) {
        window.open(redirectUrl, '_blank');
      }
      await fetchConsents();
    } catch (e) {
      console.error(e);
      setMessage('Failed to initiate Setu consent flow.');
    } finally {
      setConnecting(false);
    }
  };

  const handleManualSync = async () => {
    setSyncing(true);
    setMessage('');
    try {
      const res = await api.post('/bank-sync/sync/', {});
      setMessage(res.data.message || 'Bank sync completed. Unreviewed transactions sent to Review Inbox.');
      await fetchConsents();
    } catch (e) {
      setMessage(e.response?.data?.error || 'Failed to sync bank data.');
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400 text-sm">Loading Setu Bank Sync Status...</div>;
  }

  const activeConsent = consents.find(c => c.status === 'APPROVED');

  return (
    <div className="space-y-6 animate-in fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Landmark className="h-6 w-6 text-indigo-400" /> Setu Account Aggregator (AA) Bank Sync
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Connect your bank accounts securely via RBI-regulated Setu Account Aggregator. FundFlow automatically syncs transaction statements into your Review Inbox.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleManualSync}
            disabled={syncing}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 font-semibold text-xs border border-slate-800 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 text-emerald-400 ${syncing ? 'animate-spin' : ''}`} />
            <span>{syncing ? 'Syncing Transactions...' : 'Sync Now'}</span>
          </button>

          <button
            onClick={handleLinkBank}
            disabled={connecting}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-semibold text-xs shadow-md shadow-indigo-500/25 transition-all"
          >
            <ExternalLink className="h-4 w-4" />
            <span>{connecting ? 'Launching Setu AA...' : 'Link Bank Account'}</span>
          </button>
        </div>
      </div>

      {message && (
        <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4" /> {message}
        </div>
      )}

      {/* Connection Status Banner */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950/30 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
              activeConsent
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
            }`}>
              {activeConsent ? 'Bank Account Linked ✅' : 'Setu AA Consent Pending'}
            </span>
          </div>

          <h2 className="text-xl font-bold text-white">
            {activeConsent ? 'Automated Bank Data Feed Active' : 'Link Bank Account to Enable Auto-Sync'}
          </h2>
          <p className="text-xs text-slate-300 max-w-xl leading-relaxed">
            Setu Account Aggregator uses 256-bit encrypted data sharing regulated by RBI. Raw bank narrations are mapped and categorized automatically by FundFlow's learning engine.
          </p>
        </div>

        <button
          onClick={handleLinkBank}
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-500/20 flex items-center gap-2 shrink-0"
        >
          {activeConsent ? 'Re-Authorize / Add Bank' : 'Launch Consent Screen'} <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      {/* Consents History Table */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800">
        <h3 className="font-bold text-sm text-white mb-4 flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-emerald-400" /> Setu AA Consents ({consents.length})
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3">Consent Handle</th>
                <th className="p-3">Status</th>
                <th className="p-3">Created At</th>
                <th className="p-3">Consent URL</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {consents.length === 0 ? (
                <tr>
                  <td colSpan={4} className="p-4 text-center text-slate-400">
                    No Setu AA consent requests created yet. Click "Link Bank Account" to initiate.
                  </td>
                </tr>
              ) : (
                consents.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-900/40">
                    <td className="p-3 font-mono font-bold text-white">{item.consent_handle}</td>
                    <td className="p-3">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${
                        item.status === 'APPROVED'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : item.status === 'PENDING'
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                      }`}>
                        {item.status}
                      </span>
                    </td>
                    <td className="p-3 text-slate-400">{formatDate(item.created_at)}</td>
                    <td className="p-3">
                      {item.redirect_url ? (
                        <a
                          href={item.redirect_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-400 font-semibold hover:underline flex items-center gap-1"
                        >
                          Launch Screen <ExternalLink className="h-3 w-3" />
                        </a>
                      ) : (
                        <span className="text-slate-500">N/A</span>
                      )}
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
