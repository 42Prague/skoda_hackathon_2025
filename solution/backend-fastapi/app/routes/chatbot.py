from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
import uuid
import time
from typing import Optional
from datetime import datetime

from app.core.vector_store import search_courses

router = APIRouter(prefix="/api", tags=["chatbot"])

# Initialize LangChain OpenAI client
llm = None

def get_llm():
    global llm
    if llm is None:
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        # Use Open WebUI as proxy if OPENAI_API_BASE_URL is set
        base_url = os.getenv("OPENAI_API_BASE_URL")
        
        # If routing through Open WebUI, use Open WebUI API token
        # Otherwise, use OpenAI API key directly
        if base_url and "open-webui" in base_url:
            # Use Open WebUI API token for authentication
            api_key = os.getenv("OPEN_WEBUI_API_KEY") or os.getenv("OPENAI_API_KEY")
        else:
            # Use OpenAI API key directly
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("API key environment variable is not set")
        
        llm_kwargs = {
            "model": model_name,
            "temperature": 0.7,
            "max_tokens": 2000,  # Increased from 500 to allow longer, more detailed responses
            "api_key": api_key,
            "timeout": 180,  # 3 minutes timeout for LLM calls
            "max_retries": 2  # Retry up to 2 times on failure
        }
        
        # If OPENAI_API_BASE_URL is set, route through Open WebUI
        if base_url:
            llm_kwargs["base_url"] = base_url
        
        llm = ChatOpenAI(**llm_kwargs)
    return llm


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    use_context: bool = Field(default=True, description="Use RAG context from similar messages")


class ChatResponse(BaseModel):
    reply: str
    message_id: str
    context_used: bool = False


