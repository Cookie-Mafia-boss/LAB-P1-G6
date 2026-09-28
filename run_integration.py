#Put Input Layer
#from <input_layer> import <function>

#AI Layer
from ai_layer import enrich_record_with_recipes
#Logic_layer
from logic_layer import apply_business_rules, compute_waste_trends


def process_all(records):
    """Run each record through AI Layer, then Logic Manager."""
    results = []
    for record in records:
        enriched = enrich_record_with_recipes(record)
        processed = apply_business_rules(enriched)
        results.append(processed)
    return results

#Put the Input Layer functions below
"""
if __name__ == "__main__":
    raw = <function>
    processed = process_all(raw)

    for r in processed:
        print(f"[{r['status']:>13}] {r['notification']}")
        if r.get("recipes"):
            print(f"               recipes: {r['recipes'][:3]}")

    print()
    print("Waste trends:", compute_waste_trends(processed))
"""