// src/chat/operations.ts
import { HttpError } from "wasp/server";
// import type {  Message } from './types';

export type ChatResponse = {
  reply: string; // keep reply for frontend
  provider?: string;
  conversation_id?: number;
  agent_used?: string;
  success?: boolean;
  metadata?: {
    memories_used?: number;
    processing_time?: number;
  };
};
export type ChatArgs = {
  message: string;
  conversation_id?: number;
};

export const chatWithAI = async (
  args: ChatArgs,
  context: any
): Promise<ChatResponse> => {
  if (!context.user) {
    throw new HttpError(401, "User not authenticated");
  }

  try {
    const response = await fetch("http://127.0.0.1:8000/api/chat/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify({
        message: args.message,
        conversation_id: args.conversation_id
          ? String(args.conversation_id)
          : null, // must be string or null
        user_id: context.user.id.toString(),
        metadata: {},
      }),
    });

    const data = await response.json();

    if (!response.ok || data.error) {
      throw new HttpError(response.status, data.error || "AI service error");
    }

    // ✅ map response -> frontend contract
    return {
      reply: data.response, // map response -> reply
      provider: data.agent_used, // optional alias
      conversation_id: data.conversation_id,
      agent_used: data.agent_used,
      success: data.success,
      metadata: data.metadata,
    } as const;
  } catch (error) {
    console.error("Chat error:", error);
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new HttpError(503, "Failed to connect to AI service");
    }
    if (error instanceof HttpError) throw error;
    throw new HttpError(
      500,
      error instanceof Error ? error.message : "Unknown error"
    );
  }
};
