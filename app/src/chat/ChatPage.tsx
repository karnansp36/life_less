// src/chat/ChatPage.tsx
import { useState, useRef, useEffect } from "react";
import { chatWithAI } from "wasp/client/operations";
import { Loader2, Send, Bot, User } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import type { Message } from "./types";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! How can I help you today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(
    undefined
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [sessionId] = useState(() => `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);

  // Auto-scroll to bottom whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Debug: Log session ID on component mount
  useEffect(() => {
    console.log('=== DEBUG: ChatPage mounted ===');
    console.log('Session ID:', sessionId);
    console.log('Initial conversationId:', conversationId);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      conversationId,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    console.log('=== DEBUG: Starting chat request ===');
    console.log('Input message:', input);
    console.log('Conversation ID:', conversationId);
    console.log('Session ID:', sessionId);
    console.log('==============================');

    try {
      const { reply, agent_used, conversation_id, metadata, agent_insights } = await chatWithAI({
        message: input,
        conversation_id: conversationId ? parseInt(conversationId) : undefined,
        session_id: sessionId,
      });

      console.log('=== DEBUG: Chat response received ===');
      console.log('Reply:', reply);
      console.log('Agent used:', agent_used);
      console.log('New conversation_id:', conversation_id);
      console.log('Metadata:', metadata);
      console.log('Agent insights:', agent_insights);
      console.log('==============================');

      if (conversation_id) {
        setConversationId(conversation_id.toString());
        console.log('Updated conversationId:', conversation_id.toString());
      }

      const aiMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: reply,
        agentUsed: agent_used,
        conversationId: conversation_id?.toString(),
        metadata,
        agentInsights: agent_insights,
      };

      setMessages((prev) => [...prev, aiMessage]);

    } catch (err: any) {
      console.error('=== DEBUG: Chat error ===');
      console.error('Error:', err);
      console.error('Error name:', err?.name);
      console.error('Error message:', err?.message);
      console.error('Error status:', err?.status);
      console.error('==============================');

      const errorMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: err?.message || "Sorry, I encountered an error. Please try again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-100px)] bg-background">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-12 items-center px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary">
              <Bot className="h-3.5 w-3.5 text-primary-foreground" />
            </div>
            <h1 className="text-base font-semibold">AI Assistant</h1>
          </div>
          {/* Debug info */}
          <div className="ml-auto text-xs text-muted-foreground">
            Session: {sessionId.substring(0, 8)}...
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-2.5 ${
                message.role === "user" ? "flex-row-reverse" : ""
              }`}
            >
              {/* Avatar */}
              <div
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                  message.role === "user" ? "bg-primary" : "bg-muted"
                }`}
              >
                {message.role === "user" ? (
                  <User className="h-3.5 w-3.5 text-primary-foreground" />
                ) : (
                  <Bot className="h-3.5 w-3.5 text-muted-foreground" />
                )}
              </div>

              {/* Message Bubble */}
              <div
                className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-3 py-2.5 ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted/50"
                }`}
              >
                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </p>
                {message.role === "assistant" && (
                  <div className="mt-1 text-[10px] text-muted-foreground/70">
                    {message.agentUsed && <span>Agent: {message.agentUsed}</span>}
                    {message.metadata?.processing_time !== undefined && (
                      <span className="ml-2">
                        Time: {message.metadata.processing_time}ms
                      </span>
                    )}
                    {message.agentInsights?.model_used && (
                      <span className="ml-2">
                        Model: {message.agentInsights.model_used}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex gap-2.5">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted">
                <Bot className="h-3.5 w-3.5 text-muted-foreground" />
              </div>
              <div className="rounded-2xl bg-muted/50 px-3 py-2.5">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <div className="relative flex-1">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Message AI Assistant..."
                disabled={isLoading}
                className="pr-12 rounded-full border-0 bg-muted/50 focus-visible:ring-1"
              />
              <Button
                type="submit"
                size="sm"
                disabled={isLoading || !input.trim()}
                className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 rounded-full p-0"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          </form>
          <p className="mt-2 text-center text-xs text-muted-foreground/75">
            AI can make mistakes. Consider checking important information.
          </p>
        </div>
      </div>
    </div>
  );
}