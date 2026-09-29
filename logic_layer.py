# Checks Items with EXPIRING Status and makes/returns {Expiring soon}.
def check_expiries(inventory, alert_days=30):
    """Calculates days remaining using datetime module and reports alerts."""
    if not inventory:
        return []

    
    expiring_soon_items = []

    for item in inventory:
        if 0 < item["Days_Remaining"] <= alert_days:
            expiring_soon_items.append(item)


    # Sort items according to Days Remaining
    return sorted(expiring_soon_items, key=lambda x: x['Days_Remaining'])


def inventory_count(inventory):
    return len(inventory)
    