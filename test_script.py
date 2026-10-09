import json
from datetime import date
from unittest.mock import patch, MagicMock

# Import your procedural manager files
import ai_layer as ai_layer
import logic_layer as logic_layer


# --- HARDCODED MOCK PAYLOADS---
MOCK_GEMINI_SUCCESS_TEXT = """
### RECIPES TO PRIORITIZE
* Expiring Milk Pancakes: Uses Milk expiring tomorrow.
* Leftover Vegetable Soup: Uses Carrots.

### WASTE TRENDS
You are currently wasting 12% less food than last week.

### IMMEDIATE ACTION REQUIRED
Use the Milk today or freeze it.

### RESUPPLY RECOMMENDATIONS
Do not buy more Milk until next week.
"""

# =====================================================================
# AI LAYER TESTS
# =====================================================================

def test_ai_suggestions_success():
    """Verify core AI parsing logic functions cleanly with a valid mock response."""
    sample_inventory = [{"Food_Name": "Milk", "Status": "EXPIRED"}]
    sample_expiring = [{"Food_Name": "Carrots", "Days_Left": 1}]

    # Patch the genai Client initialized inside your ai layer
    with patch("ai_layer.genai.Client") as mock_client_cls:
        mock_client_instance = MagicMock()
        mock_interaction = MagicMock()
        mock_interaction.output_text = MOCK_GEMINI_SUCCESS_TEXT
        mock_client_instance.interactions.create.return_value = mock_interaction
        mock_client_cls.return_value = mock_client_instance

        result = ai_layer.get_ai_suggestions(sample_inventory, sample_expiring)

        # Assertions confirming accurate parsing into dictionary headers
        assert result is not None
        assert "recipes" in result
        assert "Expiring Milk Pancakes" in result["recipes"]
        assert "resupply" in result
        assert "Do not buy more Milk" in result["resupply"]
        print("test_ai_suggestions_success: PASSED")


def test_ai_suggestions_empty_inventory():
    """Verify AI logic safely shortcuts out when inventory lists are empty."""
    result = ai_layer.get_ai_suggestions([], [])
    assert result is None
    print("test_ai_suggestions_empty_inventory: PASSED")


def test_ai_suggestions_api_failure():
    """Verify Exception Matrix handling if the API returns a network exception."""
    sample_inventory = [{"Food_Name": "Milk", "Status": "EXPIRED"}]
    
    with patch("ai_layer.genai.Client") as mock_client_cls:
        mock_client_instance = MagicMock()
        mock_client_instance.interactions.create.side_effect = Exception("API Connection Failed")
        mock_client_cls.return_value = mock_client_instance

        result = ai_layer.get_ai_suggestions(sample_inventory, [])

        # Assertions verifying the try-except block returns the error dict safely
        assert isinstance(result, dict)
        assert "error" in result
        assert "API Connection Failed" in result["error"]
        print("test_ai_suggestions_api_failure: PASSED")


# =====================================================================
# LOGIC LAYER TESTS 
# =====================================================================

def test_logic_expiry_date_valid():
    """Verify correct date string formatting structure calculations."""
    # Patch only the specific 'now' method inside datetime.datetime
    with patch("logic_layer.datetime") as mock_datetime:
        # Mock now() to return a specific datetime object (Oct 5, 2026)
        from datetime import datetime as real_datetime
        mock_datetime.now.return_value = real_datetime(2026, 10, 5)
        
        # Ensure strptime still functions exactly as standard Python does
        mock_datetime.strptime = real_datetime.strptime 

        parsed_date, error = logic_layer.validate_expiry_date("25/12/2027")
        assert error is None
        assert parsed_date == date(2027, 12, 25)
        print("test_logic_expiry_date_valid: PASSED")


def test_logic_expiry_date_invalid_format():
    """Verify invalid format strings are gracefully intercepted with errors."""
    parsed_date, error = logic_layer.validate_expiry_date("2027-12-25")
    assert parsed_date is None
    assert "Invalid format" in error
    print("test_logic_expiry_date_invalid_format: PASSED")


def test_logic_expiry_date_out_of_bounds():
    """Verify protection boundaries rejecting inputs past max historical parameters."""
    with patch("logic_layer.datetime") as mock_datetime:
        from datetime import datetime as real_datetime
        mock_datetime.now.return_value = real_datetime(2026, 10, 5)
        mock_datetime.strptime = real_datetime.strptime

        # 31 years in the future exceeds MAX_YEARS (30) constraint limit
        parsed_date, error = logic_layer.validate_expiry_date("05/10/2057")
        assert parsed_date is None
        assert "future" in error
        print("test_logic_expiry_date_out_of_bounds: PASSED")


def test_logic_food_name():
    """Verify structural sanitisation rules for string values."""
    # Test valid text entry with whitespace trimming
    cleaned, error = logic_layer.validate_food_name("  Apple  ")
    assert cleaned == "Apple"
    assert error is None

    # Test numeric input disguise rejection
    cleaned, error = logic_layer.validate_food_name("123.45")
    assert cleaned is None
    assert "cannot be a number" in error
    print("test_logic_food_name: PASSED")


def test_logic_check_expiries_sorting():
    """Verify accurate threshold sorting limits for items approaching expiry."""
    sample_inventory = [
        {"Food_Name": "Milk", "Days_Remaining": 45},     # Beyond alert days limit
        {"Food_Name": "Eggs", "Days_Remaining": 5},      # Valid (2nd)
        {"Food_Name": "Yogurt", "Days_Remaining": 2},    # Valid (1st soonest)
        {"Food_Name": "Bread", "Days_Remaining": -1}     # Already expired
    ]

    expiring_soon = logic_layer.check_expiries(sample_inventory, alert_days=30)

    assert len(expiring_soon) == 2
    assert expiring_soon[0]["Food_Name"] == "Yogurt"
    assert expiring_soon[1]["Food_Name"] == "Eggs"
    print("test_logic_check_expiries_sorting: PASSED")


def test_logic_qty():
    """Verify validation strings evaluating total numeric stock quantity values."""
    qty, error = logic_layer.validate_qty("10")
    assert qty == 10
    assert error is None

    qty, error = logic_layer.validate_qty("-5")
    assert qty is None
    assert "positive integer" in error
    print("test_logic_qty: PASSED")


# Run all tests
if __name__ == "__main__":
    print("=================================================================")
    print("RUNNING TESTS FOR AI LAYER AND LOGIC LAYER FUNCTIONS")
    print("=================================================================")
    
    print("\n[AI LAYER STATUS]")
    test_ai_suggestions_success()
    test_ai_suggestions_empty_inventory()
    test_ai_suggestions_api_failure()
    
    print("\n[LOGIC LAYER STATUS]")
    test_logic_expiry_date_valid()
    test_logic_expiry_date_invalid_format()
    test_logic_expiry_date_out_of_bounds()
    test_logic_food_name()
    test_logic_check_expiries_sorting()
    test_logic_qty()
    
    print("\n=================================================================")
    print("FUNCTIONAL TESTS COMPLETED SUCCESSFULLY")
    print("=================================================================")
