import useChatStore from '../../stores/chatStore';
import { Database, Globe, FileText } from 'lucide-react';

// Map tool names to source types
const TOOL_SOURCE_MAP = {
  get_quote: { type: 'market', label: 'Market Data', icon: Database },
  get_watchlists: { type: 'local', label: 'Watchlists', icon: FileText },
  get_watchlist_items: { type: 'local', label: 'Watchlist Items', icon: FileText },
  get_price_history: { type: 'market', label: 'Price History', icon: Database },
  query_market_data: { type: 'market', label: 'DuckDB Cache', icon: Database },
  search_symbol: { type: 'market', label: 'Symbol Search', icon: Database },
  get_financial_ratios: { type: 'market', label: 'Fundamentals', icon: Database },
  export_report: { type: 'local', label: 'Export', icon: FileText },
  skill: { type: 'skill', label: 'Skill', icon: Globe },
};

export default function SourcesPanel() {
  const messages = useChatStore((s) => s.messages);

  // Collect unique tool sources
  const toolNames = new Set();
  messages
    .filter((m) => m.role === 'assistant' && m.toolCalls?.length > 0)
    .forEach((m) => m.toolCalls.forEach((tc) => toolNames.add(tc.tool)));

  const sources = [...toolNames].map((tool) => {
    const mapped = TOOL_SOURCE_MAP[tool];
    return {
      tool,
      type: mapped?.type || 'other',
      label: mapped?.label || tool,
      Icon: mapped?.icon || Globe,
    };
  });

  if (sources.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-40 text-muted-foreground/50">
        <Database className="h-5 w-5 mb-2" />
        <p className="text-xs">No data sources used yet</p>
      </div>
    );
  }

  // Group by type
  const grouped = {};
  sources.forEach((s) => {
    if (!grouped[s.type]) grouped[s.type] = [];
    grouped[s.type].push(s);
  });

  const typeLabels = { market: 'Market Data', local: 'Local', skill: 'Skills', other: 'Other' };

  return (
    <div className="space-y-4">
      {Object.entries(grouped).map(([type, items]) => (
        <div key={type}>
          <div className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60 px-3 mb-1.5">
            {typeLabels[type] || type}
          </div>
          <div className="space-y-0.5">
            {items.map((item) => {
              const Icon = item.Icon;
              return (
                <div
                  key={item.tool}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-foreground"
                >
                  <Icon className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  <span>{item.label}</span>
                  <span className="text-[10px] text-muted-foreground/50 font-mono ml-auto">
                    {item.tool}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
