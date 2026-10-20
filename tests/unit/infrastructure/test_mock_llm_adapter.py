from procurement.infrastructure.mock_llm_adapter import MockLLMAdapter


def test_extracts_quantity_product_and_singular_category():
    parsed = MockLLMAdapter().parse("I need 5 new Lenovo Laptops for the IT department")

    assert parsed.quantity == 5
    assert parsed.product_name == "Lenovo Laptops"
    assert parsed.category == "Laptop"


def test_defaults_to_quantity_one_when_no_number_is_given():
    assert MockLLMAdapter().parse("please order monitors").quantity == 1


def test_confidence_is_within_the_valid_range():
    assert 0.0 <= MockLLMAdapter().parse("buy 2 monitors").confidence <= 1.0
