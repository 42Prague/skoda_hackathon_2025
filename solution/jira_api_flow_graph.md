# Jira API v3 - Endpoint Flow Graph

This document shows the relationships and follow-up flows between Jira REST API v3 endpoints.

## Main Flow Diagram

```mermaid
graph TD
    Start([Start: Issue Key/ID]) --> GetIssue[GET Issue Endpoint]
    
    GetIssue --> ExtractData{Extract Data from Issue}
    
    ExtractData -->|Extract assignee.accountId| GetUser[GET User Endpoint]
    ExtractData -->|Extract project.key| GetProject[GET Project Endpoint]
    ExtractData -->|Extract attachment array id| GetAttachment[GET Attachment Endpoint]
    ExtractData -->|Extract customfield| GetFieldDef[GET Field Search Endpoint]
    ExtractData -->|Extract issue key| GetComments[GET Comments Endpoint]
    ExtractData -->|Extract subtasks array key| GetSubtasks[GET Subtask Endpoint]
    
    GetUser --> UserData[(User Details)]
    GetProject --> ProjectData[(Project Details)]
    GetAttachment --> AttachmentData[(Attachment Metadata)]
    GetFieldDef --> FieldData[(Field Definition)]
    GetComments --> CommentData[(Comments)]
    GetSubtasks --> SubtaskData[(Subtask Details)]
    
    style GetIssue fill:#e1f5ff
    style GetUser fill:#fff4e1
    style GetProject fill:#fff4e1
    style GetAttachment fill:#fff4e1
    style GetFieldDef fill:#fff4e1
    style GetComments fill:#fff4e1
    style GetSubtasks fill:#fff4e1
```

## Detailed Relationship Graph

```mermaid
graph LR
    subgraph IssueEndpoint["Issue Endpoint"]
        Issue[GET Issue]
        IssueFields[fields object]
        Issue --> IssueFields
    end
    
    subgraph ExtractedData["Extracted Data"]
        Assignee[assignee.accountId]
        ProjectKey[project.key]
        Attachments[attachment array id]
        CustomFields[customfield]
        Subtasks[subtasks array key]
        Comments[comment array id]
    end
    
    subgraph FollowUpEndpoints["Follow-up Endpoints"]
        User[GET User]
        Project[GET Project]
        Attachment[GET Attachment]
        FieldSearch[GET Field Search]
        CommentEndpoint[GET Comments]
        SubtaskIssue[GET Subtask]
    end
    
    IssueFields --> Assignee
    IssueFields --> ProjectKey
    IssueFields --> Attachments
    IssueFields --> CustomFields
    IssueFields --> Subtasks
    IssueFields --> Comments
    
    Assignee -->|accountId| User
    ProjectKey -->|projectKey| Project
    Attachments -->|id| Attachment
    CustomFields -->|field ID| FieldSearch
    Subtasks -->|key| SubtaskIssue
    Comments -->|issueKey| CommentEndpoint
    
    style Issue fill:#4a90e2,color:#fff
    style User fill:#f5a623,color:#fff
    style Project fill:#f5a623,color:#fff
    style Attachment fill:#f5a623,color:#fff
    style FieldSearch fill:#f5a623,color:#fff
    style CommentEndpoint fill:#f5a623,color:#fff
    style SubtaskIssue fill:#f5a623,color:#fff
```

## Data Extraction Flow

```mermaid
flowchart TD
    A[Issue Response JSON] --> B{Parse fields object}
    
    B --> C[assignee.accountId]
    B --> D[project.key]
    B --> E[attachment array]
    B --> F[customfield]
    B --> G[subtasks array]
    B --> H[comment array]
    
    C --> I[User API Call]
    D --> J[Project API Call]
    E --> K[Attachment API Call]
    F --> L[Field Search API Call]
    G --> M[Subtask API Call]
    H --> N[Comment API Call]
    
    I --> O[User Details]
    J --> P[Project Description]
    K --> Q[Attachment Metadata]
    L --> R[Field Definition]
    M --> S[Subtask Details]
    N --> T[Comment Details]
    
    style A fill:#e1f5ff
    style O fill:#d4edda
    style P fill:#d4edda
    style Q fill:#d4edda
    style R fill:#d4edda
    style S fill:#d4edda
    style T fill:#d4edda
```

