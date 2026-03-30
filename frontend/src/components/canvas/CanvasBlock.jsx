import { useState } from 'react';
import useCanvasStore from '../../stores/canvasStore';
import MessageBlock from './blocks/MessageBlock';
import NoteBlock from './blocks/NoteBlock';
import { Pin, PinOff, Trash2, GripVertical, Copy, Check } from 'lucide-react';

const BLOCK_RENDERERS = {
  message: MessageBlock,
  note: NoteBlock,
};

export default function CanvasBlock({ block }) {
  const { removeBlock, togglePin } = useCanvasStore();
  const [hovered, setHovered] = useState(false);
  const [copied, setCopied] = useState(false);

  const Renderer = BLOCK_RENDERERS[block.type];
  if (!Renderer) return null;

  const canDelete = block.type === 'note' || !block.sourceMessageId;
  const isPinned = block.metadata?.pinned;

  const handleCopy = async () => {
    const text = block.content?.text || '';
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // ignore
    }
  };

  return (
    <div
      className="group relative"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Hover toolbar */}
      <div className={`absolute -left-10 top-0 flex flex-col gap-0.5 transition-opacity duration-fast ${hovered ? 'opacity-100' : 'opacity-0'}`}>
        <button
          className="p-1 rounded text-muted-foreground/40 hover:text-muted-foreground hover:bg-muted transition-colors"
          title="Drag to reorder"
        >
          <GripVertical className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={() => togglePin(block.id)}
          className={`p-1 rounded transition-colors ${
            isPinned
              ? 'text-warning hover:text-warning/70 hover:bg-warning/10'
              : 'text-muted-foreground/40 hover:text-warning hover:bg-warning/10'
          }`}
          title={isPinned ? 'Unpin' : 'Pin'}
        >
          {isPinned ? <PinOff className="h-3.5 w-3.5" /> : <Pin className="h-3.5 w-3.5" />}
        </button>
        <button
          onClick={handleCopy}
          className="p-1 rounded text-muted-foreground/40 hover:text-foreground hover:bg-muted transition-colors"
          title="Copy as markdown"
        >
          {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
        </button>
        {canDelete && (
          <button
            onClick={() => removeBlock(block.id)}
            className="p-1 rounded text-muted-foreground/40 hover:text-destructive hover:bg-destructive/10 transition-colors"
            title="Remove"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* Pin indicator */}
      {isPinned && !hovered && (
        <div className="absolute -left-6 top-0.5">
          <Pin className="h-3 w-3 text-warning/60" />
        </div>
      )}

      {/* Block content */}
      <Renderer block={block} />
    </div>
  );
}
