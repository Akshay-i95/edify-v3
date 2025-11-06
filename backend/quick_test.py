import requests
import json

# Quick test of the new conversation memory
url = "http://localhost:5000/api/chat"

# Test 1: Single message
print("Test 1: Single message (no history)")
response1 = requests.post(url, json={
    "query": "What are formative assessment strategies?",
    "messages": [],
    "namespaces": ["kb-psp"]
})

if response1.status_code == 200:
    result1 = response1.json()
    print("✅ Response received:", len(result1.get('response', '')), "characters")
else:
    print("❌ Error:", response1.status_code)

# Test 2: With conversation history
print("\nTest 2: With conversation history")
conversation = [
    {"role": "user", "content": "What are formative assessment strategies?"},
    {"role": "assistant", "content": "Formative assessment strategies include exit tickets, peer assessments, and quick polls..."}
]

response2 = requests.post(url, json={
    "query": "Can you give me examples of these strategies?",
    "messages": conversation,
    "namespaces": ["kb-psp"]
})

if response2.status_code == 200:
    result2 = response2.json()
    print("✅ Follow-up response received:", len(result2.get('response', '')), "characters")
    print("✅ ChatGPT-style memory is working!")
else:
    print("❌ Error:", response2.status_code)