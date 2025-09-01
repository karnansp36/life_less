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
  session_id: string;
};

export type WebSocketConnectionArgs = {
  session_id: string;
};

const FASTAPI_WS_URL = process.env.FASTAPI_WS_URL || "ws://127.0.0.1:8000";
const FASTAPI_URL = process.env.FASTAPI_URL || "http://127.0.0.1:8000/api/v1/chat/chat";
const FASTAPI_KEY = process.env.FASTAPI_KEY || "asfasfwhhgj@$^$sdftr342135RGUSL";

// WebSocket connection manager
class WebSocketManager {
  private connections: Map<string, WebSocket> = new Map();
  private messageCallbacks: Map<string, (data: any) => void> = new Map();
  private connectionTimeouts: Map<string, NodeJS.Timeout> = new Map();
  private responseHandlers: Map<string, { resolve: (value: any) => void; reject: (error: any) => void }> = new Map();

  async connect(sessionId: string, userId: number): Promise<WebSocket> {
    if (this.connections.has(sessionId)) {
      const ws = this.connections.get(sessionId)!;
      if (ws.readyState === WebSocket.OPEN) {
        return ws;
      }
      // Clean up closed connection
      this.connections.delete(sessionId);
    }

    return new Promise((resolve, reject) => {
      try {
        // Use the correct WebSocket URL format for your FastAPI
        const wsUrl = `${FASTAPI_WS_URL}/api/v1/chat/ws/chat/${userId}/${sessionId}?api_key=${FASTAPI_KEY}`;
        console.log('Connecting to WebSocket:', wsUrl);
        
        const ws = new WebSocket(wsUrl);

        // Clear any existing timeout
        const existingTimeout = this.connectionTimeouts.get(sessionId);
        if (existingTimeout) {
          clearTimeout(existingTimeout);
        }

        const connectionTimeout = setTimeout(() => {
          if (ws.readyState !== WebSocket.OPEN) {
            ws.close();
            reject(new Error('WebSocket connection timeout'));
          }
        }, 10000); // 10 second timeout

        this.connectionTimeouts.set(sessionId, connectionTimeout);

        ws.onopen = () => {
          console.log('WebSocket connection established for session:', sessionId);
          clearTimeout(connectionTimeout);
          this.connectionTimeouts.delete(sessionId);
          this.connections.set(sessionId, ws);
          resolve(ws);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received:', data);
            
            // Handle different message types
            if (data.type === 'chat_response') {
              const messageId = data.metadata?.message_id || Date.now().toString();
              const handler = this.responseHandlers.get(messageId);
              if (handler) {
                handler.resolve(data);
                this.responseHandlers.delete(messageId);
              }
            } else if (data.type === 'error') {
              // Handle errors
              const handler = this.responseHandlers.get('last');
              if (handler) {
                handler.reject(new HttpError(500, data.message || 'WebSocket error'));
                this.responseHandlers.delete('last');
              }
            }
            
            // General callback
            const callback = this.messageCallbacks.get(sessionId);
            if (callback) {
              callback(data);
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          clearTimeout(connectionTimeout);
          this.connectionTimeouts.delete(sessionId);
          reject(error);
        };

        ws.onclose = (event) => {
          console.log('WebSocket connection closed for session:', sessionId, 'Code:', event.code, 'Reason:', event.reason);
          clearTimeout(connectionTimeout);
          this.connectionTimeouts.delete(sessionId);
          this.connections.delete(sessionId);
          this.messageCallbacks.delete(sessionId);
          // Reject all pending requests
          this.responseHandlers.forEach((handler) => {
            handler.reject(new Error('WebSocket connection closed'));
          });
          this.responseHandlers.clear();
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  sendMessage(sessionId: string, message: any) {
    const ws = this.connections.get(sessionId);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
      return true;
    }
    return false;
  }

  onMessage(sessionId: string, callback: (data: any) => void) {
    this.messageCallbacks.set(sessionId, callback);
  }

  close(sessionId: string) {
    const ws = this.connections.get(sessionId);
    if (ws) {
      ws.close();
      this.connections.delete(sessionId);
      this.messageCallbacks.delete(sessionId);
    }
  }

  isConnected(sessionId: string): boolean {
    const ws = this.connections.get(sessionId);
    return ws !== undefined && ws.readyState === WebSocket.OPEN;
  }

  waitForResponse(messageId: string, timeoutMs: number = 30000): Promise<any> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.responseHandlers.delete(messageId);
        reject(new HttpError(504, 'WebSocket response timeout'));
      }, timeoutMs);

      this.responseHandlers.set(messageId, {
        resolve: (data) => {
          clearTimeout(timeout);
          resolve(data);
        },
        reject: (error) => {
          clearTimeout(timeout);
          reject(error);
        }
      });
    });
  }
}

