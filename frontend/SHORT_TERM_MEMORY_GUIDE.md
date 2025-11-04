# Short-Term Memory & Follow-up Conversations Guide

A comprehensive guide for implementing conversational memory in AI applications using modern frameworks.

## 🎯 Overview

This guide demonstrates how to implement short-term memory for AI chat applications, enabling natural follow-up conversations where the AI remembers previous context within a session.

## 🏗️ Architecture Pattern

### Core Components

```
Frontend (React) → API Route → AI Provider (Groq/OpenAI/Anthropic)
     ↑                ↑              ↑
   State Mgmt    Message Array   Context Window
```

### Message Flow
1. **User Input** → Stored in frontend state
2. **Full History** → Sent to API on each request
3. **AI Response** → Added to conversation history
4. **Context Maintained** → Available for follow-ups

## 🔧 Implementation Patterns

### 1. API Route Pattern (Next.js)

```typescript
// app/api/chat/route.ts
export async function POST(req: Request) {
  const { messages, system, tools } = await req.json();

  const result = streamText({
    model: groq("llama-3.1-8b-instant"),
    messages, // 👈 Full conversation history
    system,
    tools,
    maxSteps: 20,
  });

  return result.toDataStreamResponse();
}
```

**Key Points:**
- `messages` array contains full conversation history
- Each request includes all previous messages
- AI provider receives complete context

### 2. Frontend State Management

#### Option A: Assistant-UI Framework (Recommended)

```tsx
// app/assistant.tsx
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";

export const Assistant = () => {
  const runtime = useChatRuntime({
    api: "/api/chat", // Points to your API route
    // Automatically manages message history
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <Thread />
    </AssistantRuntimeProvider>
  );
};
```

**Benefits:**
- ✅ Automatic message history management
- ✅ Built-in UI components
- ✅ Tool calling support
- ✅ Streaming responses

#### Option B: Custom Hook Pattern

```tsx
// hooks/useChat.ts
import { useState } from 'react';

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
};

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (content: string) => {
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, userMessage].map(m => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });

      const aiResponse = await response.text();
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: aiResponse,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    messages,
    sendMessage,
    isLoading,
    clearHistory: () => setMessages([]),
  };
};
```

### 3. Memory Patterns & Examples

#### Basic Follow-up Pattern
```
User: "Show me orders from last month"
AI: [Shows orders] "Here are 45 orders from last month..."

User: "Filter those by pending status"
AI: [Filters previous results] "Here are 12 pending orders from that list..."

User: "What's the total value?"
AI: [Calculates from filtered results] "The total value is $15,420..."
```

#### Context Referencing
```typescript
// Example message history structure
const messages = [
  { role: "user", content: "Show me orders from last month" },
  { role: "assistant", content: "Here are the orders...", tools: [...] },
  { role: "user", content: "Filter those by pending status" }, // 👈 "those" refers to previous
  { role: "assistant", content: "Here are the filtered results..." },
];
```

## 🛠️ Technical Implementation

### Required Dependencies

```json
{
  "dependencies": {
    "@assistant-ui/react": "^0.10.2",
    "@assistant-ui/react-ai-sdk": "^0.10.3", 
    "ai": "^4.3.9",
    "@ai-sdk/groq": "^1.2.9"
  }
}
```

### Environment Setup

```bash
# .env.local
GROQ_API_KEY=your_groq_api_key
# or
OPENAI_API_KEY=your_openai_key
# or  
ANTHROPIC_API_KEY=your_anthropic_key
```

### Project Structure
```
src/
├── app/
│   ├── api/chat/route.ts      # API endpoint
│   ├── assistant.tsx          # Main chat component
│   └── page.tsx              # App entry
├── components/
│   ├── ui/                   # UI components
│   └── chat/                 # Chat-specific components
└── hooks/
    └── useChat.ts           # Custom chat hook (if not using assistant-ui)
```

## 💡 Best Practices

### 1. Message Optimization
```typescript
// Limit message history to prevent token overflow
const limitMessages = (messages: Message[], maxMessages = 20) => {
  if (messages.length <= maxMessages) return messages;
  
  // Keep system message + recent messages
  const systemMessage = messages.find(m => m.role === 'system');
  const recentMessages = messages.slice(-maxMessages + 1);
  
  return systemMessage ? [systemMessage, ...recentMessages] : recentMessages;
};
```

