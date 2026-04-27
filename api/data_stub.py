from __future__ import annotations

from .schemas import BudgetLevel, Restaurant


def get_stub_restaurants() -> list[Restaurant]:
    # Small, diverse set for Phase 0 wiring. Replace with real dataset in Phase 1/2.
    return [
        Restaurant(
            id="del-001",
            name="Trattoria Roma",
            location="Delhi",
            cuisines=["italian"],
            cost_level=BudgetLevel.high,
            rating=4.6,
        ),
        Restaurant(
            id="del-002",
            name="Spice Route",
            location="Delhi",
            cuisines=["north indian", "mughlai"],
            cost_level=BudgetLevel.medium,
            rating=4.2,
        ),
        Restaurant(
            id="del-003",
            name="Wok & Roll",
            location="Delhi",
            cuisines=["chinese", "indo-chinese"],
            cost_level=BudgetLevel.low,
            rating=4.0,
        ),
        Restaurant(
            id="blr-001",
            name="Pasta Street",
            location="Bangalore",
            cuisines=["italian"],
            cost_level=BudgetLevel.medium,
            rating=4.3,
        ),
        Restaurant(
            id="blr-002",
            name="Dragon Palace",
            location="Bangalore",
            cuisines=["chinese", "thai"],
            cost_level=BudgetLevel.high,
            rating=4.4,
        ),
        Restaurant(
            id="blr-003",
            name="Quick Bites",
            location="Bangalore",
            cuisines=["fast food"],
            cost_level=BudgetLevel.low,
            rating=3.9,
            metadata={"tags": ["quick service"]},
        ),
        Restaurant(
            id="mum-001",
            name="Bombay Bistro",
            location="Mumbai",
            cuisines=["north indian", "street food"],
            cost_level=BudgetLevel.medium,
            rating=4.1,
            metadata={"tags": ["family-friendly"]},
        ),
        Restaurant(
            id="mum-002",
            name="Sushi Zen",
            location="Mumbai",
            cuisines=["japanese"],
            cost_level=BudgetLevel.high,
            rating=4.7,
        ),
        Restaurant(
            id="hyd-001",
            name="Biryani House",
            location="Hyderabad",
            cuisines=["hyderabadi", "biryani"],
            cost_level=BudgetLevel.low,
            rating=4.5,
        ),
        Restaurant(
            id="hyd-002",
            name="Cafe Bloom",
            location="Hyderabad",
            cuisines=["cafe", "desserts"],
            cost_level=BudgetLevel.medium,
            rating=None,  # intentionally missing to exercise min_rating filtering
        ),
    ]

