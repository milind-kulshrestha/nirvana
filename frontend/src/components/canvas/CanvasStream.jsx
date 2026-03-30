import { useEffect, useRef } from 'react';
import useChatStore from '../../stores/chatStore';
import useCanvasStore from '../../stores/canvasStore';
import CanvasBlock from './CanvasBlock';
import ErrorBoundary from '../ErrorBoundary';
import { StickyNote } from 'lucide-react';

export default function CanvasStream() {
  const messages = useChatStore((s) => s.messages);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const { blocks, syncFromMessages, addNote } = useCanvasStore();
  const endRef = useRef(null);

  // Sync blocks whenever messages change
  useEffect(() => {
    syncFromMessages(messages);
  }, [messages, syncFromMessages]);

  // Auto-scroll on new content
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [blocks, isStreaming]);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-[800px] mx-auto px-12 py-8 space-y-6">
        {blocks.map((block) => (
          <ErrorBoundary key={block.id}>
            <CanvasBlock block={block} />
          </ErrorBoundary>
        ))}

        {/* Add note button — appears after last block */}
        {blocks.length > 0 && !isStreaming && (
          <button
            onClick={() => addNote()}
            className="flex items-center gap-1.5 text-xs text-muted-foreground/40 hover:text-muted-foreground transition-colors duration-fast py-2"
          >
            <StickyNote className="h-3 w-3" />
            Add note
          </button>
        )}

        <div ref={endRef} />
      </div>
    </div>
  );
}
