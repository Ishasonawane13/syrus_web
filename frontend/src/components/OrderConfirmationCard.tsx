import React, { useState } from 'react';
import { ShieldCheck, ShieldAlert, CheckCircle2, XCircle, AlertTriangle, ArrowRight, Loader2 } from 'lucide-react';
import { OrderProposalCard, api } from '../api';

interface Props {
  proposal: OrderProposalCard;
  onExecuted?: (orderId: string) => void;
  onCancelled?: (orderId: string) => void;
}

export const OrderConfirmationCard: React.FC<Props> = ({ proposal, onExecuted, onCancelled }) => {
  const [status, setStatus] = useState<'IDLE' | 'EXECUTING' | 'EXECUTED' | 'CANCELLED' | 'ERROR'>(
    proposal.status === 'FILLED' ? 'EXECUTED' : proposal.status === 'CANCELLED' ? 'CANCELLED' : 'IDLE'
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isBuy = proposal.side === 'BUY';
  const isPassed = proposal.risk_status === 'PASSED';

  const handleConfirm = async () => {
    if (!isPassed) return;
    setStatus('EXECUTING');
    setErrorMessage(null);
    try {
      await api.executeOrder(proposal.id);
      setStatus('EXECUTED');
      onExecuted?.(proposal.id);
    } catch (err: any) {
      setStatus('ERROR');
      setErrorMessage(err.message || 'Execution failed');
    }
  };

  const handleCancel = async () => {
    setStatus('EXECUTING');
    try {
      await api.cancelOrder(proposal.id);
      setStatus('CANCELLED');
      onCancelled?.(proposal.id);
    } catch (err: any) {
      setStatus('CANCELLED');
    }
  };

  if (status === 'EXECUTED') {
    return (
      <div className="mt-3 bg-emerald-950/40 border border-emerald-500/30 rounded-xl p-4 text-sm animate-fade-in">
        <div className="flex items-center gap-2 text-emerald-400 font-semibold mb-1">
          <CheckCircle2 size={18} />
          Paper Trade Executed Successfully
        </div>
        <div className="text-slate-300 text-xs font-mono">
          Filled: {proposal.side} {proposal.quantity} {proposal.symbol} @ approx ₹{proposal.current_price.toFixed(2)}
        </div>
      </div>
    );
  }

  if (status === 'CANCELLED') {
    return (
      <div className="mt-3 bg-slate-900/60 border border-white/10 rounded-xl p-3 text-sm text-slate-400 flex items-center gap-2 animate-fade-in">
        <XCircle size={16} className="text-slate-500" />
        Order proposal was cancelled. No trade placed.
      </div>
    );
  }

  return (
    <div className="mt-3 bg-[#0d1424] border border-indigo-500/25 rounded-xl p-4 shadow-xl text-sm animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-white/10">
        <div className="flex items-center gap-2">
          <span
            className={`px-2 py-0.5 rounded text-xs font-bold font-mono uppercase ${
              isBuy ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
            }`}
          >
            {proposal.side} {proposal.order_type}
          </span>
          <span className="font-bold text-white tracking-wide text-base">{proposal.symbol}</span>
        </div>

        <div className="flex items-center gap-1.5 text-xs">
          {isPassed ? (
            <span className="glow-pill green">
              <ShieldCheck size={12} />
              Risk Passed
            </span>
          ) : (
            <span className="glow-pill red">
              <ShieldAlert size={12} />
              Risk Rejected
            </span>
          )}
        </div>
      </div>

      {/* Trade Parameters Grid */}
      <div className="grid grid-cols-3 gap-2 py-3 border-b border-white/5 font-mono text-xs">
        <div>
          <span className="text-slate-400 block text-[11px]">Quantity</span>
          <span className="font-semibold text-white text-sm">{proposal.quantity} shares</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px]">Market Price</span>
          <span className="font-semibold text-white text-sm">₹{proposal.current_price.toFixed(2)}</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px]">Est. Value</span>
          <span className="font-semibold text-indigo-300 text-sm">₹{proposal.estimated_value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
        </div>
      </div>

      {/* Safety Notice & Risk Evaluation */}
      {isPassed ? (
        <div className="py-2.5 text-xs text-slate-400 flex items-start gap-2">
          <ShieldCheck size={15} className="text-indigo-400 shrink-0 mt-0.5" />
          <span>Deterministic safety checks passed: cash available, position exposure &lt; 40%, price within limits.</span>
        </div>
      ) : (
        <div className="py-2.5 text-xs text-rose-400 bg-rose-950/20 p-2.5 rounded-lg my-2 border border-rose-500/20 flex items-start gap-2">
          <AlertTriangle size={16} className="shrink-0 mt-0.5" />
          <div>
            <strong>Order Rejected by Risk Engine:</strong>
            <p className="mt-0.5 text-slate-300">{proposal.risk_details?.reason || 'Violates risk threshold rules.'}</p>
          </div>
        </div>
      )}

      {errorMessage && (
        <div className="text-xs text-rose-400 bg-rose-950/30 p-2 rounded mb-2 border border-rose-500/30">
          {errorMessage}
        </div>
      )}

      {/* Action Buttons */}
      <div className="pt-2 flex items-center justify-end gap-2.5">
        <button
          onClick={handleCancel}
          disabled={status === 'EXECUTING'}
          className="btn-secondary text-xs py-1.5 px-3"
        >
          Cancel
        </button>

        {isPassed && (
          <button
            onClick={handleConfirm}
            disabled={status === 'EXECUTING'}
            className="btn-primary text-xs py-1.5 px-4"
          >
            {status === 'EXECUTING' ? (
              <>
                <Loader2 size={13} className="animate-spin" />
                Executing...
              </>
            ) : (
              <>
                Confirm Paper Trade
                <ArrowRight size={13} />
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
};
