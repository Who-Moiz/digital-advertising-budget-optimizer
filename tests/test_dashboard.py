from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_loads_and_handles_empty_filters():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "dashboard" / "app.py"))
    app.run(timeout=30)
    assert not app.exception
    assert len(app.metric) == 5
    app.sidebar.multiselect[0].set_value([]).run(timeout=30)
    assert not app.exception
    assert "No records" in app.info[0].value


def test_dashboard_reports_infeasible_constraints():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "dashboard" / "app.py"))
    app.run(timeout=30)
    app.sidebar.multiselect[0].set_value(["Google"]).run(timeout=30)
    assert not app.exception
    assert any("infeasible" in warning.value for warning in app.warning)
