import { create } from 'zustand';

let blockCounter = 0;
const nextId = () => `block_${Date.now()}_${++blockCounter}`;

const useCanvasStore = create((set, get) => ({
  blocks: [],
  activeBlockId: null,

  // Derive blocks from chatStore messages
  // Called after messages change or on conversation load
  syncFromMessages: (messages) => {
    const existing = get().blocks;
    const existingByMsgId = new Map(
      existing.filter((b) => b.sourceMessageId).map((b) => [b.sourceMessageId, b])
    );

    // Keep user-created blocks (no sourceMessageId) in their positions
    const userBlocks = existing.filter((b) => !b.sourceMessageId);

    const messageBlocks = messages.map((msg, i) => {
      // Reuse existing block if message already tracked
      const prev = existingByMsgId.get(msg.id);
      if (prev) {
        // Update content if message content changed (streaming)
        return {
          ...prev,
          content: {
            ...prev.content,
            text: msg.content,
            toolCalls: msg.toolCalls || [],
          },
        };
      }

      return {
        id: nextId(),
        type: 'message',
        sourceMessageId: msg.id,
        role: msg.role,
        content: {
          text: msg.content,
          toolCalls: msg.toolCalls || [],
        },
        metadata: {
          pinned: false,
          createdAt: msg.created_at || new Date().toISOString(),
        },
        order: i,
      };
    });

    // Merge: message blocks first (in order), then user blocks at the end
    set({ blocks: [...messageBlocks, ...userBlocks] });
  },

  // Add a user-created note block
  addNote: (text = '') => {
    const block = {
      id: nextId(),
      type: 'note',
      sourceMessageId: null,
      role: null,
      content: { text },
      metadata: {
        pinned: false,
        createdAt: new Date().toISOString(),
        editable: true,
      },
      order: get().blocks.length,
    };
    set((s) => ({ blocks: [...s.blocks, block] }));
    return block.id;
  },

  // Update block content
  updateBlockContent: (blockId, content) => {
    set((s) => ({
      blocks: s.blocks.map((b) =>
        b.id === blockId ? { ...b, content: { ...b.content, ...content } } : b
      ),
    }));
  },

  // Remove a block
  removeBlock: (blockId) => {
    set((s) => ({
      blocks: s.blocks.filter((b) => b.id !== blockId),
      activeBlockId: s.activeBlockId === blockId ? null : s.activeBlockId,
    }));
  },

  // Toggle pin
  togglePin: (blockId) => {
    set((s) => ({
      blocks: s.blocks.map((b) =>
        b.id === blockId
          ? { ...b, metadata: { ...b.metadata, pinned: !b.metadata.pinned } }
          : b
      ),
    }));
  },

  // Set active block (for editing/focus)
  setActiveBlock: (blockId) => set({ activeBlockId: blockId }),

  // Clear all blocks
  clearBlocks: () => set({ blocks: [], activeBlockId: null }),
}));

export default useCanvasStore;
