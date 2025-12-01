"""
Flask Backend for AI Chatbot with Assistant UI
Provides REST API endpoints for chat functionality, history management, and file operations
"""

import os
import sys
import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify, send_file, redirect
from flask_cors import CORS
import traceback

# Fix Unicode encoding issues on Windows
if sys.platform == "win32":
    import codecs
    try:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
    except:
        pass  # Ignore if already configured

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Message optimization functions for short-term memory
def limit_messages(messages: List[Dict], max_messages: int = 20) -> List[Dict]:
    """Limit message history to prevent token overflow"""
    if len(messages) <= max_messages:
        return messages
    
    # Keep system message + recent messages
    system_message = next((msg for msg in messages if msg.get('role') == 'system'), None)
    recent_messages = messages[-max_messages + 1:] if system_message else messages[-max_messages:]
    
    return [system_message] + recent_messages if system_message else recent_messages

def compress_old_context(messages: List[Dict], max_length: int = 30) -> List[Dict]:
    """Compress old context when approaching limits by summarizing early messages"""
    if len(messages) <= max_length:
        return messages
    
    # Keep system message, summarize middle, keep recent
    system_message = next((msg for msg in messages if msg.get('role') == 'system'), None)
    recent_messages = messages[-10:]  # Keep last 10 messages
    
    # Create summary of old messages (this could be enhanced with LLM summarization)
    old_messages = messages[1:-10] if system_message else messages[:-10]
    if old_messages:
        summary_content = f"[Previous conversation summary: {len(old_messages)} messages discussing various topics]"
        summary_message = {"role": "system", "content": summary_content}
        
        base_messages = [system_message] if system_message else []
        return base_messages + [summary_message] + recent_messages
    
    return messages

# CORS configuration for React frontend
CORS(app, origins=[
    "http://localhost:3000",  # React dev server
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://edify-ai-assistant.i95-dev.com",     # Production domain
    "https://edify-ai-assistant.i95-dev.com",    # Production domain HTTPS
    "http://45.79.124.136",                      # Production server IP
    "https://45.79.124.136",                     # Production server IP HTTPS
    "http://45.79.124.136:3000",                 # Production Next.js
    "http://45.79.124.136:80",                   # Production server HTTP
    "http://45.79.124.136:5000"             # Production backend
])

# Global components
chatbot_system = None
logger = logging.getLogger(__name__)

# Initialize system at startup
def init_system():
    """Initialize system on first request"""
    global chatbot_system
    if chatbot_system is None:
        logger.info("Initializing chatbot system on first request...")
        initialize_system()

# Initialize system when module loads
try:
    logger.info("Flask app starting up...")
    init_system()
except Exception as e:
    logger.warning(f"WARNING: Failed to initialize system at startup: {str(e)}")

