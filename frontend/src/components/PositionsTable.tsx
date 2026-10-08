import React from 'react';
import { Position } from '../api';
import { TrendingUp, TrendingDown, Layers } from 'lucide-react';

interface Props {
  positions: Position[];
  loading: boolean;
  onTradeSymbol?: (symbol: string) => void;
}

export const PositionsTable: React.FC<Props> = ({ positions = [], loading, onTradeSymbol }) => {
  if (loading) {
    return (
      <div className="glass-panel p-6 animate-pulse">
        <div className="h-6 w-48 bg-white/10 rounded mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-white/5 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  const items = Array.isArray(positions) ? positions : [];

  return (
    <div className="glass-panel overflow-hidden">
      <div className="p-5 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers size={18} className="text-indigo-400" />
          <h2 className="font-semibold text-base text-white">Current Holdings</h2>
          <span className="text-xs bg-white/10 text-slate-300 px-2 py-0.5 rounded-full font-mono">
            {items.length} active
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-xs uppercase text-slate-400 border-b border-white/5 bg-white/[0.02]">
              <th className="py-3.5 px-4 font-semibold">Instrument</th>
              <th className="py-3.5 px-4 font-semibold text-right">Quantity</th>
              <th className="py-3.5 px-4 font-semibold text-right">Avg Cost</th>
              <th className="py-3.5 px-4 font-semibold text-right">LTP</th>
              <th className="py-3.5 px-4 font-semibold text-right">Current Value</th>
              <th className="py-3.5 px-4 font-semibold text-right">Unrealized P&L</th>
              <th className="py-3.5 px-4 font-semibold text-center">Portfolio %</th>
              <th className="py-3.5 px-4 font-semibold text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {items.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-slate-400">
                  No stock positions currently held. Use the AI Copilot below to place simulated paper trades.
                </td>
              </tr>
            ) : (
              items.map((pos) => {
                const unPnl = pos.unrealized_pnl ?? 0;
                const unPnlPct = pos.unrealized_pnl_pct ?? 0;
                const isPos = unPnl >= 0;
                const mktVal = pos.market_value ?? 0;
                const avgPrice = pos.avg_price ?? 0;
                const currPrice = pos.current_price ?? 0;
                const allocPct = pos.allocation_pct ?? 0;

                return (
                  <tr key={pos.symbol} className="hover:bg-white/[0.03] transition-colors font-mono">
                    <td className="py-3.5 px-4 font-sans">
                      <div className="font-semibold text-white">{pos.symbol}</div>
                      <div className="text-xs text-slate-400 truncate max-w-[160px]">{pos.name}</div>
                    </td>
                    <td className="py-3.5 px-4 text-right text-slate-200">{pos.quantity ?? 0}</td>
                    <td className="py-3.5 px-4 text-right text-slate-300">₹{avgPrice.toFixed(2)}</td>
                    <td className="py-3.5 px-4 text-right text-slate-100 font-semibold">
                      ₹{currPrice.toFixed(2)}
                    </td>
                    <td className="py-3.5 px-4 text-right text-slate-100">
                      ₹{mktVal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className={`font-semibold flex items-center justify-end gap-1 ${isPos ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {isPos ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
                        {isPos ? '+' : ''}₹{unPnl.toFixed(2)}
                      </div>
                      <div className={`text-xs ${isPos ? 'text-emerald-500' : 'text-rose-500'}`}>
                        {isPos ? '+' : ''}{unPnlPct.toFixed(2)}%
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <div className="inline-block w-16 bg-white/10 h-2 rounded-full overflow-hidden mr-2 align-middle">
                        <div
                          className="bg-indigo-500 h-full rounded-full"
                          style={{ width: `${Math.min(100, allocPct * 2)}%` }}
                        ></div>
                      </div>
                      <span className="text-xs text-slate-300 font-sans">{allocPct.toFixed(1)}%</span>
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <button
                        onClick={() => onTradeSymbol?.(pos.symbol)}
                        className="text-xs bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2.5 py-1 rounded font-sans transition-colors cursor-pointer"
                      >
                        Trade
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