class AnalyticsResponse(BaseModel):
    total_messages: int
    messages_by_day: list
    avg_response_time: float


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start_time = time.time()
    message_id = str(uuid.uuid4())
    user_id = request.user_id or "anonymous"
    session_id = request.session_id or str(uuid.uuid4())
    context_used = False 
    
    # Get model name for logging and error messages
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    try:
        # Validate API key
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key is not configured. Please set OPENAI_API_KEY environment variable."
            )
        
        # Log model being used (for debugging)
        if os.getenv("DEBUG_RAG", "false").lower() == "true":
            print(f"[DEBUG] Using model: {model_name}")
            print(f"[DEBUG] Request: {request.message.strip()[:100]}...")
            print(f"[DEBUG] Use context: {request.use_context}")



        # Get LLM instance
        chat_llm = get_llm()

        # Step 1: Extract desired job/role from natural language using LLM
        extraction_prompt = """Extract the desired targeted job title, role, or career path from the user's message. 
The user might be asking about courses to become a specific role, or asking what courses they need for a particular job.

Respond with ONLY the job title or role name. If no specific job is mentioned, respond with "NONE".

Examples:
- "I want to become a software engineer" → "Software Engineer"
- "What courses do I need for a project manager role?" → "Project Manager"
- "I'm interested in data science" → "Data Scientist"
- "Show me courses" → "NONE"

User message: {user_message}

Extracted job/role:"""

        try:
            extraction_messages = [
                SystemMessage(content="You are a job title extraction assistant. Extract only the job title or role name from the user's message. Respond with just the job title, or 'NONE' if no job is mentioned."),
                HumanMessage(content=extraction_prompt.format(user_message=request.message.strip()))
            ]
            extraction_response = await chat_llm.ainvoke(extraction_messages)
            extracted_job = extraction_response.content.strip() if hasattr(extraction_response, 'content') else str(extraction_response).strip()
            
            # Clean up the extracted job (remove quotes, extra text)
            if extracted_job.upper() == "NONE" or not extracted_job or len(extracted_job) < 2:
                extracted_job = None
            else:
                # Remove quotes and clean up
                extracted_job = extracted_job.strip('"\'')
                if extracted_job.upper() == "NONE":
                    extracted_job = None
        except Exception as e:
            print(f"[WARNING] Failed to extract job from message: {e}")
            extracted_job = None

        # Step 2: Search for relevant courses using RAG
        # Use extracted job if available, otherwise use the original message
        search_query = extracted_job if extracted_job else request.message.strip()
        
        if os.getenv("DEBUG_RAG", "false").lower() == "true":
            print(f"[DEBUG] Extracted job: {extracted_job}")
            print(f"[DEBUG] Search query for courses: {search_query}")
        
        # Search for courses
        course_results = search_courses(query=search_query, limit=10)
        
        if os.getenv("DEBUG_RAG", "false").lower() == "true":
            print(f"[DEBUG] Found {len(course_results)} courses")
        
        # Step 3: Build context from course results
        context_messages = []
        if course_results:
            context_used = True
            course_contexts = []
            for i, course in enumerate(course_results[:8]):  # Limit to top 8 courses
                metadata = course.get("metadata", {})
                title = metadata.get("title", "Untitled Course")
                description = metadata.get("description", "")
                provider = metadata.get("provider", "")
                university = metadata.get("university", "")
                course_level = metadata.get("course_level", "")
                duration = metadata.get("duration", "")
                skills = metadata.get("skills", [])
                url = metadata.get("url", "")
                
                # Format course information
                course_info = f"**{title}**"
                if provider:
                    course_info += f" ({provider}"
                    if university:
                        course_info += f" - {university}"
                    course_info += ")"
                if course_level:
                    course_info += f" - Level: {course_level}"
                if duration:
                    course_info += f" - Duration: {duration}"
                if description:
                    course_info += f"\n{description[:300]}..." if len(description) > 300 else f"\n{description}"
                if skills:
                    skills_str = ", ".join(skills[:5]) if isinstance(skills, list) else str(skills)
                    course_info += f"\nSkills: {skills_str}"
                if url:
                    course_info += f"\nURL: {url}"
                
                course_contexts.append(course_info)
            
            if course_contexts:
                context_content = f"""**RELEVANT COURSES** - Here are courses that match the user's career goals:

{chr(10).join([f"{i+1}. {course}" for i, course in enumerate(course_contexts)])}

**INSTRUCTIONS**: Present these courses to the user in a clear, organized format. Include course titles, providers, levels, durations, and key skills. Format using markdown with bullet points and bold text for course names."""
                context_messages.append(SystemMessage(content=context_content))

        # Step 4: Create response messages
        system_prompt = """You are a helpful career guidance assistant for Škoda Auto employees. Your role is to help employees find relevant training courses based on their career goals.

**INSTRUCTIONS**:
1. If courses are provided in the context, present them clearly and informatively
2. Use markdown formatting with bullet points, bold text, and clear structure
3. Include specific details: course titles, providers, levels, durations, skills, and URLs
4. Be encouraging and helpful
5. If no courses are found, suggest the user refine their search or ask about specific skills

**Formatting guidelines**:
- Use **bold** for course titles
- Use bullet points (-) for lists
- Use numbered lists (1., 2., 3.) for multiple courses
- Include all relevant details from the context
- Make it easy to scan and understand"""

        messages = [
            SystemMessage(content=system_prompt),
            *context_messages,
            HumanMessage(content=f"User question: {request.message.strip()}\n\nBased on the courses provided in the context above, help the user find relevant training courses. Present the information clearly and helpfully.")
        ]

        # Debug: Log message structure
        if os.getenv("DEBUG_RAG", "false").lower() == "true":
            print(f"[DEBUG] Total messages to LLM: {len(messages)}")
            print(f"[DEBUG] Context messages: {len(context_messages)}")
            if course_results:
                print(f"[DEBUG] Courses found: {len(course_results)}")

        # Get response from LangChain with error handling
        try:
            response = await chat_llm.ainvoke(messages)
            reply = response.content if hasattr(response, 'content') else str(response)
        except Exception as llm_error:
            error_msg = str(llm_error).lower()
            # Log the full error for debugging
            print(f"[ERROR] LLM call failed: {type(llm_error).__name__}: {str(llm_error)}")
            if "timeout" in error_msg or "timed out" in error_msg:
                raise HTTPException(
                    status_code=504,
                    detail=f"LLM request timed out. The model ({model_name}) took too long to respond. This can happen with complex queries or high load. Please try again with a simpler question."
                )
            elif "rate limit" in error_msg or "429" in error_msg:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please try again later."
                )
            elif "401" in error_msg or "unauthorized" in error_msg or "authentication" in error_msg:
                raise HTTPException(
                    status_code=401,
                    detail=f"Authentication failed with LLM service. Please check your API key configuration. Error: {str(llm_error)}"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error calling LLM ({model_name}): {str(llm_error)}"
                )

        if not reply:
            reply = "Sorry, I could not generate a response."

        # Generate a message ID for the response
        assistant_message_id = str(uuid.uuid4())

        return ChatResponse(
            reply=reply,
            message_id=assistant_message_id,
            context_used=context_used
        )

    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        error_msg = str(e).lower()
        # Log the full error for debugging
        print(f"[ERROR] Chat endpoint exception: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        
        if "api key" in error_msg or "401" in error_msg or "unauthorized" in error_msg:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid API key or authentication failed. Please check your OPENAI_API_KEY or OPEN_WEBUI_API_KEY environment variable. Error: {str(e)}"
            )
        elif "rate limit" in error_msg or "429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while processing your request: {str(e)}"
            )




@router.get("/courses/search")
async def search_courses_endpoint(
    query: str = Query(..., description="Search text"),
    limit: int = Query(5, ge=1, le=50),
    course_level: Optional[str] = None,
    provider: Optional[str] = None,
    university: Optional[str] = None,
    skill: Optional[str] = None
):
    """
    Search for course embeddings stored in Qdrant.
    Supports semantic search + metadata filtering.
    """
    try:
        # ---- 1) Build Qdrant metadata filter ----
        qdrant_filter = {"must": []}

        if skill:
            qdrant_filter["must"].append({
                "key": "skills",
                "match": {"value": skill}
            })

        # ---- 2) Search Qdrant (vector similarity) ----
        results = search_courses(
            query=query,
            limit=limit,
            metadata_filter=qdrant_filter if qdrant_filter["must"] else None
        )

        # ---- 3) Format output nicely ----
        output = []
        for doc in results:
            metadata = doc.get("metadata", {})
            output.append({
                "score": doc.get("score"),
                "course_id": metadata.get("course_id"),
                "title": metadata.get("title"),
                "description": metadata.get("description"),
                "provider": metadata.get("provider"),
                "university": metadata.get("university"),
                "course_level": metadata.get("course_level"),
                "duration": metadata.get("duration"),
                "certificate_type": metadata.get("certificate_type"),
                "skills": metadata.get("skills"),
                "image_url": metadata.get("image_url"),
                "url": metadata.get("url"),
            })

        return {
            "query": query,
            "count": len(output),
            "results": output
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Course search failed: {e}")

