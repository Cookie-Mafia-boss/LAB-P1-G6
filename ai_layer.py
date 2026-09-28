import requests
import json

#AI_Layer programmed by Moses and Jerome
OLLAMA_URL = "http://localhost:11434/api/chat"

RECIPE_SYSTEM_PROMPT = (
    "You are a food waste reduction assistant. "
    "Given a food item nearing its expiry, suggest concrete ways to use it up: "
    "recipes, menu specials, or staff meals. "
    "NEVER suggest using food that has already expired on or after the expiry date. "
    "Return ONLY a JSON object of the form "
    '{"recipes": ["suggestion 1", "suggestion 2", "suggestion 3"]} '
    "with 3 to 5 short bullet-style strings. No prose outside the JSON."
)


def get_recipe_suggestions(item_name, days_to_expiry, model="qwen2.5-coder:1.5b", timeout=120):
    """Ask Ollama for recipe ideas for one item. Returns list[str] (empty on failure)."""
    user_prompt = (
        f"Item: {item_name}\n"
        f"Days until expiry: {days_to_expiry}\n"
        "Suggest ways to use it up."
    )

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": RECIPE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "format": "json",
    }

    try:
        r = requests.post(OLLAMA_URL, json=data, timeout=timeout)
        r.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Ollama request failed: {e}") from e

    content = r.json().get("message", {}).get("content", "")
    try:
        parsed = json.loads(content)
        return [str(x) for x in parsed.get("recipes", []) if str(x).strip()]
    except (json.JSONDecodeError, AttributeError):
        return []


def enrich_record_with_recipes(record, model="qwen2.5-coder:1.5b"):
    """
    Add a structured 'recipes' field to a record.
    Leaves every other field untouched — matches the Logic Manager's contract.
    """
    enriched = dict(record)   # never mutate caller's dict
    days_left = record.get("days_to_expiry")

    # Only ask the AI when the Logic Manager will actually use the recipes.
    # Rule 2 fires for: 0 <= days_left <= 3  AND  quantity >= 5
    # We're slightly more generous (<= 7) to cover Rule 3 too.
    if days_left is None or days_left < 0 or days_left > 7:
        enriched["recipes"] = []
        return enriched

    try:
        enriched["recipes"] = get_recipe_suggestions(
            record.get("Food_Name", "Item"),
            days_left,
            model=model,
        )
    except RuntimeError:
        enriched["recipes"] = []   # degrade gracefully; Logic Manager still works

    return enriched