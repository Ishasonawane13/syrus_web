import React from 'react';
import { Wallet, TrendingUp, PieChart, Activity } from 'lucide-react';
import { AccountSummary } from '../api';

interface Props {
  account: AccountSummary | null;
  loading: boolean;
}

export const PortfolioSummary: React.FC<Props> = ({ account, loading }) => {
  if (loading || !account) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 bg-white/5 rounded-2xl border border-white/5"></div>
        ))}
      </div>
    );
  }

  const totalValue = account.total_value ?? 0;
  const portfolioValue = account.portfolio_value ?? 0;
  const availableCash = account.available_cash ?? 0;
  const dailyPnl = account.daily_pnl ?? 0;
  const dailyPnlPct = account.daily_pnl_pct ?? 0;
  const totalPnl = account.total_pnl ?? ((account.realized_pnl ?? 0) + (account.unrealized_pnl ?? 0));
  const realizedPnl = account.realized_pnl ?? 0;
  const unrealizedPnl = account.unrealized_pnl ?? 0;

  const isDailyPos = dailyPnl >= 0;
  const isTotalPos = totalPnl >= 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Portfolio Value */}
      <div className="glass-panel p-5 relative overflow-hidden group">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase text-slate-400 mb-1">
          <PieChart size={14} className="text-indigo-400" />
          Total Portfolio Value
        </div>
        <div className="text-2xl font-bold font-mono tracking-tight text-white mt-1">
          ₹{totalValue.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <div className="text-xs text-slate-400 mt-2 flex items-center gap-1.5">
          <span>Positions: ₹{portfolioValue.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
        </div>
      </div>

      {/* Available Cash */}
      <div className="glass-panel p-5 relative overflow-hidden group">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase text-slate-400 mb-1">
          <Wallet size={14} className="text-cyan-400" />
          Available Cash
        </div>
        <div className="text-2xl font-bold font-mono tracking-tight text-white mt-1">
          ₹{availableCash.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <div className="text-xs text-emerald-400/90 mt-2 flex items-center gap-1">
          <span>Ready for Paper Trading</span>
        </div>
      </div>

      {/* Today's P&L */}
      <div className="glass-panel p-5 relative overflow-hidden group">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase text-slate-400 mb-1">
          <Activity size={14} className={isDailyPos ? 'text-emerald-400' : 'text-rose-400'} />
          Today's P&L
        </div>
        <div className={`text-2xl font-bold font-mono tracking-tight mt-1 ${isDailyPos ? 'text-emerald-400' : 'text-rose-400'}`}>
          {isDailyPos ? '+' : ''}₹{dailyPnl.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <div className="mt-2">
          <span className={`glow-pill ${isDailyPos ? 'green' : 'red'}`}>
            {isDailyPos ? '+' : ''}{dailyPnlPct.toFixed(2)}% Today
          </span>
        </div>
      </div>

      {/* Cumulative Returns */}
      <div className="glass-panel p-5 relative overflow-hidden group">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase text-slate-400 mb-1">
          <TrendingUp size={14} className="text-purple-400" />
          Total Returns
        </div>
        <div className={`text-2xl font-bold font-mono tracking-tight mt-1 ${isTotalPos ? 'text-emerald-400' : 'text-rose-400'}`}>
          {isTotalPos ? '+' : ''}₹{totalPnl.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <div className="text-xs text-slate-400 mt-2 flex items-center justify-between">
          <span>Realized: ₹{realizedPnl.toLocaleString('en-IN')}</span>
          <span>Unrealized: ₹{unrealizedPnl.toLocaleString('en-IN')}</span>
        </div>
      </div>
    </div>
  );
};
