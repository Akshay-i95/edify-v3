# API Ingestion Guide - Postman Usage

## 🚀 Direct API Access via Postman

### Endpoint Details

**URL:** `http://localhost:5000/api/kb/ingest`  
**Method:** `POST`  
**Content-Type:** `application/json`

---

## 📋 Request Format

### Headers
```
Content-Type: application/json
```

### Body (JSON)
```json
{
  "fileNames": [
    "kb/12/grade1/document1.pdf",
    "kb/12/grade2/document2.pdf",
    "kb/12/common/guide.pdf"
  ],
  "container": "edifydocumentcontainer"
}
```

---

## 🎯 Example Requests

### Example 1: Ingest Single File
```json
{
  "fileNames": ["kb/12/grade1/mathematics.pdf"],
  "container": "edifydocumentcontainer"
}
```

### Example 2: Ingest Multiple Files
```json
{
  "fileNames": [
    "kb/12/grade1/mathematics.pdf",
    "kb/12/grade1/science.pdf",
    "kb/12/grade1/english.pdf",
    "kb/12/grade2/history.pdf"
  ],
  "container": "edifydocumentcontainer"
}
```

### Example 3: Ingest All Files from a Grade
```json
{
  "fileNames": [
    "kb/12/grade1/math_chapter1.pdf",
    "kb/12/grade1/math_chapter2.pdf",
    "kb/12/grade1/science_unit1.pdf",
    "kb/12/grade1/science_unit2.pdf",
    "kb/12/grade1/english_lesson1.pdf"
  ],
  "container": "edifydocumentcontainer"
}
```

---

## ✅ Response Format

### Success Response (200)
```json
{
  "success": true,
  "processed": 3,
  "results": [
    {
      "fileName": "kb/12/grade1/document1.pdf",
      "success": true,
      "chunks": 15,
      "namespace": "kb-psp"
    },
    {
      "fileName": "kb/12/grade2/document2.pdf",
      "success": true,
      "chunks": 22,
      "namespace": "kb-psp"
    },
    {
      "fileName": "kb/12/common/guide.pdf",
      "success": false,
      "error": "No text extracted from file"
    }
  ]
}
```

### Error Response (400/500)
```json
{
  "success": false,
  "error": "fileNames array is required"
}
```

---

## 🔧 Postman Setup Steps

### 1. Create New Request
- Click **New** → **Request**
- Name: "Ingest Files to Pinecone"
- Save to a collection

### 2. Configure Request
- **Method:** POST
- **URL:** `http://localhost:5000/api/kb/ingest`

### 3. Set Headers
- Click **Headers** tab
- Add: `Content-Type: application/json`

### 4. Set Body
- Click **Body** tab
- Select **raw**
- Select **JSON** from dropdown
- Paste JSON payload:
```json
{
  "fileNames": [
    "kb/12/grade1/test.pdf"
  ],
  "container": "edifydocumentcontainer"
}
```

### 5. Send Request
- Click **Send** button
- Wait for response (may take 30-60 seconds per file)

---

## 📊 Other Useful Endpoints

### Get Pinecone Statistics
**GET** `http://localhost:5000/api/kb/stats`

Response:
```json
{
  "success": true,
  "stats": {
    "total_vectors": 1543,
    "dimension": 384,
    "namespaces": {
      "edify-knowledge": 1543
    },
    "index_fullness": 0.0001
  }
}
```

### List Azure Files
**GET** `http://localhost:5000/api/kb/list?container=edifydocumentcontainer&prefix=kb/12/grade1/`

Response:
```json
{
  "success": true,
  "container": "edifydocumentcontainer",
  "prefix": "kb/12/grade1/",
  "count": 25,
  "files": [
    {
      "name": "kb/12/grade1/math.pdf",
      "size": 2458392,
      "last_modified": "2025-12-20T10:30:00Z"
    }
  ]
}
```

### Delete Files from Pinecone
**POST** `http://localhost:5000/api/kb/delete`

