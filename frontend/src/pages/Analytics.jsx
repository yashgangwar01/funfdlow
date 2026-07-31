import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';
import { formatCurrency } from '../utils/formatters';
import { BarChart3, Download, PieChart as PieIcon, TrendingUp } from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Legend
} from 'recharts';

export const Analytics = () => {
  const { user } = useAuth();
  const [trends, setTrends] = useState([]);
  const [breakdown, setBreakdown] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  const currency = user?.currency || 'INR';

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [trRes, brRes, smRes] = await Promise.all([
          api.get('/analytics/trends/'),
          api.get('/analytics/category-breakdown/'),
          api.get('/analytics/summary/')
        ]);
        setTrends(trRes.data);
        setBreakdown(brRes.data);
        setSummary(smRes.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleExportCSV = async () => {
    try {
      const response = await api.get('/analytics/export-csv/', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `fundflow_report_${new Date().toISOString().slice(0,10)}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400 text-sm">Loading Analytics & Charts...</div>;
  }

  const pieData = breakdown.map(b => ({
    name: b.name,
    value: b.total_spent,
    color: b.color
  })).filter(b => b.value > 0);

  return (
    <div className="space-y-6 animate-in fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-indigo-400" /> Spending Analytics & Reports
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Visual trends, income vs. expense balance, and category allocation health.
          </p>
        </div>

        <button
          onClick={handleExportCSV}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 font-semibold text-xs border border-slate-800 transition-colors"
        >
          <Download className="h-4 w-4 text-emerald-400" /> Export Monthly CSV Report
        </button>
      </div>

      {/* Main Spending Trend Area Chart */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800">
        <h3 className="font-bold text-sm text-white mb-4 flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-indigo-400" /> Income vs Expenses vs Savings Trend (6 Months)
        </h3>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trends}>
              <defs>
                <linearGradient id="incomeGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="expenseGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="savingsGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
              />
              <Legend />
              <Area type="monotone" dataKey="income" stroke="#6366f1" fillOpacity={1} fill="url(#incomeGrad)" name="Monthly Income" />
              <Area type="monotone" dataKey="expenses" stroke="#f43f5e" fillOpacity={1} fill="url(#expenseGrad)" name="Total Expenses" />
              <Area type="monotone" dataKey="savings" stroke="#10b981" fillOpacity={1} fill="url(#savingsGrad)" name="Net Savings" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Donut Category Breakdown & Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Donut Chart */}
        <div className="glass-card rounded-2xl p-6 border border-slate-800">
          <h3 className="font-bold text-sm text-white mb-4 flex items-center gap-2">
            <PieIcon className="h-4 w-4 text-emerald-400" /> Category Breakdown
          </h3>

          <div className="h-64 w-full flex items-center justify-center">
            {pieData.length === 0 ? (
              <p className="text-xs text-slate-400">No expenses recorded for breakdown yet</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Monthly Comparison Bar */}
        <div className="glass-card rounded-2xl p-6 border border-slate-800">
          <h3 className="font-bold text-sm text-white mb-4">Monthly Allocation vs Actual Spending</h3>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={breakdown}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" fontSize={10} interval={0} angle={-20} textAnchor="end" />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
                />
                <Bar dataKey="total_spent" fill="#f43f5e" name="Spent" radius={[6, 6, 0, 0]} />
                <Bar dataKey="current_balance" fill="#10b981" name="Remaining Balance" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
