import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import { Bell, Inbox, LogOut, User as UserIcon, ShieldAlert, Sparkles, CheckCircle2 } from 'lucide-react';
import api from '../api/axios';
import { formatDate } from '../utils/formatters';

export const Navbar = () => {
  const { user, logout } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [reviewCount, setReviewCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const fetchNotifications = async () => {
    try {
      const [notifRes, countRes, reviewRes] = await Promise.all([
        api.get('/notifications/'),
        api.get('/notifications/unread-count/'),
        api.get('/bank-transactions/?status=NEEDS_REVIEW')
      ]);
      setNotifications(notifRes.data);
      setUnreadCount(countRes.data.unread_count);
      setReviewCount(reviewRes.data.length);
    } catch (err) {
      console.error('Failed to load navbar data', err);
    }
  };

  useEffect(() => {
    if (user) {
      fetchNotifications();
    }
  }, [user]);

  const handleMarkAllRead = async () => {
    try {
      await api.post('/notifications/mark-all-read/');
      setUnreadCount(0);
      setNotifications(notifications.map(n => ({ ...n, is_read: true })));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full glass-card border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-emerald-400 shadow-lg shadow-indigo-500/20">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <span className="text-xl font-bold bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
              FundFlow
            </span>
            <span className="hidden sm:inline-block ml-2 text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Setu AA Auto-Detection Active
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Review Inbox Prominent Shortcut Button */}
          <Link
            to="/review-inbox"
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-md shadow-amber-500/20 transition-all hover:scale-105 active:scale-95"
          >
            <Inbox className="h-4 w-4" />
            <span className="hidden sm:inline">Review Inbox</span>
            {reviewCount > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-slate-950 text-[10px] font-extrabold text-amber-400">
                {reviewCount}
              </span>
            )}
          </Link>

          {/* Notifications Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
            >
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white shadow-sm shadow-rose-500/50 animate-pulse">
                  {unreadCount}
                </span>
              )}
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-3 w-80 sm:w-96 glass-card rounded-2xl p-4 shadow-2xl border border-slate-700/60 z-50 animate-in fade-in slide-in-from-top-2">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
                  <h4 className="font-semibold text-white text-sm flex items-center gap-2">
                    <Bell className="h-4 w-4 text-indigo-400" /> Notifications
                  </h4>
                  {unreadCount > 0 && (
                    <button
                      onClick={handleMarkAllRead}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                    >
                      Mark all as read
                    </button>
                  )}
                </div>

                <div className="max-h-72 overflow-y-auto space-y-2.5 pr-1">
                  {notifications.length === 0 ? (
                    <p className="text-center py-6 text-slate-400 text-xs">No notifications yet</p>
                  ) : (
                    notifications.map((n) => (
                      <div
                        key={n.id}
                        className={`p-3 rounded-xl border transition-colors ${
                          n.is_read
                            ? 'bg-slate-900/40 border-slate-800/50 text-slate-400'
                            : 'bg-slate-900/90 border-indigo-500/30 text-slate-200'
                        }`}
                      >
                        <div className="flex items-start gap-2.5">
                          <div className="mt-0.5">
                            {n.type === 'AUTO_TRANSFER' ? (
                              <ShieldAlert className="h-4 w-4 text-emerald-400" />
                            ) : n.type === 'BILL_DUE' ? (
                              <Bell className="h-4 w-4 text-amber-400" />
                            ) : (
                              <CheckCircle2 className="h-4 w-4 text-indigo-400" />
                            )}
                          </div>
                          <div className="flex-1">
                            <h5 className="text-xs font-semibold text-white">{n.title}</h5>
                            <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">{n.message}</p>
                            <span className="text-[10px] text-slate-500 mt-1 block">{formatDate(n.created_at)}</span>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* User Profile Menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2.5 p-1.5 pl-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-200 border border-slate-800 transition-colors"
            >
              <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-xs text-white">
                {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
              </div>
              <span className="hidden md:inline font-medium text-xs text-slate-200 max-w-[120px] truncate">
                {user?.full_name || user?.email}
              </span>
            </button>

            {showUserMenu && (
              <div className="absolute right-0 mt-3 w-56 glass-card rounded-2xl p-2 shadow-2xl border border-slate-700/60 z-50">
                <div className="px-3 py-2 border-b border-slate-800 mb-1">
                  <p className="text-xs font-semibold text-white truncate">{user?.full_name}</p>
                  <p className="text-[11px] text-slate-400 truncate">{user?.email}</p>
                </div>
                <button
                  onClick={logout}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 transition-colors"
                >
                  <LogOut className="h-4 w-4" /> Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
