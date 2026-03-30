import useChatStore from '../../stores/chatStore';
import { Wrench, Clock } from 'lucide-react';

export default function RunSteps() {
  const messages = useChatStore((s) => s.messages);

  // Collect all tool calls from assistant messages
  const steps = messages
    .filter((m) => m.role === 'assistant' && m.toolCalls?.length > 0)
    .flatMap((m, mi) =>
      m.toolCalls.map((tc, ti) => ({
        key: `${mi}-${ti}`,
        tool: tc.tool,
        status: tc.status,
        input: tc.input,
        output: tc.output,
      }))
    );

  if (steps.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-40 text-muted-foreground/50">
        <Wrench className="h-5 w-5 mb-2" />
        <p className="text-xs">No tool calls yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {steps.map((step, i) => (
        <div
          key={step.key}
          className="flex items-start gap-2.5 px-3 py-2 rounded-lg hover:bg-muted/50 transition-colors duration-fast"
        >
          {/* Timeline dot */}
          <div className="flex flex-col items-center pt-1.5 shrink-0">
            <div
              className={`w-2 h-2 rounded-full ${
                step.status === 'running' ? 'bg-warning animate-pulse' : 'bg-success'
              }`}
            />
            {i < steps.length - 1 && (
              <div className="w-px h-full min-h-[16px] bg-border mt-1" />
            )}
          </div>

          {/* Content */}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-mono font-medium text-foreground truncate">
                {step.tool}
              </span>
              {step.status === 'running' && (
                <Clock className="h-2.5 w-2.5 text-warning animate-pulse shrink-0" />
              )}
            </div>
            {step.input && (
              <p className="text-[10px] text-muted-foreground truncate mt-0.5">
                {typeof step.input === 'string'
                  ? step.input
                  : JSON.stringify(step.input).slice(0, 80)}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
