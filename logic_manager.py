"""
Logic Manager  (Layer 3 of 5 - Made by Thierry and Audrey)
---------------------------------------------------------
The domain brain: decides what each food item's status is and what should
be done about it.

Built to receive the dict shape Ming Yuen's input layer collects
(Food_Name, Category, Expiry_Date, Date_Purchased, Inventory_Quantity)
plus what the AI layer adds on top of it:
    days_to_expiry   int   - expiry tracking, produced by Moses's part
    recipes          list[str] or str - recipe ideas from Jerome's
                     sample_request.py Ollama call
We CONSUME days_to_expiry; we never compute it ourselves - that is the
AI layer's job.

Each function takes data in and returns data out: no input(), no print().
The wording of every user-facing message is decided HERE; output_manager
just renders it.

Rules are checked top to bottom and the FIRST match wins. Rule 1 (expired
food) is a food-safety business rule from the proposal and must always be
checked first.
"""

DATE_FORMAT = "%d/%m/%Y"

# --- thresholds (team knobs - proposal: 1 week notify, 3 days remind) -------
EXPIRY_WARNING_DAYS = 7        # "is X days away from its expiry! Use it now!"
EXPIRY_REMIND_DAYS = 3         # "3 days before expiry (remind daily)"
DISPOSAL_GRACE_HOURS = 6       # proposal: 6h past expiry -> flagged for disposal
LOW_STOCK_THRESHOLD = 5        # below this -> resupply recommendation


def _as_recipe_list(recipes):
    """AI layer may hand us a list."""
    if isinstance(recipes, list):
        return [str(r) for r in recipes]
    if isinstance(recipes, str) and recipes.strip():
        return [line.strip(" -•\t") for line in recipes.splitlines() if line.strip()]
    return []


def apply_business_rules(record):
    """
    record: dict with the input-layer fields plus days_to_expiry and recipes.
    Returns a NEW dict (input untouched) with status/action/notification added.

    status:    ok | expiring_soon | expired | low_stock | unknown
    action:    none | notify | flag_disposal | recommend_restock | flag_for_review
    """
    result = dict(record)

    days_left = result.get("days_to_expiry")
    try:
        quantity = int(result.get("Inventory_Quantity", 0))
    except (TypeError, ValueError):
        quantity = 0
    name = result.get("Food_Name", "Item")
    recipes = _as_recipe_list(result.get("recipes"))

    # --- guard: AI layer did not deliver expiry tracking ---------------------
    if days_left is None:
        result["status"] = "unknown"
        result["action"] = "flag_for_review"
        result["notification"] = (
            f"{name}: could not determine expiry status (no days_to_expiry)."
        )
        return result
    days_left = int(days_left)

    # --- Rule 1: past the disposal grace period -> food-safety hard rule -----
    if days_left < 0 and abs(days_left) * 24 >= DISPOSAL_GRACE_HOURS:
        result["status"] = "expired"
        result["action"] = "flag_disposal"
        result["notification"] = (
            f"{name} has exceeded {abs(days_left) * 24:.0f} hours since its "
            f"expiry date and has been flagged for disposal."
        )
        return result

    # --- Rule 2: multi-condition - expiring very soon AND a lot on hand ------
    # (3 days or less left) AND (5+ units): worth pushing recipes hard,
    # because that combination is where food actually gets wasted.
    if days_left <= EXPIRY_REMIND_DAYS and quantity >= LOW_STOCK_THRESHOLD:
        result["status"] = "expiring_soon"
        result["action"] = "notify_and_recommend_recipes"
        recipe_txt = ", ".join(recipes[:3]) if recipes else "no recipe ideas from AI"
        result["notification"] = (
            f"URGENT: {name} ({quantity} units) expires in {days_left} day(s)! "
            f"Use it now. Suggested recipes: {recipe_txt}."
        )
        return result

    # --- Rule 3: ordinary expiry reminder -------------------------------------
    if days_left <= EXPIRY_WARNING_DAYS:
        result["status"] = "expiring_soon"
        result["action"] = "notify"
        result["notification"] = (
            f"{name} is {days_left} day(s) away from its expiry! Use it now."
        )
        return result

    # --- Rule 4: fresh but running low -> resupply recommendation -------------
    if quantity < LOW_STOCK_THRESHOLD:
        result["status"] = "low_stock"
        result["action"] = "recommend_restock"
        result["notification"] = (
            f"{name} stock is low ({quantity} unit(s) left) - consider restocking."
        )
        return result

    # --- default: everything fine ----------------------------------------------
    result["status"] = "ok"
    result["action"] = "none"
    result["notification"] = f"{name} is within acceptable range."
    return result


def apply_business_rules_batch(records):
    """Convenience: run apply_business_rules over a whole list."""
    return [apply_business_rules(r) for r in records]


def compute_waste_trends(processed_records):
    """
    'Waste Trends' from the proposal: how much was wasted vs saved.
    processed_records: items that already went through apply_business_rules.
    Returns a plain dict - output_manager renders it.
    """
    total = len(processed_records)
    expired = sum(1 for r in processed_records if r.get("status") == "expired")
    saved = sum(1 for r in processed_records if r.get("status") in ("ok", "expiring_soon"))
    return {
        "total_items": total,
        "expired_count": expired,
        "saved_count": saved,
        "waste_rate_pct": round((expired / total) * 100, 1) if total else 0.0,
    }
