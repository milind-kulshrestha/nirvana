import ReactMarkdown from 'react-markdown';
import useChatStore from '../../../stores/chatStore';

export default function MessageBlock({ block }) {
  const { isStreaming, messages } = useChatStore();
  const { text, toolCalls } = block.content || {};
  const isUser = block.role === 'user';

  // Check if this is the last assistant block currently streaming
  const isLastAssistant =
    block.role === 'assistant' &&
    isStreaming &&
    block.sourceMessageId === messages[messages.length - 1]?.id;

  return (
    <div className={isUser ? 'pl-12' : ''}>
      {/* Role label */}
      <div className={`text-[10px] font-semibold uppercase tracking-widest mb-1.5 ${
        isUser ? 'text-primary/60 text-right' : 'text-muted-foreground/60'
      }`}>
        {isUser ? 'You' : 'Agent'}
      </div>

      {/* Tool calls */}
      {toolCalls && toolCalls.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-1.5">
          {toolCalls.map((tc, j) => (
            <span
              key={j}
              className="inline-flex items-center gap-1.5 text-[11px] font-mono px-2 py-0.5 rounded-md bg-muted/80 text-muted-foreground"
            >
              {tc.status === 'running' ? (
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-warning animate-pulse" />
              ) : (
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-success" />
              )}
              {tc.tool}
            </span>
          ))}
        </div>
      )}

      {/* Content */}
      <div className={isUser
        ? 'text-sm text-foreground/80 leading-relaxed'
        : 'text-sm text-foreground leading-relaxed'
      }>
        <div className="prose prose-sm max-w-none prose-headings:text-foreground prose-p:text-foreground prose-strong:text-foreground prose-code:text-primary prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs">
          <ReactMarkdown>{text || ''}</ReactMarkdown>
        </div>

        {isLastAssistant && (
          <span className="inline-block w-2 h-4 bg-primary/60 animate-pulse ml-0.5 rounded-sm" />
        )}
      </div>
    </div>
  );
}
