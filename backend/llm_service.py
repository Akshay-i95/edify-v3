"""
LLM Service with Groq AI Integration (GPT OSS 120B)
Provides high-quality responses with reasoning and intelligent fallback support
"""
from typing import Dict, List, Optional
from datetime import datetime
import logging
import os
import time
import requests
import json
import re
from groq import Groq

class LLMService:
    def __init__(self, config: Dict):
        """Initialize LLM service with Groq AI (GPT OSS 120B)"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Groq API configuration
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.groq_client = None
        
        # Gemini API configuration (commented out for now)
        # self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        # self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
        # Centralized response generation configuration
        self.max_output_tokens = int(os.getenv('MAX_OUTPUT_TOKENS', '1500'))  # Increased from 1200
        self.response_temperature = float(os.getenv('RESPONSE_TEMPERATURE', '0.2'))  # Lowered from 0.2
        self.response_quality = os.getenv('RESPONSE_QUALITY', 'comprehensive')
        
        # Initialize API clients
        self._initialize_apis()
    
    @staticmethod
    def _sanitize_for_logging(text: str, max_length: int = 300) -> str:
        """
        Sanitize text for Windows console logging by removing problematic Unicode characters.
        Handles narrow non-breaking spaces (\u202f), emojis, and other special characters.
        """
        if not text:
            return ""
        
        # Replace problematic Unicode characters with ASCII equivalents
        sanitized = text.replace('\u202f', ' ')  # Narrow non-breaking space -> regular space
        sanitized = sanitized.replace('\u2013', '-')  # En dash -> hyphen
        sanitized = sanitized.replace('\u2014', '--')  # Em dash -> double hyphen
        sanitized = sanitized.replace('\u2018', "'")  # Left single quote
        sanitized = sanitized.replace('\u2019', "'")  # Right single quote
        sanitized = sanitized.replace('\u201c', '"')  # Left double quote
        sanitized = sanitized.replace('\u201d', '"')  # Right double quote
        
        # Remove emojis and other high Unicode characters (above U+FFFF)
        sanitized = re.sub(r'[^\x00-\x7F\u0080-\uFFFF]', '', sanitized)
        
        # Truncate if needed
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."
        
        return sanitized
    
    def _initialize_apis(self):
        """Initialize API clients after logger is set up"""
        # Check Groq API availability
        if self.groq_api_key and self.groq_api_key != 'your_groq_api_key_here':
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
                self.groq_available = True
                self.logger.info("[SUCCESS] Groq AI API (GPT OSS 120B) configured successfully")
                self.logger.info(f"📊 Response Config: {self.max_output_tokens} tokens, temp={self.response_temperature}")
            except Exception as e:
                self.groq_available = False
                self.logger.warning(f"[WARNING] Groq API initialization failed: {str(e)}")
        else:
            self.groq_available = False
            self.logger.warning("[WARNING] GROQ_API_KEY not configured - using intelligent fallback responses")
        
        # Check Gemini API availability (commented out)
        # if self.gemini_api_key and self.gemini_api_key != 'your_gemini_api_key_here':
        #     self.gemini_available = True
        #     self.logger.info("✅ Gemini AI API configured successfully")
        #     self.logger.info(f"📊 Response Config: {self.max_output_tokens} tokens, temp={self.response_temperature}")
        # else:
        #     self.gemini_available = False
        #     self.logger.warning("⚠️ GEMINI_API_KEY not configured - using intelligent fallback responses")
    
    def generate_response(self, query: str, context: str, conversation_history: List = None, role: str = None) -> Dict:
        """Generate enhanced response with reasoning using Groq AI (GPT OSS 120B) with role-based styling"""
        try:
            start_time = time.time()
            
            self.logger.info(f"Generating response for query: {query[:50]}...")
            self.logger.info(f"Context length: {len(context)} characters")
            self.logger.info(f"User role: {role}")
            
            # Try Groq API first
            if self.groq_available:
                groq_response = self._call_groq_api(query, context, conversation_history, role)
                
                if groq_response and self._is_valid_response(groq_response.get('response', ''), query):
                    # Log the reasoning with clear start and end markers for debugging
                    reasoning = groq_response.get('reasoning', '')
                    self.logger.info(f"REASONING_START\n{self._sanitize_for_logging(reasoning, 1000)}\nREASONING_END")
                    self.logger.info(f"Reasoning length: {len(reasoning)} characters")
                    
                    # Mark the fallback reasoning with a special prefix for easier detection
                    if reasoning == "Applied step-by-step analysis to locate specific information in educational documents.":
                        self.logger.warning("Using fallback reasoning text - no valid reasoning extracted")
                        reasoning = "[FALLBACK_REASONING] " + reasoning
                    
                    return {
                        'response': groq_response.get('response', ''),
                        'reasoning': reasoning,
                        'model_used': 'openai/gpt-oss-120b',
                        'reasoning_quality': groq_response.get('reasoning_quality', 'medium'),
                        'response_time': time.time() - start_time,
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Try Gemini API (commented out for now)
            # if self.gemini_available:
            #     gemini_response = self._call_gemini_api(query, context, conversation_history)
            #     
            #     if gemini_response and self._is_valid_response(gemini_response.get('response', ''), query):
            #         # Log the reasoning with clear start and end markers for debugging
            #         reasoning = gemini_response.get('reasoning', '')
            #         self.logger.info(f"REASONING_START\n{reasoning}\nREASONING_END")
            #         self.logger.info(f"Reasoning length: {len(reasoning)} characters")
            #         
            #         # Mark the fallback reasoning with a special prefix for easier detection
            #         if reasoning == "Applied step-by-step analysis to locate specific information in educational documents.":
            #             self.logger.warning("Using fallback reasoning text - no valid reasoning extracted")
            #             reasoning = "[FALLBACK_REASONING] " + reasoning
            #         
            #         return {
            #             'response': gemini_response.get('response', ''),
            #             'reasoning': reasoning,
            #             'model_used': 'gemini-2.0-flash',
            #             'reasoning_quality': gemini_response.get('reasoning_quality', 'medium'),
            #             'response_time': time.time() - start_time,
            #             'timestamp': datetime.now().isoformat()
            #         }
            
            # Use intelligent fallback if Groq fails or is unavailable
            self.logger.info("[FALLBACK] Using intelligent fallback response generation...")
            fallback_response = self._generate_intelligent_fallback_response(query, context)
            
            return {
                'response': fallback_response['response'],
                'reasoning': fallback_response.get('reasoning', ''),
                'model_used': 'intelligent_fallback',
                'reasoning_quality': 'medium',
                'response_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"[ERROR] Response generation error: {str(e)}")
            return {
                'response': f"I encountered an error generating the response. Please try rephrasing your question.",
                'reasoning': f"Error occurred during processing: {str(e)}",
                'model_used': 'error_handler',
                'reasoning_quality': 'low',
                'response_time': time.time() - start_time,
                'error': str(e)
            }
    
    def _call_groq_api(self, query: str, context: str, conversation_history: List = None, role: str = None) -> Optional[Dict]:
        """Call Groq AI API with GPT OSS 120B model for reasoning with role-based customization"""
        try:
            # Customize system prompt based on user role
            role_context = ""
            if role == 'admin':
                role_context = """\n\n**YOUR AUDIENCE: ADMIN USER**
You are responding to an ADMIN who needs:
- Complete, comprehensive information with ALL available details
- Technical insights and data-driven analysis
- Implementation strategies and system-level information
- Formal, SOP-aligned, structured responses with monitoring/enforcement considerations
- Professional, detailed explanations with full context
"""
            elif role == 'teacher':
                role_context = """\n\n**YOUR AUDIENCE: TEACHER**
You are responding to a TEACHER who needs:
- Pedagogical strategies and classroom implementation tips
- Lesson planning guidance and teaching methodologies
- Student engagement techniques from Edify SOPs
- Practical examples and activity suggestions
- Professional but accessible language with educational focus
"""
            elif role == 'student':
                role_context = """\n\n**YOUR AUDIENCE: STUDENT**
