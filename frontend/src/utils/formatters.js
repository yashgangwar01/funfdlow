export const formatCurrency = (amount, currency = 'INR') => {
  const num = parseFloat(amount) || 0;
  try {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency === 'INR' ? 'INR' : currency,
      maximumFractionDigits: 2,
    }).format(num);
  } catch (e) {
    return `${currency} ${num.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  }
};

export const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  }).format(date);
};

export const getCategoryHealth = (currentBalance, allocatedAmount) => {
  const allocated = parseFloat(allocatedAmount) || 0;
  const balance = parseFloat(currentBalance) || 0;
  
  if (allocated === 0) return { percentage: 0, status: 'normal', color: 'indigo', text: 'text-indigo-400', bg: 'bg-indigo-500' };

  const spent = allocated - balance;
  const percentage = Math.min(Math.max(round((spent / allocated) * 100), 0), 100);

  if (balance < 0 || percentage >= 90) {
    return { percentage, status: 'danger', color: 'rose', text: 'text-rose-400', bg: 'bg-rose-500', border: 'border-rose-500/40' };
  } else if (percentage >= 70) {
    return { percentage, status: 'warning', color: 'amber', text: 'text-amber-400', bg: 'bg-amber-500', border: 'border-amber-500/40' };
  }
  return { percentage, status: 'healthy', color: 'emerald', text: 'text-emerald-400', bg: 'bg-emerald-500', border: 'border-emerald-500/40' };
};

function round(val) {
  return Math.round(val * 10) / 10;
}