def initialize_system():
    """Initialize the chatbot system components"""
    global chatbot_system
    try:
        logger.info("Initializing system components...")
        
        # Configuration from environment variables
        config = {
            'vector_db_type': os.getenv('VECTOR_DB_TYPE', 'pinecone'),
            'vector_db_path': os.getenv('VECTOR_DB_PATH', './vector_store_pinecone'),
            'collection_name': os.getenv('COLLECTION_NAME', 'pdf_chunks'),
            'embedding_model': os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2'),
            'max_context_chunks': int(os.getenv('MAX_CONTEXT_CHUNKS', '8')),
            'min_similarity_threshold': float(os.getenv('MIN_SIMILARITY_THRESHOLD', '0.52')),
            'enable_citations': os.getenv('ENABLE_CITATIONS', 'true').lower() == 'true',
            'enable_context_expansion': os.getenv('ENABLE_CONTEXT_EXPANSION', 'true').lower() == 'true',
            'max_context_length': int(os.getenv('MAX_CONTEXT_LENGTH', '6000')),
            # Azure configuration
            'azure_connection_string': os.getenv('AZURE_STORAGE_CONNECTION_STRING'),
            'azure_account_name': os.getenv('AZURE_STORAGE_ACCOUNT_NAME'),
            'azure_account_key': os.getenv('AZURE_STORAGE_ACCOUNT_KEY'),
            'azure_container_name': os.getenv('AZURE_STORAGE_CONTAINER_NAME'),
            'azure_folder_path': os.getenv('AZURE_BLOB_FOLDER_PATH'),
            # Edify API configuration
            'edify_api_key': os.getenv('EDIFY_API_KEY'),
            'edify_api_base_url': os.getenv('EDIFY_API_BASE_URL'),
            'edify_api_endpoint': os.getenv('EDIFY_API_ENDPOINT'),
            'edify_api_timeout': os.getenv('EDIFY_API_TIMEOUT'),
            # Pinecone configuration
            'pinecone_api_key': os.getenv('PINECONE_API_KEY'),
            'pinecone_environment': os.getenv('PINECONE_ENVIRONMENT', 'us-east-1-aws'),
            'pinecone_index_name': os.getenv('PINECONE_INDEX_NAME', 'chatbot-chunks')
        }
        
        # Initialize Vector Database
        from vector_db import EnhancedVectorDBManager
        vector_db = EnhancedVectorDBManager(config)
        
        # Initialize AI Chatbot
        from chatbot import AIChhatbotInterface
        chatbot = AIChhatbotInterface(vector_db, config)
        
        # Initialize LLM Service
        from llm_service import LLMService
        llm_service = LLMService(config)
        
        # Connect LLM service to chatbot
        chatbot.llm_service = llm_service
        
        chatbot_system = {
            'vector_db': vector_db,
            'chatbot': chatbot,
            'llm_service': llm_service,
            'config': config,
            'status': 'ready'
        }
        
        logger.info("SUCCESS: System components loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"ERROR: Failed to load system components: {str(e)}")
        logger.error(traceback.format_exc())
        return False

# API Routes

@app.route('/', methods=['GET'])
def root():
    """Root endpoint - API information"""
    return jsonify({
        'message': 'Edify AI Assistant Backend API',
        'version': '3.0',
        'status': 'online',
        'endpoints': {
            'health': '/api/health',
            'chat': '/api/chat',
            'mobile_chat': '/api/mobile/chat',
            'system_status': '/api/system/status',
            'file_download': '/api/files/download/<filename>'
        },
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'system_ready': chatbot_system is not None and chatbot_system.get('status') == 'ready'
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Send a message and get AI response - stateless version for Assistant UI Cloud"""
    try:
        # Ensure system is initialized
        if not chatbot_system or chatbot_system.get('status') != 'ready':
            logger.warning("WARNING: Chatbot system not ready, attempting to initialize...")
            init_system()
            
            if not chatbot_system or chatbot_system.get('status') != 'ready':
                logger.error("ERROR: Failed to initialize chatbot system")
                return jsonify({'error': 'System not ready - initialization failed'}), 503
        
        data = request.get_json()
        raw_messages = data.get('messages', [])  # Full conversation history as messages array
        
        # Handle both old format (message + messages) and new format (messages only)
        if data and 'message' in data:
            # Old format - single message
            user_message = data['message']
        elif raw_messages and len(raw_messages) > 0:
            # New format - extract latest user message from messages array
            last_message = raw_messages[-1]
            if last_message.get('role') == 'user' and 'content' in last_message:
                content = last_message['content']
                if isinstance(content, list) and len(content) > 0 and content[0].get('type') == 'text':
                    user_message = content[0]['text']
                elif isinstance(content, str):
                    user_message = content
                else:
                    return jsonify({'error': 'Invalid message content format'}), 400
            else:
                return jsonify({'error': 'Last message must be from user'}), 400
        else:
            return jsonify({'error': 'Message content is required'}), 400
        # Extract parameters from both JSON body and URL query parameters
        raw_namespaces = data.get('namespaces', None) or request.args.get('namespaces', None)
        role = data.get('role', None) or request.args.get('role', None)
        thread_id = data.get('thread_id', None)  # Thread ID for conversation continuity
        
        # Normalize and validate namespaces - support both kb-* and edipedia-* formats
        namespaces = None
        if raw_namespaces:
            if isinstance(raw_namespaces, str):
                raw_namespaces = [ns.strip() for ns in raw_namespaces.split(',') if ns.strip()]
            
            # Valid namespace patterns
            valid_kb_namespaces = ['kb-psp', 'kb-msp', 'kb-ssp', 'kb-esp']
            valid_edipedia_namespaces = ['edipedia-k12', 'edipedia-preschools', 'edipedia-edifyho']
            all_valid_namespaces = valid_kb_namespaces + valid_edipedia_namespaces
            
            # Filter and validate namespaces
            validated_namespaces = []
            for ns in raw_namespaces:
                ns = ns.lower().strip()
                if ns in all_valid_namespaces:
                    validated_namespaces.append(ns)
            
            namespaces = validated_namespaces if validated_namespaces else None
        
        # Optimize message history to prevent token overflow
        optimized_messages = limit_messages(raw_messages, max_messages=20)
        messages = compress_old_context(optimized_messages, max_length=30)
        
        # Log the conversation for debugging
        logger.info(f"🏷️ Target namespaces: {namespaces}")
        logger.info(f"👤 User role: {role}")
        logger.info(f"💬 Message optimization: {len(raw_messages)} → {len(messages)} messages in context")
        
        # Get AI response
        chatbot = chatbot_system['chatbot']
        llm_service = chatbot_system['llm_service']
        
        # Process with chatbot (includes vector search and full message history)
        response_data = chatbot.process_query(
            user_query=user_message,
            include_context=True,
            messages=messages,  # Pass full messages array instead of conversation_history
            thread_id=thread_id,  # Pass thread ID for conversation continuity
            namespaces=namespaces,
            role=role  # Pass role for admin-specific behavior
        )
        
        # Extract response content
        ai_content = response_data.get('response', 'I apologize, but I encountered an error processing your request.')
        
        # Process reasoning
        reasoning = response_data.get('reasoning', '')
        if reasoning is None:
            reasoning = ''
        
        # Clean up reasoning text
        if reasoning:
            for prefix in ["AI reasoning process:", "AI reasoning:", "Reasoning process:"]:
                if reasoning.startswith(prefix):
                    reasoning = reasoning[len(prefix):].strip()
        
        # Default reasoning if none provided
        if not reasoning or len(reasoning.strip()) < 10:
            reasoning = "I analyzed your question and retrieved relevant information from our educational database to provide you with an accurate, helpful response."
        
        # 👤 ADMIN ROLE ONLY: Show sources only for admin role
        show_sources = role == 'admin'
        logger.info(f"📁 Sources visibility: {show_sources} (role: {role})")
        
        # Conditionally include sources based on role
        sources_to_include = response_data.get('sources', []) if show_sources else []
        
        metadata = {
            'sources': sources_to_include,
            'context_used': response_data.get('context_used', False),
            'processing_time': response_data.get('processing_time', 0),
            'model_used': response_data.get('model_used', 'unknown'),
            'reasoning': reasoning,
            'has_reasoning': bool(reasoning),
            'confidence': response_data.get('confidence', 0),
            'is_follow_up': response_data.get('is_follow_up', False),
            'follow_up_context': response_data.get('follow_up_context', None),
            'show_sources': show_sources  # Add flag for frontend reference
        }
        
        return jsonify({
            'response': ai_content,
            'metadata': metadata,
            'reasoning': reasoning,
            'has_reasoning': bool(reasoning),
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/download/<path:filename>')
def download_file(filename):
    """Generate secure download URL and redirect to Azure storage"""
    try:
        if not chatbot_system or not chatbot_system['chatbot'].azure_service:
            # Try to initialize Azure service directly
            logger.info(f"Azure service not available, attempting to create it on demand...")
            
            config = {
                'azure_connection_string': os.getenv('AZURE_STORAGE_CONNECTION_STRING'),
                'azure_account_name': os.getenv('AZURE_STORAGE_ACCOUNT_NAME'),
                'azure_account_key': os.getenv('AZURE_STORAGE_ACCOUNT_KEY'),
                'azure_container_name': os.getenv('AZURE_STORAGE_CONTAINER_NAME'),
                'azure_folder_path': os.getenv('AZURE_BLOB_FOLDER_PATH')
            }
            
            try:
                from azure_blob_service import create_azure_download_service
                azure_service = create_azure_download_service(config)
                if not azure_service:
                    return jsonify({'error': 'Failed to initialize Azure download service'}), 503
            except Exception as e:
                logger.error(f"Failed to create Azure service on demand: {str(e)}")
                return jsonify({'error': 'Azure download service not available'}), 503
        else:
            azure_service = chatbot_system['chatbot'].azure_service
        
        logger.info(f"Attempting to download file: {filename}")
        
        # Generate secure download URL from Azure with longer expiry
        download_url = azure_service.generate_download_url(filename, expiry_hours=24)
        
        if download_url:
            logger.info(f"Redirecting to Azure download URL for: {filename}")
            # Redirect to the Azure blob storage URL with SAS token
            return redirect(download_url)
        else:
            logger.warning(f"File not found in Azure storage: {filename}")
            return jsonify({'error': 'File not found in Azure storage'}), 404
            
    except Exception as e:
        logger.error(f"Error generating download URL: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Get system status and configuration"""
    try:
        if not chatbot_system:
            return jsonify({
                'status': 'not_initialized',
                'components': {}
            })
        
        config = chatbot_system.get('config', {})
        
        return jsonify({
            'status': chatbot_system.get('status', 'unknown'),
            'components': {
                'vector_db': chatbot_system.get('vector_db') is not None,
                'chatbot': chatbot_system.get('chatbot') is not None,
                'llm_service': chatbot_system.get('llm_service') is not None,
                'azure_service': chatbot_system.get('chatbot') and 
                               chatbot_system['chatbot'].azure_service is not None
            },
            'configuration': {
                'vector_db_type': config.get('vector_db_type'),
                'embedding_model': config.get('embedding_model'),
                'max_context_chunks': config.get('max_context_chunks'),
                'enable_citations': config.get('enable_citations'),
                'enable_context_expansion': config.get('enable_context_expansion'),
                'pinecone_index_name': config.get('pinecone_index_name') if config.get('vector_db_type') == 'pinecone' else None,
                'pinecone_environment': config.get('pinecone_environment') if config.get('vector_db_type') == 'pinecone' else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mobile/chat', methods=['POST'])
def mobile_chat():
    """Mobile API - Simple chat endpoint that returns only the AI response"""
    try:
        # Ensure system is initialized
        if not chatbot_system or chatbot_system.get('status') != 'ready':
            logger.warning("WARNING: Chatbot system not ready, attempting to initialize...")
            init_system()
            
            if not chatbot_system or chatbot_system.get('status') != 'ready':
                logger.error("ERROR: Failed to initialize chatbot system")
                return jsonify({'error': 'System not ready - initialization failed'}), 503
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message content is required'}), 400
        
        user_message = data['message']
        raw_messages = data.get('messages', [])  # Full conversation history as messages array
        
        # Extract parameters from both JSON body and URL query parameters (like regular API)
        raw_namespaces = data.get('namespaces', None) or request.args.get('namespaces', None)
        role = data.get('role', None) or request.args.get('role', None)
        
        # Normalize and validate namespaces - support both kb-* and edipedia-* formats
        namespaces = None
        if raw_namespaces:
            if isinstance(raw_namespaces, str):
                raw_namespaces = [ns.strip() for ns in raw_namespaces.split(',') if ns.strip()]
            
            # Valid namespace patterns
            valid_kb_namespaces = ['kb-psp', 'kb-msp', 'kb-ssp', 'kb-esp']
            valid_edipedia_namespaces = ['edipedia-k12', 'edipedia-preschools', 'edipedia-edifyho']
            all_valid_namespaces = valid_kb_namespaces + valid_edipedia_namespaces
            
            # Filter and validate namespaces
            validated_namespaces = []
            for ns in raw_namespaces:
                ns = ns.lower().strip()
                if ns in all_valid_namespaces:
                    validated_namespaces.append(ns)
            
            namespaces = validated_namespaces if validated_namespaces else None
        
        # Optimize message history for mobile (smaller limit)
        optimized_messages = limit_messages(raw_messages, max_messages=15)
        messages = compress_old_context(optimized_messages, max_length=20)
        
        logger.info(f"📱 Mobile API - Processing message: {user_message[:50]}...")
        logger.info(f"📱 Mobile API - Message optimization: {len(raw_messages)} → {len(messages)} messages")
        logger.info(f"📱 Mobile API - Namespaces: {namespaces}")
        logger.info(f"📱 Mobile API - Role: {role}")
        
        # Get AI response
        chatbot = chatbot_system['chatbot']
        
        # Process with chatbot (includes vector search and full message history)
        response_data = chatbot.process_query(
            user_query=user_message,
            include_context=True,
            messages=messages,  # Pass full messages array instead of conversation_history
            namespaces=namespaces
        )
        
        # Extract only the AI response content - no metadata, sources, or reasoning
        ai_response = response_data.get('response', 'I apologize, but I encountered an error processing your request.')
        
        # Return simple response
        return jsonify({
            'response': ai_response
        })
        
    except Exception as e:
        logger.error(f"📱 Mobile API - Error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'An error occurred processing your request'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize system
    initialize_system()
    
    # Run the app
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
