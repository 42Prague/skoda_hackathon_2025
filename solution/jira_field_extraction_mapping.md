# Jira API Field Extraction Mapping

This document shows how to extract specific fields from Jira API responses to create a simplified JSON structure.

## Structure Overview

The JSON structure supports:
- **Multiple projects** (array of projects)
- **Multiple stories** per project (array of stories)
- **Multiple subtasks** per story (array of subtasks)
- **Multiple assignees** per story/subtask (array of assignees)

## Simplified JSON Structure (Multiple Projects, Stories, and Subtasks)

```json
{
  "user_id": "5b10a2844c20165700ede21g",
  "projects": [
    {
      "project_id": "10000",
      "project_key": "DEMO",
      "project_name": "Demo Project",
      "project_description": "This project was created as an example for REST.",
      "stories": [
        {
          "story_id": "10002",
          "story_key": "DEMO-1",
          "story_p_id": "10000",
          "story_p_key": "DEMO",
          "story_description": { ... },
          "story_description_text": "Implement user authentication system",
          "story_points": 8,
          "story_assignees": [
            {
              "account_id": "5b10a2844c20165700ede21g",
              "display_name": "Mia Krystof",
              "email_address": "mia@example.com"
            },
            {
              "account_id": "5b10a2844c20165700ede22h",
              "display_name": "John Smith",
              "email_address": "john.smith@example.com"
            }
          ],
          "subtasks": [
            {
              "subtask_id": "10003",
              "subtask_key": "DEMO-2",
              "subtask_p_id": "10000",
              "subtask_p_key": "DEMO",
              "subtask_description": { ... },
              "subtask_description_text": "Design login UI components",
              "subtask_points": 3,
              "subtask_assignees": [ ... ]
            }
          ]
        }
      ]
    }
  ]
}
```

**Note**: See `jira_simplified_response.json` for the complete example with multiple projects, stories, and subtasks.

## Field Mapping from Jira API Responses

### 1. User ID
**Source**: `GET /rest/api/3/user?accountId={accountId}`
```json
{
  "accountId": "5b10a2844c20165700ede21g"  // → user_id
}
```

### 2. Project Information
**Source**: `GET /rest/api/3/project/{projectIdOrKey}`
```json
{
  "id": "10000",                    // → project.project_id
  "key": "DEMO",                    // → project.project_key
  "name": "Demo Project",           // → project.project_name
  "description": "This project..."  // → project.project_description
}
```

### 3. Story Information
**Source**: `GET /rest/api/3/issue/{issueIdOrKey}?expand=names,renderedFields`

#### Story ID and Key
```json
{
  "id": "10002",      // → story.story_id
  "key": "DEMO-1"     // → story.story_key
}
```

#### Story Project ID
```json
{
  "fields": {
    "project": {
      "id": "10000",   // → story.story_p_id
      "key": "DEMO"    // → story.story_p_key
    }
  }
}
```

#### Story Description
```json
{
  "fields": {
    "description": {
      "type": "doc",
      "version": 1,
      "content": [...]  // → story.story_description (ADF format)
    }
  }
}
```

**For plain text description**, use `expand=renderedFields`:
```json
{
  "renderedFields": {
    "description": "Main order flow broken"  // → story.story_description_text
  }
}
```

#### Story Points
**Note**: Story points is a custom field. You need to find the custom field ID first.

1. Find the field ID: `GET /rest/api/3/field/search?query=Story%20Points`
2. Extract from issue:
```json
{
  "fields": {
    "customfield_10001": 5  // → story.story_points (field ID varies)
  }
}
```

**Alternative**: Use field names with `expand=names`:
```json
{
  "names": {
    "customfield_10001": "Story Points"
  },
  "fields": {
    "customfield_10001": 5
  }
}
```

#### Story Assignees
**Standard Assignee** (single assignee):
```json
{
  "fields": {
    "assignee": {
      "accountId": "5b10a2844c20165700ede21g",  // → story.story_assignees[].account_id
      "displayName": "Mia Krystof",             // → story.story_assignees[].display_name
      "emailAddress": "mia@example.com"          // → story.story_assignees[].email_address
    }
  }
}
```

**Multiple Assignees**: Standard Jira only supports one assignee per issue. For multiple assignees, you need to:
1. Check for custom fields that support multiple users (e.g., `customfield_XXXXX` with type `multiuserpicker`)
2. Search for the field: `GET /rest/api/3/field/search?query=Assignee&type=custom`
3. Extract from issue: `fields.customfield_XXXXX` (returns array of user objects)

#### Subtasks
**Source**: `GET /rest/api/3/issue/{issueIdOrKey}?expand=subtasks`

