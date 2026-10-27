import React from 'react';
import { RefreshCw } from 'lucide-react';

interface RepairBadgeProps {
  cycle: number;
  maxCycles?: number;
}

export const RepairBadge: React.FC<RepairBadgeProps> = ({ cycle, maxCycles = 3 }) => {
  if (cycle <= 0) return null;

  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-medium">
      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
      <span>
        Self-Heal Cycle #{cycle} / {maxCycles}
      </span>
    </div>
  );
};
