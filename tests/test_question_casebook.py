import pandas as pd


def test_question_catalog_and_casebook_are_complete(built_project):
    target, summary = built_project
    catalog = pd.read_csv(target / "results/ds_question_catalog.csv")
    casebook = (target / "reports/ds_question_casebook.md").read_text(encoding="utf-8")
    assert summary["ds_questions_covered"] == 106
    assert len(catalog) == 106
    assert catalog["current_synthetic_answer"].notna().all()
    assert catalog["category"].nunique() >= 13
    assert "Current synthetic answer" in casebook
    assert "Q106" in casebook
    assert "Literature support" in casebook
    assert "Project data support" in casebook
    assert "Evidence boundary" in casebook
