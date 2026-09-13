import { openai } from "@ai-sdk/openai";
import { streamText } from "ai";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export const maxDuration = 30;

export async function POST(req: Request) {
  try {
    const session = await getServerSession(authOptions);

    if (!session || !session.user || !session.user.id) {
      return new Response("Unauthorized", { status: 401 });
    }

    const userId = session.user.id;
    const { messages, conversationId } = await req.json();

    if (!messages || !Array.isArray(messages)) {
      return new Response("Invalid request", { status: 400 });
    }

    let currentConversationId = conversationId;
    const latestMessage = messages[messages.length - 1];

    // Create a new conversation if one doesn't exist
    if (!currentConversationId) {
      const newConversation = await prisma.conversation.create({
        data: {
          userId,
          title: latestMessage.content.substring(0, 50) || "New Conversation",
        },
      });
      currentConversationId = newConversation.id;
    }

    // Save the user's message
    await prisma.message.create({
      data: {
        conversationId: currentConversationId,
        role: "user",
        content: latestMessage.content,
      },
    });

    const result = streamText({
      model: openai("gpt-4o-mini"),
      system: "You are Lumina, a helpful and premium AI assistant. Respond in markdown format.",
      messages,
      async onFinish({ text }) {
        await prisma.message.create({
          data: {
            conversationId: currentConversationId,
            role: "assistant",
            content: text,
          },
        });
      },
    });

    return result.toTextStreamResponse({
      headers: {
        "x-conversation-id": currentConversationId,
      },
    });
  } catch (error) {
    console.error("Error in chat API:", error);
    return new Response("Internal Server Error", { status: 500 });
  }
}
