import json
import logging
from app.core.config import get_settings
from app.schemas.ai import AffordabilityImpact, AffordabilityResponse, ParsedExpenseItem

logger = logging.getLogger(__name__)
settings = get_settings()


async def parse_expense_with_gemini(text: str) -> list[ParsedExpenseItem]:
    """Parse Roman Urdu / English natural language text into expense line items."""
    # System prompt specifically tuned for Pakistani students and Roman Urdu
    prompt = f"""You are an expense parser for a Pakistani student expense tracker app called 'Talib-e-Kharch'.
Extract all individual expenses from the user's natural language input (which may be in English, Urdu, or Roman Urdu).

User input: "{text}"

For each expense item, determine:
1. description: Concise English or Roman Urdu name (e.g., "Biryani Lunch", "Rickshaw", "Printing notes", "Photocopy")
2. amount: numeric value in PKR (Pakistani Rupees)
3. category: One of ["Food & Canteen", "Transport", "Academic", "Personal", "Health", "Entertainment", "Utilities", "Other"]
4. icon: Material icon name (restaurant, directions_subway, school, shopping_bag, local_hospital, sports_esports, bolt, more_horiz)

Respond ONLY with a valid JSON array of objects, with keys "description", "amount", "category", "icon".
Do NOT include markdown fences, backticks, or any conversational text. Just the raw JSON array.
Example:
[
  {{"description": "Campus Lunch", "amount": 450.0, "category": "Food & Canteen", "icon": "restaurant"}},
  {{"description": "Rickshaw to Metro", "amount": 180.0, "category": "Transport", "icon": "directions_subway"}}
]
"""

    if not settings.GEMINI_API_KEY:
        # Fallback intelligent parser if API key is not yet configured by user
        return _fallback_local_parse(text)

    try:
        import httpx

        model = settings.GEMINI_MODEL or "gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "response_mime_type": "application/json"},
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(url, json=payload)
            if res.status_code == 200:
                data = res.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                items = json.loads(content)
                return [ParsedExpenseItem(**item) for item in items]
            else:
                logger.error(f"Gemini API returned status {res.status_code}: {res.text}")
                return _fallback_local_parse(text)
    except Exception as e:
        logger.error(f"Gemini parsing failed: {e}")
        return _fallback_local_parse(text)


def _fallback_local_parse(text: str) -> list[ParsedExpenseItem]:
    """Smart regex fallback when Gemini key is not set or network fails."""
    import re

    # Match patterns like "lunch 450", "chai 80", "rickshaw 200", "500 biryani"
    items: list[ParsedExpenseItem] = []
    lower = text.lower()

    matches = re.findall(r"([a-zA-Z\s]+?)\s*(\d+(?:\.\d+)?)\s*(?:rs|rupees|ka|ke)?", lower)
    if matches:
        for desc, amt in matches:
            d = desc.strip(" ,.-")
            if not d:
                d = "Expense"
            try:
                val = float(amt)
                cat = "Food & Canteen"
                icon = "restaurant"
                if any(w in d for w in ["rickshaw", "metro", "bus", "uber", "indrive", "petrol", "bike"]):
                    cat = "Transport"
                    icon = "directions_subway"
                elif any(w in d for w in ["book", "photocopy", "print", "sheet", "exam", "fees"]):
                    cat = "Academic"
                    icon = "school"
                items.append(ParsedExpenseItem(description=d.capitalize(), amount=val, category=cat, icon=icon))
            except ValueError:
                continue

    if not items:
        # Check reverse order: "450 lunch"
        rev_matches = re.findall(r"(\d+(?:\.\d+)?)\s*([a-zA-Z\s]+)", lower)
        for amt, desc in rev_matches:
            d = desc.strip(" ,.-")
            if not d:
                d = "Expense"
            try:
                val = float(amt)
                items.append(ParsedExpenseItem(description=d.capitalize(), amount=val, category="Other", icon="more_horiz"))
            except ValueError:
                continue

    if not items:
        items.append(ParsedExpenseItem(description=text[:40].strip(), amount=100.0, category="Other", icon="more_horiz"))

    return items


