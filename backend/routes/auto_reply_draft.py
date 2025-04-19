from fastapi import APIRouter, Query
from services.auto_reply_draft import process_emails
from typing import Optional

router = APIRouter(tags=["Auto Reply Draft"])

@router.post("/auto-reply/run")
async def run_auto_reply(max_emails: Optional[int] = Query(5, description="Maximum number of recent emails to process")):
    """
    Process recent emails and create auto-reply drafts for those that need replies.
    
    This endpoint:
    1. Fetches recent emails from Gmail
    2. Uses Claude AI to determine if each email needs a reply
    3. Generates appropriate replies for emails that need responses
    4. Creates threaded draft replies in Gmail
    
    Returns information about processed emails and created drafts.
    """
    result = process_emails(max_emails=max_emails)
    return result
