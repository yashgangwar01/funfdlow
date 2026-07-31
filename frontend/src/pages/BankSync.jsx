import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';
import { formatDate } from '../utils/formatters';
import { AA_PROVIDERS } from '../utils/aaProviders';
import {
  Landmark, ShieldCheck, RefreshCw, ExternalLink, CheckCircle2,
  AlertTriangle, ArrowRight, Phone, ChevronDown, Info, X
} from 'lucide-react';

export const BankSync = () => {
  const { user } = useAuth();
  const [consents, setConsents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('info'); // 'info' | 'error'

  // VUA form state
  const [showVuaForm, setShowVuaForm] = useState(false);
  const [phone, setPhone] = useState('');
  const [aaProvider, setAaProvider] = useState(AA_PROVIDERS[0]?.handle || '');
  const [connecting, setConnecting] = useState(false);
  const [phoneError, setPhoneError] = useState('');

  // Optionally fetch provider list from backend (falls back to static list)
  const [providers, setProviders] = useState(AA_PROVIDERS);

  useEffect(() => {
    fetchConsents();
    api.get('/bank-sync/aa-providers/')
      .then(res => { if (res.data?.length) setProviders(res.data); })
      .catch(() => {}); // silently use static fallback
  }, []);

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

  const validatePhone = (val) => {
    if (!/^\d{10}$/.test(val)) return 'Enter a valid 10-digit mobile number.';
    return '';
  };

  const handleLinkBank = async (e) => {
    e.preventDefault();
    const err = validatePhone(phone);
    if (err) { setPhoneError(err); return; }
    setPhoneError('');

    const vua = `${phone}@${aaProvider}`;
    setConnecting(true);
    setMessage('');
    try {
      const res = await api.post('/bank-sync/consent/', { vua });
      const redirectUrl = res.data.redirect_url;
      setMessage('Redirecting to Setu AA Consent Screen…');
      setMessageType('info');
      setShowVuaForm(false);
      setPhone('');
      if (redirectUrl) window.open(redirectUrl, '_blank');
      await fetchConsents();
    } catch (e) {
      const errMsg = e.response?.data?.vua?.[0]
        || e.response?.data?.detail
        || e.response?.data?.error
        || 'Failed to initiate Setu consent flow.';
      setMessage(errMsg);
      setMessageType('error');
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
      setMessageType('info');
      await fetchConsents();
    } catch (e) {
      setMessage(e.response?.data?.error || 'Failed to sync bank data.');
      setMessageType('error');
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
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Landmark className="h-6 w-6 text-indigo-400" /> Setu Account Aggregator Bank Sync
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Connect your bank accounts securely via RBI-regulated Setu Account Aggregator. FundFlow automatically syncs transaction statements into your Review Inbox.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            id="sync-now-btn"
            onClick={handleManualSync}
            disabled={syncing}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 font-semibold text-xs border border-slate-800 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 text-emerald-400 ${syncing ? 'animate-spin' : ''}`} />
            <span>{syncing ? 'Syncing...' : 'Sync Now'}</span>
          </button>

          <button
            id="link-bank-btn"
            onClick={() => setShowVuaForm(true)}
            disabled={connecting}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-semibold text-xs shadow-md shadow-indigo-500/25 transition-all"
          >
            <ExternalLink className="h-4 w-4" />
            <span>Link Bank Account</span>
          </button>
        </div>
      </div>

      {/* Status message */}
      {message && (
        <div className={`p-4 rounded-xl border text-xs font-semibold flex items-center gap-2 ${
          messageType === 'error'
            ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
            : 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300'
        }`}>
          {messageType === 'error'
            ? <AlertTriangle className="h-4 w-4 shrink-0" />
            : <CheckCircle2 className="h-4 w-4 shrink-0" />
          }
          {message}
        </div>
      )}

      {/* VUA Input Modal / Inline Form */}
      {showVuaForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-5">
            {/* Modal header */}
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Landmark className="h-5 w-5 text-indigo-400" /> Link Your Bank Account
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Enter the mobile number and Account Aggregator app you use to get started.
                </p>
              </div>
              <button
                id="close-vua-form-btn"
                onClick={() => { setShowVuaForm(false); setPhoneError(''); }}
                className="text-slate-500 hover:text-white transition-colors mt-0.5"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Helper callout */}
            <div className="flex gap-2 p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-300 leading-relaxed">
              <Info className="h-4 w-4 shrink-0 mt-0.5" />
              <span>
                An <strong>Account Aggregator (AA)</strong> is an RBI-regulated app that securely shares your bank data with FundFlow — without giving FundFlow your banking password.
                Enter the mobile number linked to your AA app below, then pick which app you use.
              </span>
            </div>

            <form onSubmit={handleLinkBank} className="space-y-4">
              {/* Phone number */}
              <div className="space-y-1.5">
                <label htmlFor="vua-phone" className="block text-xs font-semibold text-slate-300">
                  Mobile Number <span className="text-rose-400">*</span>
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                  <input
                    id="vua-phone"
                    type="tel"
                    inputMode="numeric"
                    maxLength={10}
                    value={phone}
                    onChange={e => { setPhone(e.target.value.replace(/\D/g, '')); setPhoneError(''); }}
                    placeholder="e.g. 9999999999"
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/40 transition"
                    required
                  />
                </div>
                {phoneError && (
                  <p className="text-rose-400 text-[11px] flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3" /> {phoneError}
                  </p>
                )}
                <p className="text-[11px] text-slate-500">
                  The 10-digit number registered with your Account Aggregator app.
                </p>
              </div>

              {/* AA Provider dropdown */}
              <div className="space-y-1.5">
                <label htmlFor="vua-provider" className="block text-xs font-semibold text-slate-300">
                  Account Aggregator App <span className="text-rose-400">*</span>
                </label>
                <div className="relative">
                  <select
                    id="vua-provider"
                    value={aaProvider}
                    onChange={e => setAaProvider(e.target.value)}
                    className="w-full appearance-none pl-4 pr-9 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/40 transition cursor-pointer"
                  >
                    {providers.map(p => (
                      <option key={p.handle} value={p.handle}>{p.label}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                </div>
                <p className="text-[11px] text-slate-500">
                  Select the AA app installed on your phone (e.g. OneMoney, Anumati).
                </p>
              </div>

              {/* VUA preview */}
              {phone.length === 10 && (
                <div className="px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-700 text-xs font-mono text-emerald-400">
                  VUA: {phone}@{aaProvider}
                </div>
              )}

              <button
                id="submit-vua-btn"
                type="submit"
                disabled={connecting}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-bold text-sm shadow-md shadow-indigo-500/25 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <ExternalLink className="h-4 w-4" />
                {connecting ? 'Launching Setu AA Consent...' : 'Launch Consent Screen'}
              </button>
            </form>
          </div>
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
          id="banner-link-bank-btn"
          onClick={() => setShowVuaForm(true)}
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
