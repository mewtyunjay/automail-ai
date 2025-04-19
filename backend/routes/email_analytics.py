from fastapi import APIRouter, Query, HTTPException, Response
from services.email_analytics import generate_email_analytics
from typing import Optional, Dict, Any

router = APIRouter(tags=["Email Analytics"])

@router.get("/email-analytics")
async def get_email_analytics(
    response: Response,
    max_emails: Optional[int] = Query(20, description="Maximum number of recent emails to analyze")
) -> Dict[str, Any]:
    """
    Generate comprehensive analytics from recent emails.
    
    This endpoint:
    1. Processes recent emails to extract:
       - Financial transactions and summary
       - Upcoming meetings and appointments
       - Todo items and action items
       - Emails requiring replies
    2. Returns structured analytics data for frontend display
    
    Returns:
        A dictionary with comprehensive email analytics data
    """
    # Add CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    
    try:
        result = generate_email_analytics(max_emails=max_emails)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))
            
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating email analytics: {str(e)}")
