import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { Sparkles, AlertTriangle, ShieldCheck, RefreshCw, CheckCircle2, ArrowRight } from 'lucide-react';

export const Insights = () => {
  const [insight, setInsight] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchInsights = async () => {
    try {
      const res = await api.get('/insights/latest/');
      setInsight(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const res = await api.post('/insights/generate/');
      setInsight(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400 text-sm">Generating AI Financial Insights...</div>;
  }

  return (
    <div className="space-y-6 animate-in fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-indigo-400" /> AI Financial Recommendations
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Automated spending pattern analysis & actionable advice to optimize your financial health.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-semibold text-xs shadow-md shadow-indigo-500/25 transition-all"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          <span>{refreshing ? 'Analyzing...' : 'Re-Run AI Analysis'}</span>
        </button>
      </div>

      {/* Main Health Card */}
      <div className="glass-card rounded-2xl p-6 border border-indigo-500/30 bg-gradient-to-r from-indigo-950/40 via-slate-900 to-slate-900/90 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 font-bold text-xs">
              AI Financial Health Score
            </span>
          </div>
          <h2 className="text-3xl font-extrabold text-white">
            {insight?.overall_health_score || 85} / 100
          </h2>
          <p className="text-xs text-slate-300 max-w-xl leading-relaxed">
            "{insight?.narrative_summary}"
          </p>
        </div>

        <div className="flex h-28 w-28 shrink-0 items-center justify-center rounded-full bg-slate-900 border-4 border-indigo-500/50 shadow-xl shadow-indigo-500/10 font-black text-2xl text-indigo-400">
          {insight?.overall_health_score || 85}%
        </div>
      </div>

      {/* Alerts & Actionable Steps Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Risk Flags & Alerts */}
        <div className="glass-card rounded-2xl p-6 border border-slate-800">
          <h3 className="font-bold text-sm text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-rose-400" /> Active Budget & Risk Warnings
          </h3>

          <div className="space-y-3">
            {!insight?.alerts || insight.alerts.length === 0 ? (
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" /> No budget warnings active. All categories within normal parameters.
              </div>
            ) : (
              insight.alerts.map((alert, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs space-y-1">
                  <span className="font-bold text-rose-300 block">{alert.title}</span>
                  <p className="text-slate-300 leading-relaxed">{alert.message}</p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Actionable Steps */}
        <div className="glass-card rounded-2xl p-6 border border-slate-800">
          <h3 className="font-bold text-sm text-white mb-4 flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-400" /> Recommended Action Items
          </h3>

          <div className="space-y-3">
            {!insight?.actionable_steps || insight.actionable_steps.length === 0 ? (
              <p className="text-xs text-slate-400 py-4">Maintain current spending discipline.</p>
            ) : (
              insight.actionable_steps.map((item, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-xs space-y-1">
                  <span className="font-bold text-indigo-300 block">{item.category}</span>
                  <p className="text-slate-300 leading-relaxed">{item.suggestion}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
