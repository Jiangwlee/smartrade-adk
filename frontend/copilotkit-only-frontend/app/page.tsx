import { CopilotChatWrapper } from "@/components/copilot-chat-wrapper";

export default function Home() {
  return (
    <main className="flex-1 min-h-0 flex flex-col">
      <section className="flex-1 min-h-0 w-full px-4 pb-0 flex flex-col chat-section">
        <div className="content-shell flex flex-col flex-1 min-h-0 items-stretch chat-shell">
          <CopilotChatWrapper />
        </div>
      </section>
    </main>
  );
}
