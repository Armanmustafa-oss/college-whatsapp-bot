"""
Unit & Integration Tests for the Analytics Dashboard (`dashboard/app.py`).

These tests verify the dashboard's API endpoints, data fetching logic (mocked),
and HTML rendering (if applicable).
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from dashboard.app import app, fetch_conversation_metrics_async, fetch_real_time_status_async, create_interaction_volume_chart, create_intent_pie_chart, create_sentiment_gauge

# --- Test Client for Dashboard FastAPI App ---
client = TestClient(app)

# --- Test Dashboard Endpoints ---
@patch("dashboard.app.supabase") # Mock Supabase client used by dashboard
def test_dashboard_home(mock_supabase):
    """Test the main dashboard HTML page loads successfully."""
    # Mock the async data fetching functions to return dummy data
    with patch("dashboard.app.fetch_conversation_metrics_async", new_callable=AsyncMock) as mock_fetch_metrics, \
         patch("dashboard.app.fetch_real_time_status_async", new_callable=AsyncMock) as mock_fetch_status:

        mock_fetch_metrics.return_value = {
            "total_interactions": 100,
            "avg_response_time": 1.5,
            "positive_sentiment_rate": 85.0,
            "escalated_conversations": 2,
            "intent_distribution": {"admissions": 30, "fees": 25},
            "sentiment_over_time": [{"date_str": "2024-01-01", "positive": 10, "negative": 2}]
        }
        mock_fetch_status.return_value = {
            "last_interaction": "2024-01-01T12:00:00Z",
            "system_status": "Operational",
            "active_sessions": 5,
            "recent_errors": 0
        }

        response = client.get("/")

        assert response.status_code == 200
        assert "College Bot Command Center" in response.text # Check for key title
        assert "100" in response.text # Check for metric display
        assert "Operational" in response.text # Check for status display

@patch("dashboard.app.supabase")
def test_metrics_api(mock_supabase):
    """Test the /api/metrics endpoint."""
    with patch("dashboard.app.fetch_conversation_metrics_async", new_callable=AsyncMock) as mock_fetch_metrics:
        expected_metrics = {
            "total_interactions": 50,
            "avg_response_time": 1.2,
            "positive_sentiment_rate": 90.0,
            "escalated_conversations": 1,
            "intent_distribution": {},
            "sentiment_over_time": []
        }
        mock_fetch_metrics.return_value = expected_metrics

        response = client.get("/api/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data == expected_metrics

def test_health_check_dashboard():
    """Test the dashboard's health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "dashboard"
    assert "timestamp" in data

# --- Test Chart Generation Functions (Mock Plotly) ---
@patch("plotly.graph_objects.Figure")
@patch("plotly.express.line")
def test_create_interaction_volume_chart(mock_px_line, mock_go_figure):
    """Test the interaction volume chart generation."""
    mock_fig_instance = MagicMock()
    mock_px_line.return_value = mock_fig_instance
    mock_fig_instance.to_html.return_value = "<div>Mock Chart HTML</div>"

    data = [{"date_str": "2024-01-01", "positive": 5, "negative": 2}, {"date_str": "2024-01-02", "positive": 7, "negative": 1}]
    chart_html = create_interaction_volume_chart(data)

    mock_px_line.assert_called_once() # Check if plotly function was called
    assert "Mock Chart HTML" in chart_html

@patch("plotly.graph_objects.Figure")
@patch("plotly.express.pie")
def test_create_intent_pie_chart(mock_px_pie, mock_go_figure):
    """Test the intent pie chart generation."""
    mock_fig_instance = MagicMock()
    mock_px_pie.return_value = mock_fig_instance
    mock_fig_instance.to_html.return_value = "<div>Mock Pie Chart HTML</div>"

    intent_counts = {"admissions": 30, "fees": 25, "courses": 20}
    chart_html = create_intent_pie_chart(intent_counts)

    mock_px_pie.assert_called_once() # Check if plotly function was called
    assert "Mock Pie Chart HTML" in chart_html

@patch("plotly.graph_objects.Figure")
def test_create_sentiment_gauge(mock_go_figure):
    """Test the sentiment gauge chart generation."""
    mock_fig_instance = MagicMock()
    mock_go_figure.return_value = mock_fig_instance
    mock_fig_instance.to_html.return_value = "<div>Mock Gauge HTML</div>"

    gauge_html = create_sentiment_gauge(88.5)

    mock_go_figure.assert_called_once() # Check if plotly function was called
    assert "Mock Gauge HTML" in gauge_html