"""
Logic Manager  (Layer 3 of 5 - Made by Thierry)
---------------------------------------------------------
Domain brain of the Food Waste Management Tracker.

Contract with neighbouring layers (do not break these):
    INPUT  -> a dict from ai_manager.enrich_record() that ALREADY contains
              days_to_expiry, waste_risk_score, recipe_suggestions.
              We CONSUME days_to_expiry; we never compute it - expiry
              tracking belongs to the AI layer (Moses/Jerome).
    OUTPUT -> a NEW dict (we never mutate our input) with three extra keys:
              status     (str)  one of the STATUS_* constants below
              action     (str)  one of the ACTION_* constants below
              notification (str) ready-to-print wording decided HERE in the
                       logic layer - output_manager just prints it.

Pure functions only: no input(), no print(), no network. That keeps the
whole layer testable without a human at the keyboard.

Rules are ordered and the FIRST match wins - keep Rule 1 (expired) on top
because it is a food-safety business rule that must never be overridden by
a restock suggestion. Rule 2 is the multi-condition rule the brief asks
for (it combines an AI output field, a date field and quantity).
"""

# --- status vocabulary (single source of truth for the whole app) ----------
STATUS_OK = "ok"
STATUS_EXPIRING_SOON = "expiring_soon"
STATUS_EXPIRED = "expired"
STATUS_HIGH_WASTE_RISK = "high_waste_risk"
STATUS_LOW_STOCK = "low_stock"
STATUS_UNKNOWN = "unknown"

# --- action vocabulary ------------------------------------------------------
ACTION_NONE = "none"
ACTION_NOTIFY = "notify"
ACTION_FLAG_DISPOSAL = "flag_disposal"
ACTION_URGENT_RECIPES = "urgent_notify_and_recommend_recipes"
ACTION_RECOMMEND_RESTOCK = "recommend_restock"
ACTION_FLAG_REVIEW = "flag_for_review"

# --- thresholds (tune these as a pair - they are YOUR layer's knobs) --------
EXPIRY_WARNING_DAYS = 7      # "1 week notification" from the proposal
EXPIRY_REMIND_DAYS = 3       # "3 days before expiry (remind daily)"
DISPOSAL_GRACE_HOURS = 6     # proposal: food 6h past expiry is flagged for disposal
OVERSTOCK_THRESHOLD = 50     # quantity at/above this is "overstocked"
LOW_STOCK_THRESHOLD = 5      # quantity below this triggers a restock hint
HIGH_RISK_SCORE = 0.6        # waste_risk_score at/above this counts as "high"


def apply_business_rules(ai_enriched_record):
    """
    Decide status/action/notification for one AI-enriched record.

    ai_enriched_record: dict with the io_manager keys plus
        days_to_expiry     int   (may be negative - AI layer computed it)
        waste_risk_score   float 0.0-1.0 (AI layer)
        recipe_suggestions list[str]      (AI layer)

    Returns a NEW dict = input + status/action/notification.
    """
    record = dict(ai_enriched_record)

    days_left = record.get("days_to_expiry")
    try:
        quantity = int(record.get("Inventory_Quantity", 0))
    except (TypeError, ValueError):
        quantity = 0
    name = record.get("Food_Name", "Item")

    # --- sanity guard: AI layer did not deliver what we need -----------------
    if days_left is None:
        record["status"] = STATUS_UNKNOWN
        record["action"] = ACTION_FLAG_REVIEW
        record["notification"] = (
            f"{name}: could not determine expiry status "
            f"(missing days_to_expiry from AI layer)."
        )
        return record

    # --- Rule 1: past the disposal grace period -> food-safety hard rule ----
    # Single condition on purpose: once food is expired, quantity and risk
    # score are irrelevant - it is going in the bin either way.
    if days_left < 0 and abs(days_left) * 24 >= DISPOSAL_GRACE_HOURS:
        record["status"] = STATUS_EXPIRED
        record["action"] = ACTION_FLAG_DISPOSAL
        record["notification"] = (
            f"{name} has exceeded {abs(days_left) * 24:.0f} hours since its "
            f"expiry date and has been flagged for disposal."
        )
        return record

    # --- Rule 2: MULTI-CONDITION rule using AI output fields ----------------
    # Fires only when expiry proximity AND overstock AND AI risk score all
    # agree - this is the "domain idea" rule from the brief.
    risk = float(record.get("waste_risk_score", 0) or 0)
    if (days_left <= EXPIRY_REMIND_DAYS
            and quantity >= OVERSTOCK_THRESHOLD
            and risk >= HIGH_RISK_SCORE):
        recipes = record.get("recipe_suggestions", [])
        record["status"] = STATUS_HIGH_WASTE_RISK
        record["action"] = ACTION_URGENT_RECIPES
        record["notification"] = (
            f"URGENT: {name} ({quantity} units) expires in {days_left} "
            f"day(s) and the AI flags high waste risk (score {risk:.2f}). "
            f"Suggested recipes: {', '.join(recipes) if recipes else 'none available'}."
        )
        return record

    # --- Rule 3: ordinary "use it now" reminder ------------------------------
    if days_left <= EXPIRY_WARNING_DAYS:
        record["status"] = STATUS_EXPIRING_SOON
        record["action"] = ACTION_NOTIFY
        record["notification"] = (
            f"{name} is {days_left} day(s) away from its expiry! Use it now."
        )
        return record

    # --- Rule 4: fresh item but running low -> resupply recommendation ------
    if quantity < LOW_STOCK_THRESHOLD:
        record["status"] = STATUS_LOW_STOCK
        record["action"] = ACTION_RECOMMEND_RESTOCK
        record["notification"] = (
            f"{name} stock is low ({quantity} unit(s) left) - consider restocking."
        )
        return record

    # --- default: nothing to do ----------------------------------------------
    record["status"] = STATUS_OK
    record["action"] = ACTION_NONE
    record["notification"] = f"{name} is within acceptable range."
    return record


def apply_business_rules_batch(ai_enriched_records):
    """Convenience: run apply_business_rules over a whole list."""
    return [apply_business_rules(r) for r in ai_enriched_records]


def compute_waste_trends(processed_records):
    """
    'Waste Trends' output from the proposal: how much was wasted vs saved.

    processed_records: list of dicts that already went through
    apply_business_rules(). Returns a plain dict - output_manager decides
    how to render it.
    """
    total = len(processed_records)
    expired = sum(1 for r in processed_records if r.get("status") == STATUS_EXPIRED)
    saved = sum(
        1 for r in processed_records
        if r.get("status") in (STATUS_OK, STATUS_EXPIRING_SOON)
    )
    return {
        "total_items": total,
        "expired_count": expired,
        "saved_count": saved,
        "waste_rate_pct": round((expired / total) * 100, 1) if total else 0.0,
    }
