import { useState, useRef, useEffect } from 'react';
import useCanvasStore from '../../../stores/canvasStore';

export default function NoteBlock({ block }) {
  const { updateBlockContent } = useCanvasStore();
  const [editing, setEditing] = useState(!block.content.text);
  const [text, setText] = useState(block.content.text || '');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (editing && textareaRef.current) {
      textareaRef.current.focus();
      // Auto-resize
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [editing]);

  const handleBlur = () => {
    if (!text.trim()) {
      // Remove empty notes
      useCanvasStore.getState().removeBlock(block.id);
      return;
    }
    updateBlockContent(block.id, { text });
    setEditing(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      handleBlur();
    }
  };

  if (editing) {
    return (
      <div className="relative">
        <div className="text-[10px] font-semibold uppercase tracking-widest mb-1.5 text-warning/60">
          Note
        </div>
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            e.target.style.height = 'auto';
            e.target.style.height = e.target.scrollHeight + 'px';
          }}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          placeholder="Write a note..."
          className="w-full bg-transparent text-sm text-foreground leading-relaxed resize-none outline-none border-l-2 border-warning/30 pl-3 py-1"
          rows={2}
        />
      </div>
    );
  }

  return (
    <div
      className="cursor-text"
      onDoubleClick={() => setEditing(true)}
    >
      <div className="text-[10px] font-semibold uppercase tracking-widest mb-1.5 text-warning/60">
        Note
      </div>
      <div className="text-sm text-foreground leading-relaxed border-l-2 border-warning/30 pl-3 py-1 whitespace-pre-wrap">
        {block.content.text}
      </div>
    </div>
  );
}
