import { useState, useEffect, useRef } from 'react';
import useChatStore from '../stores/chatStore';

export default function AISidebar() {
  const {
    sidebarOpen,
    closeSidebar,
    messages,
    conversations,
    currentConversationId,
    isStreaming,
    pendingActions,
    error,
    sendMessage,
    loadConversations,
    createConversation,
    selectConversation,
    deleteConversation,
    confirmAction,
    rejectAction,
    clearError,
  } = useChatStore();

  const [input, setInput] = useState('');
  const [showHistory, setShowHistory] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (sidebarOpen) {
      loadConversations();
      inputRef.current?.focus();
    }
  }, [sidebarOpen, loadConversations]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    const content = input.trim();
    setInput('');
    await sendMessage(content);
  };

  const handleNewChat = async () => {
    await createConversation();
    setShowHistory(false);
  };

  if (!sidebarOpen) return null;

  return (
    <div className="h-full w-96 flex-shrink-0 bg-white shadow-2xl z-30 flex flex-col border-l border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611l-.722.12a9.066 9.066 0 01-6.826 0l-.722-.12c-1.717-.293-2.299-2.379-1.067-3.61L5 14.5" />
          </svg>
          <h2 className="text-sm font-semibold text-gray-900">AI Assistant</h2>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleNewChat}
            className="text-xs text-indigo-600 hover:text-indigo-700 px-2 py-1 rounded hover:bg-indigo-50 transition"
            title="New conversation"
          >
            + New
          </button>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="text-gray-500 hover:text-gray-700 p-1 rounded hover:bg-gray-100 transition"
            title="Conversation history"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
          <button
            onClick={closeSidebar}
            className="text-gray-500 hover:text-gray-700 p-1 rounded hover:bg-gray-100 transition"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Conversation History Dropdown */}
      {showHistory && (
        <div className="border-b border-gray-200 max-h-48 overflow-y-auto bg-gray-50">
          {conversations.length === 0 ? (
            <p className="text-sm text-gray-500 p-3">No conversations yet</p>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                className={`flex items-center justify-between px-3 py-2 hover:bg-gray-100 cursor-pointer text-sm ${
                  conv.id === currentConversationId ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700'
                }`}
              >
                <span
                  onClick={() => {
                    selectConversation(conv.id);
                    setShowHistory(false);
                  }}
                  className="flex-1 truncate"
                >
                  {conv.title || 'New conversation'}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation(conv.id);
                  }}
                  className="text-gray-400 hover:text-red-500 ml-2 p-1"
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))
          )}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isStreaming && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-sm">Ask me about your stocks, watchlists, or market trends.</p>
            <div className="mt-4 space-y-2">
              {['What are my watchlists?', 'Scan my watchlist for opportunities', 'Research AAPL'].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => {
                    setInput(suggestion);
                    inputRef.current?.focus();
                  }}
                  className="block w-full text-left text-sm px-3 py-2 rounded-lg bg-gray-50 hover:bg-gray-100 text-gray-700 transition"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={msg.id || i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              {/* Tool calls indicator */}
              {msg.toolCalls && msg.toolCalls.length > 0 && (
                <div className="mb-2 space-y-1">
                  {msg.toolCalls.map((tc, j) => (
                    <div key={j} className="flex items-center gap-1 text-xs text-gray-500">
                      {tc.status === 'running' ? (
                        <span className="animate-pulse">&#9889;</span>
                      ) : (
                        <span>&#10003;</span>
                      )}
                      <span>{tc.tool}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Message content */}
              <div className="whitespace-pre-wrap">{msg.content}</div>

              {/* Streaming cursor */}
              {msg.role === 'assistant' && isStreaming && i === messages.length - 1 && (
                <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-0.5" />
              )}
            </div>
          </div>
        ))}

        {/* Pending Actions */}
        {pendingActions.map((action) => (
          <div key={action.id} className="bg-amber-50 border border-amber-200 rounded-lg p-3">
            <p className="text-sm font-medium text-amber-800 mb-1">Action Requires Confirmation</p>
            <p className="text-sm text-amber-700 mb-3">{action.description}</p>
            <div className="flex gap-2">
              <button
                onClick={() => confirmAction(action.id)}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-1.5 px-3 rounded transition"
              >
                Approve
              </button>
              <button
                onClick={() => rejectAction(action.id)}
                className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm font-medium py-1.5 px-3 rounded transition"
              >
                Reject
              </button>
            </div>
          </div>
        ))}

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <p className="text-sm text-red-700">{error}</p>
            <button onClick={clearError} className="text-xs text-red-500 hover:text-red-700 mt-1">
              Dismiss
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="border-t border-gray-200 p-3">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isStreaming ? 'AI is responding...' : 'Ask anything...'}
            disabled={isStreaming}
            className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-lg transition disabled:opacity-50"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}
