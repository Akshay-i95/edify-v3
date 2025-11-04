# 🏷️ Edify AI Assistant - Namespace Integration Guide

## Overview
The Edify AI Assistant now supports **namespace-based search** to target specific educational domains. This allows filtering search results to K-12, Preschool, or Administrative content.

---

## 🔗 URL Query String Integration

### Basic Usage
Add the `namespaces` parameter to the chatbot URL:

```
https://edify-ai-assistant.i95-dev.com?namespaces=<namespace1,namespace2>
```

### Available Namespaces
| Namespace | Description | Content Type |
|-----------|-------------|--------------|
| `k12` | K-12 Education | Academic curriculum, assessments, K-12 policies |
| `preschool` | Early Childhood | Preschool activities, early learning, child development |
| `administrative` | School Administration | Forms, procedures, administrative policies |

### URL Examples

#### Single Namespace
```bash
# K-12 content only
https://edify-ai-assistant.i95-dev.com?namespaces=k12

# Preschool content only
https://edify-ai-assistant.i95-dev.com?namespaces=preschool

# Administrative content only
https://edify-ai-assistant.i95-dev.com?namespaces=administrative
```

#### Multiple Namespaces
```bash
# K-12 + Preschool content
https://edify-ai-assistant.i95-dev.com?namespaces=k12,preschool

# All educational content
https://edify-ai-assistant.i95-dev.com?namespaces=k12,preschool,administrative
```

#### Auto-Detection (Default)
```bash
# No namespaces specified - AI auto-detects best namespace
https://edify-ai-assistant.i95-dev.com
```

---

## 🎯 Visual Indicators

When namespaces are specified, the chatbot header displays active namespace badges:

- **K-12** → Blue badge labeled "K-12"
- **Preschool** → Blue badge labeled "Preschool" 
- **Administrative** → Blue badge labeled "Admin"

**No badges shown** = Auto-detection mode (backend determines best namespace)

---

## 📡 API Integration Details

### Frontend → Backend Data Flow

#### 1. URL Parameter Extraction
```javascript
// Frontend extracts namespaces from URL
const searchParams = useSearchParams();
const namespacesParam = searchParams.get('namespaces');
const namespaces = namespacesParam?.split(',').map(ns => ns.trim());
```

#### 2. API Request Format
```javascript
// POST /api/chat?namespaces=k12,preschool
{
  "message": "What are assessment strategies?",
  "namespaces": ["k12", "preschool"],
  "conversation_history": []
}
```

#### 3. Backend Processing
```python
# Flask receives and processes namespaces
namespaces = data.get('namespaces', None)
response_data = chatbot.process_query(
    user_query=user_message,
    namespaces=namespaces  # Passed to search engine
)
```

### API Payload Structure

#### Request Payload
```json
{
  "message": "User's question here",
  "namespaces": ["k12", "preschool"],
  "conversation_history": [
    {
      "role": "user", 
      "content": "Previous question"
    },
    {
      "role": "assistant",
      "content": "Previous response"
    }
  ]
}
```

#### Response Payload
```json
{
  "response": "AI assistant response",
  "reasoning": "AI reasoning process",
  "sources": [
    {
      "title": "Document Title",
      "filename": "document.pdf",
      "download_url": "https://...",
      "source_namespace": "k12"
    }
  ],
  "metadata": {
    "confidence": 0.85,
    "chunks_used": 12,
    "processing_time": 2.5,
    "namespaces_searched": ["k12", "preschool"]
  }
}
```

---

## 🛠️ Integration Examples

### JavaScript/React Integration
```javascript
// Function to open chatbot with specific namespace
function openChatbot(namespaces = null) {
  const baseUrl = 'https://edify-ai-assistant.i95-dev.com';
  const url = namespaces 
    ? `${baseUrl}?namespaces=${namespaces.join(',')}` 
    : baseUrl;
    
  window.open(url, '_blank');
}

// Usage examples
openChatbot(['k12']);                    // K-12 only
openChatbot(['k12', 'preschool']);       // K-12 + Preschool
openChatbot(['administrative']);         // Admin only
openChatbot();                          // Auto-detect
```

### Direct API Calls
```javascript
// Direct API integration (if embedding chatbot)
async function queryChatbot(message, namespaces = null) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: message,
      namespaces: namespaces,
      conversation_history: []
    })
  });
  
  return await response.json();
}

// Usage
const result = await queryChatbot(
  "What are K-12 assessment methods?", 
  ["k12"]
);
```

---

## 🎯 Use Case Scenarios

### 1. K-12 Teacher Dashboard
```javascript
// Link from K-12 section
const k12ChatUrl = "https://edify-ai-assistant.i95-dev.com?namespaces=k12";
```

### 2. Preschool Resources Page
```javascript
// Link from preschool section
const preschoolChatUrl = "https://edify-ai-assistant.i95-dev.com?namespaces=preschool";
```

### 3. Administrative Portal
```javascript
// Link from admin dashboard
const adminChatUrl = "https://edify-ai-assistant.i95-dev.com?namespaces=administrative";
```

### 4. Multi-Domain Search
```javascript
// Link for comprehensive search
const comprehensiveUrl = "https://edify-ai-assistant.i95-dev.com?namespaces=k12,preschool,administrative";
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. No Namespace Badges Showing
- **Cause**: No `namespaces` parameter in URL
- **Solution**: Add `?namespaces=k12` to URL or use auto-detection

#### 2. Wrong Content Returned
- **Cause**: Incorrect namespace specified
- **Solution**: Verify namespace spelling: `k12`, `preschool`, `administrative`

#### 3. Mixed Results When Single Namespace Expected
- **Cause**: Multiple namespaces in URL
- **Solution**: Use single namespace: `?namespaces=k12`

### Validation Rules
- Namespace values are case-insensitive
- Invalid namespaces are filtered out
- Empty namespace parameter defaults to auto-detection
- Comma-separated values: `k12,preschool` ✅
- Spaces are automatically trimmed: `k12, preschool` ✅

---

## 📊 Performance Impact

### Search Performance by Namespace
| Configuration | Search Time | Result Quality | Use Case |
|---------------|-------------|---------------|-----------|
| Single namespace | ~1-2s | High precision | Targeted queries |
| Multiple namespaces | ~2-4s | High recall | Comprehensive search |
| Auto-detection | ~2-3s | Balanced | General queries |

### Recommendation
- Use **single namespace** for domain-specific queries
- Use **multiple namespaces** for cross-domain research
- Use **auto-detection** for general help and mixed queries

---

## 🔧 Technical Implementation Notes

### Backend Search Flow
1. **Namespace Validation**: Filter valid namespaces
2. **Multi-Namespace Search**: Query each namespace in Pinecone
3. **Result Aggregation**: Combine and rank results
4. **Source Attribution**: Tag results with source namespace

### Frontend URL Handling
1. **Parameter Extraction**: Parse URL query string
2. **Validation**: Filter valid namespaces
3. **UI Updates**: Show namespace badges
4. **API Integration**: Pass to backend via query parameter

---

## 📞 Support & Contact

For technical integration support or questions about namespace implementation:

- **Development Team**: Edify AI Assistant Team
- **Documentation**: This guide
- **Test Environment**: `http://localhost:3000?namespaces=k12`
- **Production URL**: `https://edify-ai-assistant.i95-dev.com?namespaces=k12`

---

**Last Updated**: October 15, 2025  
**Version**: 1.0  
**Status**: Production Ready ✅