```json
{
  "fields": {
    "subtasks": [
      {
        "id": "10003",           // → story.subtasks[].subtask_id
        "key": "DEMO-2",          // → story.subtasks[].subtask_key
        "fields": {
          "project": {
            "id": "10000",        // → story.subtasks[].subtask_p_id
            "key": "DEMO"         // → story.subtasks[].subtask_p_key
          },
          "description": { ... }, // → story.subtasks[].subtask_description
          "assignee": { ... }     // → story.subtasks[].subtask_assignees[]
        }
      }
    ]
  }
}
```

**Note**: To get full subtask details (including story points), you need to make separate API calls for each subtask: `GET /rest/api/3/issue/{subtaskKey}?expand=names,renderedFields`

## Complete Extraction Flow (Multiple Projects/Stories)

### Step 1: Get All Projects (or specific projects)
```bash
GET /rest/api/3/project/search
# Or get specific project:
GET /rest/api/3/project/{projectKey}
```

### Step 2: Get All Issues for Each Project
```bash
GET /rest/api/3/search?jql=project=DEMO AND issuetype=Story&expand=names,renderedFields,subtasks
```

### Step 3: For Each Story, Extract Data
From story response:
- Extract: `id`, `key`, `fields.project.id`, `fields.project.key`
- Extract: `fields.description` and `renderedFields.description`
- Extract: `fields.assignee.accountId` (and check for custom multi-assignee fields)
- Extract: `fields.subtasks[]` array

### Step 4: Get Story Points Field ID (once per Jira instance)
```bash
GET /rest/api/3/field/search?query=Story%20Points&type=custom
```
- Extract field ID (e.g., "customfield_10001")
- Use this ID to get story points: `fields.customfield_10001`

### Step 5: Get User Details for Each Assignee
For each unique `accountId` found:
```bash
GET /rest/api/3/user?accountId={accountId}
```

### Step 6: Get Full Details for Each Subtask
For each subtask in `fields.subtasks[]`:
```bash
GET /rest/api/3/issue/{subtaskKey}?expand=names,renderedFields
```
Extract the same fields as for stories (description, points, assignees)

## Python Extraction Example (Multiple Projects/Stories/Subtasks)

