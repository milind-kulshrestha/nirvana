import { useState } from 'react';
import useChatStore from '../stores/chatStore';
import ChatMessageList from '../components/chat/ChatMessageList';
import CanvasStream from '../components/canvas/CanvasStream';
import WelcomeState from '../components/canvas/WelcomeState';
import TopBar from '../components/layout/TopBar';
import ComposeBar from '../components/layout/ComposeBar';

export default function AgentHub() {
  const { messages, isStreaming } = useChatStore();
  const [mode, setMode] = useState('canvas'); // 'chat' | 'canvas'
  const hasMessages = messages.length > 0 || isStreaming;

  return (
    <div className="flex flex-col h-full">
      <TopBar mode={mode} onModeChange={setMode} />
      {hasMessages ? (
        mode === 'canvas' ? <CanvasStream /> : <ChatMessageList />
      ) : (
        <WelcomeState />
      )}
      <ComposeBar />
    </div>
  );
}
