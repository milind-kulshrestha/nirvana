import { create } from 'zustand';

const API_BASE = 'http://localhost:8000';

const useChatStore = create((set, get) => ({
  // State
  conversations: [],
  currentConversationId: null,
  messages: [],
  isStreaming: false,
  pendingActions: [],
  error: null,
  sidebarOpen: false,

  // Sidebar
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  openSidebar: () => set({ sidebarOpen: true }),
  closeSidebar: () => set({ sidebarOpen: false }),

  // Conversations
  loadConversations: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/chat/conversations`, {
        credentials: 'include',
      });
      if (res.ok) {
        const data = await res.json();
        set({ conversations: data });
      }
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  },

  createConversation: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/chat/conversations`, {
        method: 'POST',
        credentials: 'include',
      });
      if (res.ok) {
        const conv = await res.json();
        set({
          currentConversationId: conv.id,
          messages: [],
        });
        return conv;
      }
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
    return null;
  },

  selectConversation: async (conversationId) => {
    set({ currentConversationId: conversationId, messages: [] });
    try {
      const res = await fetch(
        `${API_BASE}/api/chat/conversations/${conversationId}/messages`,
        { credentials: 'include' }
      );
      if (res.ok) {
        const messages = await res.json();
        set({ messages });
      }
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  },

  deleteConversation: async (conversationId) => {
    try {
      await fetch(`${API_BASE}/api/chat/conversations/${conversationId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      const { currentConversationId, conversations } = get();
      set({
        conversations: conversations.filter((c) => c.id !== conversationId),
        ...(currentConversationId === conversationId
          ? { currentConversationId: null, messages: [] }
          : {}),
      });
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  },

  // Send message with SSE streaming
  sendMessage: async (content, componentContext = null) => {
    const { currentConversationId } = get();

    // Add user message to UI immediately
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };
    set((s) => ({
      messages: [...s.messages, userMessage],
      isStreaming: true,
      error: null,
    }));

    // Create placeholder for assistant message
    const assistantMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      toolCalls: [],
    };
    set((s) => ({
      messages: [...s.messages, assistantMessage],
    }));

    try {
      const res = await fetch(`${API_BASE}/api/chat/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          content,
          conversation_id: currentConversationId,
          component_context: componentContext,
        }),
      });

      if (!res.ok) {
        throw new Error(`Chat request failed: ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const data = line.slice(6).trim();
          if (!data) continue;

          try {
            const event = JSON.parse(data);
            const { messages } = get();
            const lastIdx = messages.length - 1;

            switch (event.type) {
              case 'token':
                // Append token to assistant message
                set({
                  messages: messages.map((m, i) =>
                    i === lastIdx
                      ? { ...m, content: m.content + event.content }
                      : m
                  ),
                });
                break;

              case 'tool_call':
                set({
                  messages: messages.map((m, i) =>
                    i === lastIdx
                      ? {
                          ...m,
                          toolCalls: [
                            ...(m.toolCalls || []),
                            { tool: event.tool, input: event.input, status: 'running' },
                          ],
                        }
                      : m
                  ),
                });
                break;

              case 'tool_result':
                set({
                  messages: messages.map((m, i) =>
                    i === lastIdx
                      ? {
                          ...m,
                          toolCalls: (m.toolCalls || []).map((tc) =>
                            tc.tool === event.tool
                              ? { ...tc, output: event.output, status: 'done' }
                              : tc
                          ),
                        }
                      : m
                  ),
                });
                break;

              case 'action_proposed':
                set((s) => ({
                  pendingActions: [
                    ...s.pendingActions,
                    {
                      id: event.action_id,
                      action_type: event.action_type,
                      description: event.description,
                    },
                  ],
                }));
                break;

              case 'done':
                if (event.conversation_id) {
                  set({ currentConversationId: event.conversation_id });
                }
                break;

              case 'error':
                set({ error: event.message });
                break;
            }
          } catch (e) {
            console.error('Failed to parse SSE event:', e);
          }
        }
      }
    } catch (error) {
      set({ error: error.message });
    } finally {
      set({ isStreaming: false });
      // Refresh conversations list
      get().loadConversations();
    }
  },

  // Actions
  confirmAction: async (actionId) => {
    try {
      const res = await fetch(`${API_BASE}/api/chat/actions/${actionId}/confirm`, {
        method: 'POST',
        credentials: 'include',
      });
      if (res.ok) {
        set((s) => ({
          pendingActions: s.pendingActions.filter((a) => a.id !== actionId),
        }));
        return true;
      }
    } catch (error) {
      console.error('Failed to confirm action:', error);
    }
    return false;
  },

  rejectAction: async (actionId) => {
    try {
      const res = await fetch(`${API_BASE}/api/chat/actions/${actionId}/reject`, {
        method: 'POST',
        credentials: 'include',
      });
      if (res.ok) {
        set((s) => ({
          pendingActions: s.pendingActions.filter((a) => a.id !== actionId),
        }));
        return true;
      }
    } catch (error) {
      console.error('Failed to reject action:', error);
    }
    return false;
  },

  // Clear
  clearError: () => set({ error: null }),
  clearMessages: () => set({ messages: [], currentConversationId: null }),
}));

export default useChatStore;
