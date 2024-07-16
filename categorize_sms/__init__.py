import azure.functions as func
import json
import logging
import os
from typing import Dict, Optional
import anthropic
import aiohttp
from hubspot import HubSpot
import asyncio
from functools import lru_cache
import time
from asyncio import Lock

# Access API keys from environment variables
# Set these in your Azure Function App settings or local.settings.json for local development
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
BONZO_API_KEYS: Dict[str, str] = json.loads(os.environ.get("BONZO_API_KEYS", "{}"))

class RateLimiter:
    def __init__(self, rate, per):
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()
        self.lock = Lock()

    async def acquire(self):
        async with self.lock:
            now = time.time()
            time_passed = now - self.last_check
            self.last_check = now
            self.allowance += time_passed * (self.rate / self.per)
            if self.allowance > self.rate:
                self.allowance = self.rate
            if self.allowance < 1:
                await asyncio.sleep(1 - self.allowance)
                self.allowance = 0
            else:
                self.allowance -= 1

# Initialize the rate limiter
rate_limiter = RateLimiter(30, 60)  # 30 requests per 60 seconds

def get_bonzo_api_key(owner_id: str) -> Optional[str]:
    return BONZO_API_KEYS.get(owner_id)

@lru_cache(maxsize=1000)
async def call_anthropic_api(message: str) -> str:
    prompt = f"""
    You are an AI assistant for a competitive mortgage sales brokerage. Categorize the following SMS response from a potential lead into one of these categories:
    - New
    - Working With Someone Else
    - Not Interested
    - Garden Lead - Send Quote
    - Who are you?
    - Already Closed
    - Holding Off
    - Not Licensed in State/Loan Product Not Available
    - HELOC / No Cash-Out Interest
    - Ask For LE / Already In Process
    - Land Loan
    - Wrong Number
    - Already in Process
    - Spanish
    - Hard DNC Language

    Guidelines:
    - 'Working With Someone Else' should be used when the lead explicitly mentions they're working with another lender, regardless of their tone.
    - 'Not Interested' is for responses that indicate hostility or a very clear, firm rejection that would make further outreach potentially negative.
    - 'Garden Lead - Send Quote' is crucial for leads who express disinterest but aren't hostile. This allows for one final automated text with our best rates.
    - Prioritize 'Ask For LE / Already In Process' for any hint of ongoing process or interest in rates.
    - 'Hard DNC Language' only for explicit, unambiguous opt-out requests.
    - For ambiguous responses, prefer categories that allow for follow-up.
    - 'Spanish' for responses in Spanish, regardless of content.

    SMS response: "{message}"

    Category:"""

    try:
        await rate_limiter.acquire()  # Wait for rate limit
        async with aiohttp.ClientSession() as session:
            completion = await anthropic.Completion.create(
                model="claude-v1",
                prompt=prompt,
                max_tokens_to_sample=1000,
                api_key=ANTHROPIC_API_KEY,
                session=session
            )
        return completion.completion.strip()
    except Exception as e:
        logging.error(f"Error calling Anthropic API: {e}")
        raise  # Re-raise the exception to be handled by the caller

async def categorize_sms(message: str) -> str:
    try:
        return await call_anthropic_api(message)
    except Exception as e:
        logging.error(f"Error during SMS categorization: {e}")
        return "Uncategorized"

async def update_bonzo_contact(api_key: str, contact_id: str, category: str):
    # TODO: Implement the actual Bonzo API call here
    try:
        # This is a placeholder. Replace with actual Bonzo API call
        logging.info(f"Updating Bonzo contact {contact_id} with category: {category}")
        # Simulating an API call
        await asyncio.sleep(1)
        logging.info(f"Updated Bonzo contact {contact_id} with category: {category}")
    except Exception as e:
        logging.error(f"Error updating Bonzo contact: {e}")
        # Don't raise the exception, just log it

async def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body: Dict[str, str] = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"status": "error", "error": "Invalid JSON in request body"}),
            mimetype="application/json",
            status_code=400
        )

    message: Optional[str] = req_body.get('message') or req.params.get('message')
    contact_id: Optional[str] = req_body.get('contactId') or req.params.get('contactId')
    owner_id: Optional[str] = req_body.get('ownerId') or req.params.get('ownerId')

    if not message or not message.strip():
        return func.HttpResponse(
            json.dumps({"status": "error", "error": "Please provide a non-empty 'message'"}),
            mimetype="application/json",
            status_code=400
        )

    if not contact_id or not contact_id.strip():
        return func.HttpResponse(
            json.dumps({"status": "error", "error": "Please provide a valid 'contactId'"}),
            mimetype="application/json",
            status_code=400
        )

    if not owner_id:
        return func.HttpResponse(
            json.dumps({"status": "error", "error": "Please provide an 'ownerId'"}),
            mimetype="application/json",
            status_code=400
        )

    api_key = get_bonzo_api_key(owner_id)
    if not api_key:
        return func.HttpResponse(
            json.dumps({"status": "error", "error": "Invalid owner_id provided"}),
            mimetype="application/json",
            status_code=400
        )

    logging.info(f"Received message: {message} for contact: {contact_id} from owner: {owner_id}")

    try:
        category = await categorize_sms(message)
        logging.info(f"Categorized message as: {category}")

        # Asynchronously update Bonzo contact
        asyncio.create_task(update_bonzo_contact(api_key, contact_id, category))

        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "message": message,
                "category": category,
                "contactId": contact_id,
                "ownerId": owner_id
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error during API call or categorization: {e}")
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "error": "An error occurred during message categorization",
                "details": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )
