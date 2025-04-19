from fastapi import APIRouter, Query, HTTPException, Body
from services.email_finance import analyze_financial_emails, save_transactions_to_database
from typing import Optional, List, Dict, Any

router = APIRouter(tags=["Email Finance"])

@router.post("/email-finance/analyze")
async def analyze_finances(
    max_emails: Optional[int] = Query(20, description="Maximum number of recent emails to process"),
    days_back: Optional[int] = Query(30, description="Only process emails from the last N days"),
    save_to_db: Optional[bool] = Query(False, description="Save extracted transactions to database")
):
    """
    Process recent emails and extract financial transaction data.
    
    This endpoint:
    1. Fetches recent emails from Gmail
    2. Uses Claude AI to analyze each email for financial transactions
    3. Extracts income, expenses, and other financial details
    4. Calculates summary statistics (total income, expenses, net cash flow)
    5. Optionally saves transactions to the database
    
    Returns information about processed emails and extracted financial data.
    """
    result = analyze_financial_emails(max_emails=max_emails, days_back=days_back)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    
    # Save transactions to database if requested
    if save_to_db and result.get("transactions_found", 0) > 0:
        success = save_transactions_to_database(result.get("transactions", []))
        result["saved_to_database"] = success
    
    return result

@router.post("/email-finance/save")
async def save_transactions(transactions: List[Dict[str, Any]] = Body(...)):
    """
    Save extracted financial transactions to the database.
    
    This endpoint:
    1. Takes a list of transaction objects
    2. Saves them to the database
    3. Returns success or failure status
    """
    if not transactions:
        return {"status": "success", "message": "No transactions to save"}
    
    success = save_transactions_to_database(transactions)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save transactions to database")
        
    return {
        "status": "success", 
        "message": f"Saved {len(transactions)} transactions to database"
    }

@router.get("/email-finance/summary")
async def get_financial_summary(days_back: Optional[int] = Query(30, description="Get summary for the last N days")):
    """
    Get a financial summary from recent emails without saving to database.
    
    This endpoint:
    1. Analyzes recent emails for financial data
    2. Returns a summary of income, expenses, and cash flow
    """
    result = analyze_financial_emails(max_emails=50, days_back=days_back)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    
    # Return just the summary part for a cleaner response
    summary = result.get("summary", {})
    summary["processed_emails"] = result.get("processed", 0)
    summary["transactions_found"] = result.get("transactions_found", 0)
    summary["period"] = f"Last {days_back} days"
    
    return summary