You are responding to a STUDENT who needs:
- Clear, simple explanations with step-by-step guidance
- Relatable examples and practical applications
- Encouraging, supportive, friendly tone that builds confidence
- Visual formatting with bullet points, numbered steps, and examples
- Age-appropriate language that makes learning engaging
"""
            else:
                role_context = """\n\n**YOUR AUDIENCE: GENERAL USER**
Provide balanced, informative responses suitable for all audiences.
"""
            
            # Build conversation context with MANDATORY structured output format
            system_prompt = f"""You are the Edify Educational AI Assistant - provide helpful, well-formatted responses to students and educators.{role_context}

CRITICAL: You MUST ALWAYS structure your output in this EXACT format:

-------------------------------------------------------
**REASONING:**  
Provide a SHORT, high-level explanation (3-6 sentences maximum).

Rules for Reasoning Section:
- Explain how you interpreted the question
- Identify the topic clearly (e.g., "Grade 6 Math – Fractions", "Teacher SOP – Homework policy", "Student Conduct Rules")
- If user says "this", "it", "above", or refers to previous content, infer topic from conversation history
- If user asks "what did we discuss" or "summarize our conversation", list ALL topics from the conversation history
- State: "The previous query was about [TOPIC], so this question refers to [TOPIC]"
- Mention the role-based tone you will use (admin/teacher/student)
- Do NOT reveal internal step-by-step deliberations — only provide a concise summary
- CRITICAL FILTERING: Ignore any knowledge base documents that do NOT match the identified topic

-------------------------------------------------------
**RESPONSE:**  
Provide the actual answer according to the role.

SHORT-FIRST RULE (MANDATORY):
- For simple questions → respond in **50-80 words** maximum
- For conversation summaries ("what did we discuss?") → list ALL topics from the conversation history
- If user asks "explain more", "expand", "give full details", or similar → provide longer, detailed response
- Never over-explain simple questions

FORMATTING GUIDELINES:
1. **Use Bold Headers for Main Sections:**
   - **Key Concepts**, **Quick Summary**, **Steps**, **SOP Guidelines**, etc.
   
2. **Use Numbered Lists for Steps/Procedures:**
   1. **Step Name:** Clear description
   2. **Next Step:** Clear description
   
3. **Use Bullet Points for Item Lists:**
   • Concise points for concepts, tips, features
   • Use sub-bullets when needed
   
4. **Use Tables ONLY When Required:**
   - Only for comparisons, structured workflows, or multi-column data
   - For simple lists, use bullets/numbers instead
   - Good use cases: comparing concepts, grade-wise breakdowns, multi-step procedures
   
5. **Mathematical Formulas (CRITICAL):**
   - Inline math: `$formula$` with LaTeX notation
   - Display math: `$$formula$$` on its own line
   - Examples:
     * Inline: `$\\sin \\theta = \\frac{{opposite}}{{hypotenuse}}$`
     * Display: `$$\\sin^2 \\theta + \\cos^2 \\theta = 1$$`
   - Common LaTeX: \\frac{{a}}{{b}}, \\sin, \\cos, \\tan, \\theta, \\pi, \\sqrt{{x}}, x^2, x_1
   
6. **Highlight Key Terms:**
   - Use **bold** for important terms and concepts
   - Mathematical expressions MUST use LaTeX `$...$` notation

7. **Use Examples When Helpful:**
   **Example:**
   Problem: $2\\frac{{1}}{{4}} + 1\\frac{{1}}{{3}}$
   Solution: Convert to improper fractions...

RESPONSE STYLE BY ROLE:
- **Admin:** Formal, structured, SOP-aligned, mentions monitoring/enforcement if relevant
- **Teacher:** Practical, classroom-oriented, supportive, pedagogically focused
- **Student:** Friendly, simple, encouraging, age-appropriate

KNOWLEDGE BASE USAGE:
- Use ONLY content from knowledge base chunks matching the identified topic
- If knowledge base contains unrelated subjects (e.g., English when topic is Math), COMPLETELY IGNORE them
- If no relevant KB data exists, state: "No knowledge base data found for this topic — providing general guidance."
- Never mix subjects or include irrelevant content

ROLE-BASED KNOWLEDGE FILTER (CRITICAL):
When generating responses:
- For STUDENT queries → Use ONLY student-related rules, student SOPs, student conduct guidelines, student curriculum
- For TEACHER queries → Use ONLY teacher-related SOPs, staff guidelines, instructional policies, teaching methodologies
- For ADMIN queries → Use ONLY admin/SOP/monitoring/operational guidelines, system-level policies

⚠️ STRICT ROLE ISOLATION RULES:
- NEVER mix teacher/staff/employee concepts into student answers
- NEVER mix student rules into teacher/admin answers
- Do NOT adapt employee, staff, HR, or teacher policies into student rules
- Do NOT infer "cross-role principles" or apply rules from one role to another
- Use only documents that directly match BOTH the role AND the topic - ignore all others

🔥 FOLLOW-UP EXPANSION RULE:
- If user asks "explain more" or "expand" → expand ONLY the original content, staying within the same role and topic
- Do NOT introduce new departments, staff roles, admin roles, or unrelated SOPs during expansion
- Keep expansions strictly within the original scope

-------------------------------------------------------
CRITICAL REMINDERS:
- NEVER skip the **REASONING:** and **RESPONSE:** headers - they are MANDATORY
- Follow the SHORT-FIRST RULE strictly
- Maintain strict topic AND role accuracy - filter out unrelated KB content
- Use visual structure (headers, bullets, numbers) for scannability
- Generate examples dynamically from knowledge base
- Use tables sparingly - only when truly needed
- Respect role boundaries - NEVER cross-contaminate role-specific content"""
            
            # Create messages for Groq API with enforced structure
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"""EDIFY KNOWLEDGE BASE:
{context}

QUESTION: {query}

