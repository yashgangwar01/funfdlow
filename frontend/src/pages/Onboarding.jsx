import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Sparkles, ArrowRight, CheckCircle2, PieChart, ShieldCheck, DollarSign, Calendar } from 'lucide-react';
import { formatCurrency } from '../utils/formatters';

const DEFAULT_ONBOARDING_CATEGORIES = [
  { name: 'Savings & Emergency Fund', allocation_type: 'PERCENTAGE', allocation_value: 20, is_savings_category: true, color: '#10b981', icon: 'PiggyBank' },
  { name: 'Rent & Housing', allocation_type: 'PERCENTAGE', allocation_value: 30, is_savings_category: false, color: '#6366f1', icon: 'Home' },
  { name: 'Groceries & Household', allocation_type: 'PERCENTAGE', allocation_value: 15, is_savings_category: false, color: '#3b82f6', icon: 'ShoppingCart' },
  { name: 'Bills & Utilities', allocation_type: 'PERCENTAGE', allocation_value: 10, is_savings_category: false, color: '#f59e0b', icon: 'Zap' },
  { name: 'Loans & EMIs', allocation_type: 'PERCENTAGE', allocation_value: 10, is_savings_category: false, color: '#ef4444', icon: 'CreditCard' },
  { name: 'Transportation & Fuel', allocation_type: 'PERCENTAGE', allocation_value: 5, is_savings_category: false, color: '#8b5cf6', icon: 'Car' },
  { name: 'Entertainment & Dining', allocation_type: 'PERCENTAGE', allocation_value: 5, is_savings_category: false, color: '#ec4899', icon: 'Film' },
  { name: 'Investments', allocation_type: 'PERCENTAGE', allocation_value: 5, is_savings_category: false, color: '#14b8a6', icon: 'TrendingUp' },
];

export const Onboarding = () => {
  const { user, completeOnboarding } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [monthlySalary, setMonthlySalary] = useState(user?.monthly_salary || 75000);
  const [salaryCreditDay, setSalaryCreditDay] = useState(user?.salary_credit_day || 1);
  const [currency, setCurrency] = useState(user?.currency || 'INR');
  const [categories, setCategories] = useState(DEFAULT_ONBOARDING_CATEGORIES);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const totalPercentage = categories.reduce((sum, c) => sum + (parseFloat(c.allocation_value) || 0), 0);

  const handleCategoryChange = (index, value) => {
    const updated = [...categories];
    updated[index].allocation_value = parseFloat(value) || 0;
    setCategories(updated);
  };

  const handleFinish = async () => {
    setError('');
    if (Math.round(totalPercentage) !== 100) {
      setError(`Total percentage allocation must equal 100%. Currently at ${totalPercentage}%`);
      return;
    }

    setLoading(true);
    try {
      await completeOnboarding({
        monthly_salary: parseFloat(monthlySalary),
        salary_credit_day: parseInt(salaryCreditDay),
        currency,
        categories
      });
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Onboarding failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 sm:p-6 bg-slate-950">
      <div className="w-full max-w-4xl glass-card rounded-3xl p-6 sm:p-10 shadow-2xl border border-slate-800">
        
        {/* Header Steps Progress */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-6 mb-8">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-emerald-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Salary Allocation Onboarding</h2>
              <p className="text-xs text-slate-400">Step {step} of 2</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className={`h-2.5 w-12 rounded-full ${step >= 1 ? 'bg-indigo-500' : 'bg-slate-800'}`} />
            <div className={`h-2.5 w-12 rounded-full ${step >= 2 ? 'bg-indigo-500' : 'bg-slate-800'}`} />
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-semibold">
            {error}
          </div>
        )}

        {/* Step 1: Salary & Credit Day */}
        {step === 1 && (
          <div className="space-y-6">
            <div className="space-y-1">
              <h3 className="text-lg font-bold text-white">Monthly Salary & Credit Date</h3>
              <p className="text-xs text-slate-400">Configure your monthly salary details so FundFlow can execute automated allocations.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                  <DollarSign className="h-4 w-4 text-indigo-400" /> Monthly Salary
                </label>
                <input
                  type="number"
                  value={monthlySalary}
                  onChange={(e) => setMonthlySalary(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500 font-bold"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                  <Calendar className="h-4 w-4 text-emerald-400" /> Credit Day of Month
                </label>
                <input
                  type="number"
                  min="1"
                  max="31"
                  value={salaryCreditDay}
                  onChange={(e) => setSalaryCreditDay(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Currency</label>
                <select
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                >
                  <option value="INR">INR (₹)</option>
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                </select>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-400 block">Total Monthly Budget to Distribute</span>
                <span className="text-xl font-bold text-emerald-400">
                  {formatCurrency(monthlySalary, currency)}
                </span>
              </div>
              <button
                onClick={() => setStep(2)}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-semibold text-sm shadow-md shadow-indigo-500/20 flex items-center gap-2"
              >
                Configure Category Rules <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Category Allocation Builder */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-white">Customize Salary Allocation Rules</h3>
                <p className="text-xs text-slate-400">Distribute 100% of your monthly salary across your categories.</p>
              </div>

              <div className={`px-4 py-2 rounded-xl text-xs font-bold border ${
                Math.round(totalPercentage) === 100
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
              }`}>
                Total: {totalPercentage}% / 100%
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-96 overflow-y-auto pr-1">
              {categories.map((cat, idx) => {
                const amount = (parseFloat(monthlySalary) * cat.allocation_value) / 100;
                return (
                  <div
                    key={idx}
                    className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between gap-3"
                  >
                    <div>
                      <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                        <span className="h-2 w-2 rounded-full" style={{ backgroundColor: cat.color }} />
                        {cat.name}
                      </h4>
                      <span className="text-[11px] text-emerald-400 font-semibold mt-0.5 block">
                        {formatCurrency(amount, currency)} / mo
                      </span>
                    </div>

                    <div className="flex items-center gap-1">
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={cat.allocation_value}
                        onChange={(e) => handleCategoryChange(idx, e.target.value)}
                        className="w-16 px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-white text-xs font-bold text-center"
                      />
                      <span className="text-xs text-slate-400 font-bold">%</span>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex gap-4 pt-4 border-t border-slate-800">
              <button
                onClick={() => setStep(1)}
                className="px-5 py-3 rounded-xl bg-slate-900 text-slate-300 font-semibold text-sm border border-slate-800"
              >
                Back
              </button>

              <button
                onClick={handleFinish}
                disabled={loading || Math.round(totalPercentage) !== 100}
                className="flex-1 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-bold text-sm shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {loading ? 'Executing Initial Allocation...' : 'Complete Onboarding & Distribute Salary'}
                <CheckCircle2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
