import React from 'react';

interface StatusPillProps {
  status: 'RUNNING' | 'PASS' | 'FAIL' | 'CLOUD' | 'LOCAL' | string;
}

export const StatusPill: React.FC<StatusPillProps> = ({ status }) => {
  const normalized = status.toUpperCase();

  let colorClasses = 'bg-slate-800 text-slate-300 border-slate-700';
  if (normalized === 'RUNNING') {
    colorClasses = 'bg-blue-500/10 text-blue-400 border-blue-500/30 animate-pulse';
  } else if (normalized === 'PASS') {
    colorClasses = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  } else if (normalized === 'FAIL') {
    colorClasses = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
  } else if (normalized === 'CLOUD') {
    colorClasses = 'bg-purple-500/10 text-purple-400 border-purple-500/30';
  } else if (normalized === 'LOCAL') {
    colorClasses = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide border ${colorClasses}`}
    >
      {normalized}
    </span>
  );
};