### 2. Context Compression
```typescript
// Summarize old context when approaching limits
const compressOldContext = async (messages: Message[]) => {
  if (messages.length > 30) {
    const oldMessages = messages.slice(0, -10);
    const summary = await summarizeConversation(oldMessages);
    
    return [
      { role: 'system', content: `Previous context: ${summary}` },
      ...messages.slice(-10)
    ];
  }
  return messages;
};
```

### 3. Tool State Management
```typescript
// Maintain tool results in conversation context
const handleToolCall = async (toolName: string, args: any) => {
  const result = await executeToolCall(toolName, args);
  
  // Include tool result in message history
  return {
    role: 'assistant',
    content: '', 
    tool_calls: [{ name: toolName, arguments: args }],
    tool_results: [{ content: JSON.stringify(result) }]
  };
};
```

## 🔄 Memory Persistence Options

### Option 1: Session-Only (Current Implementation)
- ✅ Simple to implement
- ✅ No database required
- ❌ Lost on page refresh
- ❌ No cross-device sync

### Option 2: Local Storage
```typescript
// Save to localStorage
const saveConversation = (messages: Message[]) => {
  localStorage.setItem('chat-history', JSON.stringify(messages));
};

// Load from localStorage
const loadConversation = (): Message[] => {
  const saved = localStorage.getItem('chat-history');
  return saved ? JSON.parse(saved) : [];
};
```

### Option 3: Database Persistence
```typescript
// Save to database (example with Prisma)
const saveToDatabase = async (sessionId: string, messages: Message[]) => {
  await prisma.chatSession.upsert({
    where: { id: sessionId },
    create: { id: sessionId, messages: JSON.stringify(messages) },
    update: { messages: JSON.stringify(messages) },
  });
};
```

### Option 4: Cloud Assistant-UI
```typescript
// Using Assistant-UI cloud service
const cloud = new AssistantCloud({
  baseUrl: process.env.NEXT_PUBLIC_ASSISTANT_BASE_URL!,
  anonymous: true, // or implement user auth
});

const runtime = useChatRuntime({
  api: "/api/chat",
  cloud, // Enables persistent conversations
});
```

## 🎨 UI Patterns

### Conversation Indicators
```tsx
// Show conversation state
const ConversationStatus = ({ messages }: { messages: Message[] }) => {
  const contextLength = messages.length;
  
  return (
    <div className="text-sm text-gray-500">
      {contextLength > 0 && (
        <span>💬 {contextLength} messages in context</span>
      )}
    </div>
  );
};
```

### Clear Context Button
```tsx
const ClearContextButton = ({ onClear }: { onClear: () => void }) => (
  <button 
    onClick={onClear}
    className="text-xs text-gray-400 hover:text-gray-600"
  >
    🗑️ Clear conversation
  </button>
);
```

## 🧪 Testing Follow-up Scenarios

### Test Cases
1. **Basic Reference**: "Show orders" → "Filter those by status"
2. **Multi-step**: "Get customers" → "Show orders for John" → "Refund the last one"
3. **Context Switch**: "Product data" → "Now customer data" → "Combine insights"
4. **Tool Chaining**: "Search products" → "Update the first one" → "Show the changes"

### Example Test Flow
```typescript
// Test conversation memory
const testConversation = async () => {
  // Step 1: Initial request
  await sendMessage("Show me all products");
  
  // Step 2: Follow-up referencing previous
  await sendMessage("Filter those by price over $100");
  
  // Step 3: Action on filtered results  
  await sendMessage("Update the first product's description");
  
  // Verify context is maintained throughout
  expect(conversation.length).toBe(6); // 3 user + 3 assistant messages
};
```

## 🚀 Quick Start Template

```typescript
// Minimal implementation
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";
import { Thread, AssistantRuntimeProvider } from "@assistant-ui/react";

export default function ChatApp() {
  const runtime = useChatRuntime({
    api: "/api/chat",
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="h-screen flex flex-col">
        <header>
          <h1>AI Assistant with Memory</h1>
        </header>
        <main className="flex-1">
          <Thread />
        </main>
      </div>
    </AssistantRuntimeProvider>
  );
}
```

## 📚 Additional Resources

- [Assistant-UI Documentation](https://assistant-ui.com)
- [AI SDK Documentation](https://ai-sdk.dev)
- [Groq Models](https://console.groq.com/docs/models)
- [OpenAI Chat Completions](https://platform.openai.com/docs/guides/chat)

---

## 🏷️ Tags
`#ai-chat` `#conversation-memory` `#follow-up` `#context-management` `#assistant-ui` `#next.js` `#react`

*Last updated: September 2025*