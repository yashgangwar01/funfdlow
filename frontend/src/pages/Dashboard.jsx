import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import api from '../api/axios';
import { formatCurrency } from '../utils/formatters';
import { CategoryCard } from '../components/CategoryCard';
import {
  Wallet,
  PieChart,
  CreditCard,
  ShieldCheck,
  Sparkles,
  ArrowUpRight,
  RefreshCw,
  Calendar,
  AlertTriangle,
  Inbox,
  Landmark
} from 'lucide-react';
import { motion } from 'framer-motion';

export const Dashboard = () => {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [categories, setCategories] = useState([]);
  const [upcomingBills, setUpcomingBills] = useState([]);
  const [aiInsight, setAiInsight] = useState(null);
  const [reviewCount, setReviewCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [allocationLoading, setAllocationLoading] = useState(false);

  const fetchDashboardData = async () => {
    try {
      const [sumRes, catRes, billsRes, insightRes, reviewRes] = await Promise.all([
        api.get('/analytics/summary/'),
        api.get('/categories/'),
        api.get('/bills/upcoming/'),
        api.get('/insights/latest/'),
        api.get('/bank-transactions/?status=NEEDS_REVIEW')
      ]);
      setSummary(sumRes.data);
      setCategories(catRes.data);
      setUpcomingBills(billsRes.data);
      setAiInsight(insightRes.data);
      setReviewCount(reviewRes.data.length);
    } catch (err) {
      console.error('Failed to load dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleRunAllocation = async () => {
    setAllocationLoading(true);
    try {
      await api.post('/categories/run-allocation/');
      await fetchDashboardData();
    } catch (e) {
      console.error(e);
    } finally {
      setAllocationLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="flex items-center gap-3 text-indigo-400 font-semibold text-sm">
          <RefreshCw className="h-5 w-5 animate-spin" /> Loading FundFlow Dashboard...
        </div>
      </div>
    );
  }

  const currency = user?.currency || 'INR';

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      
      {/* Prominent Review Inbox Alert Banner if pending items exist */}
      {reviewCount > 0 ? (
        <div className="p-5 rounded-2xl bg-gradient-to-r from-amber-500/20 via-slate-900 to-indigo-950/40 border border-amber-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 shrink-0">
              <Inbox className="h-6 w-6" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-white flex items-center gap-1.5">
                Auto-Detected Bank Transactions Pending Review
              </h4>
              <p className="text-xs text-slate-300 mt-0.5">
                You have <span className="font-extrabold text-amber-300">{reviewCount} auto-detected transactions</span> waiting for category confirmation.
              </p>
            </div>
          </div>

          <Link
            to="/review-inbox"
            className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center justify-center gap-1.5 shadow-md shadow-amber-500/20 shrink-0"
          >
            Review Transactions <ArrowUpRight className="h-4 w-4" />
          </Link>
        </div>
      ) : (
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-between gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>Setu AA Bank Ingestion Pipeline Active — All expenses are auto-categorized.</span>
          </div>
          <Link to="/bank-sync" className="text-indigo-400 hover:underline font-semibold flex items-center gap-1">
            Bank Sync Settings <ArrowUpRight className="h-3 w-3" />
          </Link>
        </div>
      )}

      {/* Top Banner & Quick Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            Welcome back, {user?.full_name?.split(' ')[0] || 'User'} 👋
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Salary Credit Day: <span className="text-indigo-300 font-medium">Day {user?.salary_credit_day}</span> of every month
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRunAllocation}
            disabled={allocationLoading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 font-semibold text-xs border border-slate-800 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 text-emerald-400 ${allocationLoading ? 'animate-spin' : ''}`} />
            <span>{allocationLoading ? 'Allocating...' : 'Run Salary Allocation'}</span>
          </button>

          <Link
            to="/bank-sync"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-semibold text-xs shadow-md shadow-indigo-500/25 transition-all hover:scale-105"
          >
            <Landmark className="h-4 w-4" /> Link Bank Account
          </Link>
        </div>
      </div>

      {/* Executive Summary Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card rounded-2xl p-5 border border-slate-800/80 bg-gradient-to-br from-slate-900/90 to-indigo-950/20">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase">Monthly Salary</span>
            <Wallet className="h-4 w-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-extrabold text-white">
            {formatCurrency(summary?.monthly_salary, currency)}
          </div>
          <span className="text-[11px] text-emerald-400 font-semibold mt-1 block">
            Automatic Monthly Credit
          </span>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-800/80 bg-gradient-to-br from-slate-900/90 to-blue-950/20">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase">Allocated Budget</span>
            <PieChart className="h-4 w-4 text-blue-400" />
          </div>
          <div className="text-2xl font-extrabold text-white">
            {formatCurrency(summary?.total_allocated, currency)}
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">
            Across {categories.length} Spending Categories
          </span>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-800/80 bg-gradient-to-br from-slate-900/90 to-rose-950/20">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase">Spent This Month</span>
            <CreditCard className="h-4 w-4 text-rose-400" />
          </div>
          <div className="text-2xl font-extrabold text-white">
            {formatCurrency(summary?.total_spent, currency)}
          </div>
          <span className="text-[11px] text-rose-300 font-semibold mt-1 block">
            {summary?.spent_percentage}% of Total Salary
          </span>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-800/80 bg-gradient-to-br from-slate-900/90 to-emerald-950/20">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase">Savings Buffer</span>
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-extrabold text-white">
            {formatCurrency(summary?.savings_balance, currency)}
          </div>
          <span className="text-[11px] text-emerald-400 font-semibold mt-1 block">
            Smart Cover Protection Active
          </span>
        </div>
      </div>

      {/* AI Recommendation Widget */}
      {aiInsight && (
        <div className="glass-card rounded-2xl p-5 border border-indigo-500/30 bg-gradient-to-r from-indigo-950/40 via-slate-900 to-slate-900">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 mt-0.5">
              <Sparkles className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white">{aiInsight.title || 'AI Financial Insight'}</h3>
                <Link to="/insights" className="text-xs text-indigo-400 hover:underline font-semibold flex items-center gap-1">
                  View All <ArrowUpRight className="h-3 w-3" />
                </Link>
              </div>
              <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                {aiInsight.recommendation}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Categories Grid Header */}
      <div className="flex items-center justify-between pt-2">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <PieChart className="h-5 w-5 text-indigo-400" /> Active Category Balances
        </h2>
        <Link to="/categories" className="text-xs text-indigo-400 hover:underline font-semibold flex items-center gap-1">
          Manage Allocations <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {/* Categories Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {categories.map((category) => (
          <CategoryCard
            key={category.id}
            category={category}
            currency={currency}
          />
        ))}
      </div>

      {/* Upcoming Bills & Smart Cover Status Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
        <div className="glass-card rounded-2xl p-5 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Calendar className="h-4 w-4 text-amber-400" /> Upcoming Bills & EMIs
            </h3>
            <Link to="/bills" className="text-xs text-indigo-400 hover:underline font-semibold">
              View All
            </Link>
          </div>

          <div className="space-y-3">
            {upcomingBills.length === 0 ? (
              <p className="text-xs text-slate-400 py-4 text-center">No upcoming bills for the next 7 days</p>
            ) : (
              upcomingBills.slice(0, 3).map((bill) => (
                <div key={bill.id} className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <div>
                    <span className="font-semibold text-white text-xs block">{bill.title}</span>
                    <span className="text-[11px] text-slate-400 block">Due in {bill.days_until_due} days ({bill.category_name})</span>
                  </div>
                  <span className="font-extrabold text-amber-400 text-xs">
                    {formatCurrency(bill.amount, currency)}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-400" /> Smart Cover Auto-Transfer System
            </h3>
            <Link to="/smart-cover" className="text-xs text-indigo-400 hover:underline font-semibold">
              Configure Rules
            </Link>
          </div>

          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-slate-300 text-xs leading-relaxed space-y-2">
            <p className="font-semibold text-emerald-300">
              🛡️ Savings Buffer Protection is Active
            </p>
            <p className="text-[11px] text-slate-300">
              When any spending category drops below threshold, Smart Cover automatically transfers funds from Savings to cover the shortfall seamlessly.
            </p>
          </div>
        </div>
      </div>

    </div>
  );
};
