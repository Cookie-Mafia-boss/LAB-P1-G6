#!/usr/bin/env python3
"""
Food Waste Management System - Main Entry Point

Thin orchestrator that coordinates all application layers:
- Data Layer: SQLite persistence, CSV migration, inventory management
- Logic Layer: Validation, expiry checking, business rules
- AI Layer: AI-powered recipe suggestions, waste trend analysis, resupply recommendations
- Input/Output Layer: ALL UI, display, and user interaction (Rich CLI)

This file ONLY handles:
- Application initialization and shutdown
- Dependency injection / service creation
- Main event loop dispatching to I/O layer functions
"""

from data_layer import initialise_inventory, save_inventory, close_database, get_data_manager
from ai_layer import AIService
from classes.ai_client import GeminiClient
from classes.ai_prompt import KitchenPromptBuilder
from input_output_layer import (
    show_main_menu,
    get_user_choice,
    show_startup_alert,
    run_add_food_item,
    run_delete_food_item,
    run_update_food_item,
    run_check_expires,
    run_search_inventory,
    run_filter_by_status,
    run_ai_suggestions,
    run_view_stats,
    show_info,
    show_error,
    check_expires,
    display_items,
)

# Global AI service instance (lazy initialization)
_ai_service = None


def get_ai_service() -> AIService:
    """Return the shared AIService instance, creating it when necessary."""
    global _ai_service
    if _ai_service is None:
        # Try to use real Gemini client; falls back to safe defaults if API fails
        client = GeminiClient()
        _ai_service = AIService(client=client, prompt_builder=KitchenPromptBuilder())
    return _ai_service


def main() -> None:
    """Main application entry point."""
    # Initialize inventory (loads from SQLite, migrates CSV on first run)
    inventory = initialise_inventory()
    data_manager = get_data_manager()
    # AI service is created lazily only when option 8 is selected
    ai_service_factory = get_ai_service

    # Show startup expiry alert
    show_startup_alert(inventory)

    # Main menu loop
    while True:
        show_main_menu()
        choice = get_user_choice()

        try:
            if choice == "1":
                # View Inventory
                console = __import__('rich.console', fromlist=['Console']).Console()
                console.print(display_items(inventory, "Current Food Inventory"))
                show_info(f"Total items: {inventory.get_length()}")

            elif choice == "2":
                run_add_food_item(inventory)
                save_inventory(inventory)

            elif choice == "3":
                run_delete_food_item(inventory)
                # save_inventory is now called inside run_delete_food_item

            elif choice == "4":
                run_update_food_item(inventory)
                save_inventory(inventory)

            elif choice == "5":
                run_check_expires(inventory)

            elif choice == "6":
                run_search_inventory(inventory, data_manager)

            elif choice == "7":
                run_filter_by_status(inventory, data_manager)

            elif choice == "8":
                # Create AI service on-demand
                ai_service = ai_service_factory()
                run_ai_suggestions(inventory, ai_service)
                run_view_stats(inventory)

            elif choice == "9":
                show_info("Saving inventory...")
                save_inventory(inventory)
                close_database()
                show_info("Goodbye!")
                break

        except KeyboardInterrupt:
            show_info("\nOperation cancelled.")
        except Exception as e:
            show_error(f"Error: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        show_info("\nApplication interrupted. Goodbye!")
        close_database()
    except Exception as e:
        show_error(f"Fatal Error: {e}")
        close_database()