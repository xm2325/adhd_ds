def test_generated_data_passes_all_rules(validation):
    assert validation["failure_count"].sum() == 0
