# Jira Agent Integration (`JiraAgentTools`)

A Python client toolkit designed for AI agents and automation scripts to interact with Atlassian Jira Cloud using the **Jira REST API v3** and **Agile REST API v1**.

---

## ⚠️ Security Notice

> **Do not hardcode API tokens directly into your source code.**
> Always load credentials through environment variables or a secrets manager. If your token was previously committed or shared in plain text, revoke it immediately at [Atlassian API Tokens Console](https://id.atlassian.com/manage-profile/security/api-tokens).

---

## Setup & Configuration

### 1. Requirements

Install the dependencies:

```bash
pip install requests python-dotenv
```

### 2. Environment Variables

Create a `.env` file in the root of your project:

```env
JIRA_BASE_URL="https://your-domain.atlassian.net"
JIRA_USER_EMAIL="user@example.com"
JIRA_API_TOKEN="your_atlassian_api_token_here"
```

---

## Architecture Overview

```
                      ┌──────────────────────────────────────┐
                      │            JiraAgentTools            │
                      └──────────────────┬───────────────────┘
                                         │
        ┌────────────────────────────────┼───────────────────────────────┐
        ▼                                ▼                               ▼
┌──────────────┐                 ┌───────────────┐               ┌───────────────┐
│ Search & Read│                 │ Issue Actions │               │ Agile & Board │
├──────────────┤                 ├───────────────┤               ├───────────────┤
│ • JQL Search │                 │ • Assignee    │               │ • Boards List │
│ • Issue Info │                 │ • Transitions │               │ • Active View │
└──────────────┘                 │ • Comments    │               │ • Sprint Data │
                                 └───────────────┘               └───────────────┘
```

---

## Class Reference: `JiraAgentTools`

### Initialization

```python
class JiraAgentTools:
    def __init__(self, base_url: str = None, email: str = None, api_token: str = None):
        ...
```

* Defaults to reading `JIRA_BASE_URL`, `JIRA_USER_EMAIL`, and `JIRA_API_TOKEN` from the environment if parameters are omitted.
* Authenticates using HTTP Basic Auth (`email` + `api_token`).

---

### Core Methods

#### 1. Issue Management

##### `search_issues_jql(jql_query: str, max_results: int = 10) -> dict`
Executes a Jira Query Language (JQL) search and extracts summary, status, assignee, priority, and description fields.
* **Endpoint:** `POST /rest/api/3/search`
* **Parameters:**
  * `jql_query` (*str*): The JQL search string (e.g., `"project = DEV AND status = 'In Progress'"`).
  * `max_results` (*int*): Limit on number of issues returned (default: `10`).
* **Returns:** Raw JSON dictionary of search results or an error response dictionary.

##### `get_issue_details(issue_key: str) -> dict`
Retrieves a normalized representation of an individual Jira issue.
* **Endpoint:** `GET /rest/api/3/issue/{issue_key}`
* **Parameters:**
  * `issue_key` (*str*): Ticket key (e.g., `"PROJ-123"`).
* **Returns:**
  ```python
  {
      "key": "PROJ-123",
      "summary": "Fix login redirect bug",
      "status": "In Progress",
      "assignee": "Jane Doe",
      "priority": "High"
  }
  ```

##### `assign_issue(issue_key: str, account_id: str) -> dict`
Reassigns an existing ticket to a team member using their Atlassian Account ID.
* **Endpoint:** `PUT /rest/api/3/issue/{issue_key}/assignee`
* **Parameters:**
  * `issue_key` (*str*): Ticket key (e.g., `"PROJ-123"`).
  * `account_id` (*str*): Atlassian account ID string.

##### `update_issue_status(issue_key: str, transition_id: str) -> dict`
Advances an issue through its lifecycle using workflow transition IDs.
* **Endpoint:** `POST /rest/api/3/issue/{issue_key}/transitions`
* **Parameters:**
  * `issue_key` (*str*): Ticket identifier.
  * `transition_id` (*str*): ID representing the workflow step.

##### `add_comment_to_issue(issue_key: str, comment_text: str) -> dict`
Adds a comment to an issue formatted as Atlassian Document Format (ADF v1).
* **Endpoint:** `POST /rest/api/3/issue/{issue_key}/comment`
* **Parameters:**
  * `issue_key` (*str*): Ticket identifier.
  * `comment_text` (*str*): Plaintext comment to insert.

---

#### 2. Agile & Board Operations

##### `get_all_boards() -> dict`
Lists all accessible Jira Agile/Kanban boards.
* **Endpoint:** `GET /rest/agile/1.0/board`
* **Returns:** List of boards containing `board_id`, `board_name`, and `type`.

##### `get_issues_in_sprint(sprint_id: str) -> dict`
Fetches and aggregates all issues assigned to a designated sprint.
* **Endpoint:** `GET /rest/agile/1.0/sprint/{sprint_id}/issue`
* **Parameters:**
  * `sprint_id` (*str*): The numerical ID of the sprint.

##### `get_active_board_view(board_id: int) -> dict`
Finds the active sprint on a given board and organizes its issues grouped by status column.
* **Endpoint(s):**
  1. `GET /rest/agile/1.0/board/{board_id}/sprint?state=active`
  2. `GET /rest/agile/1.0/sprint/{sprint_id}/issue`
* **Returns:**
  ```python
  {
      "sprint_name": "Sprint 14",
      "columns": {
          "To Do": [{"key": "PROJ-101", "summary": "...", "assignee": "..."}],
          "In Progress": [{"key": "PROJ-98", "summary": "...", "assignee": "..."}],
          "Done": [{"key": "PROJ-92", "summary": "...", "assignee": "..."}]
      }
  }
  ```

---

## Complete Example Implementation

```python
import os
from collections import defaultdict
from typing import Any, Dict
import requests
from requests.auth import HTTPBasicAuth


class JiraAgentTools:
    def __init__(
        self,
        base_url: str = None,
        email: str = None,
        api_token: str = None,
    ):
        self.base_url = (base_url or os.getenv("JIRA_BASE_URL", "")).rstrip("/")
        email = email or os.getenv("JIRA_USER_EMAIL")
        api_token = api_token or os.getenv("JIRA_API_TOKEN")

        if not self.base_url or not email or not api_token:
            raise ValueError("Jira base URL, email, and API token must be provided.")

        self.auth = HTTPBasicAuth(email, api_token)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def search_issues_jql(self, jql_query: str, max_results: int = 10) -> Dict[str, Any]:
        url = f"{self.base_url}/rest/api/3/search"
        payload = {
            "jql": jql_query,
            "maxResults": max_results,
            "fields": ["summary", "status", "assignee", "priority", "description"],
        }
        response = requests.post(url, json=payload, auth=self.auth, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return {"error": response.status_code, "message": response.text}

    def get_issue_details(self, issue_key: str) -> Dict[str, Any]:
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        response = requests.get(url, auth=self.auth, headers=self.headers)
        if response.status_code == 200:
            fields = response.json().get("fields", {})
            return {
                "key": issue_key,
                "summary": fields.get("summary"),
                "status": fields.get("status", {}).get("name"),
                "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
                "priority": fields.get("priority", {}).get("name"),
            }
        return {"error": response.status_code, "message": response.text}

    def assign_issue(self, issue_key: str, account_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/assignee"
        payload = {"accountId": account_id}
        response = requests.put(url, json=payload, auth=self.auth, headers=self.headers)
        if response.status_code in [200, 204]:
            return {"success": True, "message": f"Successfully assigned {issue_key}."}
        return {"error": response.status_code, "message": response.text}

    def update_issue_status(self, issue_key: str, transition_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
        payload = {"transition": {"id": transition_id}}
        response = requests.post(url, json=payload, auth=self.auth, headers=self.headers)
        if response.status_code in [200, 204]:
            return {"success": True, "message": f"Successfully transitioned {issue_key}."}
        return {"error": response.status_code, "message": response.text}

    def add_comment_to_issue(self, issue_key: str, comment_text: str) -> Dict[str, Any]:
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": comment_text}],
                    }
                ],
            }
        }
        response = requests.post(url, json=payload, auth=self.auth, headers=self.headers)
        if response.status_code in [200, 201]:
            return {"success": True, "message": f"Comment added to {issue_key}."}
        return {"error": response.status_code, "message": response.text}

    def get_all_boards(self) -> Dict[str, Any]:
        url = f"{self.base_url}/rest/agile/1.0/board"
        response = requests.get(url, auth=self.auth, headers=self.headers)
        if response.status_code == 200:
            boards = [
                {
                    "board_id": board.get("id"),
                    "board_name": board.get("name"),
                    "type": board.get("type"),
                }
                for board in response.json().get("values", [])
            ]
            return {"boards": boards}
        return {"error": response.status_code, "message": response.text}

    def get_issues_in_sprint(self, sprint_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
        response = requests.get(url, auth=self.auth, headers=self.headers)
        if response.status_code == 200:
            issues = []
            for issue in response.json().get("issues", []):
                fields = issue.get("fields", {})
                issues.append({
                    "key": issue.get("key"),
                    "summary": fields.get("summary"),
                    "status": fields.get("status", {}).get("name"),
                    "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
                    "priority": fields.get("priority", {}).get("name"),
                })
            return {"sprint_id": sprint_id, "total_issues": len(issues), "issues": issues}
        return {"error": response.status_code, "message": response.text}

    def get_active_board_view(self, board_id: int) -> Dict[str, Any]:
        sprints_url = f"{self.base_url}/rest/agile/1.0/board/{board_id}/sprint?state=active"
        response = requests.get(sprints_url, auth=self.auth, headers=self.headers)

        if response.status_code != 200 or not response.json().get("values"):
            return {"error": "No active sprint found for this board."}

        active_sprint = response.json()["values"][0]
        sprint_id = active_sprint["id"]
        sprint_name = active_sprint["name"]

        issues_url = f"{self.base_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
        issues_resp = requests.get(issues_url, auth=self.auth, headers=self.headers)

        if issues_resp.status_code != 200:
            return {"error": issues_resp.status_code, "message": issues_resp.text}

        board_columns = defaultdict(list)
        for issue in issues_resp.json().get("issues", []):
            fields = issue.get("fields", {})
            status = fields.get("status", {}).get("name", "Unknown")
            board_columns[status].append({
                "key": issue.get("key"),
                "summary": fields.get("summary"),
                "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
            })

        return {"sprint_name": sprint_name, "columns": dict(board_columns)}
```