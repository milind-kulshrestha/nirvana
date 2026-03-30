import { useEffect, useState } from 'react';
import useChatStore from '../../stores/chatStore';
import { Bot, TrendingUp, Search, PieChart, Clock, ArrowRight, Command } from 'lucide-react';

const QUICK_PROMPTS = [
  { label: 'Scan my watchlist for opportunities', icon: TrendingUp, desc: 'Find movers and setups' },
  { label: 'Summarize ETF trends today', icon: PieChart, desc: 'Sector rotation check' },
  { label: 'Deep-dive AAPL valuation', icon: Search, desc: 'Fundamental analysis' },
];

export default function WelcomeState() {
  const { sendMessage, conversations, loadConversations, selectConversation } = useChatStore();
  const [recentLoaded, setRecentLoaded] = useState(false);

  useEffect(() => {
    if (!recentLoaded) {
      loadConversations();
      setRecentLoaded(true);
    }
  }, [recentLoaded, loadConversations]);

  const recentConvs = conversations.slice(0, 3);
  const hasRecent = recentConvs.length > 0;

  return (
    <div className="flex-1 flex items-center justify-center px-6">
      <div className="w-full max-w-xl">
        {/* Hero */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-5">
            <Bot className="h-8 w-8 text-primary" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground mb-2">
            Your AI Research Analyst
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-md mx-auto">
            Ask about your stocks, scan watchlists, analyze ETFs, or dive deep into any company.
            Press <kbd className="text-[10px] bg-muted px-1.5 py-0.5 rounded border border-border mx-0.5">⌘K</kbd> anytime for quick actions.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6">
          {/* Quick Prompts */}
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60 mb-2 px-1">
              Quick Start
            </div>
            <div className="space-y-1.5">
              {QUICK_PROMPTS.map((prompt) => {
                const Icon = prompt.icon;
                return (
                  <button
                    key={prompt.label}
                    onClick={() => sendMessage(prompt.label)}
                    className="flex items-center gap-3 w-full text-left px-4 py-3 rounded-xl bg-muted/40 hover:bg-muted border border-transparent hover:border-border text-foreground transition-all duration-fast group"
                  >
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 group-hover:bg-primary/15 transition-colors">
                      <Icon className="h-4 w-4 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium">{prompt.label}</div>
                      <div className="text-[11px] text-muted-foreground">{prompt.desc}</div>
                    </div>
                    <ArrowRight className="h-3.5 w-3.5 text-muted-foreground/30 group-hover:text-muted-foreground transition-colors shrink-0" />
                  </button>
                );
              })}
            </div>
          </div>

          {/* Recent Analyses */}
          {hasRecent && (
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60 mb-2 px-1">
                Recent
              </div>
              <div className="space-y-1">
                {recentConvs.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => selectConversation(conv.id)}
                    className="flex items-center gap-3 w-full text-left px-4 py-2.5 rounded-xl hover:bg-muted/50 text-foreground transition-colors duration-fast group"
                  >
                    <Clock className="h-3.5 w-3.5 text-muted-foreground/40 shrink-0" />
                    <span className="flex-1 text-sm truncate">
                      {conv.title || 'Untitled analysis'}
                    </span>
                    <span className="text-[10px] text-muted-foreground/40 shrink-0">
                      {formatRelativeTime(conv.updated_at || conv.created_at)}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffMin = Math.floor(diffMs / 60000);
  const diffHr = Math.floor(diffMs / 3600000);
  const diffDay = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHr < 24) return `${diffHr}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  return date.toLocaleDateString();
}
