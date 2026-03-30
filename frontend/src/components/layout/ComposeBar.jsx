import { useState, useRef, useEffect } from 'react';
import useChatStore from '../../stores/chatStore';
import useAIContextStore from '../../stores/aiContextStore';
import { ArrowUp } from 'lucide-react';

export default function ComposeBar() {
  const { isStreaming, sendMessage } = useChatStore();
  const { attachedContexts, clearContexts } = useAIContextStore();
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  }, [input]);

  const handleSubmit = async (e) => {
    e?.preventDefault();
    if (!input.trim() || isStreaming) return;
    const content = input.trim();
    const context = attachedContexts.length > 0 ? { attachedContexts } : null;
    setInput('');
    clearContexts();
    await sendMessage(content, context);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="shrink-0 border-t border-border bg-card/50 px-5 py-3">
      <div className="max-w-[800px] mx-auto">
        <div className="relative flex items-end gap-2 bg-background border border-border rounded-xl px-4 py-2.5 focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary transition-all duration-fast">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isStreaming ? 'Analyzing...' : 'Ask anything about your portfolio...'}
            disabled={isStreaming}
            rows={1}
            className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground resize-none outline-none disabled:opacity-50 leading-relaxed max-h-[200px]"
          />
          <button
            onClick={handleSubmit}
            disabled={isStreaming || !input.trim()}
            className="shrink-0 w-8 h-8 flex items-center justify-center rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground transition-colors duration-fast disabled:opacity-30 disabled:hover:bg-primary active:scale-[0.95]"
          >
            <ArrowUp className="h-4 w-4" strokeWidth={2.5} />
          </button>
        </div>
        <p className="text-[10px] text-muted-foreground/50 mt-1.5 text-center">
          Shift+Enter for new line · Enter to send
        </p>
      </div>
    </div>
  );
}
