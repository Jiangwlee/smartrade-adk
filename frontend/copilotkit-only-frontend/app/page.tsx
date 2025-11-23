import { CopilotChatWrapper } from "@/components/copilot-chat-wrapper";

export default function Home() {
  return (
    <main className="content-shell flex flex-col items-center min-h-screen p-4">
      <div className="content-shell chat-panel flex">
        <CopilotChatWrapper/>
      </div>
    </main>
  );
}
