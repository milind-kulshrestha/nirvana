import { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import useChatStore from '../../stores/chatStore';

export default function ChatMessageList() {
  const { messages, isStreaming, pendingActions, error, confirmAction, rejectAction, clearError } =
    useChatStore();
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5">
      {messages.map((msg, i) => (
        <div key={msg.id || i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
          <div
            className={`max-w-[720px] rounded-xl px-4 py-3 text-sm leading-relaxed ${
              msg.role === 'user'
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted/60 text-foreground'
            }`}
          >
            {/* Tool calls */}
            {msg.toolCalls && msg.toolCalls.length > 0 && (
              <div className="mb-2.5 space-y-1">
                {msg.toolCalls.map((tc, j) => (
                  <div key={j} className="flex items-center gap-1.5 text-xs text-muted-foreground font-mono">
                    {tc.status === 'running' ? (
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-warning animate-pulse" />
                    ) : (
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-success" />
                    )}
                    <span>{tc.tool}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Content */}
            <div className={`prose prose-sm max-w-none ${
                msg.role === 'user' ? 'prose-invert' : ''
              }`}>
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>

            {/* Streaming cursor */}
            {msg.role === 'assistant' && isStreaming && i === messages.length - 1 && (
              <span className="inline-block w-2 h-4 bg-primary/60 animate-pulse ml-0.5 rounded-sm" />
            )}
          </div>
        </div>
      ))}

      {/* Pending Actions */}
      {pendingActions.map((action) => (
        <div key={action.id} className="max-w-[720px] mx-auto bg-warning/10 border border-warning/20 rounded-xl p-4">
          <p className="text-sm font-medium text-warning mb-1">Action Requires Confirmation</p>
          <p className="text-sm text-foreground mb-3">{action.description}</p>
          <div className="flex gap-2">
            <button
              onClick={() => confirmAction(action.id)}
              className="flex-1 bg-success hover:bg-success/90 text-white text-sm font-medium py-1.5 px-3 rounded-lg transition-colors duration-fast active:scale-[0.98]"
            >
              Approve
            </button>
            <button
              onClick={() => rejectAction(action.id)}
              className="flex-1 bg-secondary hover:bg-secondary/80 text-secondary-foreground text-sm font-medium py-1.5 px-3 rounded-lg transition-colors duration-fast active:scale-[0.98]"
            >
              Reject
            </button>
          </div>
        </div>
      ))}

      {/* Error */}
      {error && (
        <div className="max-w-[720px] mx-auto bg-destructive/10 border border-destructive/20 rounded-xl p-4">
          <p className="text-sm text-destructive">{error}</p>
          <button onClick={clearError} className="text-xs text-destructive/70 hover:text-destructive mt-1 transition-colors duration-fast">
            Dismiss
          </button>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}