## Complete Workflow Example

```mermaid
sequenceDiagram
    participant Client
    participant IssueAPI as Issue API
    participant UserAPI as User API
    participant ProjectAPI as Project API
    participant FieldAPI as Field API
    participant CommentAPI as Comment API
    
    Client->>IssueAPI: GET issue with expand=subtasks
    IssueAPI-->>Client: Issue JSON with fields
    
    Note over Client: Extract assignee.accountId
    Client->>UserAPI: GET user by accountId
    UserAPI-->>Client: User details
    
    Note over Client: Extract project.key
    Client->>ProjectAPI: GET project by key
    ProjectAPI-->>Client: Project description
    
    Note over Client: Extract customfield value
    Client->>FieldAPI: GET field search query=Skills
    FieldAPI-->>Client: Field definition
    
    Note over Client: Extract issue key
    Client->>CommentAPI: GET comments for issue
    CommentAPI-->>Client: Comments array
    
    Note over Client: Extract subtasks array key
    loop For each subtask
        Client->>IssueAPI: GET subtask by key
        IssueAPI-->>Client: Subtask details
    end
```

## Field Mapping Reference

### From Issue Response → Follow-up Calls

| Issue Field Path | Extracted Value | Follow-up Endpoint | Purpose |
|-----------------|----------------|-------------------|---------|
| `fields.assignee.accountId` | `"5b10a2844c20165700ede21g"` | `GET /rest/api/3/user?accountId=xxx` | Get assignee details |
| `fields.project.key` | `"EX"` | `GET /rest/api/3/project/EX` | Get project description |
| `fields.attachment[].id` | `10000` | `GET /rest/api/3/attachment/10000` | Get attachment metadata |
| `fields.customfield_10000` | Field value | `GET /rest/api/3/field/search?query=Skills` | Get field definition |
| `fields.sub-tasks[].outwardIssue.key` | `"ED-2"` | `GET /rest/api/3/issue/ED-2` | Get subtask details |
| `key` | `"DEMO-1"` | `GET /rest/api/3/issue/DEMO-1/comment` | Get all comments |

## Common Use Cases

### Use Case 1: Get Complete Issue Information
```
1. GET /rest/api/3/issue/{key}?expand=subtasks,names,renderedFields
   ↓ Extract: assignee.accountId, project.key, customfield_XXXXX
2. GET /rest/api/3/user?accountId={accountId}
3. GET /rest/api/3/project/{projectKey}
4. GET /rest/api/3/field/search?query=Skills
```

### Use Case 2: Get Issue with All Attachments
```
1. GET /rest/api/3/issue/{key}
   ↓ Extract: attachment[].id
2. For each attachment:
   GET /rest/api/3/attachment/{id}
   GET /rest/api/3/attachment/content/{id} (download)
```

### Use Case 3: Get Issue with All Subtasks
```
1. GET /rest/api/3/issue/{key}?expand=subtasks
   ↓ Extract: sub-tasks[].outwardIssue.key
2. For each subtask:
   GET /rest/api/3/issue/{subtaskKey}
```

### Use Case 4: Get Issue with Comments
```
1. GET /rest/api/3/issue/{key}
   ↓ Extract: key
2. GET /rest/api/3/issue/{key}/comment?startAt=0&maxResults=50
```

## Notes

- **Expand Parameter**: Use `expand=subtasks,names,renderedFields` to get subtasks and readable field names in a single call
- **Pagination**: Comments and field search support pagination with `startAt` and `maxResults`
- **Custom Fields**: Custom field IDs follow pattern `customfield_XXXXX` where XXXXX is the field ID
- **Account IDs**: Always use `accountId` (not username) for user lookups in v3 API
- **ADF Format**: Description and comment bodies use Atlassian Document Format (structured JSON)

