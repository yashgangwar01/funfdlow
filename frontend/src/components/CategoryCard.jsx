import React from 'react';
import { motion } from 'framer-motion';
import { formatCurrency, getCategoryHealth } from '../utils/formatters';
import {
  Wallet,
  PiggyBank,
  Home,
  ShoppingCart,
  Zap,
  CreditCard,
  Car,
  Film,
  TrendingUp,
  ShieldCheck
} from 'lucide-react';

const ICON_MAP = {
  PiggyBank,
  Home,
  ShoppingCart,
  Zap,
  CreditCard,
  Car,
  Film,
  TrendingUp,
  Wallet
};

export const CategoryCard = ({ category, currency }) => {
  const IconComponent = ICON_MAP[category.icon] || Wallet;
  const allocated = category.allocated_monthly_amount || 0;
  const balance = parseFloat(category.current_balance) || 0;
  const spent = Math.max(0, allocated - balance);
  const health = getCategoryHealth(balance, allocated);

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      className={`glass-card glass-card-hover rounded-2xl p-5 border relative overflow-hidden flex flex-col justify-between ${health.border || 'border-slate-800'}`}
    >
      {/* Category Header */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div
              className="p-2.5 rounded-xl shadow-inner flex items-center justify-center"
              style={{ backgroundColor: `${category.color}20`, color: category.color }}
            >
              <IconComponent className="h-5 w-5" />
            </div>
            <div>
              <h4 className="font-bold text-sm text-white flex items-center gap-1.5">
                {category.name}
                {category.is_savings_category && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30 flex items-center gap-1">
                    <ShieldCheck className="h-3 w-3" /> Buffer
                  </span>
                )}
              </h4>
              <span className="text-[11px] text-slate-400">
                {category.allocation_type === 'PERCENTAGE'
                  ? `${category.allocation_value}% of salary`
                  : `Fixed ${formatCurrency(category.allocation_value, currency)}`}
              </span>
            </div>
          </div>
        </div>

        {/* Balance & Spent Amounts */}
        <div className="grid grid-cols-2 gap-2 my-3 py-2 px-3 rounded-xl bg-slate-900/60 border border-slate-800/60">
          <div>
            <span className="text-[10px] uppercase font-semibold text-slate-400 block">Remaining</span>
            <span className={`text-base font-bold ${balance < 0 ? 'text-rose-400' : 'text-slate-100'}`}>
              {formatCurrency(balance, currency)}
            </span>
          </div>
          <div className="text-right">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block">Spent / Allocated</span>
            <span className="text-xs font-semibold text-slate-300">
              {formatCurrency(spent, currency)} / {formatCurrency(allocated, currency)}
            </span>
          </div>
        </div>

        {/* Progress Bar with Framer Motion Fill */}
        <div className="space-y-1.5 mt-4">
          <div className="flex justify-between text-[11px] font-semibold">
            <span className="text-slate-400">Budget Usage</span>
            <span className={health.text}>{health.percentage}% Used</span>
          </div>
          <div className="h-2.5 w-full bg-slate-900 rounded-full overflow-hidden p-0.5 border border-slate-800">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(health.percentage, 100)}%` }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
              className={`h-full rounded-full ${health.bg}`}
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
};
