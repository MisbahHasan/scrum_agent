import os
import requests
from requests.auth import HTTPBasicAuth
from collections import defaultdict

new_api_atlassian_key =''
class JiraAgentTools:
    def __init__(self):
        self.base_url = "https://misbhsn2611.atlassian.net/"
        self.auth = HTTPBasicAuth(
            'misbhsn2611@gmail.com',
            new_api_atlassian_key
           
        )
        self.headers = {"Content-Type": "application/json"}

    def search_issues_jql(self, jql_query: str, max_results: int = 10) -> dict:
        """Fetches issues matching a Jira Query Language (JQL) string."""
        url = f"{self.base_url}/rest/api/3/search"
        payload = {
            "jql": jql_query,
            "maxResults": max_results,
            "fields": ["summary", "status", "assignee", "priority", "description"]
        }
        response = requests.post(url, json=payload, auth=self.auth, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        return {"error": response.status_code, "message": response.text}

    def get_issue_details(self, issue_key: str) -> dict:
        """Retrieves detailed information for a specific task or story."""
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        response = requests.get(url, auth=self.auth, headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            fields = data.get("fields", {})
            return {
                "key": issue_key,
                "summary": fields.get("summary"),
                "status": fields.get("status", {}).get("name"),
                "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
                "priority": fields.get("priority", {}).get("name"),
            }
        return {"error": response.status_code, "message": response.text}

    def assign_issue(self, issue_key: str, account_id: str) -> dict:
        """Assigns or reassigns a specific Jira issue to a team member using their account ID."""
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/assignee"
        payload = {"accountId": account_id}
        response = requests.put(url, json=payload, auth=self.auth, headers=self.headers)
        
        if response.status_code in [204, 200]:
            return {"success": True, "message": f"Successfully assigned {issue_key}."}
        return {"error": response.status_code, "message": response.text}

    def update_issue_status(self, issue_key: str, transition_id: str) -> dict:
        """Moves a task across workflow stages using a transition ID."""
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
        payload = {"transition": {"id": transition_id}}
        response = requests.post(url, json=payload, auth=self.auth, headers=self.headers)
        
        if response.status_code in [204, 200]:
            return {"success": True, "message": f"Successfully transitioned {issue_key}."}
        return {"error": response.status_code, "message": response.text}

    def add_comment_to_issue(self, issue_key: str, comment_text: str) -> dict:
        """Appends a progress update or note to an existing task."""
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": comment_text
                            }
                        ]
                    }
                ]
            }
        }
        response = requests.post(url, json=payload, auth=self.auth, headers=self.headers)
        
        if response.status_code in [201, 200]:
            return {"success": True, "message": f"Comment added to {issue_key}."}
        return {"error": response.status_code, "message": response.text}
    def get_issues_in_sprint(self, sprint_id: str) -> dict:
        """Retrieves details of all issues belonging to a specific sprint using its sprint ID."""
        # Note: Jira Agile REST API uses /rest/agile/1.0/
        url = f"{self.base_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
        
        response = requests.get(url, auth=self.auth, headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            issues_summary = []
            
            for issue in data.get("issues", []):
                fields = issue.get("fields", {})
                issues_summary.append({
                    "key": issue.get("key"),
                    "summary": fields.get("summary"),
                    "status": fields.get("status", {}).get("name"),
                    "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
                    "priority": fields.get("priority", {}).get("name")
                })
            
            return {
                "sprint_id": sprint_id,
                "total_issues": len(issues_summary),
                "issues": issues_summary
            }
            
        return {"error": response.status_code, "message": response.text}

    def get_all_boards(self) -> dict:
        """Retrieves all Jira software boards and their IDs."""
        url = f"{self.base_url}/rest/agile/1.0/board"
        response = requests.get(url, auth=self.auth, headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            boards = []
            for board in data.get("values", []):
                boards.append({
                    "board_id": board.get("id"),
                    "board_name": board.get("name"),
                    "type": board.get("type") # e.g., 'scrum' or 'kanban'
                })
            return {"boards": boards}
            
        return {"error": response.status_code, "message": response.text}


    def get_active_board_view(self, board_id: int) -> dict:
        """
        Fetches issues from the active sprint of a board and groups them 
        by their status columns (e.g., To Do, In Progress, Done).
        """
        # 1. Find the active sprint ID for the board
        sprints_url = f"{self.base_url}/rest/agile/1.0/board/{board_id}/sprint?state=active"
        response = requests.get(sprints_url, auth=self.auth, headers=self.headers)
        
        if response.status_code != 200 or not response.json().get("values"):
            return {"error": "No active sprint found for this board."}
            
        active_sprint = response.json()["values"][0]
        sprint_id = active_sprint["id"]
        sprint_name = active_sprint["name"]

        # 2. Fetch all issues in this active sprint
        issues_url = f"{self.base_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
        issues_response = requests.get(issues_url, auth=self.auth, headers=self.headers)
        
        if issues_response.status_code != 200:
            return {"error": issues_response.status_code, "message": issues_response.text}

        # 3. Group issues by status name (To Do, In Progress, Done)
        board_columns = defaultdict(list)
        
        for issue in issues_response.json().get("issues", []):
            fields = issue.get("fields", {})
            status = fields.get("status", {}).get("name", "Unknown")
            
            issue_data = {
                "key": issue.get("key"),
                "summary": fields.get("summary"),
                "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned"
            }
            board_columns[status].append(issue_data)

        return {
            "sprint_name": sprint_name,
            "columns": dict(board_columns)
        }


jira = JiraAgentTools()

def get_active_board_view(input:str):
    '''
    Fetches the view of a Jira board based on the provided input.

    Args:
        input (str): The identifier for the Jira board view to fetch.

    Returns:
        The fetched board view.
    '''
    return jira.get_active_board_view(input)
def get_issue_details(input:str):
    '''
    Fetches the details of a Jira issue based on the provided input.

    Args:
        input (str): The identifier for the Jira issue to fetch.

    Returns:
        The fetched issue details.
    '''
    return jira.get_issue_details(input)
def get_all_boards():
    '''
    Fetches all Jira boards.

    Args:No Input required
        

    Returns:
        The fetched boards.
    '''
    return jira.get_all_boards()


    
   