// Global WebSocket manager
const wsManager = new WebSocketManager();

/**
 * Establish WebSocket connection
 */
export const connectWebSocket = async (args: WebSocketConnectionArgs, context: any) => {
  if (!context.user) {
    throw new HttpError(401, "User not authenticated");
  }

  try {
    await wsManager.connect(args.session_id, parseInt(context.user.id));
    return { success: true, session_id: args.session_id };
  } catch (error: any) {
    console.error('WebSocket connection error:', error);
    throw new HttpError(500, `Failed to connect: ${error.message}`);
  }
};

/**
 * Send message via WebSocket
 */
export const sendWebSocketMessage = async (args: ChatArgs, context: any): Promise<ChatResponse> => {
  if (!context.user) {
    throw new HttpError(401, "User not authenticated");
  }

  const sessionId = args.session_id;
  const messageId = Date.now().toString();
  
  if (!wsManager.isConnected(sessionId)) {
    // Try to reconnect
    try {
      await wsManager.connect(sessionId, parseInt(context.user.id));
    } catch (error) {
      throw new HttpError(503, "WebSocket connection not established");
    }
  }

  // Send message
  const messageSent = wsManager.sendMessage(sessionId, {
    message: args.message,
    type: 'chat',
    conversation_id: args.conversation_id,
    message_id: messageId
  });

  if (!messageSent) {
    throw new HttpError(500, 'Failed to send message via WebSocket');
  }

  // Wait for response
  try {
    const response = await wsManager.waitForResponse(messageId, 30000);
    
    if (response.type === 'chat_response') {
      return {
        reply: response.content,
        conversation_id: response.metadata?.conversation_id,
        agent_used: response.metadata?.agent_coordination?.primary_agent,
        success: true,
        metadata: {
          timestamp: response.timestamp,
          processing_time: response.metadata?.processing_time,
          agents_involved: response.metadata?.agent_coordination?.agents_involved,
        },
        agent_insights: response.metadata?.agent_coordination,
      };
    } else {
      throw new HttpError(500, response.message || 'Unexpected response type');
    }
  } catch (error) {
    throw error;
  }
};

/**
 * Close WebSocket connection
 */
export const closeWebSocket = async (args: WebSocketConnectionArgs, context: any) => {
  if (!context.user) {
    throw new HttpError(401, "User not authenticated");
  }

  wsManager.close(args.session_id);
  return { success: true, session_id: args.session_id };
};

// Fallback to REST API if WebSocket fails
export const chatWithAI = async (args: ChatArgs, context: any): Promise<ChatResponse> => {
  if (!context.user) {
    throw new HttpError(401, "User not authenticated");
  }

  // First try WebSocket
  try {
    console.log('Attempting WebSocket connection for chat...');
    const result = await sendWebSocketMessage(args, context);
    console.log('WebSocket chat successful');
    return result;
  } catch (wsError) {
    console.warn('WebSocket failed, falling back to REST API:', wsError);
    
    // Fallback to REST API
    try {
      console.log('Using REST API fallback...');
      
      const payload = {
        message: args.message,
        user_id: parseInt(context.user.id),
        session_id: args.session_id,
        conversation_id: args.conversation_id || null,
      };

      console.log('REST API payload:', payload);

      const response = await fetch(FASTAPI_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": FASTAPI_KEY,
        },
        body: JSON.stringify(payload),
      });

      console.log('REST API response status:', response.status);

      if (!response.ok) {
        let errorMessage = `AI service error: ${response.status} ${response.statusText}`;
        try {
          const errorData = await response.text();
          console.log('REST API error response:', errorData);
          try {
            const parsedError = JSON.parse(errorData);
            errorMessage = parsedError.detail || parsedError.error || errorMessage;
          } catch {
            errorMessage = errorData || errorMessage;
          }
        } catch (e) {
          console.log('Could not read error response body:', e);
        }
        throw new HttpError(response.status, errorMessage);
      }

      const data = await response.json();
      console.log('REST API success response:', data);

      return {
        reply: data.response,
        conversation_id: data.conversation_id,
        agent_used: data.agent_used || data.agent_insights?.primary_agent,
        success: true,
        metadata: data.metadata,
        agent_insights: data.agent_insights,
      };
    } catch (restError: any) {
      console.error('REST API also failed:', restError);
      if (restError instanceof HttpError) {
        throw restError;
      }
      throw new HttpError(500, restError.message || "Both WebSocket and REST API failed");
    }
  }
};

/**
 * Check WebSocket connection status
 */
export const checkWebSocketStatus = async (args: WebSocketConnectionArgs, context: any) => {
  if (!context.user) {
    throw new HttpError(401, "User not authenticated");
  }

  return {
    connected: wsManager.isConnected(args.session_id),
    session_id: args.session_id,
    user_id: context.user.id
  };
};