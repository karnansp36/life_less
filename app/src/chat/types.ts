// src/chat/types.ts
export type ChatResponse = {
  reply: string;
  provider?: string;
};

export type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt?: string; // Optional for historical messages
};

// Add this if you need to type the API response for conversation history
export type ConversationHistoryResponse = Message[];