from fastapi import APIRouter, Query, HTTPException
from services.email_reminders import extract_reminders_from_emails, save_reminders_to_database
from typing import Optional

router = APIRouter(tags=["Email Reminders"])

@router.post("/email-reminders/extract")
async def extract_reminders(max_emails: Optional[int] = Query(10, description="Maximum number of recent emails to process")):
    """
    Process recent emails and extract reminders/todos from them.
    
    This endpoint:
    1. Fetches recent emails from Gmail
    2. Uses Claude AI to analyze each email for reminders, todos, tasks, and action items
    3. Extracts relevant details including deadlines, priorities, and context
    4. Returns the structured reminder data
    
    Returns information about processed emails and extracted reminders.
    """
    result = extract_reminders_from_emails(max_emails=max_emails)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
        
    return result

@router.post("/email-reminders/save")
async def save_reminders(reminders: list):
    """
    Save extracted reminders to the database.
    
    This endpoint:
    1. Takes a list of reminder objects
    2. Saves them to the database
    3. Returns success or failure status
    
    Note: This is a placeholder endpoint for future database integration.
    """
    success = save_reminders_to_database(reminders)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save reminders to database")
        
    return {"status": "success", "message": f"Saved {len(reminders)} reminders to database"}
