import React, { useEffect, useState } from 'react';
import { ShoppingBag, CheckCircle, Clock, XCircle, AlertCircle } from 'lucide-react';
import { api, OrderItem } from '../api';

export const OrdersView: React.FC = () => {
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchOrders = async () => {
    try {
      const data = await api.getOrders();
      setOrders(data.orders);
      setLoading(false);
    } catch {}
  };

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'FILLED':
        return (
          <span className="glow-pill green">
            <CheckCircle size={11} /> FILLED
          </span>
        );
      case 'PENDING_APPROVAL':
        return (
          <span className="glow-pill amber">
            <Clock size={11} /> PENDING APPROVAL
          </span>
        );
      case 'REJECTED':
        return (
          <span className="glow-pill red">
            <AlertCircle size={11} /> REJECTED
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="glow-pill indigo">
            <XCircle size={11} /> CANCELLED
          </span>
        );
      default:
        return <span className="glow-pill indigo">{status}</span>;
    }
  };

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

  return (
    <div className="glass-panel overflow-hidden">
      <div className="p-5 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShoppingBag size={18} className="text-indigo-400" />
          <h2 className="font-semibold text-base text-white">Order History</h2>
          <span className="text-xs bg-white/10 text-slate-300 px-2 py-0.5 rounded-full font-mono">
            {orders.length} orders
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-xs uppercase text-slate-400 border-b border-white/5 bg-white/[0.02]">
              <th className="py-3 px-4 font-semibold">Time</th>
              <th className="py-3 px-4 font-semibold">Side</th>
              <th className="py-3 px-4 font-semibold">Instrument</th>
              <th className="py-3 px-4 font-semibold text-right">Quantity</th>
              <th className="py-3 px-4 font-semibold text-right">Est. Value</th>
              <th className="py-3 px-4 font-semibold text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 font-mono text-xs">
            {orders.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-400 font-sans">
                  No orders found.
                </td>
              </tr>
            ) : (
              orders.map((o) => {
                const isBuy = o.side === 'BUY';
                return (
                  <tr key={o.id} className="hover:bg-white/[0.03] transition-colors">
                    <td className="py-3 px-4 text-slate-400">
                      {new Date(o.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                          isBuy ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                        }`}
                      >
                        {o.side}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-sans font-semibold text-white">
                      {o.symbol}
                      <span className="text-slate-500 font-mono text-[11px] ml-1">({o.order_type})</span>
                    </td>
                    <td className="py-3 px-4 text-right text-slate-200">{o.quantity}</td>
                    <td className="py-3 px-4 text-right text-indigo-300">
                      ₹{o.estimated_value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-center">{getStatusBadge(o.status)}</td>
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
