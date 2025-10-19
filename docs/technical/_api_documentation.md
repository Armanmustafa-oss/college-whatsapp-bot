
#### File: `docs/technical/3_api_documentation.md`

```markdown
# API Documentation

## Public Endpoints

### POST /webhook
- **Purpose**: Receive messages from Twilio
- **Authentication**: Twilio signature validation
- **Rate Limit**: 100 requests/minute per phone number
- **Request Body**: Twilio webhook format
- **Response**: `{"status": "ok"}`

### GET /health
- **Purpose**: Health check for monitoring
- **Authentication**: None
- **Response**: `{"status": "healthy", "version": "2.0"}`

## Admin Endpoints (Authenticated)

### GET /api/metrics
- **Purpose**: Fetch dashboard metrics
- **Authentication**: Bearer token required
- **Response**: JSON with KPIs
- **Parameters**: `days_back` (default: 30)

### GET /api/conversations
- **Purpose**: Fetch recent conversations
- **Authentication**: Bearer token required
- **Parameters**: 
  - `limit` (default: 20)
  - `language` (optional)
  - `date_from` (optional)

### POST /api/content/update
- **Purpose**: Update knowledge base content
- **Authentication**: Bearer token required
- **Request Body**: 
  ```json
  {
    "document_id": "string",
    "content": "string"
  }

