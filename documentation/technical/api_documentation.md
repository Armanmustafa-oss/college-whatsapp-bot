# API Documentation: College WhatsApp Bot

## Overview
This document details the API endpoints exposed by the College WhatsApp Bot application. The primary purpose is to handle incoming webhooks from Twilio for WhatsApp messages and provide health checks and metrics.

## Base URL
The base URL for the API is the root of your deployed application (e.g., `https://your-app-name.up.railway.app`).

## Authentication
*   **Webhook Endpoint (`/webhook`):** Twilio authenticates the request using its signature. No additional API key is required for receiving messages *from* Twilio. Securing the endpoint against unauthorized *calls to* the bot requires other mechanisms (e.g., rate limiting, potentially validating the `From` number against a known list if needed).
*   **Other Endpoints:** No standard API key authentication is implemented for internal endpoints like `/health` or `/metrics`. Access should be controlled by network policies or the deployment platform.

## Endpoints

### 1. Webhook Handler (Twilio)

*   **Endpoint:** `POST /webhook`
*   **Purpose:** Receives incoming message notifications from Twilio's WhatsApp Business API.
*   **Authentication:** Implicitly authenticated by Twilio using request signature validation (recommended practice, though not strictly required by Twilio itself, it's good security).
*   **Request Body (Form Data):**
    *   `From` (string, required): The sender's WhatsApp number (e.g., `whatsapp:+1234567890`).
    *   `Body` (string, required): The text content of the message sent by the user.
    *   `To` (string): The WhatsApp number the message was sent to (your bot's number).
    *   `MessageSid` (string): A unique identifier for the incoming message from Twilio.
    *   *(Other Twilio fields may be present but are not used by the core logic)*
*   **Response:**
    *   **Success:** `200 OK` with a plain text response of "OK".
    *   **Error (Twilio Error):** `400 Bad Request` with an error message.
    *   **Error (Internal Server Error):** `500 Internal Server Error` with an error message.
*   **Example Request (from Twilio):**
    ```http
    POST /webhook HTTP/1.1
    Host: your-app-name.up.railway.app
    Content-Type: application/x-www-form-urlencoded

    From=whatsapp%3A%2B1234567890&Body=Hi%20there%21&To=whatsapp%3A%2B0987654321&MessageSid=SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    ```
*   **Example Response (Success):**
    ```text
    OK
    ```

### 2. Health Check

*   **Endpoint:** `GET /health`
*   **Purpose:** Provides a simple health check endpoint for load balancers, monitoring tools, or deployment platforms to verify the application is running.
*   **Authentication:** None.
*   **Request Body:** None.
*   **Response:**
    *   **Success:** `200 OK`
        *   **Body (JSON):**
            ```json
            {
                "status": "ok",
                "timestamp": "2024-01-15T10:30:00.123456Z",
                "environment": "production"
            }
            ```
*   **Example Request:**
    ```http
    GET /health HTTP/1.1
    Host: your-app-name.up.railway.app
    ```
*   **Example Response:**
    ```json
    {
        "status": "ok",
        "timestamp": "2024-01-15T10:30:00.123456Z",
        "environment": "production"
    }
    ```

### 3. Bot Metrics (Internal/Optional)

*   **Endpoint:** `GET /metrics` (Defined in `bot/main.py` - example implementation)
*   **Purpose:** Exposes internal performance metrics collected by the `PerformanceTracker`. This is primarily for custom monitoring tools or debugging. *Note: For standard metrics exposition (like Prometheus), a dedicated library would be used.*
*   **Authentication:** None (by default).
*   **Request Body:** None.
*   **Response:**
    *   **Success:** `200 OK`
        *   **Body (JSON):** Structure depends on the `PerformanceTracker.get_current_metrics()` implementation. Example:
            ```json
            {
                "response_time_general_avg": {
                    "count": 150,
                    "avg": 1.234,
                    "min": 0.5,
                    "max": 4.1,
                    "p95": 2.8
                },
                "api_call_duration_groq_avg": {
                    "count": 148,
                    "avg": 0.678,
                    "min": 0.3,
                    "max": 1.2,
                    "p95": 1.0
                }
            }
            ```
*   **Example Request:**
    ```http
    GET /metrics HTTP/1.1
    Host: your-app-name.up.railway.app
    ```
*   **Example Response:**
    ```json
    {
        "response_time_general_avg": {
            "count": 150,
            "avg": 1.234,
            "min": 0.5,
            "max": 4.1,
            "p95": 2.8
        },
        "api_call_duration_groq_avg": {
            "count": 148,
            "avg": 0.678,
            "min": 0.3,
            "max": 1.2,
            "p95": 1.0
        }
    }
    ```

### 4. Dashboard Endpoints

*   **Base URL:** The dashboard runs as a separate service (if defined in `Procfile`).
*   **Primary Endpoint:** `GET /` (Root path of the dashboard service).
*   **Purpose:** Serves the interactive FastAPI dashboard application.
*   **Authentication:** Currently no authentication implemented in the provided dashboard code. This should be added for production using FastAPI's security features if access control is required.
*   **Response:** Serves the main HTML page containing Plotly charts and metrics.

## Error Codes

*   `200 OK`: Request processed successfully.
*   `400 Bad Request`: Client error (e.g., invalid request format from Twilio, missing required fields).
*   `500 Internal Server Error`: Server error occurred while processing the request.

## Notes

*   The primary interaction mechanism with the bot *for receiving messages* is the Twilio webhook (`/webhook`). This is not a standard REST API intended for general programmatic access *by external clients*.
*   The `/health` and `/metrics` endpoints are for operational/monitoring purposes.
*   Rate limiting logic is implemented within the `/webhook` handler based on the `From` number.
*   All data exchange with external services (Twilio, Groq, Supabase) happens internally within the application logic.