```python
import requests
import json
from typing import Dict, List, Any

def extract_jira_data(base_url: str, auth: tuple, project_keys: List[str] = None) -> Dict:
    """
    Extract Jira data for multiple projects, stories, and subtasks.
    
    Args:
        base_url: Jira base URL (e.g., "https://your-domain.atlassian.net")
        auth: Authentication tuple (username, api_token) or (email, api_token)
        project_keys: List of project keys to extract. If None, extracts all projects.
    
    Returns:
        Dictionary with user_id and projects array
    """
    
    # Find story points field ID (once)
    story_points_field_id = find_story_points_field(base_url, auth)
    
    # Get projects
    if project_keys:
        projects_data = []
        for project_key in project_keys:
            project_data = get_project_data(base_url, auth, project_key, story_points_field_id)
            if project_data:
                projects_data.append(project_data)
    else:
        # Get all projects
        projects_url = f"{base_url}/rest/api/3/project/search"
        projects_response = requests.get(projects_url, auth=auth).json()
        projects_data = []
        for project in projects_response.get("values", []):
            project_data = get_project_data(
                base_url, auth, project["key"], story_points_field_id
            )
            if project_data:
                projects_data.append(project_data)
    
    # Get user_id from first assignee found (or use a specific user)
    user_id = None
    if projects_data and projects_data[0].get("stories"):
        first_story = projects_data[0]["stories"][0]
        if first_story.get("story_assignees"):
            user_id = first_story["story_assignees"][0]["account_id"]
    
    return {
        "user_id": user_id,
        "projects": projects_data
    }


def find_story_points_field(base_url: str, auth: tuple) -> str:
    """Find the custom field ID for Story Points."""
    field_search_url = f"{base_url}/rest/api/3/field/search?query=Story%20Points&type=custom"
    fields_response = requests.get(field_search_url, auth=auth).json()
    for field in fields_response.get("values", []):
        if "Story Points" in field.get("name", "") or "Story point" in field.get("name", ""):
            return field["id"]
    return None


def get_project_data(base_url: str, auth: tuple, project_key: str, story_points_field_id: str) -> Dict:
    """Get project data with all stories and subtasks."""
    # Get project details
    project_url = f"{base_url}/rest/api/3/project/{project_key}"
    project_response = requests.get(project_url, auth=auth).json()
    
    # Get all stories for this project
    jql = f"project={project_key} AND issuetype=Story"
    search_url = f"{base_url}/rest/api/3/search?jql={jql}&expand=names,renderedFields,subtasks&maxResults=100"
    search_response = requests.get(search_url, auth=auth).json()
    
    stories = []
    for issue in search_response.get("issues", []):
        story = extract_story_data(issue, story_points_field_id, base_url, auth)
        if story:
            stories.append(story)
    
    return {
        "project_id": project_response.get("id"),
        "project_key": project_response.get("key"),
        "project_name": project_response.get("name"),
        "project_description": project_response.get("description", ""),
        "stories": stories
    }


def extract_story_data(issue: Dict, story_points_field_id: str, base_url: str, auth: tuple) -> Dict:
    """Extract story data from issue response."""
    fields = issue.get("fields", {})
    project = fields.get("project", {})
    
    # Extract assignees (standard + custom multi-assignee if exists)
    assignees = []
    assignee = fields.get("assignee")
    if assignee:
        user_data = get_user_data(base_url, auth, assignee.get("accountId"))
        assignees.append(user_data)
    
    # Check for custom multi-assignee field
    for field_key, field_value in fields.items():
        if field_key.startswith("customfield_") and isinstance(field_value, list):
            # Check if it's a user picker field
            if field_value and isinstance(field_value[0], dict) and "accountId" in field_value[0]:
                for user_obj in field_value:
                    user_data = get_user_data(base_url, auth, user_obj.get("accountId"))
                    if user_data and user_data not in assignees:
                        assignees.append(user_data)
    
    # Extract story points
    story_points = fields.get(story_points_field_id) if story_points_field_id else None
    
    # Extract subtasks
    subtasks = []
    subtasks_list = fields.get("subtasks", [])
    for subtask in subtasks_list:
        subtask_key = subtask.get("key")
        if subtask_key:
            subtask_data = get_subtask_data(base_url, auth, subtask_key, story_points_field_id)
            if subtask_data:
                subtasks.append(subtask_data)
    
    return {
        "story_id": issue.get("id"),
        "story_key": issue.get("key"),
        "story_p_id": project.get("id"),
        "story_p_key": project.get("key"),
        "story_description": fields.get("description"),
        "story_description_text": issue.get("renderedFields", {}).get("description", ""),
        "story_points": story_points,
        "story_assignees": assignees,
        "subtasks": subtasks
    }


def get_subtask_data(base_url: str, auth: tuple, subtask_key: str, story_points_field_id: str) -> Dict:
    """Get full subtask data."""
    subtask_url = f"{base_url}/rest/api/3/issue/{subtask_key}?expand=names,renderedFields"
    subtask_response = requests.get(subtask_url, auth=auth).json()
    
    fields = subtask_response.get("fields", {})
    project = fields.get("project", {})
    
    # Extract assignees
    assignees = []
    assignee = fields.get("assignee")
    if assignee:
        user_data = get_user_data(base_url, auth, assignee.get("accountId"))
        assignees.append(user_data)
    
    story_points = fields.get(story_points_field_id) if story_points_field_id else None
    
    return {
        "subtask_id": subtask_response.get("id"),
        "subtask_key": subtask_response.get("key"),
        "subtask_p_id": project.get("id"),
        "subtask_p_key": project.get("key"),
        "subtask_description": fields.get("description"),
        "subtask_description_text": subtask_response.get("renderedFields", {}).get("description", ""),
        "subtask_points": story_points,
        "subtask_assignees": assignees
    }


def get_user_data(base_url: str, auth: tuple, account_id: str) -> Dict:
    """Get user data by account ID."""
    if not account_id:
        return None
    
    user_url = f"{base_url}/rest/api/3/user?accountId={account_id}"
    try:
        user_response = requests.get(user_url, auth=auth).json()
        return {
            "account_id": user_response.get("accountId"),
            "display_name": user_response.get("displayName"),
            "email_address": user_response.get("emailAddress", "")
        }
    except:
        return {
            "account_id": account_id,
            "display_name": "Unknown",
            "email_address": ""
        }


# Usage example:
# result = extract_jira_data(
#     base_url="https://your-domain.atlassian.net",
#     auth=("your-email@example.com", "your-api-token"),
#     project_keys=["DEMO", "PROD"]  # or None for all projects
# )
# print(json.dumps(result, indent=2))
```

## Notes

- **Story Points**: This is typically a custom field. The field ID varies by Jira instance. You need to search for it first.
- **Description**: The `description` field is in ADF (Atlassian Document Format). Use `renderedFields.description` for plain text.
- **Multiple Assignees**: Standard Jira only supports one assignee. If you need multiple, check for custom fields.
- **User Email**: May be hidden based on privacy settings. Use the user endpoint to get it if available.

