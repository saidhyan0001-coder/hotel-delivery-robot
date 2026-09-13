import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { redirect } from "next/navigation";
import ChatUI from "@/components/ChatUI";
import Sidebar from "@/components/Sidebar";

export default async function ChatPage({ params }: { params: { id: string } }) {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect("/login");
  }

  return (
    <div className="flex h-screen bg-white dark:bg-zinc-950 overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        <ChatUI conversationId={params.id} />
      </div>
    </div>
  );
}
