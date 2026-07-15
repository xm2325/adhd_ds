def test_interactive_dashboard_contains_operational_views(built_project):
    target, summary = built_project
    dashboard = target / "reports" / "operations_dashboard.html"
    pages_version = target / "docs" / "index.html"
    assert summary["synthetic_referrals"] > 1000
    assert dashboard.exists()
    assert pages_version.exists()
    html = dashboard.read_text(encoding="utf-8")
    for marker in [
        "Operations command centre",
        "Interactive scenario planner",
        "Appointment support workflow",
        "Data and model controls",
        "Decision and service impact",
        "Operational decision register",
        "Role view",
        "Referral timeline",
        "Resource optimisation and pilot design",
        "Service-level control board",
        "Champion–challenger monitoring",
        "window.DASHBOARD_DATA=",
    ]:
        assert marker in html
    assert "No real patient or company data are used" in html
    assert "getElementById('planExtra')" in html
    assert "exportSupport" in html
    assert "exportDecisions" in html
    assert "localStorage" in html
    assert "attendanceMonitoring" in html
    assert "renderOptimisation" in html
    assert "optimisationPareto" in html
    assert "serviceLevelBoard" in html