async def evaluate_affordability(
    query: str,
    amount: float,
    current_balance: float,
    safe_daily: float,
    days_left: int,
) -> AffordabilityResponse:
    """Evaluate whether an expense is safe, safe with trade-offs, or risky for a student."""
    cushion_after = current_balance - amount
    new_safe_daily = max(0.0, cushion_after / max(days_left, 1))

    prompt = f"""You are a caring, financially-wise mentor for a Pakistani college student.
The student wants to make an unplanned purchase:
Item/Request: "{query}"
Cost: Rs. {amount}
Current Available Cash: Rs. {current_balance}
Days Left in Stipend Cycle: {days_left} days
Current Safe Daily Allowance: Rs. {safe_daily:.1f}/day
New Safe Daily Allowance if purchased: Rs. {new_safe_daily:.1f}/day

Evaluate this purchase realistically for a student on a tight budget.
Determine:
1. "verdict": One of ["safe", "safe_with_tradeoff", "dangerous"]
2. "verdict_label": Short friendly badge e.g. "Safe to Buy", "Safe with Trade-off", "Budget Risk"
3. "explanation": 2-3 warm, culturally aware sentences in English advising the student on the tradeoff (e.g. mention cutting down on canteen snacks or weekend outing).
4. "buffer_percentage": estimated percentage (0-100) of financial safety buffer remaining.

Return ONLY a valid JSON object with keys: "verdict", "verdict_label", "explanation", "buffer_percentage".
Do NOT include markdown backticks or commentary.
"""

    verdict = "safe"
    verdict_label = "Safe to Buy"
    explanation = f"You can afford this expense. Your remaining daily allowance will be Rs. {new_safe_daily:.0f}/day."
    buffer = 80.0

    if cushion_after < 0:
        verdict = "dangerous"
        verdict_label = "Exceeds Balance"
        explanation = f"This purchase of Rs. {amount} exceeds your remaining cash (Rs. {current_balance}). You will need to borrow or skip essential expenses."
        buffer = 10.0
    elif new_safe_daily < 300:
        verdict = "dangerous"
        verdict_label = "Severe Crunch"
        explanation = f"Buying this leaves only Rs. {new_safe_daily:.0f}/day for food and transport for {days_left} days. We recommend postponing."
        buffer = 30.0
    elif amount > current_balance * 0.35:
        verdict = "safe_with_tradeoff"
        verdict_label = "Safe with Trade-off"
        explanation = f"You can afford this, but it consumes over a third of your cash. Daily safe spend drops from Rs. {safe_daily:.0f} to Rs. {new_safe_daily:.0f}."
        buffer = 55.0

    if settings.GEMINI_API_KEY:
        try:
            import httpx

            model = settings.GEMINI_MODEL or "gemini-2.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "response_mime_type": "application/json"},
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    ai_data = json.loads(res.json()["candidates"][0]["content"]["parts"][0]["text"])
                    verdict = ai_data.get("verdict", verdict)
                    verdict_label = ai_data.get("verdict_label", verdict_label)
                    explanation = ai_data.get("explanation", explanation)
                    buffer = float(ai_data.get("buffer_percentage", buffer))
        except Exception as e:
            logger.error(f"Gemini affordability check failed: {e}")

    impacts = [
        AffordabilityImpact(
            metric="Daily Safe Spend",
            subtitle=f"Next {days_left} days allowance",
            before=round(safe_daily, 1),
            after=round(new_safe_daily, 1),
            icon="local_cafe",
        ),
        AffordabilityImpact(
            metric="Remaining Cash",
            subtitle="Available stipend",
            before=round(current_balance, 1),
            after=round(max(0.0, cushion_after), 1),
            icon="account_balance_wallet",
        ),
    ]

    return AffordabilityResponse(
        verdict=verdict,
        verdict_label=verdict_label,
        explanation=explanation,
        buffer_percentage=buffer,
        impacts=impacts,
    )
