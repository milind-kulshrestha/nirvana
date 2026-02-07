import useChatStore from '../stores/chatStore';
import useAIContextStore from '../stores/aiContextStore';

export default function SendToAIButton({ componentId, label = 'Ask AI' }) {
  const { openSidebar, sendMessage } = useChatStore();
  const captureComponent = useAIContextStore((s) => s.captureComponent);

  const handleClick = async (e) => {
    e.stopPropagation();

    // Capture component data
    const context = await captureComponent(componentId);
    if (!context) return;

    // Open sidebar and send with context
    openSidebar();
    await sendMessage(
      `Analyze this ${context.data?.type || 'component'}`,
      context,
    );
  };

  return (
    <button
      onClick={handleClick}
      className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-700 bg-white hover:bg-indigo-50 border border-indigo-200 rounded-full px-2 py-0.5 shadow-sm transition"
      title={label}
    >
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082" />
      </svg>
      AI
    </button>
  );
}
