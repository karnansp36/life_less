// src/chat/operations.ts
import { HttpError } from 'wasp/server';

export type ChatResponse = {
  reply: string;
  provider?: string;
};

export const chatWithAI = async (
  args: { message: string },
  context: any
): Promise<ChatResponse> => {
  if (!context.user) {
    throw new HttpError(401, 'User not authenticated');
  }

  try {
    const response = await fetch('http://127.0.0.1:8000/chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',  // Important for CORS with credentials
      body: JSON.stringify({ prompt: args.message }),
    });

    const data = await response.json();

    // Check for error response from FastAPI
    if (!response.ok || data.error) {
      const errorMessage = data.error || 'AI service error';
      throw new HttpError(response.status, errorMessage);
    }

    // Handle response
    const reply = data.reply;
    if (typeof reply !== 'string') {
      throw new Error('Invalid response format from API');
    }

    return { 
      reply,
      provider: data.provider // Include provider info if needed
    };
  } catch (error) {
    console.error('Chat error:', error);
    
    // Provide more specific error messages
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new HttpError(503, 'Failed to connect to AI service');
    }
    if (error instanceof HttpError) {
      throw error;
    }
    throw new HttpError(500, error instanceof Error ? error.message : 'Unknown error');
  }
};