// src/chat/operations.ts
import { HttpError } from 'wasp/server';
import type {  Message } from './types';

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
      credentials: 'include',
      body: JSON.stringify({ 
        prompt: args.message,
        user_id: context.user.id // Include user ID from context
      }),
    });

    const data = await response.json();

    if (!response.ok || data.error) {
      const errorMessage = data.error || 'AI service error';
      throw new HttpError(response.status, errorMessage);
    }

    return { 
      reply: data.reply,
      provider: data.provider
    };
  } catch (error) {
    console.error('Chat error:', error);
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new HttpError(503, 'Failed to connect to AI service');
    }
    if (error instanceof HttpError) {
      throw error;
    }
    throw new HttpError(500, error instanceof Error ? error.message : 'Unknown error');
  }
};

// Add new operation to fetch conversation history
export const getConversationHistory = async (
  args: {},
  context: any
): Promise<Message[]> => {
  if (!context.user) {
    throw new HttpError(401, 'User not authenticated');
  }

  try {
    const response = await fetch(`http://127.0.0.1:8000/conversation/${context.user.id}`, {
      method: 'GET',
      credentials: 'include',
    });

    const data = await response.json();

    if (!response.ok || data.error) {
      throw new HttpError(response.status, data.error || 'Failed to fetch history');
    }

    return data.messages.map((msg: any) => ({
      id: msg.id.toString(),
      role: msg.role,
      content: msg.content,
      createdAt: msg.created_at
    }));
  } catch (error) {
    console.error('History fetch error:', error);
    throw new HttpError(500, 'Failed to load conversation history');
  }
};