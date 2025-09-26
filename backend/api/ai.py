"""AI processing API endpoints for FastAPI Email Helper API.

This module provides REST API endpoints for email classification, action item extraction,
and summarization using existing AI processor functionality.
"""

import time
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from backend.models.ai_models import (
    EmailClassificationRequest, EmailClassificationResponse,
    ActionItemRequest, ActionItemResponse,
    SummaryRequest, SummaryResponse,
    AIErrorResponse, AvailableTemplatesResponse
)
from backend.services.ai_service import AIService, get_ai_service
from backend.api.auth import get_current_user
from backend.models.user import User

# Create router with prefix and tags
router = APIRouter(prefix="/ai", tags=["ai"])


@router.post(
    "/classify",
    response_model=EmailClassificationResponse,
    summary="Classify email content",
    description="Classify email content using AI to determine category, confidence, and reasoning"
)
async def classify_email(
    request: EmailClassificationRequest,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service)
):
    """Classify email content using AI.
    
    This endpoint uses the existing email classification logic to categorize emails
    into predefined categories with confidence scores and explanations.
    """
    try:
        start_time = time.time()
        
        result = await ai_service.classify_email_async(
            subject=request.subject,
            content=request.content,
            sender=request.sender,
            context=request.context
        )
        
        processing_time = time.time() - start_time
        
        # Handle potential errors in the result
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI classification failed: {result['error']}"
            )
        
        return EmailClassificationResponse(
            category=result.get('category', 'work_relevant'),
            confidence=result.get('confidence', 0.5),
            reasoning=result.get('reasoning', 'Classification completed'),
            alternative_categories=result.get('alternatives', []),
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI processing failed: {str(e)}"
        )


@router.post(
    "/action-items",
    response_model=ActionItemResponse,
    summary="Extract action items from email",
    description="Extract action items, deadlines, and urgency from email content"
)
async def extract_action_items(
    request: ActionItemRequest,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service)
):
    """Extract action items from email content.
    
    This endpoint analyzes email content to identify action items, deadlines,
    urgency levels, and relevant links.
    """
    try:
        result = await ai_service.extract_action_items(
            email_content=request.email_content,
            context=request.context
        )
        
        # Handle potential errors in the result
        if "error" in result and not result.get("action_items"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Action item extraction failed: {result['error']}"
            )
        
        return ActionItemResponse(
            action_items=result.get('action_items', []),
            urgency=result.get('urgency', 'unknown'),
            deadline=result.get('deadline'),
            confidence=result.get('confidence', 0.0),
            due_date=result.get('due_date'),
            action_required=result.get('action_required'),
            explanation=result.get('explanation'),
            relevance=result.get('relevance'),
            links=result.get('links', [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Action item extraction failed: {str(e)}"
        )


@router.post(
    "/summarize",
    response_model=SummaryResponse,
    summary="Generate email summary",
    description="Generate concise or detailed summaries of email content with key points"
)
async def summarize_email(
    request: SummaryRequest,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service)
):
    """Generate email summary.
    
    This endpoint creates brief or detailed summaries of email content,
    extracting key points and providing confidence scores.
    """
    try:
        start_time = time.time()
        
        result = await ai_service.generate_summary(
            email_content=request.email_content,
            summary_type=request.summary_type
        )
        
        processing_time = time.time() - start_time
        
        # Handle potential errors in the result
        if "error" in result and result.get("confidence", 0) == 0.0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Summarization failed: {result['error']}"
            )
        
        return SummaryResponse(
            summary=result.get('summary', 'Unable to generate summary'),
            key_points=result.get('key_points', []),
            confidence=result.get('confidence', 0.0),
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {str(e)}"
        )


@router.get(
    "/templates",
    response_model=AvailableTemplatesResponse,
    summary="Get available prompt templates",
    description="Retrieve list of available AI prompt templates and their descriptions"
)
async def get_available_templates(
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service)
):
    """Get available prompt templates.
    
    This endpoint returns a list of available prompty templates that can be used
    for AI processing, along with their descriptions.
    """
    try:
        result = await ai_service.get_available_templates()
        
        return AvailableTemplatesResponse(
            templates=result.get('templates', []),
            descriptions=result.get('descriptions', {})
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve templates: {str(e)}"
        )


# Health check endpoint for AI services
@router.get(
    "/health",
    summary="AI service health check",
    description="Check if AI processing services are available and configured"
)
async def ai_health_check(
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service)
):
    """Check AI service health.
    
    This endpoint verifies that AI services are properly configured and accessible.
    """
    try:
        # Try to initialize AI service
        ai_service._ensure_initialized()
        
        # Get available templates as a basic connectivity test
        templates_result = await ai_service.get_available_templates()
        template_count = len(templates_result.get('templates', []))
        
        return {
            "status": "healthy",
            "ai_processor_available": ai_service._initialized,
            "templates_available": template_count,
            "message": f"AI services are operational with {template_count} templates available"
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "ai_processor_available": False,
                "templates_available": 0,
                "error": str(e),
                "message": "AI services are not available"
            }
        )