import { useState, useEffect } from 'react';
import useChatStore from '../../stores/chatStore';
import useLayoutStore from '../../stores/layoutStore';
import { API_BASE } from '../../config';
import { ChevronDown, Plus, Trash2, MessageSquare, LayoutGrid, MessageCircle, PanelRight } from 'lucide-react';
import ContextChips from '../topbar/ContextChips';
import ContextChipPicker from '../topbar/ContextChipPicker';

const MODE_TABS = [
  { key: 'canvas', label: 'Canvas', icon: LayoutGrid },
  { key: 'chat', label: 'Chat', icon: MessageCircle },
];

export default function TopBar({ mode = 'canvas', onModeChange }) {
  const {
    conversations,
    currentConversationId,
    selectedModel,
    setSelectedModel,
    tokenUsage,
    isStreaming,
    loadConversations,
    createConversation,
    selectConversation,
    deleteConversation,
  } = useChatStore();

  const [showConversations, setShowConversations] = useState(false);
  const [availableModels, setAvailableModels] = useState([]);

  const CONTEXT_WINDOWS = {
    'anthropic/claude-sonnet-4-6': 200000,
    'anthropic/claude-opus-4-6': 200000,
    'anthropic/claude-haiku-4-5-20251001': 200000,
    'gpt-4o': 128000,
    'gpt-4o-mini': 128000,
    'gemini/gemini-2.0-flash': 1048576,
    'gemini/gemini-1.5-pro': 2097152,
    'groq/llama-3.3-70b-versatile': 128000,
  };

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    fetch(`${API_BASE}/api/settings/models`, { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : []))
      .then(setAvailableModels)
      .catch(() => {});
  }, []);

  const currentConv = conversations.find((c) => c.id === currentConversationId);
  const displayName = currentConv?.title || 'New Analysis';

  const handleNewChat = async () => {
    await createConversation();
    setShowConversations(false);
  };

  // Token usage indicator
  const maxTokens = CONTEXT_WINDOWS[selectedModel] || 200000;
  const usedTokens = tokenUsage ? (tokenUsage.input_tokens || 0) + (tokenUsage.output_tokens || 0) : 0;
  const pct = maxTokens > 0 ? Math.min((usedTokens / maxTokens) * 100, 100) : 0;
  const fmt = (n) => (n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n));

  const { rightRailOpen, toggleRightRail } = useLayoutStore();

  return (
    <div className="flex items-center justify-between h-12 px-5 border-b border-border bg-card/50 shrink-0">
      {/* Left: Conversation selector + context chips */}
      <div className="flex items-center gap-2 min-w-0">
      <div className="relative shrink-0">
        <button
          onClick={() => setShowConversations(!showConversations)}
          className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-sm font-medium text-foreground hover:bg-muted transition-colors duration-fast"
        >
          <MessageSquare className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="max-w-[240px] truncate">{displayName}</span>
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        </button>

        {showConversations && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setShowConversations(false)} />
            <div className="absolute top-full left-0 mt-1 z-50 w-72 bg-popover border border-border rounded-xl shadow-lg overflow-hidden">
              <div className="p-2 border-b border-border">
                <button
                  onClick={handleNewChat}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-primary hover:bg-primary/5 rounded-lg transition-colors duration-fast"
                >
                  <Plus className="h-3.5 w-3.5" />
                  New Analysis
                </button>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {conversations.length === 0 ? (
                  <p className="text-sm text-muted-foreground p-3">No conversations yet</p>
                ) : (
                  conversations.map((conv) => (
                    <div
                      key={conv.id}
                      className={`flex items-center justify-between px-3 py-2 hover:bg-muted cursor-pointer text-sm transition-colors duration-fast ${
                        conv.id === currentConversationId ? 'bg-primary/5 text-primary' : 'text-foreground'
                      }`}
                    >
                      <span
                        onClick={() => {
                          selectConversation(conv.id);
                          setShowConversations(false);
                        }}
                        className="flex-1 truncate"
                      >
                        {conv.title || 'Untitled'}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteConversation(conv.id);
                        }}
                        className="text-muted-foreground hover:text-destructive ml-2 p-1 transition-colors duration-fast opacity-0 group-hover:opacity-100"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </>
        )}
      </div>
      <ContextChips />
      <ContextChipPicker />
      </div>

      {/* Center: Mode tabs */}
      {onModeChange && (
        <div className="flex gap-0.5 bg-muted/60 rounded-lg p-0.5">
          {MODE_TABS.map((tab) => {
            const Icon = tab.icon;
            const active = mode === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => onModeChange(tab.key)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all duration-fast ${
                  active
                    ? 'bg-background shadow-sm text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Icon className="h-3 w-3" />
                {tab.label}
              </button>
            );
          })}
        </div>
      )}

      {/* Right: Model selector + token usage */}
      <div className="flex items-center gap-3">
        {/* Token usage */}
        {tokenUsage && usedTokens > 0 && (
          <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground tabular-nums">
            <div className="w-16 h-1 bg-muted rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  pct > 80 ? 'bg-destructive' : pct > 50 ? 'bg-warning' : 'bg-primary'
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span>{fmt(usedTokens)}</span>
          </div>
        )}

        {/* Model selector */}
        {availableModels.length > 0 && (
          <select
            aria-label="Model"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            disabled={isStreaming}
            className="text-xs border border-border rounded-lg px-2 py-1 bg-background text-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none disabled:opacity-50 transition-all duration-fast"
          >
            {availableModels.map((m) => (
              <option key={m.id} value={m.id}>
                {m.display_name}
              </option>
            ))}
          </select>
        )}

        {/* Right rail toggle */}
        <button
          onClick={toggleRightRail}
          className={`p-1.5 rounded-lg transition-colors duration-fast ${
            rightRailOpen
              ? 'bg-primary/10 text-primary'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted'
          }`}
          title={rightRailOpen ? 'Close panel' : 'Open panel'}
        >
          <PanelRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