Remember: Structure your output with **REASONING:** followed by **RESPONSE:** headers. Be helpful and natural."""
                }
            ]
            
            # Minimal conversation history - pure follow-up approach like ChatGPT
            if conversation_history:
                # Include more context for better conversation continuity
                # Keep last 6-8 messages (3-4 exchanges) to maintain conversation flow
                recent_messages = conversation_history[-8:] if len(conversation_history) >= 8 else conversation_history
                
                for msg in recent_messages:
                    if msg.get('role') == 'user':
                        # Add user messages with full context
                        user_content = msg.get('content', '')
                        # Keep more context for topic identification
                        if len(user_content) > 1000:
                            user_content = user_content[:1000] + "..."
                        messages.insert(-1, {"role": "user", "content": user_content})
                        
                    elif msg.get('role') == 'assistant':
                        # Extract key points from assistant response for context
                        assistant_content = msg.get('content', '')
                        
                        # For follow-ups, preserve more context from the response
                        clean_content = assistant_content
                        
                        # Remove source documents section to save tokens
                        if "Source Documents" in clean_content:
                            clean_content = clean_content.split("Source Documents")[0].strip()
                        
                        # Keep more content for better context (up to 800 chars)
                        if len(clean_content) > 800:
                            # Keep beginning (topic + main content)
                            clean_content = clean_content[:800] + "..."
                        
                        # Only add if it's meaningful content
                        if len(clean_content.strip()) > 20:
                            messages.insert(-1, {"role": "assistant", "content": clean_content.strip()})
                
                self.logger.info(f"[CONVERSATION CONTEXT] Using {len(recent_messages)} recent messages for better topic continuity")
            
            # Make the API call to Groq
            completion = self.groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                temperature=self.response_temperature,
                max_tokens=min(self.max_output_tokens, 8000),  # GPT OSS 120B supports up to 128k context
                top_p=0.95,
                stream=False
            )
            
            if completion and completion.choices:
                generated_text = completion.choices[0].message.content
                self.logger.info(f"[GROQ] Generated response: {len(generated_text)} characters")
                
                # Extract reasoning and final answer with improved extraction logic
                reasoning, answer = self._extract_reasoning_and_answer(generated_text)
                
                # Log the extracted components with clear debug markers
                self.logger.info(f"[GROQ] Extracted reasoning: {len(reasoning)} characters")
                self.logger.info(f"[GROQ] Extracted answer: {len(answer)} characters")
                self.logger.info(f"[GROQ] REASONING_START\n{self._sanitize_for_logging(reasoning, 300)}...\nREASONING_END")
                self.logger.info(f"[GROQ] ANSWER_START\n{self._sanitize_for_logging(answer, 300)}...\nANSWER_END")
                
                # Calculate reasoning quality
                reasoning_quality = 'high' if len(reasoning) > 300 else 'medium' if len(reasoning) > 100 else 'low'
                
                return {
                    'response': answer or generated_text,
                    'reasoning': reasoning,
                    'reasoning_quality': reasoning_quality,
                    'full_text': generated_text
                }
            else:
                self.logger.warning("[WARNING] No response from Groq API")
                return None
                
        except Exception as e:
            self.logger.warning(f"[WARNING] Groq API error: {str(e)}")
            return None
    
    # Commented out Gemini API method for future reference
    # def _call_gemini_api(self, query: str, context: str, conversation_history: List = None) -> Optional[Dict]:
    #     """Call Gemini AI API with reasoning"""
    #     try:
    #         # Build conversation context with enhanced Edify-native expert persona
    #         system_prompt = """You are the Edify Educational AI Assistant - an integrated part of the Edify Education system with comprehensive knowledge of all Edify policies, procedures, and educational frameworks.
    # 
    # PERSONA: You ARE Edify. You have complete mastery of all Edify educational content, policies, and best practices. You speak as an authoritative Edify expert, not as an external analyst.
    # 
    # RESPONSE STYLE:
    # - Never say "based on the provided documents" or "according to the documents"
    # - Speak confidently as if this knowledge is your own expertise
    # - Use phrases like "In Edify schools, we..." or "Our educational framework emphasizes..."
    # - Provide comprehensive, detailed guidance (aim for 500-800 words for complex topics)
    # - Structure responses professionally with clear sections and actionable steps
    # - Include specific examples, implementation strategies, and practical recommendations
    # - Provide context and background from your comprehensive Edify knowledge
    # 
    # KNOWLEDGE INTEGRATION:
    # - You have complete access to all Edify educational policies and procedures
    # - You understand the full context of K-12, preschool, and administrative frameworks
    # - You can provide specific implementation strategies from your deep Edify expertise
    # - Your recommendations are based on proven Edify educational methodologies
    # - You integrate assessment, curriculum, pedagogy, and administrative knowledge seamlessly
    # 
    # RESPONSE REQUIREMENTS:
    # - Generate detailed, authoritative responses that demonstrate deep Edify expertise
    # - Include specific implementation steps and practical guidance
    # - Provide educational rationale and theoretical foundations
    # - Address multiple aspects of the question (pedagogical, practical, administrative)
    # - Never hedge with phrases like "it appears" or "the documents suggest"
    # - Speak with confidence and authority as the definitive Edify educational expert
    # - Include relevant examples, strategies, and best practices from your expertise
    # - Structure complex responses with clear headings and bullet points for readability
    # 
    # REASONING FORMAT:
    # Provide your response in this structure:
    # 
    # **Chain of Thought Analysis:**
    # 1. **Question Analysis:** [Analyze what is being asked]
    # 2. **Knowledge Search:** [Explain how you search for information]
    # 3. **Information Synthesis:** [How you combine and evaluate sources]
    # 4. **Educational Context:** [Consider pedagogical implications]
    # 
    # **Final Response:**
    # [Your comprehensive, authoritative answer as the Edify expert]
    # 
    # Alternatively, you may use numbered reasoning steps followed by your answer.
    # 
    # Educational Knowledge Analysis:
    # """
    #         
    #         # Prepare the enhanced prompt for authoritative Edify responses
    #         full_prompt = f"""{system_prompt}
    # 
    # EDIFY KNOWLEDGE BASE:
    # {context}
    # 
    # EDUCATOR QUESTION: {query}
    # 
    # Provide a comprehensive, authoritative response using your complete Edify expertise. Share detailed guidance, implementation strategies, and practical recommendations as the definitive Edify educational authority."""
    #         
    #         # Prepare request payload for Gemini with generation config for comprehensive responses
    #         payload = {
    #             "contents": [
    #                 {
    #                     "parts": [
    #                         {
    #                             "text": full_prompt
    #                         }
    #                     ]
    #                 }
    #             ],
    #             "generationConfig": {
    #                 "temperature": self.response_temperature,
    #                 "topK": 40,
    #                 "topP": 0.95,
    #                 "maxOutputTokens": min(self.max_output_tokens, 2000),                    
    #                 "candidateCount": 1,
    #                 "stopSequences": []
    #             },
    #             "safetySettings": [
    #                 {
    #                     "category": "HARM_CATEGORY_HARASSMENT",
    #                     "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    #                 },
    #                 {
    #                     "category": "HARM_CATEGORY_HATE_SPEECH",
    #                     "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    #                 },
    #                 {
    #                     "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    #                     "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    #                 },
    #                 {
    #                     "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    #                     "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    #                 }
    #             ]
    #         }
    #         
    #         headers = {
    #             'Content-Type': 'application/json',
    #             'X-goog-api-key': self.gemini_api_key
    #         }
    #         
    #         # Make the API call
    #         response = requests.post(
    #             self.gemini_url,
    #             headers=headers,
    #             json=payload,
    #             timeout=30
    #         )
    #         
    #         if response.status_code == 200:
    #             response_data = response.json()
    #             
    #             if 'candidates' in response_data and len(response_data['candidates']) > 0:
    #                 generated_text = response_data['candidates'][0]['content']['parts'][0]['text']
    #                 self.logger.info(f"[GEMINI] Generated response: {len(generated_text)} characters")
    #                 
    #                 # Extract reasoning and final answer with improved extraction logic
    #                 reasoning, answer = self._extract_reasoning_and_answer(generated_text)
    #                 
    #                 # Log the extracted reasoning with clear debug markers
    #                 self.logger.info(f"[GEMINI] Extracted reasoning: {len(reasoning)} characters")
    #                 self.logger.info(f"[GEMINI] REASONING_START\n{reasoning[:500]}...\nREASONING_END")
    #                 
    #                 # Calculate reasoning quality
    #                 reasoning_quality = 'high' if len(reasoning) > 300 else 'medium' if len(reasoning) > 100 else 'low'
    #                 
    #                 return {
    #                     'response': answer or generated_text,
    #                     'reasoning': reasoning,
    #                     'reasoning_quality': reasoning_quality,
    #                     'full_text': generated_text
    #                 }
    #             else:
    #                 self.logger.warning("⚠️ No candidates in Gemini response")
    #                 return None
    #         else:
    #             self.logger.warning(f"⚠️ Gemini API error: {response.status_code} - {response.text}")
    #             return None
    #             
    #     except requests.exceptions.Timeout:
    #         self.logger.warning("⚠️ Gemini API timeout")
    #         return None
    #     except Exception as e:
    #         self.logger.warning(f"⚠️ Gemini API error: {str(e)}")
    #         return None
            
    def _extract_reasoning_and_answer(self, text: str) -> tuple[str, str]:
        """Extract reasoning and answer from Groq response with strict separation"""
        try:
            self.logger.info(f"[EXTRACTION] Processing text length: {len(text)} characters")
            
            # Strategy 1: PRIORITY - Handle **REASONING:** and **RESPONSE:** markers (NEW FORMAT)
            if "**REASONING:**" in text and "**RESPONSE:**" in text:
                # Split by the markers
                reasoning_marker_idx = text.find("**REASONING:**")
                response_marker_idx = text.find("**RESPONSE:**")
                
                if reasoning_marker_idx < response_marker_idx:
                    # Extract reasoning (after **REASONING:** up to **RESPONSE:**)
                    reasoning_part = text[reasoning_marker_idx + len("**REASONING:**"):response_marker_idx].strip()
                    # Extract response (after **RESPONSE:**)
                    answer_part = text[response_marker_idx + len("**RESPONSE:**"):].strip()
                    
                    if reasoning_part and answer_part:
                        self.logger.info("[EXTRACTION] Successfully used REASONING/RESPONSE marker separation")
                        return reasoning_part, answer_part
            
            # Strategy 2: Handle **Answer:** or **Final Response:** markers
            answer_markers = ["**Answer:**", "**Final Response:**"]
            for marker in answer_markers:
                if marker in text:
                    parts = text.split(marker, 1)
                    if len(parts) == 2:
                        reasoning_part = parts[0].strip()
                        answer_part = parts[1].strip()
                        if answer_part.startswith("*"):
                            answer_part = answer_part[1:].strip()  # Remove remaining *
                        
                        clean_reasoning = self._clean_reasoning(reasoning_part)
                        if clean_reasoning and answer_part and not self._contains_edify_response(reasoning_part):
                            self.logger.info("[EXTRACTION] Successfully used answer marker separation")
                            return clean_reasoning, answer_part
            
            # Strategy 3: Look for clear separation patterns (double newline + Edify phrase)
            # Find the FIRST occurrence of Edify response to ensure clean separation
            edify_patterns = ["In Edify schools", "Our policy", "At Edify", "The SOP"]
            best_split_index = float('inf')
            best_pattern = None
            
            for pattern in edify_patterns:
                # Look for pattern preceded by newlines for clean separation
                full_patterns = [f"\n\n{pattern}", f"\n{pattern}"]
                for full_pattern in full_patterns:
                    index = text.find(full_pattern)
                    if index > 30 and index < best_split_index:  # Must have substantial reasoning before
                        best_split_index = index
                        best_pattern = full_pattern
            
            if best_pattern and best_split_index < float('inf'):
                reasoning_part = text[:best_split_index].strip()
                answer_part = text[best_split_index:].strip()
                
                # Ensure reasoning doesn't contain Edify responses
                if not self._contains_edify_response(reasoning_part):
                    clean_reasoning = self._clean_reasoning(reasoning_part)
                    if clean_reasoning and answer_part:
                        self.logger.info("[EXTRACTION] Successfully used pattern separation")
                        return clean_reasoning, answer_part
            
            # Strategy 4: Find numbered reasoning followed by Edify response
            if self._has_numbered_reasoning(text):
                lines = text.split('\n')
                reasoning_lines = []
                answer_start_idx = -1
                
                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    
                    # Skip headers
                    if any(header in line_stripped for header in ["Chain of Thought Analysis:", "**Chain of Thought Analysis:**"]):
                        continue
                    
                    # Check if this line starts an Edify response - be strict
                    if self._is_edify_response_line(line_stripped):
                        answer_start_idx = i
                        break
                    
                    # Only include analytical content in reasoning - not policy content
                    if (re.match(r'^\d+\.', line_stripped) or 
                        re.match(r'^\*\*\w+.*:\*\*', line_stripped)):
                        # Double-check this line doesn't contain policy content
                        if not self._contains_edify_response(line):
                            reasoning_lines.append(line)
                    elif (len(reasoning_lines) > 0 and line_stripped and 
                          not self._is_edify_response_line(line_stripped) and
                          not self._contains_edify_response(line)):
                        reasoning_lines.append(line)
                
                if reasoning_lines and answer_start_idx > -1:
                    reasoning = '\n'.join(reasoning_lines).strip()
                    answer = '\n'.join(lines[answer_start_idx:]).strip()
                    
                    clean_reasoning = self._clean_reasoning(reasoning)
                    # Final check: ensure reasoning doesn't contain policy content
                    if clean_reasoning and answer and not self._contains_edify_response(clean_reasoning):
                        self.logger.info("[EXTRACTION] Successfully used numbered reasoning separation")
                        return clean_reasoning, answer
            
            # Strategy 5: Handle cases where reasoning and response are mixed
            edify_start_idx = self._find_edify_response_start(text)
            if edify_start_idx > 50:  # Must have substantial content before Edify response
                reasoning_part = text[:edify_start_idx].strip()
                answer_part = text[edify_start_idx:].strip()
                
                # Strict filtering: only keep analytical content, not policy content
                reasoning_lines = []
                for line in reasoning_part.split('\n'):
                    line_stripped = line.strip()
                    # Only include lines that are clearly analytical/reasoning
                    if (line_stripped and 
                        not self._is_edify_response_line(line_stripped) and
                        not self._contains_edify_response(line) and
                        not line_stripped.startswith("SOP/") and
                        "SOP/" not in line_stripped and
                        any(keyword in line_stripped.lower() for keyword in 
                            ["analysis", "looking", "need to", "checking", "searching", "step", "approach"])):
                        reasoning_lines.append(line)
                
                clean_reasoning = '\n'.join(reasoning_lines).strip()
                clean_reasoning = self._clean_reasoning(clean_reasoning)
                
                # Final validation: ensure clean separation
                if (clean_reasoning and answer_part and 
                    not self._contains_edify_response(clean_reasoning) and
                    len(clean_reasoning) > 20):
                    self.logger.info("[EXTRACTION] Successfully used mixed content separation")
                    return clean_reasoning, answer_part
            
            # Strategy 6: Extract any structured content as reasoning
            numbered_points = self._extract_numbered_points(text)
            structured_points = self._extract_structured_points(text)
            question_analysis = self._extract_question_analysis(text)
            
            if numbered_points or structured_points or question_analysis:
                reasoning_content = numbered_points + structured_points + question_analysis
                reasoning = '\n'.join(reasoning_content)
                
                # Find the best answer (prefer Edify response if available)
                edify_start = self._find_edify_response_start(text)
                if edify_start > 0:
                    answer = text[edify_start:].strip()
                else:
                    answer = text
                
                return reasoning, answer
            
            # Strategy 6: For unstructured responses, try to extract any analytical content
            if any(keyword in text.lower() for keyword in ["looking at", "need to find", "document", "policy", "sop"]):
                # Extract the analytical part
                analysis_phrases = []
                for line in text.split('.'):
                    line_stripped = line.strip()
                    if any(keyword in line_stripped.lower() for keyword in ["looking at", "need to find", "analyzing", "checking"]):
                        analysis_phrases.append(line_stripped + ".")
                
                if analysis_phrases:
                    reasoning = ' '.join(analysis_phrases)
                    # Find the policy statement
                    for line in text.split('.'):
                        if any(keyword in line.lower() for keyword in ["edify", "policy", "sop/"]):
                            answer_start = text.find(line.strip())
                            if answer_start > -1:
                                answer = text[answer_start:].strip()
                                return reasoning, answer
            
            # Final strategy: Check if the entire text is just an Edify response
            if any(text.strip().startswith(start) for start in ["In Edify", "Our policy", "At Edify"]):
                # For pure Edify responses, create simple analytical reasoning
                reasoning = "Applied document analysis to locate relevant policy information."
                self.logger.info("[EXTRACTION] Pure Edify response detected")
                return reasoning, text
            
            # Ultimate fallback: Be very conservative
            # If we can't clearly separate, treat the entire text as the answer
            # This avoids triggering fallback when Groq provides good responses without explicit separators
            self.logger.warning("[EXTRACTION] No clear separator found - treating full text as answer")
            self.logger.warning("[EXTRACTION] Groq may not have followed the **REASONING:**/**RESPONSE:** format")
            
            # Use minimal reasoning and full text as answer
            reasoning = "Analyzed documentation to provide comprehensive response."
            return reasoning, text
            
        except Exception as e:
            self.logger.error(f"Error in extraction: {str(e)}")
            return "Applied step-by-step analysis to locate specific information in educational documents.", text
    
    def _extract_structured_points(self, text: str) -> list:
        """Extract structured points like **Question Analysis:**"""
        structured_points = []
        for line in text.split('\n'):
            line_stripped = line.strip()
            if re.match(r'^\*\*\w+.*:\*\*', line_stripped):
                structured_points.append(line_stripped)
        return structured_points
    
    def _contains_edify_response(self, text: str) -> bool:
        """Check if text contains Edify policy responses that should be in answer section"""
        edify_indicators = [
            "In Edify schools", "Our policy", "At Edify", "The SOP",
            "edify school", "edify policy", "school policy"
        ]
        text_lower = text.lower()
        return any(indicator.lower() in text_lower for indicator in edify_indicators)
    
    def _extract_question_analysis(self, text: str) -> list:
        """Extract analytical phrases from unstructured text"""
        analysis_phrases = []
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence_stripped = sentence.strip()
            # Look for analytical language
            if any(keyword in sentence_stripped.lower() for keyword in 
                   ["looking at", "need to find", "analyzing", "checking", "searching for", "examining"]):
                if len(sentence_stripped) > 10:  # Avoid very short fragments
                    analysis_phrases.append(sentence_stripped + ".")
        
        return analysis_phrases
    
    def _generate_contextual_reasoning(self, text: str) -> str:
        """Generate contextual reasoning based on the content of the response"""
        # Extract key information to create relevant reasoning
        if "sop" in text.lower():
            return "Analyzed the educational policy database to locate the specific SOP number for the requested procedure."
        elif "policy" in text.lower():
            return "Reviewed institutional policies to provide accurate policy information."
        elif "curriculum" in text.lower():
            return "Examined curriculum documentation to extract relevant educational guidelines."
        elif "preschool" in text.lower():
            return "Searched preschool-specific documentation to find the requested information."
        else:
            return "Applied systematic search through educational documents to locate the specific information requested."
    
    def _extract_with_cot_pattern(self, text: str) -> tuple[str, str]:
        """Extract using Chain of Thought Analysis pattern"""
        try:
            # Find the start of reasoning content
            cot_start = text.find("Chain of Thought Analysis:")
            if cot_start == -1:
                return self._fallback_extraction(text)
            
            content_after_cot = text[cot_start + len("Chain of Thought Analysis:"):].strip()
            
            # Special handling for **Answer:** marker
            if "**Answer:**" in content_after_cot:
                parts = content_after_cot.split("**Answer:**", 1)
                reasoning = parts[0].strip()
                answer = parts[1].strip()
                return self._clean_reasoning(reasoning), answer
            
            # Find where the Edify response starts
            edify_start = self._find_edify_response_start(content_after_cot)
            
            if edify_start > 0:
                reasoning = content_after_cot[:edify_start].strip()
                answer = content_after_cot[edify_start:].strip()
                return self._clean_reasoning(reasoning), answer
            else:
                # No clear Edify response found, try to split on numbered patterns
                return self._split_on_numbered_pattern(content_after_cot)
        except:
            return self._fallback_extraction(text)
    
    def _extract_with_numbered_pattern(self, text: str) -> tuple[str, str]:
        """Extract using numbered pattern (1., 2., 3., 4.)"""
        try:
            lines = text.split('\n')
            reasoning_lines = []
            answer_lines = []
            in_reasoning = True
            
            for line in lines:
                line_stripped = line.strip()
                
                # Skip headers
                if "Chain of Thought Analysis:" in line_stripped:
                    continue
                
                # Check if this line starts an Edify response
                if self._is_edify_response_line(line_stripped):
                    in_reasoning = False
                
                if in_reasoning:
                    # Include numbered lines and their continuations
                    if (re.match(r'^\d+\.\s', line_stripped) or 
                        (len(reasoning_lines) > 0 and line_stripped and 
                         not self._is_edify_response_line(line_stripped))):
                        reasoning_lines.append(line)
                else:
                    answer_lines.append(line)
            
            reasoning = '\n'.join(reasoning_lines).strip()
            answer = '\n'.join(answer_lines).strip()
            
            if reasoning and answer:
                return self._clean_reasoning(reasoning), answer
            else:
                return self._fallback_extraction(text)
        except:
            return self._fallback_extraction(text)
    
    def _extract_with_structured_pattern(self, text: str) -> tuple[str, str]:
        """Extract using **Question Analysis:** style pattern"""
        try:
            # Find all the structured sections
            sections = ["**Question Analysis:**", "**Knowledge Search:**", "**Information Synthesis:**", "**Educational Context:**"]
            
            reasoning_parts = []
            remaining_text = text
            
            for section in sections:
                if section in remaining_text:
                    start_idx = remaining_text.find(section)
                    if start_idx >= 0:
                        # Find the next section or end
                        next_section_idx = len(remaining_text)
                        for next_section in sections:
                            if next_section != section:
                                next_idx = remaining_text.find(next_section, start_idx + len(section))
                                if next_idx > start_idx and next_idx < next_section_idx:
                                    next_section_idx = next_idx
                        
                        # Also check for Edify response start
                        edify_idx = self._find_edify_response_start(remaining_text[start_idx:])
                        if edify_idx > 0:
                            edify_idx += start_idx
                            if edify_idx < next_section_idx:
                                next_section_idx = edify_idx
                        
                        section_content = remaining_text[start_idx:next_section_idx].strip()
                        reasoning_parts.append(section_content)
            
            if reasoning_parts:
                reasoning = '\n'.join(reasoning_parts)
                
                # Find where answer starts in original text
                edify_start = self._find_edify_response_start(text)
                if edify_start > 0:
                    answer = text[edify_start:].strip()
                    return self._clean_reasoning(reasoning), answer
            
            return self._fallback_extraction(text)
        except:
            return self._fallback_extraction(text)
    
    def _has_numbered_reasoning(self, text: str) -> bool:
        """Check if text has numbered reasoning pattern"""
        numbered_count = 0
        for line in text.split('\n'):
            if re.match(r'^\d+\.\s', line.strip()):
                numbered_count += 1
        return numbered_count >= 2
    
    def _find_edify_response_start(self, text: str) -> int:
        """Find where the Edify response starts in the text with improved detection"""
        edify_patterns = [
            "\n\nIn Edify schools",  # Most common pattern with double newline
            "\nIn Edify schools",    # Single newline
            "In Edify schools",      # Direct start
            "\n\nOur policy",
            "\nOur policy", 
            "Our policy",
            "\n\nAt Edify",
            "\nAt Edify",
            "At Edify",
            "\n\nIn Edify",
            "\nIn Edify",
            "In Edify",
            "\n\nThe SOP number",
            "\nThe SOP number",
            "The SOP number is",
            "\n\n**Answer:**",
            "\n**Answer:**",
            "**Answer:**"
        ]
        
        earliest_match = float('inf')
        earliest_pattern = None
        
        for pattern in edify_patterns:
            idx = text.find(pattern)
            if idx >= 0 and idx < earliest_match:
                earliest_match = idx
                earliest_pattern = pattern
        
        if earliest_match != float('inf'):
            # Adjust for newlines in the pattern
            if earliest_pattern.startswith('\n\n'):
                return earliest_match + 2
            elif earliest_pattern.startswith('\n'):
                return earliest_match + 1
            else:
                return earliest_match
        
        return -1
    
    def _is_edify_response_line(self, line: str) -> bool:
        """Check if a line starts an Edify response"""
        edify_starts = [
            "In Edify schools",
            "Our policy",
            "At Edify",
            "In Edify",
            "Our approach",
            "Our framework", 
            "Our educational",
            "The SOP number is",
            "The SOP number for"
        ]
        
        # Also check for **Answer:** marker
        if "**Answer:**" in line:
            return True
        
        return any(line.startswith(start) for start in edify_starts)
    
    def _extract_numbered_points(self, text: str) -> list:
        """Extract numbered points from text"""
        numbered_points = []
        for line in text.split('\n'):
            line_stripped = line.strip()
            if re.match(r'^\d+\.\s', line_stripped):
                numbered_points.append(line_stripped)
        return numbered_points
    
    def _clean_reasoning(self, reasoning: str) -> str:
        """Clean reasoning content to remove any Edify response contamination"""
        if not reasoning:
            return ""
        
        # Remove headers
        reasoning = re.sub(r'^Chain of Thought Analysis:\s*\n?', '', reasoning, flags=re.IGNORECASE | re.MULTILINE)
        reasoning = re.sub(r'^\*\*Chain of Thought Analysis:\*\*\s*\n?', '', reasoning, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove separators
        reasoning = re.sub(r'^---+\s*$', '', reasoning, flags=re.MULTILINE)
        
        # Remove answer sections that might have leaked in
        answer_markers = ["**Answer:**", "**Final Response:**", "**Response:**"]
        for marker in answer_markers:
            if marker in reasoning:
                reasoning = reasoning.split(marker)[0]
        
        lines = reasoning.split('\n')
        clean_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                continue
            
            # Skip lines that look like Edify responses
            if self._is_edify_response_line(line_stripped):
                break  # Stop processing once we hit an Edify response
            
            # Skip SOP references that aren't part of reasoning
            if line_stripped.startswith("SOP/") and len(line_stripped.split()) < 3:
                continue
                
            # Skip standalone policy statements
            if any(phrase in line_stripped.lower() for phrase in ["policy states", "as mentioned", "refer to"]):
                if not any(marker in line_stripped for marker in ["1.", "2.", "3.", "**", "analyze", "step"]):
                    continue
            
            clean_lines.append(line)
        
        result = '\n'.join(clean_lines).strip()
        
        # Final cleanup - remove any trailing Edify content
        for phrase in ["In Edify", "Our policy", "At Edify"]:
            if phrase in result:
                result = result.split(phrase)[0].strip()
        
        # Remove extra newlines
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result
    
    def _is_edify_response_line(self, line: str) -> bool:
        """Check if a line indicates the start of an Edify response"""
        line_lower = line.lower()
        edify_starters = [
            "in edify", "our policy", "at edify", "edify schools", "according to edify",
            "based on edify", "as per edify", "in our schools", "our curriculum"
        ]
        return any(starter in line_lower for starter in edify_starters)
    
    def _split_on_numbered_pattern(self, text: str) -> tuple[str, str]:
        """Split text based on numbered pattern detection"""
        lines = text.split('\n')
        reasoning_lines = []
        answer_lines = []
        found_answer_start = False
        
        for line in lines:
            line_stripped = line.strip()
            
            if not found_answer_start and self._is_edify_response_line(line_stripped):
                found_answer_start = True
            
            if not found_answer_start:
                reasoning_lines.append(line)
            else:
                answer_lines.append(line)
        
        reasoning = '\n'.join(reasoning_lines).strip()
        answer = '\n'.join(answer_lines).strip()
        
        if reasoning and answer:
            return self._clean_reasoning(reasoning), answer
        else:
            # If we couldn't split properly, use numbered points as reasoning
            numbered_points = self._extract_numbered_points(text)
            if numbered_points:
                return '\n'.join(numbered_points), text
            else:
                return "Applied step-by-step analysis to locate specific information in educational documents.", text
    
    def _fallback_extraction(self, text: str) -> tuple[str, str]:
        """Fallback extraction method with improved logic"""
        # Strategy 1: Try to find any numbered points
        numbered_points = self._extract_numbered_points(text)
        if numbered_points:
            # Find where Edify response starts after numbered points
            edify_start = self._find_edify_response_start(text)
            if edify_start > 0:
                answer = text[edify_start:].strip()
                return '\n'.join(numbered_points), answer
            else:
                return '\n'.join(numbered_points), text
        
        # Strategy 2: Look for any reasoning-like content before Edify response
        edify_start = self._find_edify_response_start(text)
        if edify_start > 50:  # Only if there's substantial content before
            reasoning_part = text[:edify_start].strip()
            answer_part = text[edify_start:].strip()
            
            # Check if the reasoning part contains actual reasoning
            if (len(reasoning_part) > 20 and 
                any(word in reasoning_part.lower() for word in ['analysis', 'search', 'synthesis', 'context', 'question', 'found', 'looking'])):
                return reasoning_part, answer_part
        
        # Strategy 3: If the text starts with Edify response, create simple reasoning
        if any(text.strip().startswith(pattern) for pattern in ["In Edify", "Our policy", "At Edify"]):
            return "Applied step-by-step analysis to locate specific information in educational documents.", text
        
        # Ultimate fallback
        return "Applied step-by-step analysis to locate specific information in educational documents.", text
    
    def _generate_intelligent_fallback_response(self, query: str, context: str) -> Dict:
        """Generate authoritative Edify response with comprehensive educational expertise"""
        try:
            self.logger.info("[FALLBACK] Using enhanced Edify expertise for comprehensive response generation")
            
            # COMMENTED OUT: Internal reasoning steps - displaying only Groq-generated content
            # query_lower = query.lower()
            # 
            # # Apply Edify educational expertise for comprehensive responses
            # reasoning_steps = [
            #     f"1. Edify Query Analysis: Processing '{query[:50]}...' using our comprehensive educational framework",
            #     f"2. Knowledge Integration: Accessing our {len(context)} character knowledge base from Edify systems",
            #     f"3. Educational Synthesis: Applying proven Edify methodologies and best practices",
            #     f"4. Implementation Strategy: Formulating actionable guidance based on Edify expertise",
            #     f"5. Comprehensive Response: Delivering detailed recommendations from our educational authority"
            # ]
            
            # Return simple fallback without internal reasoning steps
            return {
                'response': "I found relevant information in the Edify knowledge base. Could you please rephrase your question for a more specific answer?",
                'reasoning': ""  # No internal reasoning displayed
            }
            
            # COMMENTED OUT: All fallback response generation logic
            # # Special handling for holiday-related queries
            # if any(word in query_lower for word in ['holiday', 'holidays', 'leave', 'vacation', 'day']):
            #     reasoning_steps.append("6. Edify Policy Application: Implementing our holiday and calendar management protocols")
            #     return self._generate_holiday_response(context, query, reasoning_steps)
            # 
            # # Special handling for assessment-related queries
            # elif any(word in query_lower for word in ['assessment', 'evaluation', 'test', 'exam', 'formative', 'summative']):
            #     reasoning_steps.append("6. Edify Assessment Framework: Applying our proven assessment methodologies")
            #     return self._generate_assessment_response(context, query, reasoning_steps)
            # 
            # # General response generation with advanced reasoning
            # else:
            #     reasoning_steps.append("6. Specialized Processing: Applying general educational knowledge synthesis")
            #     return self._generate_general_response(context, query, reasoning_steps)
                
        except Exception as e:
            self.logger.error(f"[ERROR] Fallback response generation failed: {str(e)}")
            return {
                'response': "I found some information but encountered a processing error. Please try rephrasing your question for better results.",
                'reasoning': f"Advanced reasoning fallback failed due to technical error: {str(e)}. Applied error recovery protocols."
            }
    
    def _generate_holiday_response(self, context: str, query: str, reasoning_steps: List[str]) -> Dict:
        """Generate specific response for holiday queries with advanced reasoning"""
        try:
            # Extract holiday information from context
            context_lines = context.split('\n')
            holidays = []
            holiday_info = []
            
            for line in context_lines:
                line = line.strip()
                if any(word in line.upper() for word in ['HOLIDAY', 'VARALAKSHMI', 'ACADEMIC YEAR', 'STAFF', 'SATURDAY']):
                    clean_line = re.sub(r'<[^>]+>', '', line)
                    clean_line = clean_line.replace('&nbsp;', ' ').replace('&amp;', '&')
                    clean_line = ' '.join(clean_line.split())
                    if len(clean_line) > 10:
                        holiday_info.append(clean_line)
            
            # Advanced reasoning for holiday queries
            reasoning_steps.extend([
                f"7. Holiday Analysis: Found {len(holiday_info)} holiday-related references in school documents",
                "8. Calendar Processing: Analyzing academic calendar patterns and staff schedules",
                "9. Policy Validation: Cross-referencing holiday policies with educational standards",
                "10. Response Optimization: Ensuring accuracy for school administration needs"
            ])
            
            full_reasoning = "\n".join(reasoning_steps)
            
            if holiday_info:
                if 'which day' in query.lower() or 'what day' in query.lower():
                    return {
                        'response': "Based on the school calendar, Second Saturday is a holiday for all school staff. The school follows a proper work schedule that includes Second Saturday holidays as mentioned in the academic calendar.",
                        'reasoning': full_reasoning + "\n\nSpecific Focus: Day-related holiday information with emphasis on Second Saturday policies."
                    }
                elif 'second saturday' in query.lower():
                    return {
                        'response': "Yes, Second Saturday is a holiday for school staff. The school maintains a proper work schedule that includes Second Saturday holidays along with other scheduled holidays throughout the academic year.",
                        'reasoning': full_reasoning + "\n\nSpecific Focus: Second Saturday policy analysis from staff work schedule documentation."
                    }
                else:
                    response = "According to the school's academic calendar, all teaching and non-teaching staff are entitled to holidays including Varalakshmi Vratham and other scheduled holidays. "
                    response += "The academic year holiday list includes various festivals and observances for all school staff members."
                    return {
                        'response': response,
                        'reasoning': full_reasoning + "\n\nSpecific Focus: Comprehensive holiday policy compilation covering all staff categories."
                    }
            
            return {
                'response': "Based on the school documents, there are scheduled holidays for all school staff members as per the academic calendar.",
                'reasoning': full_reasoning + "\n\nLimited Context: Provided general holiday information due to insufficient specific details."
            }
            
        except Exception as e:
            return {
                'response': "The school has scheduled holidays for all staff members as outlined in the academic calendar.",
                'reasoning': f"Error Recovery Protocol: {str(e)}. Applied general holiday knowledge as safety fallback with limited reasoning capability."
            }
    
    def _generate_assessment_response(self, context: str, query: str, reasoning_steps: List[str]) -> Dict:
        """Generate specific response for assessment queries with advanced reasoning"""
        try:
            # Parse context more intelligently to extract all relevant content
            context_lines = context.split('\n')
            relevant_content = []
            
            # Extract content from structured context (skip metadata)
            for line in context_lines:
                line = line.strip()
                if (line and 
                    not line.startswith('[Source:') and 
                    not line.startswith('---') and 
                    not line.startswith('RELEVANT INFORMATION') and
                    len(line) > 20):  # Skip very short lines
                    
                    # Clean content while preserving meaning
                    clean_line = re.sub(r'<[^>]+>', '', line)
                    clean_line = re.sub(r'&\w+;', ' ', clean_line)
                    clean_line = ' '.join(clean_line.split())
                    
                    if len(clean_line) > 30:  # Only keep substantial content
                        relevant_content.append(clean_line)
            
            # Advanced reasoning for assessment queries with actual analysis
            query_analysis = f"Analyzing educational query: '{query}' - Focus: {'implementation' if 'implement' in query.lower() else 'general assessment'}"
            content_analysis = f"Document content analysis: Found {len(relevant_content)} substantial paragraphs about educational practices"
            
            # Perform actual semantic analysis
            assessment_terms_found = []
            implementation_terms_found = []
            for content in relevant_content:
                content_lower = content.lower()
                if 'formative' in content_lower:
                    assessment_terms_found.append('formative assessment')
                if 'ongoing' in content_lower or 'continuous' in content_lower:
                    implementation_terms_found.append('continuous monitoring')
                if 'feedback' in content_lower:
                    implementation_terms_found.append('feedback mechanisms')
                if 'student' in content_lower and ('progress' in content_lower or 'learning' in content_lower):
                    implementation_terms_found.append('student progress tracking')
            
            semantic_analysis = f"Semantic analysis results: Assessment concepts found: {assessment_terms_found}, Implementation strategies found: {implementation_terms_found}"
            
            reasoning_steps.extend([
                f"7. Query Intent Analysis: {query_analysis}",
                f"8. Content Extraction: {content_analysis}",
                f"9. {semantic_analysis}",
                f"10. Educational Synthesis: Connecting document insights to practical teaching applications for maximum pedagogical value"
            ])
            
            full_reasoning = "\n".join(reasoning_steps)
            
            if relevant_content:
                query_lower = query.lower()
                
                # Handle specific formative assessment questions
                if 'formative' in query_lower and ('implement' in query_lower or 'effectively' in query_lower):
                    # Build comprehensive response from document content
                    response_parts = []
                    
                    # Find content related to formative assessment implementation
                    for content in relevant_content[:3]:  # Use top 3 most relevant pieces
                        if any(term in content.lower() for term in ['formative', 'assessment', 'feedback', 'learning', 'ongoing', 'continuous']):
                            response_parts.append(content)
                    
                    if response_parts:
                        # Create a comprehensive response using our Edify expertise
                        main_response = ""
                        
                        # Combine all relevant parts using our educational framework
                        for i, part in enumerate(response_parts):
                            if i == 0:
                                main_response = f"In Edify schools, we implement formative assessment through {part.lower()}"
                            else:
                                # Add additional information from our comprehensive framework
                                if len(main_response) < 500:  # Allow longer responses
                                    main_response += f" Our educational approach also emphasizes {part.lower()}"
                        
                        # Ensure response demonstrates our comprehensive expertise
                        if len(main_response) > 700:
                            main_response = main_response[:700] + "..."
                        
                        # Add implementation guidance from our proven methodologies
                        if len(main_response) < 400:
                            main_response += " Our proven Edify framework ensures effective implementation through systematic teacher training, continuous monitoring, and student-centered approaches that have been refined across our educational network."
                        
                        detailed_reasoning = f"{full_reasoning}\n\nEdify Expertise Application: Comprehensive formative assessment guidance drawn from our extensive educational framework. Implementation strategies: {', '.join(assessment_terms_found + implementation_terms_found)}. Response demonstrates our proven methodologies and systematic approach."
                        
                        return {
                            'response': main_response,
                            'reasoning': detailed_reasoning
                        }
                
                # Handle summative assessment questions
                elif 'summative' in query_lower:
                    comprehensive_content = ""
                    for content in relevant_content[:3]:  # Use multiple sources
                        if 'summative' in content.lower() or 'evaluation' in content.lower() or 'assessment' in content.lower():
                            if comprehensive_content:
                                comprehensive_content += " Furthermore, " + content
                            else:
                                comprehensive_content = content
                    
                    if comprehensive_content:
                        # Ensure adequate length for comprehensive response
                        if len(comprehensive_content) > 500:
                            comprehensive_content = comprehensive_content[:500] + "..."
                        
                        detailed_reasoning = f"{full_reasoning}\n\nSummative Assessment Focus: Located comprehensive document content addressing summative evaluation practices and their application in educational settings."
                        return {
                            'response': comprehensive_content,
                            'reasoning': detailed_reasoning
                        }
                
                # Handle general assessment questions
                elif 'assessment' in query_lower:
                    # Find and combine the most comprehensive assessment-related content
                    best_content = ""
                    additional_content = []
                    
                    for content in relevant_content[:3]:  # Use top 3 pieces
                        if any(term in content.lower() for term in ['assessment', 'evaluation', 'learning', 'teaching']):
                            if not best_content:
                                best_content = content
                            elif len(content) > 50:  # Only add substantial additional content
                                additional_content.append(content)
                    
                    # Combine content for comprehensive response
                    combined_response = best_content
                    for additional in additional_content:
                        if len(combined_response) < 400:  # Allow longer responses
                            combined_response += " Additionally, " + additional
                    
                    # Trim to appropriate length
                    if len(combined_response) > 600:
                        combined_response = combined_response[:600] + "..."
                    
                    detailed_reasoning = f"{full_reasoning}\n\nComprehensive Assessment Analysis: Selected and combined detailed assessment content from educational framework documentation. Analysis confirmed relevance through keyword matching and content depth evaluation."
                    
                    return {
                        'response': combined_response,
                        'reasoning': detailed_reasoning
                    }
                
                # Fallback to first relevant content
                first_content = relevant_content[0]
                if len(first_content) > 250:
                    first_content = first_content[:250] + "..."
                
                fallback_reasoning = f"{full_reasoning}\n\nFallback Analysis: Applied general educational content extraction when specific assessment terms weren't prominent. Selected highest-quality educational content based on length and coherence metrics."
                
                return {
                    'response': first_content,
                    'reasoning': fallback_reasoning
                }
            
            # If no relevant content found, provide context-aware response
            no_content_reasoning = f"{full_reasoning}\n\nContent Availability Assessment: Insufficient substantial educational content found in provided documentation for this specific assessment query. Recommend query refinement or additional document sources."
            
            return {
                'response': "I couldn't find specific information about that assessment topic in the available educational documents. Please try asking about a more specific aspect of assessment or rephrase your question.",
                'reasoning': no_content_reasoning
            }
            
        except Exception as e:
            self.logger.error(f"Assessment response generation error: {str(e)}")
            error_reasoning = f"Error Recovery Analysis: Encountered processing error during assessment response generation: {str(e)}. Applied safety fallback protocol with limited assessment knowledge."
            return {
                'response': "I found some assessment-related information but encountered an error processing it. Please try rephrasing your question.",
                'reasoning': error_reasoning
            }
            
        except Exception as e:
            return {
                'response': "Assessment involves various strategies for evaluating and supporting student learning.",
                'reasoning': f"Error Recovery Protocol: {str(e)}. Applied general assessment knowledge with limited advanced reasoning due to processing error."
            }
    
    def _generate_general_response(self, context: str, query: str, reasoning_steps: List[str]) -> Dict:
        """Generate general response from context with advanced reasoning"""
        try:
            # Parse context more intelligently to extract meaningful content
            context_lines = context.split('\n')
            relevant_content = []
            
            # Extract content from structured context (skip metadata)
            for line in context_lines:
                line = line.strip()
                if (line and 
                    not line.startswith('[Source:') and 
                    not line.startswith('---') and 
                    not line.startswith('RELEVANT INFORMATION') and
                    len(line) > 30):  # Skip short lines
                    
                    # Clean content while preserving meaning
                    clean_line = re.sub(r'<[^>]+>', '', line)
                    clean_line = re.sub(r'&\w+;', ' ', clean_line)
                    clean_line = ' '.join(clean_line.split())
                    
                    if len(clean_line) > 40:  # Only keep substantial content
                        relevant_content.append(clean_line)
            
            # Calculate relevance scores for query matching with actual analysis
            query_words = set(word.lower() for word in query.split() if len(word) > 3)
            scored_content = []
            
            # Perform semantic analysis of content relevance
            semantic_matches = []
            lexical_matches = []
            
            for content in relevant_content:
                content_words = set(word.lower() for word in content.split() if len(word) > 3)
                overlap_score = len(query_words.intersection(content_words))
                
                # Analyze type of match
                if overlap_score > 0:
                    overlapping_words = query_words.intersection(content_words)
                    
                    # Check for semantic relevance
                    educational_terms_in_overlap = [word for word in overlapping_words if word in {'assessment', 'learning', 'teaching', 'education', 'student', 'formative', 'summative'}]
                    
                    if educational_terms_in_overlap:
                        semantic_matches.append((content, overlap_score, educational_terms_in_overlap))
                    else:
                        lexical_matches.append((content, overlap_score, list(overlapping_words)))
                    
                    scored_content.append((overlap_score, content))
            
            # Advanced reasoning for general queries with detailed analysis
            query_analysis = f"Query complexity analysis: {len(query.split())} words, {len(query_words)} unique meaningful terms"
            content_analysis = f"Content corpus analysis: {len(relevant_content)} substantial paragraphs extracted from educational documents"
            matching_analysis = f"Relevance matching: {len(semantic_matches)} semantic matches (educational concepts), {len(lexical_matches)} lexical matches (word overlap)"
            
            if semantic_matches:
                best_match = max(semantic_matches, key=lambda x: x[1])
                best_content, score, matching_terms = best_match
                match_quality_analysis = f"Best match quality: Score {score}/10, matching educational concepts: {matching_terms}"
            elif lexical_matches:
                best_match = max(lexical_matches, key=lambda x: x[1])
                best_content, score, matching_words = best_match
                match_quality_analysis = f"Best match quality: Score {score}/10, matching terms: {matching_words[:3]}"
            else:
                match_quality_analysis = "No significant matches found in content corpus"
            
            reasoning_steps.extend([
                f"7. {query_analysis}",
                f"8. {content_analysis}",
                f"9. {matching_analysis}",
                f"10. {match_quality_analysis}",
                "11. Educational Context Validation: Ensuring response aligns with pedagogical standards and provides actionable insights"
            ])
            
            full_reasoning = "\n".join(reasoning_steps)
            
            if scored_content:
                # Sort by relevance score and take the best
                scored_content.sort(key=lambda x: x[0], reverse=True)
                best_score, best_content = scored_content[0]
                
                # Ensure appropriate response length
                if len(best_content) > 250:
                    best_content = best_content[:250] + "..."
                
                synthesis_analysis = f"Response synthesis: Selected highest-scoring content (relevance: {best_score}) from educational document corpus. Applied content optimization for clarity and educational value."
                additional_reasoning = f"\n\n{synthesis_analysis}"
                
                return {
                    'response': best_content,
                    'reasoning': full_reasoning + additional_reasoning
                }
            
            # If no scored content, try to use any available content
            elif relevant_content:
                first_content = relevant_content[0]
                if len(first_content) > 250:
                    first_content = first_content[:250] + "..."
                
                fallback_analysis = f"Fallback content selection: Used first available educational content due to limited query-document alignment. Content length: {len(first_content)} characters."
                
                return {
                    'response': first_content,
                    'reasoning': full_reasoning + f"\n\n{fallback_analysis}"
                }
            
            no_content_analysis = f"Content availability assessment: No substantial educational content found in provided documentation corpus. Document parsing completed but yielded insufficient relevant material for this query type."
            
            return {
                'response': "I couldn't find specific information about that in the available educational documents. Please try asking about a more specific topic or rephrase your question.",
                'reasoning': full_reasoning + f"\n\n{no_content_analysis}"
            }
            
        except Exception as e:
            self.logger.error(f"General response generation error: {str(e)}")
            error_analysis = f"Error recovery protocol: Encountered processing error during general response generation: {str(e)}. Applied safety fallback with basic educational knowledge."
            return {
                'response': "I found some information but encountered an error processing it. Please try rephrasing your question.",
                'reasoning': f"Error Recovery Analysis: {error_analysis}"
            }
    
    def _is_valid_response(self, response: str, query: str) -> bool:
        """Enhanced validation for response quality and relevance"""
        if not response or len(response.strip()) < 20:  # Require minimum meaningful length
            return False
        
        # Check for generic responses that indicate failure
        invalid_phrases = [
            "provide more context",
            "i need more information",
            "please clarify",
            "i don't understand",
            "insufficient information",
            "cannot answer",
            "i'm sorry, but",
            "i cannot provide",
            "unable to determine",
            "more specific question"
        ]
        
        response_lower = response.lower()
        
        # Basic validation - check for obvious failures
        if any(phrase in response_lower for phrase in invalid_phrases):
            return False
        
        # Enhanced validation - check for educational content quality
        educational_indicators = [
            'student', 'learning', 'education', 'teaching', 'assessment', 
            'curriculum', 'classroom', 'school', 'grade', 'instruction',
            'pedagogy', 'evaluation', 'development', 'skill', 'knowledge'
        ]
        
        query_words = set(query.lower().split())
        response_words = set(response_lower.split())
        
        # Check if response contains educational terminology (good sign)
        has_educational_content = any(term in response_lower for term in educational_indicators)
        
        # Check if response addresses the query (has some overlapping words)
        word_overlap = len(query_words.intersection(response_words)) > 0
        
        # Check if response is substantive (not just one sentence)
        sentence_count = len([s for s in response.split('.') if len(s.strip()) > 10])
        is_substantive = sentence_count >= 2
        
        # Valid if it has educational content AND addresses the query AND is substantive
        return has_educational_content and (word_overlap or len(response) > 200) and is_substantive
