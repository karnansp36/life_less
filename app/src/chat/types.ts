// src/chat/types.ts

// Response from your FastAPI backend
export type FastAPIResponse = {
  response: string;           // The actual AI response content
  conversation_id?: number;   // Conversation ID (number)
  message_id?: number;        // Message ID if available
  metadata?: {
    processing_time?: number;
    timestamp?: string;
    agents_involved?: string[];
    persona_adapted?: boolean;
  };
  agent_insights?: {
    primary_agent?: string;
    emotion_analysis_completed?: boolean;
    memory_context_retrieved?: boolean;
    model_used?: string;
    confidence?: number;
  };
  agent_used?: string;        // Which agent was used
};

// Response expected by your Wasp operation
export type ChatResponse = {
  reply: string;              // Mapped from response
  conversation_id?: number;
  agent_used?: string;
  success: boolean;
  metadata?: Record<string, any>;
};

// Message type for frontend display
export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;            // This will store the response text
  createdAt?: string;
  agentUsed?: string;         // For displaying which agent responded
  conversationId?: string;    // String version for frontend
  metadata?: {
    processing_time?: number;
    timestamp?: string;
    agents_involved?: string[];
    persona_adapted?: boolean;
    memories_used?: number;
  };
  agentInsights?: {
    primary_agent?: string;
    emotion_analysis_completed?: boolean;
    memory_context_retrieved?: boolean;
    model_used?: string;
    confidence?: number;
  };
};

// For conversation history
export type ConversationHistoryResponse = Message[];