"""AI processing API endpoints for FastAPI Email Helper API.

This module provides REST API endpoints for email classification, action item extraction,
and summarization using existing AI processor functionality.
"""

import time
import json
import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse

from backend.models.ai_models import (
    EmailClassificationRequest, EmailClassificationResponse,
    ActionItemRequest, ActionItemResponse,
    SummaryRequest, SummaryResponse,
    AvailableTemplatesResponse
)
from backend.core.dependencies import get_ai_service

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
    ai_service = Depends(get_ai_service)
):
    """Classify email content using AI.

    This endpoint uses the existing email classification logic to categorize emails
    into predefined categories with confidence scores and explanations.
    """
    import logging
    import traceback
    logger = logging.getLogger(__name__)

    try:
        start_time = time.time()

        # Build email content from components
        email_text = f"Subject: {request.subject}\nFrom: {request.sender}\n\n{request.content}"
        if request.context:
            email_text += f"\n\nContext: {request.context}"

        logger.info(f"Classifying email: {request.subject[:50]}...")

        # Classify the email
        result = await ai_service.classify_email(
            email_content=email_text,
            context=request.context
        )

        logger.info(f"Classification result: {result.get('category')}")

        # Handle potential errors in the result BEFORE making additional calls
        if "error" in result:
            logger.error(f"Classification error: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI classification failed: {result['error']}"
            )

        # Also generate one-line summary
        logger.info("Generating summary...")
        summary_result = await ai_service.generate_summary(
            email_content=email_text,
            summary_type="brief"
        )

        logger.info(f"Summary generated: {len(summary_result.get('summary', ''))} chars")
        logger.info(f"Summary generated: {len(summary_result.get('summary', ''))} chars")

        processing_time = time.time() - start_time

        response = EmailClassificationResponse(
            ai_category=result.get('category', 'work_relevant'),  # Standardized field name
            category=result.get('category', 'work_relevant'),  # Backward compatibility
            confidence=result.get('confidence'),  # No fake default - None if AI didn't provide one
            reasoning=result.get('reasoning', 'Classification completed'),
            alternative_categories=result.get('alternatives', []),
            processing_time=processing_time,
            one_line_summary=summary_result.get('summary', '')  # Include one-line summary
        )

        logger.info(f"Classification complete in {processing_time:.2f}s")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Classification failed with exception: {str(e)}")
        logger.error(traceback.format_exc())
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
    ai_service = Depends(get_ai_service)
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
    ai_service = Depends(get_ai_service)
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
    ai_service = Depends(get_ai_service)
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
    ai_service = Depends(get_ai_service)
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


@router.post(
    "/classify-batch-stream",
    summary="Classify emails with streaming progress",
    description="Classify multiple emails and stream progress updates in real-time"
)
async def classify_batch_stream(
    email_ids: List[str],
    ai_service = Depends(get_ai_service)
):
    """Stream classification progress for batch email processing.

    This endpoint classifies multiple emails and streams progress updates
    as Server-Sent Events (SSE) for real-time UI updates.
    """
    from backend.core.dependencies import get_email_provider

    async def generate_progress():
        try:
            email_provider = get_email_provider()
            total = len(email_ids)

            # Send initial progress
            yield f"data: {json.dumps({'current': 0, 'total': total, 'status': 'starting', 'message': 'Starting classification...'})}\n\n"

            for idx, email_id in enumerate(email_ids, 1):
                try:
                    # Fetch email data
                    email = email_provider.get_email_by_id(email_id)

                    if not email:
                        yield f"data: {json.dumps({'current': idx, 'total': total, 'status': 'error', 'email_id': email_id, 'message': f'Email {email_id} not found'})}\n\n"
                        continue

                    # Send processing update
                    yield f"data: {json.dumps({'current': idx, 'total': total, 'status': 'processing', 'email_id': email_id, 'message': f'Classifying email {idx}/{total}...'})}\n\n"

                    # Build email content (use standardized field names with backward compat)
                    email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{email.get('content', email.get('body', ''))}"

                    # Classify email
                    start_time = time.time()
                    result = await ai_service.classify_email(
                        email_content=email_text,
                        context=None
                    )
                    processing_time = time.time() - start_time

                    # Send success update with classification result
                    # Use standardized field name with backward compatibility
                    response_data = {
                        'current': idx,
                        'total': total,
                        'status': 'success',
                        'email_id': email_id,
                        'ai_category': result.get('category', 'work_relevant'),  # Standardized
                        'category': result.get('category', 'work_relevant'),  # Backward compatibility
                        'processing_time': processing_time,
                        'message': f'Classified email {idx}/{total}'
                    }
                    if result.get('confidence') is not None:
                        response_data['confidence'] = result.get('confidence')

                    yield f"data: {json.dumps(response_data)}\n\n"

                    # Small delay to prevent overwhelming the AI service
                    await asyncio.sleep(1)

                except Exception as e:
                    yield f"data: {json.dumps({'current': idx, 'total': total, 'status': 'error', 'email_id': email_id, 'error': str(e), 'message': f'Error classifying email {idx}/{total}'})}\n\n"

            # Send completion
            yield f"data: {json.dumps({'current': total, 'total': total, 'status': 'complete', 'message': 'Classification complete'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'error': str(e), 'message': 'Classification failed'})}\n\n"

    return StreamingResponse(
        generate_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering for Nginx
        }
    )
