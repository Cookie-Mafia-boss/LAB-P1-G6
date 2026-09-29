# Checks Items with EXPIRING Status and makes/returns {Expiring soon}.
def check_expiries(inventory, alert_days=30):
    """Calculates days remaining using datetime module and reports alerts."""
    if not inventory:
        return []

<<<<<<< HEAD
=======
    
>>>>>>> ccb4b06753ff59e084999f7c2bba9faa1945c0df
    expiring_soon_items = []

    for item in inventory:
        if 0 <= item["Days_Remaining"] <= alert_days:
            expiring_soon_items.append(item)

<<<<<<< HEAD
=======

>>>>>>> ccb4b06753ff59e084999f7c2bba9faa1945c0df
    # Sort items according to Days Remaining
    return sorted(expiring_soon_items, key=lambda x: x['Days_Remaining'])


def inventory_count(inventory):
<<<<<<< HEAD
    return len(inventory)
=======
    return len(inventory)
    
>>>>>>> ccb4b06753ff59e084999f7c2bba9faa1945c0df
