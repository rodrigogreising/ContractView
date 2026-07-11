from decimal import Decimal

from app.budget import calculate_budget

CATEGORIES=[{"code":"personnel","label":"Personnel","limit":"100.00"},{"code":"facilities","label":"Facilities","limit":"50.00"}]

def test_exact_category_and_total_decimal_availability():
    result=calculate_budget({"Personnel":Decimal("33.33"),"Facilities":Decimal("16.67")},CATEGORIES)
    assert result["categories"]==[
        {"code":"personnel","name":"Personnel","requested":Decimal("33.33"),"budgeted":Decimal("100.00"),"remaining":Decimal("66.67"),"overBudget":False},
        {"code":"facilities","name":"Facilities","requested":Decimal("16.67"),"budgeted":Decimal("50.00"),"remaining":Decimal("33.33"),"overBudget":False},
    ]
    assert result["total"]=={"requested":Decimal("50.00"),"budgeted":Decimal("150.00"),"remaining":Decimal("100.00"),"overBudget":False}

def test_over_budget_fixture_blocks_and_corrected_value_passes():
    over=calculate_budget({"Personnel":Decimal("100.01")},CATEGORIES)
    corrected=calculate_budget({"Personnel":Decimal("100.00")},CATEGORIES)
    assert over["categories"][0]["remaining"]==Decimal("-0.01") and over["categories"][0]["overBudget"] and over["total"]["overBudget"]
    assert corrected["categories"][0]["remaining"]==Decimal("0.00") and not corrected["categories"][0]["overBudget"] and not corrected["total"]["overBudget"]

def test_decimal_property_requested_plus_remaining_equals_budgeted():
    for cents in range(0,10001,137):
        requested=Decimal(cents)/100
        result=calculate_budget({"Personnel":requested},CATEGORIES)["categories"][0]
        assert result["requested"]+result["remaining"]==result["budgeted"]
