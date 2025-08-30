// src/chat/operations.ts
import { HttpError } from "wasp/server";

export type ChatResponse = {
  reply: string;
  conversation_id?: number;
  agent_used?: string;
  success: boolean;
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
};

export type ChatArgs = {
  message: string;
  conversation_id?: number;
  session_id: string; // required for backend
};

const FASTAPI_URL = process.env.FASTAPI_URL || "http://127.0.0.1:8000/api/v1/chat/chat";
const FASTAPI_KEY = process.env.FASTAPI_KEY || "asfasfwhhgj@$^$sdftr342135RGUSL";

/**
 * Send a user message to FastAPI backend and return AI response
 */
export const chatWithAI = async (
  args: ChatArgs,
  context: any
): Promise<ChatResponse> => {
  if (!context.user) {
    throw new HttpError(401, "User not authenticated");
  }

  try {
    // ✅ FIX: Match the FastAPI ChatRequest schema
    const payload = {
      message: args.message,
      user_id: parseInt(context.user.id), // Ensure this is a number
      session_id: args.session_id,
      conversation_id: args.conversation_id || null, // Send null instead of undefined
    };

    // Debug logging
    console.log('=== DEBUG: Sending to FastAPI ===');
    console.log('URL:', FASTAPI_URL);
    console.log('Payload:', JSON.stringify(payload, null, 2));
    console.log('User ID type:', typeof payload.user_id, 'Value:', payload.user_id);
    console.log('Session ID:', payload.session_id);
    console.log('Conversation ID:', payload.conversation_id);
    console.log('API Key present:', !!FASTAPI_KEY);
    console.log('==============================');

    const response = await fetch(FASTAPI_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": FASTAPI_KEY,
      },
      body: JSON.stringify(payload),
    });

    // Debug response status
    console.log('=== DEBUG: Response from FastAPI ===');
    console.log('Status:', response.status, response.statusText);
    console.log('Headers:', Object.fromEntries([...response.headers]));

    if (!response.ok) {
      let errorMessage = `AI service error: ${response.status} ${response.statusText}`;
      let errorDetails: any = null;
      
      // Try to get detailed error from response body
      try {
        const errorData = await response.text();
        console.log('Error response body:', errorData);
        try {
          const parsedError = JSON.parse(errorData);
          errorMessage = parsedError.detail || parsedError.error || errorMessage;
          errorDetails = parsedError;
        } catch (parseError) {
          errorMessage = errorData || errorMessage;
        }
      } catch (e) {
        console.log('Could not read error response body:', e);
      }
      
      console.log('Full error:', { errorMessage, errorDetails });
      console.log('==============================');
      
      throw new HttpError(response.status, errorMessage);
    }

    const data = await response.json();
    console.log('=== DEBUG: Success response ===');
    console.log('Response data:', JSON.stringify(data, null, 2));
    console.log('Response type:', typeof data);
    console.log('Has response field:', 'response' in data);
    console.log('Has conversation_id:', 'conversation_id' in data);
    console.log('==============================');

    return {
      reply: data.response,
      conversation_id: data.conversation_id,
      agent_used: data.agent_used || data.agent_insights?.primary_agent,
      success: true,
      metadata: data.metadata,
      agent_insights: data.agent_insights,
    };
  } catch (error: any) {
    console.error('=== DEBUG: ChatWithAI error ===');
    console.error('Error name:', error.name);
    console.error('Error message:', error.message);
    console.error('Error stack:', error.stack);
    
    if (error instanceof TypeError && error.message.includes("fetch")) {
      console.error('Network error - Failed to connect to AI service');
      throw new HttpError(503, "Failed to connect to AI service");
    }
    if (error instanceof HttpError) {
      console.error('HTTP error thrown');
      throw error;
    }

    console.error('Unknown error type');
    throw new HttpError(500, error.message || "Unknown backend error");
  }
};