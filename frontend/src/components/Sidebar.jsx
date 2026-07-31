import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import api from '../api/axios';
import {
  LayoutDashboard,
  Inbox,
  Landmark,
  PieChart,
  Receipt,
  ShieldCheck,
  CalendarClock,
  BarChart3,
  Target,
  Sparkles,
  Settings
} from 'lucide-react';

export const Sidebar = () => {
  const [reviewCount, setReviewCount] = useState(0);

  useEffect(() => {
    const fetchReviewCount = async () => {
      try {
        const res = await api.get('/bank-transactions/?status=NEEDS_REVIEW');
        setReviewCount(res.data.length);
      } catch (e) {
        console.error(e);
      }
    };
    fetchReviewCount();
  }, []);

  const NAV_ITEMS = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Review Inbox', path: '/review-inbox', icon: Inbox, badge: reviewCount },
    { name: 'Setu Bank Sync', path: '/bank-sync', icon: Landmark },
    { name: 'Salary & Allocation', path: '/categories', icon: PieChart },
    { name: 'Transactions', path: '/transactions', icon: Receipt },
    { name: 'Smart Cover Rules', path: '/smart-cover', icon: ShieldCheck },
    { name: 'Bills & Reminders', path: '/bills', icon: CalendarClock },
    { name: 'Analytics & Trends', path: '/analytics', icon: BarChart3 },
    { name: 'Financial Goals', path: '/goals', icon: Target },
    { name: 'AI Insights', path: '/insights', icon: Sparkles },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 glass-card border-r border-slate-800/80 min-h-[calc(100vh-4rem)] p-4 hidden md:flex flex-col justify-between">
      <div className="space-y-1.5">
        <div className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Core Navigation
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-indigo-600/90 to-indigo-500/90 text-white shadow-md shadow-indigo-500/20 border border-indigo-400/30'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/60'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="h-4 w-4" />
                <span>{item.name}</span>
              </div>
              {item.badge > 0 && (
                <span className="px-1.5 py-0.5 rounded-full bg-amber-500 text-[10px] font-extrabold text-slate-950 shadow-sm animate-pulse">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>

      <div className="glass-card rounded-xl p-3.5 border border-indigo-500/20 bg-indigo-950/20">
        <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs mb-1">
          <ShieldCheck className="h-4 w-4 text-emerald-400" /> Smart Cover Active
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Savings buffer is monitoring category depletion & auto-covering shortfalls.
        </p>
      </div>
    </aside>
  );
};
