import useAIContextStore from '../../stores/aiContextStore';
import { X, BarChart3, PieChart, TrendingUp, FileText } from 'lucide-react';

const TYPE_ICONS = {
  watchlist: BarChart3,
  etf: PieChart,
  stock: TrendingUp,
  dataset: FileText,
};

const TYPE_COLORS = {
  watchlist: 'bg-primary/10 text-primary border-primary/20',
  etf: 'bg-success/10 text-success border-success/20',
  stock: 'bg-warning/10 text-warning border-warning/20',
  dataset: 'bg-muted text-muted-foreground border-border',
};

export default function ContextChips() {
  const { attachedContexts, detachContext } = useAIContextStore();

  if (attachedContexts.length === 0) return null;

  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {attachedContexts.map((ctx) => {
        const Icon = TYPE_ICONS[ctx.type] || FileText;
        const colors = TYPE_COLORS[ctx.type] || TYPE_COLORS.dataset;
        return (
          <span
            key={ctx.id}
            className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full border ${colors}`}
          >
            <Icon className="h-3 w-3 shrink-0" />
            <span className="max-w-[120px] truncate">{ctx.label}</span>
            <button
              onClick={() => detachContext(ctx.id)}
              className="ml-0.5 hover:opacity-70 transition-opacity"
            >
              <X className="h-2.5 w-2.5" />
            </button>
          </span>
        );
      })}
    </div>
  );
}
