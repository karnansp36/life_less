// src/chat/types.ts
export type ChatResponse = {
  response: string;
  conversation_id?: number;
  agent_used: string;
  success: boolean;
  metadata?: Record<string, any>;
};

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt?: string;
  agentUsed?: string;
  conversationId?: string;
  metadata?: {
    memories_used?: number;
    processing_time?: number;
  };
};

// Add this if you need to type the API response for conversation history
export type ConversationHistoryResponse = Message[];
