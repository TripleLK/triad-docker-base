# Lab Equipment API Documentation

This document describes how to use the lab equipment API endpoints for creating and updating lab equipment pages.

## Authentication

All API requests require authentication using a token. You can include the token in one of these ways:

1. **Bearer Token in Authorization Header (recommended)**:
   ```
   Authorization: Bearer your-api-token
   ```

2. **Token Query Parameter** (for testing only):
   ```
   ?token=your-api-token
   ```

## Creating API Tokens

To create an API token, use the management command:

```bash
python manage.py create_api_token "Token Name" --description "Optional description"
```

This will output the token value, which should be kept secure.

## API Endpoints

### Create or Update Lab Equipment

**Endpoint**: `/api/lab-equipment/`
**Method**: `POST`
**Content-Type**: `application/json`

This endpoint can be used to create new lab equipment pages or update existing ones. If a `slug` is provided and matches an existing page, it will update that page. Otherwise, it will create a new page.

#### Request Body Schema

```json
{
  "title": "Equipment Name",                    // Required
  "slug": "equipment-slug",                     // Optional, will be auto-generated if not provided
  "short_description": "Brief description",     // Required
  "full_description": "<p>HTML content</p>",    // Optional
  "source_url": "https://example.com/source",   // Optional
  "is_published": true,                         // Optional, defaults to true
  "tags": ["tag1", "tag2"],                     // Optional
  
  "specifications": [                           // Optional
    {
      "name": "Group Name",                     // Required
      "specs": [                                // Required
        {
          "key": "Spec Name",                   // Required
          "value": "Spec Value"                 // Required
        }
      ]
    }
  ],
  
  "features": [                                 // Optional
    "Feature 1",
    "Feature 2"
  ],
  
  "models": [                                   // Optional
    {
      "name": "Model Name",                     // Required
      "model_number": "MODEL-100",              // Optional
      "specifications": [                       // Optional
        {
          "name": "Group Name",
          "specs": [
            {
              "key": "Spec Name",
              "value": "Spec Value"
            }
          ]
        }
      ]
    }
  ],
  
  "images": [                                   // Optional
    "https://example.com/image1.jpg",           // URL strings for external images
    {
      "external_image_url": "https://example.com/image2.jpg"  // Alternative format
    }
  ]
}
```

#### Response

**Success (201 Created)** - New page created:
```json
{
  "success": true,
  "message": "Lab equipment page created successfully",
  "page_id": 123,
  "page_slug": "equipment-slug"
}
```

**Success (200 OK)** - Existing page updated:
```json
{
  "success": true,
  "message": "Lab equipment page updated successfully",
  "page_id": 123,
  "page_slug": "equipment-slug"
}
```

**Error (400 Bad Request)** - Invalid data:
```json
{
  "success": false,
  "error": "Missing required fields: title, short_description"
}
```

**Error (401 Unauthorized)** - Authentication failed:
```json
{
  "success": false,
  "error": "API token is missing. Provide a token in the Authorization header."
}
```

## Usage Examples

### Python Example

```python
import requests
import json

API_TOKEN = "your-api-token"
API_ENDPOINT = "https://your-site.com/api/lab-equipment/"

data = {
    "title": "Test Equipment",
    "short_description": "A test equipment",
    "specifications": [
        {
            "name": "Dimensions",
            "specs": [
                {"key": "Height", "value": "10 inches"},
                {"key": "Width", "value": "5 inches"}
            ]
        }
    ]
}

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

response = requests.post(
    API_ENDPOINT, 
    headers=headers, 
    data=json.dumps(data)
)

print(response.json())
```

### cURL Example

```bash
curl -X POST \
  -H "Authorization: Bearer your-api-token" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Equipment","short_description":"A test equipment"}' \
  https://your-site.com/api/lab-equipment/
``` 