Body:
```json
{
  "fileNames": ["math.pdf", "science.pdf"],
  "namespace": "edify-knowledge"
}
```

---

## 🎯 Common Use Cases

### Use Case 1: Get List of Files First
```bash
# Step 1: List files
GET http://localhost:5000/api/kb/list?prefix=kb/12/grade1/

# Step 2: Copy file names from response
# Step 3: Use in ingest request
POST http://localhost:5000/api/kb/ingest
{
  "fileNames": ["kb/12/grade1/file1.pdf", "kb/12/grade1/file2.pdf"]
}
```

### Use Case 2: Batch Processing
```json
{
  "fileNames": [
    "kb/12/grade1/doc1.pdf",
    "kb/12/grade1/doc2.pdf",
    "kb/12/grade1/doc3.pdf",
    "kb/12/grade1/doc4.pdf",
    "kb/12/grade1/doc5.pdf"
  ],
  "container": "edifydocumentcontainer"
}
```

### Use Case 3: Re-ingest After Update
```json
{
  "fileNames": ["kb/12/grade1/updated_curriculum.pdf"],
  "container": "edifydocumentcontainer"
}
```
The API automatically deletes old vectors before re-ingesting.

---

## ⚡ Tips

1. **Batch Size:** Process 5-10 files at a time for best results
2. **Timeout:** Set Postman timeout to 5 minutes for large batches
3. **Container:** Default is "edifydocumentcontainer" (can be omitted)
4. **File Paths:** Must include full path from container root
5. **Progress:** Check terminal where `app.py` is running for detailed logs

---

## 🐛 Troubleshooting

### Error: "fileNames array is required"
- Make sure body is valid JSON
- Ensure `fileNames` is an array, not a string

### Error: "Failed to download PDF"
- Check file path is correct
- Verify file exists in Azure container
- Check Azure connection string is valid

### Timeout Error
- Reduce batch size
- Increase Postman timeout setting
- Check backend logs for actual error

### No Text Extracted
- File might be scanned (OCR will be attempted)
- File might be corrupted
- File might not be a valid PDF

---

## 📝 Sample Postman Collection

Save this as `edify-ingestion.postman_collection.json`:

```json
{
  "info": {
    "name": "Edify KB Ingestion",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Ingest Files",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"fileNames\": [\n    \"kb/12/grade1/test.pdf\"\n  ],\n  \"container\": \"edifydocumentcontainer\"\n}"
        },
        "url": {
          "raw": "http://localhost:5000/api/kb/ingest",
          "protocol": "http",
          "host": ["localhost"],
          "port": "5000",
          "path": ["api", "kb", "ingest"]
        }
      }
    },
    {
      "name": "Get Stats",
      "request": {
        "method": "GET",
        "url": {
          "raw": "http://localhost:5000/api/kb/stats",
          "protocol": "http",
          "host": ["localhost"],
          "port": "5000",
          "path": ["api", "kb", "stats"]
        }
      }
    },
    {
      "name": "List Files",
      "request": {
        "method": "GET",
        "url": {
          "raw": "http://localhost:5000/api/kb/list?container=edifydocumentcontainer&prefix=kb/12/",
          "protocol": "http",
          "host": ["localhost"],
          "port": "5000",
          "path": ["api", "kb", "list"],
          "query": [
            {
              "key": "container",
              "value": "edifydocumentcontainer"
            },
            {
              "key": "prefix",
              "value": "kb/12/"
            }
          ]
        }
      }
    },
    {
      "name": "Delete Files",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"fileNames\": [\"test.pdf\"],\n  \"namespace\": \"edify-knowledge\"\n}"
        },
        "url": {
          "raw": "http://localhost:5000/api/kb/delete",
          "protocol": "http",
          "host": ["localhost"],
          "port": "5000",
          "path": ["api", "kb", "delete"]
        }
      }
    }
  ]
}
```

Import this into Postman using **Import** → **Paste Raw Text**
