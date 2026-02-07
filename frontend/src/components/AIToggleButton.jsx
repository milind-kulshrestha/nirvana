import useChatStore from '../stores/chatStore';

export default function AIToggleButton() {
  const { sidebarOpen, toggleSidebar } = useChatStore();

  return (
    <button
      onClick={toggleSidebar}
      className={`fixed bottom-6 right-6 z-40 w-12 h-12 rounded-full shadow-lg flex items-center justify-center transition-all ${
        sidebarOpen
          ? 'bg-gray-200 hover:bg-gray-300 text-gray-600'
          : 'bg-indigo-600 hover:bg-indigo-700 text-white'
      }`}
      title={sidebarOpen ? 'Close AI Assistant' : 'Open AI Assistant'}
    >
      {sidebarOpen ? (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      ) : (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611l-.722.12a9.066 9.066 0 01-6.826 0l-.722-.12c-1.717-.293-2.299-2.379-1.067-3.61L5 14.5" />
        </svg>
      )}
    </button>
  );
}
