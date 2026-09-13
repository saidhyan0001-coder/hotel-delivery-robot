"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { signOut, useSession } from "next-auth/react";
import { useTheme } from "next-themes";
import {
  Plus,
  MessageSquare,
  Search,
  Trash2,
  LogOut,
  Sun,
  Moon,
  Sparkles,
  Menu,
  X,
} from "lucide-react";

interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

export default function Sidebar() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const { data: session } = useSession();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    fetchConversations();
  }, [pathname]);

  const fetchConversations = async () => {
    try {
      const res = await fetch("/api/conversations");
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
      }
    } catch (error) {
      console.error("Failed to fetch conversations:", error);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this chat?")) return;

    try {
      const res = await fetch(`/api/conversations/${id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setConversations((prev) => prev.filter((c) => c.id !== id));
        if (pathname === `/chat/${id}`) {
          router.push("/");
        }
      }
    } catch (error) {
      console.error("Failed to delete conversation:", error);
    }
  };

  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <>
      {/* Mobile Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="md:hidden fixed top-3 left-3 z-50 p-2 rounded-lg bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 text-gray-700 dark:text-gray-200 shadow-sm"
        aria-label="Toggle Menu"
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Backdrop for mobile */}
      {isOpen && (
        <div
          onClick={() => setIsOpen(false)}
          className="md:hidden fixed inset-0 bg-black/40 backdrop-blur-xs z-40"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-40 w-72 bg-gray-50/80 dark:bg-zinc-950/80 backdrop-blur-md border-r border-gray-200/60 dark:border-zinc-800/60 flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        {/* Header / Logo */}
        <div className="p-4 flex items-center justify-between border-b border-gray-200/40 dark:border-zinc-800/40">
          <Link href="/" className="flex items-center gap-2 font-bold text-xl tracking-tight text-gray-900 dark:text-gray-100">
            <div className="p-1.5 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 text-white shadow-md">
              <Sparkles size={20} />
            </div>
            <span>Lumina AI</span>
          </Link>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <Link
            href="/"
            onClick={() => setIsOpen(false)}
            className="flex items-center justify-center gap-2 w-full py-2.5 px-4 bg-zinc-900 hover:bg-zinc-800 dark:bg-zinc-100 dark:hover:bg-white text-white dark:text-zinc-900 font-medium rounded-xl shadow-xs transition-all duration-200"
          >
            <Plus size={18} />
            <span>New Chat</span>
          </Link>
        </div>

        {/* Search Bar */}
        <div className="px-3 py-1">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 text-gray-400 dark:text-zinc-500" size={16} />
            <input
              type="text"
              placeholder="Search chats..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-sm bg-gray-200/50 dark:bg-zinc-900/50 border border-transparent focus:border-gray-300 dark:focus:border-zinc-700 rounded-lg text-gray-900 dark:text-gray-100 outline-none transition"
            />
          </div>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
          <div className="text-xs font-semibold px-2 py-1 text-gray-400 dark:text-zinc-500 uppercase tracking-wider">
            History
          </div>

          {filteredConversations.length === 0 ? (
            <p className="text-xs text-gray-400 dark:text-zinc-600 px-2 py-4 text-center">
              No conversations found.
            </p>
          ) : (
            filteredConversations.map((conv) => {
              const isActive = pathname === `/chat/${conv.id}`;
              return (
                <Link
                  key={conv.id}
                  href={`/chat/${conv.id}`}
                  onClick={() => setIsOpen(false)}
                  className={`group relative flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 ${
                    isActive
                      ? "bg-white dark:bg-zinc-900 text-gray-900 dark:text-gray-100 font-medium shadow-xs border border-gray-200/50 dark:border-zinc-800/50"
                      : "text-gray-600 dark:text-zinc-400 hover:bg-gray-200/50 dark:hover:bg-zinc-900/50 hover:text-gray-900 dark:hover:text-gray-200"
                  }`}
                >
                  <MessageSquare size={16} className="shrink-0 opacity-70" />
                  <span className="truncate flex-1">{conv.title}</span>

                  <button
                    onClick={(e) => handleDelete(e, conv.id)}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-500 rounded transition"
                    title="Delete conversation"
                  >
                    <Trash2 size={14} />
                  </button>
                </Link>
              );
            })
          )}
        </div>

        {/* Footer / User Profile & Settings */}
        <div className="p-3 border-t border-gray-200/40 dark:border-zinc-800/40 space-y-2">
          {/* Theme Toggle */}
          {mounted && (
            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="flex items-center justify-between w-full px-3 py-2 text-sm text-gray-600 dark:text-zinc-400 hover:bg-gray-200/50 dark:hover:bg-zinc-900/50 rounded-lg transition"
            >
              <span className="flex items-center gap-2">
                {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
                <span>{theme === "dark" ? "Light Mode" : "Dark Mode"}</span>
              </span>
            </button>
          )}

          {/* User Info & Logout */}
          <div className="flex items-center justify-between px-3 py-2 bg-white/50 dark:bg-zinc-900/50 rounded-lg border border-gray-200/30 dark:border-zinc-800/30">
            <div className="truncate text-xs font-medium text-gray-700 dark:text-zinc-300">
              {session?.user?.email || "User"}
            </div>
            <button
              onClick={() => signOut()}
              className="p-1 text-gray-500 hover:text-red-500 dark:text-zinc-400 dark:hover:text-red-400 transition"
              title="Sign Out"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
