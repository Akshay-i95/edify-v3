# Chatbot UI & Streaming Integration – Documentation

## Overview

This project uses the `@assistant-ui/react` library with Next.js (App Router) to build a modern, streaming AI chat interface. The backend is a Python service, and the Next.js API route (`/api/chat`) acts as a proxy, adapting backend responses to the format required by assistant-ui.

---

## UI Approach

### Frontend:
- Built with **Next.js** and **React**
- Uses `@assistant-ui/react` and `@assistant-ui/react-ai-sdk` for chat UI and streaming
- The `useChatRuntime` hook is configured to call `/api/chat` for chat messages
- The UI expects streaming responses in the AI SDK "data stream" format
- **Structured Response Display**: Shows reasoning, main response, and source information in collapsible sections

### Backend Proxy (route.ts):
- Receives chat messages from the UI
- Forwards them to the Python backend, manages session logic
- Streams the backend's response to the UI in the required format
- **Enhanced Response Processing**: Handles reasoning, sources, confidence scores, and metadata

---

## Response Structure

The backend now provides rich, structured responses with:

### 1. **Reasoning Section** (Collapsible)
- AI's thought process and decision-making steps
- Displayed first in a collapsible `<details>` element
- Prefixed with 🤔 **Reasoning:** header

### 2. **Main Response** 
- The core AI answer to the user's question
- Streamed word-by-word for typing effect
- Prefixed with 💬 **Response:** header

### 3. **Sources & References** (Collapsible)
- Document sources with relevance scores
- PDF download links for referenced documents
- Page numbers and content snippets
- Confidence score for the overall response
- Prefixed with 📚 **Sources & References:** header

---

## Streaming Protocol

### Format:
```
Each chunk: 0:"text content"\n
End of stream: d:{"finishReason":"stop","usage":{"promptTokens":0,"completionTokens":0}}\n
Error: d:{"finishReason":"error", ...}\n
```

### Structured Streaming:
1. **Reasoning Section**: Streamed first with collapsible `<details>` HTML
2. **Main Response**: Core AI answer streamed word-by-word  
3. **Sources Section**: Document references with download links in collapsible format

### Why:
- This matches the AI SDK/assistant-ui protocol, which expects newline-delimited, prefixed JSON/text chunks
- The UI parses and displays each chunk as it arrives, enabling real-time streaming
- HTML elements (`<details>`, `<summary>`) provide collapsible sections for better UX

---

## Challenge & Solution

### Problem:
- The UI was not displaying streamed responses, or showed `[object Object]` due to incorrect streaming format
- Multiple attempts (SSE, JSON objects, OpenAI-style) failed due to subtle protocol mismatches

### Solution:
Carefully matched the streaming format to the AI SDK/assistant-ui requirements:
- Used `0:"..."` for text chunks (not JSON objects)
- Used `d:{...}` for finish/error signals
- Streamed word-by-word for a smooth typing effect
- Ensured proper escaping and chunking
- **Added structured content streaming** with reasoning and sources sections

### Result:
- The UI now displays streamed responses in real time, with no parsing errors
- **Enhanced UX** with collapsible reasoning and source sections
- Rich metadata display including confidence scores and PDF downloads

---

## Key Files

- `frontend/chatbot/app/assistant.tsx` – UI setup with `useChatRuntime`
- `frontend/chatbot/app/api/chat/route.ts` – API route handling streaming and structured content
- `frontend/chatbot/components/assistant-ui/markdown-text.tsx` – Enhanced markdown renderer with HTML support

---

## Summary

This integration demonstrates how to bridge a custom backend with a modern streaming chat UI by carefully matching the expected streaming protocol. The enhanced version now includes:

1. **Structured Content Streaming**: Reasoning → Response → Sources
2. **Collapsible UI Elements**: Better information organization
3. **Rich Metadata Display**: Confidence scores, document sources, PDF downloads
4. **Smooth Streaming Experience**: Word-by-word typing effects

**Key Takeaway:** The success of streaming integration depends on precise protocol matching and thoughtful UX design for complex, multi-part responses.

