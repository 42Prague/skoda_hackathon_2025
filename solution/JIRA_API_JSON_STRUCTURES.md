# Jira Cloud Platform REST API v3 - JSON Structures

This document contains the JSON structures and schemas extracted from the [Jira Cloud Platform REST API v3 documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#version).

## Table of Contents

- [Error Collection Schema](#error-collection-schema)
- [Pagination Response](#pagination-response)
- [Resource Expansion](#resource-expansion)
- [MCP Integration](#mcp-integration)

---

## Error Collection Schema

The standard error response structure used by Jira Cloud Platform REST API v3.

### Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "id": "https://docs.atlassian.com/jira/REST/schema/error-collection#",
  "title": "Error Collection",
  "type": "object",
  "properties": {
    "errorMessages": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Array of error messages"
    },
    "errors": {
      "type": "object",
      "patternProperties": {
        ".+": {
          "type": "string"
        }
      },
      "additionalProperties": false,
      "description": "Object containing field-specific error messages"
    },
    "status": {
      "type": "integer",
      "description": "HTTP status code"
    }
  },
  "additionalProperties": false
}
```

### Example Error Response

```json
{
  "errorMessages": [
    "The issue key 'INVALID-123' does not exist."
  ],
  "errors": {
    "summary": "Summary is required",
    "project": "Project key is invalid"
  },
  "status": 404
}
```

### MCP Reference

When using MCP (Model Context Protocol) to interact with Jira API:

```typescript
// MCP tool call for error handling
{
  "tool": "jira_api_call",
  "errorHandling": {
    "schema": "error-collection",
    "validate": true
  }
}
```

---

## Pagination Response

Standard pagination structure for operations that return collections of items.

### Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Pagination Response",
  "type": "object",
  "properties": {
    "startAt": {
      "type": "integer",
      "description": "Index of the first item returned in the page",
      "minimum": 0
    },
    "maxResults": {
      "type": "integer",
      "description": "Maximum number of items that a page can return",
      "minimum": 1
    },
    "total": {
      "type": "integer",
      "description": "Total number of items contained in all pages (may change as client requests subsequent pages)",
      "minimum": 0
    },
    "isLast": {
      "type": "boolean",
      "description": "Indicates whether the page returned is the last one"
    },
    "values": {
      "type": "array",
      "description": "Array of result items",
      "items": {}
    }
  },
  "required": ["startAt", "maxResults", "values"]
}
```

### Example Pagination Response

```json
{
  "startAt": 0,
  "maxResults": 10,
  "total": 200,
  "isLast": false,
  "values": [
    {
      "id": "10000",
      "key": "PROJ-1",
      "name": "Example Project"
    },
    {
      "id": "10001",
      "key": "PROJ-2",
      "name": "Another Project"
    }
  ]
}
```

### Query Parameters

- `startAt`: Starting index (default: 0)
- `maxResults`: Maximum items per page (varies by operation)
- `orderBy`: Field to order by (e.g., `?orderBy=name`, `?orderBy=-name` for descending)

### MCP Reference

```typescript
// MCP tool call with pagination
{
  "tool": "jira_list_issues",
  "parameters": {
    "startAt": 0,
    "maxResults": 50,
    "orderBy": "-updated"
  },
  "pagination": {
    "autoPaginate": true,
    "maxPages": 10
  }
}
```

---

## Resource Expansion

Resources can be expanded to include nested objects using the `expand` query parameter.

### Expansion Example

```json
{
  "expand": "widgets,names,renderedFields",
  "self": "https://your-domain.atlassian.net/rest/api/3/resource/KEY-1",
  "id": "10000",
  "key": "KEY-1",
  "widgets": {
    "widgets": [
      {
        "id": "widget-1",
        "name": "Widget One"
      }
    ],
    "size": 5
  },
  "names": {
    "summary": "Summary",
    "description": "Description"
  },
  "renderedFields": {
    "summary": "<p>Rendered Summary</p>",
    "description": "<p>Rendered Description</p>"
  }
}
```

### Expansion Syntax

- Single expansion: `?expand=names`
- Multiple expansions: `?expand=names,renderedFields`
- Nested expansion: `?expand=names.widgets` (using dot notation)

### MCP Reference

```typescript
// MCP tool call with expansion
{
  "tool": "jira_get_issue",
  "parameters": {
    "issueKey": "PROJ-1",
    "expand": ["names", "renderedFields", "changelog"]
  }
}
```

---

## Common Request/Response Patterns

### Issue Object (Simplified)

```json
{
  "expand": "operations,versionedRepresentations,editmeta,changelog,renderedFields",
  "id": "10000",
  "self": "https://your-domain.atlassian.net/rest/api/3/issue/10000",
  "key": "PROJ-1",
  "fields": {
    "summary": "Example Issue",
    "description": {
      "type": "doc",
      "version": 1,
      "content": [
        {
          "type": "paragraph",
          "content": [
            {
              "type": "text",
              "text": "Issue description"
            }
          ]
        }
      ]
    },
    "status": {
      "self": "https://your-domain.atlassian.net/rest/api/3/status/1",
      "description": "The issue is open and ready for the assignee to start work on it.",
      "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png",
      "name": "To Do",
      "id": "1",
      "statusCategory": {
        "self": "https://your-domain.atlassian.net/rest/api/3/statuscategory/2",
        "id": 2,
        "key": "new",
        "colorName": "blue-gray",
        "name": "To Do"
      }
    },
    "created": "2025-01-15T10:00:00.000+0000",
    "updated": "2025-01-15T11:00:00.000+0000"
  }
}
```

### Create Issue Request

```json
{
  "fields": {
    "project": {
      "key": "PROJ"
    },
    "summary": "New Issue Summary",
    "description": {
      "type": "doc",
      "version": 1,
      "content": [
        {
          "type": "paragraph",
          "content": [
            {
              "type": "text",
              "text": "Issue description"
            }
          ]
        }
      ]
    },
    "issuetype": {
      "name": "Bug"
    }
  }
}
```

---

## MCP Integration

### MCP Tool Definitions

When integrating Jira API with MCP, you can define tools for common operations:

#### Get Issue

```json
{
  "name": "jira_get_issue",
  "description": "Get a Jira issue by key",
  "inputSchema": {
    "type": "object",
    "properties": {
      "issueKey": {
        "type": "string",
        "description": "Issue key (e.g., PROJ-1)"
      },
      "expand": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Fields to expand"
      }
    },
    "required": ["issueKey"]
  }
}
```

#### Search Issues

```json
{
  "name": "jira_search_issues",
  "description": "Search for issues using JQL",
  "inputSchema": {
    "type": "object",
    "properties": {
      "jql": {
        "type": "string",
        "description": "JQL query string"
      },
      "startAt": {
        "type": "integer",
        "default": 0
      },
      "maxResults": {
        "type": "integer",
        "default": 50
      },
      "fields": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Fields to return"
      }
    },
    "required": ["jql"]
  }
}
```

#### Create Issue

```json
{
  "name": "jira_create_issue",
  "description": "Create a new Jira issue",
  "inputSchema": {
    "type": "object",
    "properties": {
      "fields": {
        "type": "object",
        "properties": {
          "project": {
            "type": "object",
            "properties": {
              "key": {
                "type": "string"
              }
            }
          },
          "summary": {
            "type": "string"
          },
          "description": {
            "type": "object"
          },
          "issuetype": {
            "type": "object",
            "properties": {
              "name": {
                "type": "string"
              }
            }
          }
        },
        "required": ["project", "summary", "issuetype"]
      }
    },
    "required": ["fields"]
  }
}
```

### MCP Configuration Example

```json
{
  "mcpServers": {
    "jira": {
      "command": "node",
      "args": ["jira-mcp-server.js"],
      "env": {
        "JIRA_BASE_URL": "https://your-domain.atlassian.net",
        "JIRA_EMAIL": "your-email@example.com",
        "JIRA_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

---

## API Version Information

- **API Version**: v3 (latest)
- **Base URL**: `https://<site-url>/rest/api/3/`
- **Documentation**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/

### Key Features of v3

- Support for **Atlassian Document Format (ADF)** in:
  - `body` in comments
  - `comment` in worklogs
  - `description` and `environment` fields in issues
  - `textarea` type custom fields (multi-line text fields)

---

## Authentication Headers

### Basic Authentication

```http
Authorization: Basic <base64-encoded-email:api-token>
```

### OAuth 2.0 (3LO)

```http
Authorization: Bearer <access-token>
```

### Special Headers

- `X-Atlassian-Token: no-check` - Required for multipart/form-data requests
- `X-Force-Accept-Language: true` - Force language processing
- `X-AAccountId` - Response header containing Atlassian account ID

---

## Status Codes

Standard HTTP status codes are used:

- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `204 No Content` - Successful request with no content
- `303 See Other` - Asynchronous operation (check `Location` header)
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## References

- [Jira Cloud Platform REST API v3 Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#version)
- [Atlassian Document Format](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)
- [JQL (Jira Query Language)](https://support.atlassian.com/jira-service-management-cloud/docs/use-advanced-search-with-jira-query-language-jql/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)

---

**Last Updated**: 2025-01-15  
**API Version**: v3  
**Source**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#version

