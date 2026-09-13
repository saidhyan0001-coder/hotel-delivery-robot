"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useRouter } from "next/navigation";
import {
  Send,
  Square,
  Sparkles,
  Copy,
  Check,
  RefreshCw,
  Paperclip,
  Mic,
  Lightbulb,
  Code,
  PenTool,
  HelpCircle,
  AlertCircle,
} from "lucide-react";

interface Message {
  id?: string;
  role: "user" | "assistant" | "system";
  content: string;
}

interface ChatUIProps {
  conversationId?: string;
}

export default function ChatUI({ conversationId }: ChatUIProps) {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load existing messages if conversationId is present
  useEffect(() => {
    if (conversationId) {
      fetch(`/api/conversations/${conversationId}`)
        .then((res) => res.json())
        .then((data) => {
          if (data?.messages) {
            setMessages(
              data.messages.map((m: any) => ({
                id: m.id,
                role: m.role as "user" | "assistant" | "system",
                content: m.content,
              }))
            );
          }
        })
        .catch((err) => {
          console.error("Failed to load conversation:", err);
          setError("Failed to load conversation messages.");
        });
    }
  }, [conversationId]);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Auto-grow textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isLoading) {
        sendMessage(input);
      }
    }
  };

  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  };

  const sendMessage = async (contentToSend: string) => {
    if (!contentToSend.trim() || isLoading) return;

    setError(null);
    const userMessage: Message = { role: "user", content: contentToSend };
    const updatedMessages = [...messages, userMessage];

    setMessages(updatedMessages);
    setInput("");
    setIsLoading(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: updatedMessages,
          conversationId,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      // Check for new conversation ID in headers
      const newConvId = response.headers.get("x-conversation-id");
      if (newConvId && !conversationId) {
        router.push(`/chat/${newConvId}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("No response stream reader available");
      }

      // Add empty assistant message placeholder
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

      let assistantContent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        assistantContent += chunk;

        setMessages((prev) => {
          const newMsgs = [...prev];
          newMsgs[newMsgs.length - 1] = {
            role: "assistant",
            content: assistantContent,
          };
          return newMsgs;
        });
      }
    } catch (err: any) {
      if (err.name !== "AbortError") {
        console.error("Failed to send message:", err);
        setError("Failed to generate response. Please check your connection or API configuration.");
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const regenerateResponse = () => {
    if (messages.length === 0 || isLoading) return;
    const lastUserMessageIndex = [...messages].reverse().findIndex((m) => m.role === "user");
    if (lastUserMessageIndex === -1) return;

    const actualIndex = messages.length - 1 - lastUserMessageIndex;
    const lastUserMessage = messages[actualIndex];
    const previousMessages = messages.slice(0, actualIndex);
    
    setMessages(previousMessages);
    sendMessage(lastUserMessage.content);
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSuggestionClick = (promptText: string) => {
    setInput(promptText);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-white dark:bg-zinc-950 overflow-hidden relative">
      {/* Header */}
      <header className="h-14 border-b border-gray-200/50 dark:border-zinc-800/50 flex items-center justify-between px-6 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md z-10">
        <div className="flex items-center gap-2 font-medium text-sm text-gray-700 dark:text-gray-200">
          <Sparkles size={16} className="text-blue-500" />
          <span>Lumina Assistant</span>
        </div>
      </header>

      {/* Message Area */}
      <div className="flex-1 overflow-y-auto px-4 md:px-0 py-6">
        <div className="max-w-3xl mx-auto space-y-6 pb-24">
          {error && (
            <div className="flex items-center gap-2 p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 text-sm">
              <AlertCircle size={18} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {messages.length === 0 ? (
            /* Empty State / Welcome Screen */
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-8 animate-fade-in">
              <div className="p-4 rounded-3xl bg-blue-50 dark:bg-zinc-900 border border-blue-100 dark:border-zinc-800 text-blue-600 dark:text-blue-400 shadow-sm">
                <Sparkles size={40} />
              </div>
              <div className="space-y-2">
                <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
                  Hello, I'm Lumina.
                </h1>
                <p className="text-gray-500 dark:text-zinc-400 text-base md:text-lg">
                  What can I help you with today?
                </p>
              </div>

              {/* Suggestion Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl px-4">
                <button
                  onClick={() => handleSuggestionClick("Explain quantum computing in simple terms")}
                  className="flex items-start gap-3 p-4 text-left rounded-2xl bg-gray-50 dark:bg-zinc-900/50 border border-gray-200/60 dark:border-zinc-800/60 hover:bg-gray-100 dark:hover:bg-zinc-900 transition-all duration-200 group"
                >
                  <HelpCircle className="text-blue-500 shrink-0 mt-0.5" size={18} />
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-200 group-hover:text-blue-600 dark:group-hover:text-blue-400">
                      Explain something
                    </div>
                    <div className="text-xs text-gray-500 dark:text-zinc-400 mt-0.5">
                      Quantum computing in simple terms
                    </div>
                  </div>
                </button>

                <button
                  onClick={() => handleSuggestionClick("Help me write a compelling essay outline on climate action")}
                  className="flex items-start gap-3 p-4 text-left rounded-2xl bg-gray-50 dark:bg-zinc-900/50 border border-gray-200/60 dark:border-zinc-800/60 hover:bg-gray-100 dark:hover:bg-zinc-900 transition-all duration-200 group"
                >
                  <PenTool className="text-indigo-500 shrink-0 mt-0.5" size={18} />
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                      Help me write
                    </div>
                    <div className="text-xs text-gray-500 dark:text-zinc-400 mt-0.5">
                      An essay outline on climate action
                    </div>
                  </div>
                </button>

                <button
                  onClick={() => handleSuggestionClick("Write a React component for a custom modal dialog")}
                  className="flex items-start gap-3 p-4 text-left rounded-2xl bg-gray-50 dark:bg-zinc-900/50 border border-gray-200/60 dark:border-zinc-800/60 hover:bg-gray-100 dark:hover:bg-zinc-900 transition-all duration-200 group"
                >
                  <Code className="text-emerald-500 shrink-0 mt-0.5" size={18} />
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-200 group-hover:text-emerald-600 dark:group-hover:text-emerald-400">
                      Help me code
                    </div>
                    <div className="text-xs text-gray-500 dark:text-zinc-400 mt-0.5">
                      React component for a custom modal
                    </div>
                  </div>
                </button>

                <button
                  onClick={() => handleSuggestionClick("Brainstorm 5 unique startup ideas using AI in education")}
                  className="flex items-start gap-3 p-4 text-left rounded-2xl bg-gray-50 dark:bg-zinc-900/50 border border-gray-200/60 dark:border-zinc-800/60 hover:bg-gray-100 dark:hover:bg-zinc-900 transition-all duration-200 group"
                >
                  <Lightbulb className="text-amber-500 shrink-0 mt-0.5" size={18} />
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-200 group-hover:text-amber-600 dark:group-hover:text-amber-400">
                      Brainstorm ideas
                    </div>
                    <div className="text-xs text-gray-500 dark:text-zinc-400 mt-0.5">
                      Startup ideas for AI in education
                    </div>
                  </div>
                </button>
              </div>
            </div>
          ) : (
            /* Messages List */
            messages.map((message, index) => (
              <div
                key={message.id || index}
                className={`flex flex-col ${
                  message.role === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-5 py-3.5 ${
                    message.role === "user"
                      ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 shadow-sm"
                      : "bg-gray-100/80 dark:bg-zinc-900/80 text-gray-900 dark:text-gray-100 border border-gray-200/50 dark:border-zinc-800/50"
                  }`}
                >
                  {message.role === "user" ? (
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
                  ) : (
                    <div className="prose dark:prose-invert prose-sm max-w-none leading-relaxed">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>

                {/* Message Action Controls */}
                <div className="flex items-center gap-2 mt-1.5 px-1 text-gray-400 dark:text-zinc-500">
                  <button
                    onClick={() => copyToClipboard(message.content, message.id || String(index))}
                    className="p-1 hover:text-gray-600 dark:hover:text-gray-300 rounded transition"
                    title="Copy response"
                  >
                    {copiedId === (message.id || String(index)) ? (
                      <Check size={14} className="text-emerald-500" />
                    ) : (
                      <Copy size={14} />
                    )}
                  </button>

                  {message.role === "assistant" && index === messages.length - 1 && !isLoading && (
                    <button
                      onClick={regenerateResponse}
                      className="p-1 hover:text-gray-600 dark:hover:text-gray-300 rounded transition"
                      title="Regenerate response"
                    >
                      <RefreshCw size={14} />
                    </button>
                  )}
                </div>
              </div>
            ))
          )}

          {/* Thinking Indicator */}
          {isLoading && messages[messages.length - 1]?.role === "user" && (
            <div className="flex items-center gap-2 text-xs text-gray-400 dark:text-zinc-500 animate-pulse pl-2">
              <Sparkles size={14} className="text-blue-500 animate-spin" />
              <span>Lumina is thinking...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Floating Bottom Input Area */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-white via-white/80 to-transparent dark:from-zinc-950 dark:via-zinc-950/80 dark:to-transparent z-10">
        <div className="max-w-3xl mx-auto">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage(input);
            }}
            className="relative flex items-end gap-2 bg-gray-100/90 dark:bg-zinc-900/90 border border-gray-200 dark:border-zinc-800 rounded-2xl p-2 shadow-lg backdrop-blur-md focus-within:border-gray-400 dark:focus-within:border-zinc-700 transition"
          >
            {/* Disabled Attachment Placeholder */}
            <button
              type="button"
              disabled
              className="p-2.5 text-gray-400 dark:text-zinc-600 cursor-not-allowed rounded-xl"
              title="File attachment (Disabled)"
            >
              <Paperclip size={18} />
            </button>

            {/* Auto-growing Textarea */}
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask Lumina anything..."
              className="flex-1 bg-transparent border-0 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-zinc-500 focus:outline-none resize-none max-h-48 py-2.5 px-1"
            />

            {/* Disabled Mic Placeholder */}
            <button
              type="button"
              disabled
              className="p-2.5 text-gray-400 dark:text-zinc-600 cursor-not-allowed rounded-xl"
              title="Voice input (Disabled)"
            >
              <Mic size={18} />
            </button>

            {/* Send / Stop Generation Button */}
            {isLoading ? (
              <button
                type="button"
                onClick={stopGeneration}
                className="p-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl shadow-xs transition"
                title="Stop generation"
              >
                <Square size={18} />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className="p-2.5 bg-zinc-900 hover:bg-zinc-800 dark:bg-zinc-100 dark:hover:bg-white text-white dark:text-zinc-900 disabled:opacity-30 disabled:cursor-not-allowed rounded-xl shadow-xs transition"
              >
                <Send size={18} />
              </button>
            )}
          </form>
          <div className="text-center text-[10px] text-gray-400 dark:text-zinc-600 mt-2">
            Lumina can make mistakes. Consider checking important info.
          </div>
        </div>
      </div>
    </div>
  );
}
