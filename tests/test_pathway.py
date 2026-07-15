def test_pathway_counts_are_monotone(pathway):
    counts = pathway["stage_summary"]["patient_count"].tolist()
    assert all(first >= second for first, second in zip(counts, counts[1:]))
