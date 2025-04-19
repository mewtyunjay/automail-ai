from fastapi import APIRouter
from services.email_tagging import tag_emails

router = APIRouter()

@router.post("/email-tagging/run")
def run_email_tagging():
    """Trigger the email tagging microservice."""
    result = tag_emails()
    return result
