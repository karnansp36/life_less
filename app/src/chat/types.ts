export type ChatResponse = {
  reply: string;
};


export type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
};