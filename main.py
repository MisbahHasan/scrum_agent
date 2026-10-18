
from dotenv import load_dotenv
import os
load_dotenv()
import asyncio
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from scrumtools import get_active_board_view, get_issue_details, get_all_boards

import os
import logging
import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import  InMemorySessionService
from google.adk.tools.agent_tool import AgentTool
from google.genai import types
from dotenv import load_dotenv
import os
load_dotenv()
# Ignore warnings from ADK and Gemini APIs
logging.getLogger("google.adk.runners").setLevel(logging.ERROR)
logging.getLogger("google_genai.types").setLevel(logging.ERROR)

from google.genai import types
# Required for ADK to use Vertex AI (Service Account) instead of a public API Key
# SERVICE_ACCOUNT_PATH = r"alert-vista-487414-k1-e2fe728f240f.json"
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_PATH
# os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
# os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT")
# os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("GOOGLE_CLOUD_LOCATION") 
# Define the app_name, user_id and session_id for testing the agents
APP_NAME = "shop_concierge_app"
USER_ID = "user_1"

session_service = InMemorySessionService()

async def test_agent(query, agent):
  """Sends a query to the agent and prints the final response."""

  print(f"\n>>> User Query: {query}")

  # Create a session
  session = await session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
  )

  # Create a Runner
  runner = Runner(
      app_name=APP_NAME,
      agent=agent,
      session_service=session_service,
  )

  # Prepare the user's message in ADK format
  content = types.Content(role='user', parts=[types.Part(text=query)])

  final_response_text = None
  # Consume the full stream so ADK can clean up its tracing context.
  async for event in runner.run_async(user_id=USER_ID, session_id=session.id, new_message=content):
      if event.is_final_response():
          if event.content and event.content.parts:
             final_response_text = event.content.parts[0].text
  print(f"<<< Agent Response: {final_response_text}")

from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
# zapierjira_key='YzljMWZkYjUtNzQ2OS00NzJiLThhZTgtYmU4OGVlOTgyMjc2OmdEMFRZc2ZJMFFHWDRPUXRtTkd2TnNSL1VwQzMvK09MQ1k3UGxOY0k4TzQ9'

atlassian_api_key = ''
jira_key = '
  '
# api_key = 'OWFhZWYyZGUtMTRlMi00ZmFlLTljMTItMzI4NGRmNWM4YzBmOi9HY2lFTlNWOUxMaElqWGhEeHhBbnh6VmR6aHJjcGNiZ2YwOEFMSlNkb2c9'


# )

jira_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://mcp.atlassian.com/v2/mcp?tools=all",
        headers={
            "Authorization": f"Bearer {atlassian_api_key}"
        }
    )
)

scrum_agent2 = Agent(
    model='gemini-2.5-pro',
    name='scrum_agent2',
    description=('''
      You are a helpful, efficient, and precise Jira Project Management Assistant AI. Your core job is to help users interact with their Atlassian Jira boards smoothly through natural language.


        '''),
    instruction='''
    You are a Jira Project Management Assistant AI. 
    Your role is to assist users in managing their Jira boards, issues, and sprints effectively.
      You can fetch details about active sprints, specific issues, and all available boards. 
      Use the provided tools to retrieve information from Jira based on user queries.


    ''',
    tools=[get_active_board_view, get_issue_details, get_all_boards],
)
from google.adk.tools import google_search



# agent = Agent(
#     model="gemini-2.5-pro",
#     name="agent",
#     instruction="You are an ai assistant and your job is to answer questions",
#     tools=[google_search],
# )

story_creator_agent = Agent(
    model='gemini-2.5-pro',
    name='scrum_agent1',
    description=('''
         You are an expert Agile Technical Product Manager and Engineering Lead. 
Analyze the provided technical document, architecture blueprint, or PRD, and break it down into granular, well-defined Jira user stories that cover all implementation phases required.
        '''),
    instruction='''
1. **Analyze the Document:** Identify core modules, architectural layers, features, or workflow phases outlined in the source text.
2. **Break Down Stories:** Create distinct Jira user stories covering the full scope.
3. use jira_toolset to create tasks in the atlassian jira board in space Data Science Project .
4. site:https://misbhsn2611.atlassian.net/, key:DSP


    ''',
    tools=[jira_toolset],
)

scrum_master = Agent(
    model='gemini-2.5-pro',
    name='scrum_master',
    description=('''
        The primary orchestrator agent responsible for managing agile project workflows, sprint tracking, and backlog refinement. It coordinates specialized sub-agents.
        '''),
    instruction='''
You are the Scrum Agent, the lead orchestrator and Scrum Master assistant for agile software development workflows. Your primary responsibility is to understand user intents related to project management, sprint planning, and backlog tracking, and intelligently delegate tasks to your specialized sub-agents.

## Core Responsibilities:
1. **Intent Analysis:** Evaluate incoming requests from developers, product owners, or team leads to determine the appropriate agile action (e.g., creating user stories, fetching ticket details, updating sprint boards, or assigning tasks).
2. **Orchestration & Delegation:** Route tasks to the correct sub-agents (e.g., invoking the Create Story Agent(story_creator_agent) for new Jira tickets, or the Read Story Agent (scrum_agent2) for querying backlog status and acceptance criteria).
3. **Workflow Coordination:** Handle multi-step agile operations by chaining sub-agent outputs together when necessary (e.g., reading an existing story, updating its parameters, and pushing changes back).
4. **Agile Best Practices:** Maintain adherence to Scrum principles, ensuring user stories follow clear formats, acceptance criteria are defined, and blockers are flagged.

## Operational Guidelines:
- Always confirm the context (project key, sprint, or board) before executing destructive or creation workflows.
- Synthesize responses from sub-agents into clear, professional, and actionable summaries for the user.
- If a request is ambiguous or lacks necessary details (like story points, descriptions, or acceptance criteria), prompt the user for clarification before delegating to sub-agents.
    ''',
    sub_agents=[story_creator_agent, scrum_agent2],
)



# Import your ADK components, session_service, APP_NAME, USER_ID, and scrum_agent1 here
# from your_module import session_service, APP_NAME, USER_ID, scrum_agent1, types, Runner, jira_toolset

app = Flask(__name__)
CORS(app)
# --- Mock or imported variables (Replace with your actual imports) ---
APP_NAME = "ScrumAgentApp"
USER_ID = "user_123"

async def run_scrum_agent(query, agent):
    """Sends a query to the agent and returns the final response text."""
    print(f"\n>>> User Query: {query}")

    # Create a session
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
    )

    # Create a Runner
    runner = Runner(
        app_name=APP_NAME,
        agent=agent,
        session_service=session_service,
    )

    # Prepare the user's message in ADK format
    content = types.Content(role='user', parts=[types.Part(text=query)])

    final_response_text = "No response generated."
    
    # Consume the full stream so ADK can clean up its tracing context.
    async for event in runner.run_async(user_id=USER_ID, session_id=session.id, new_message=content):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text

    return final_response_text


@app.route("/", methods=["GET"])
def index():
    """Serves the standalone index.html file."""
    return send_file("uiindex.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    # Handle both JSON requests (from fetch) or form submissions
    if request.is_json:
        data = request.get_json()
        query = data.get("query")
    else:
        query = request.form.get("query")

    if not query:
        return jsonify({"success": False, "error": "Query cannot be empty."}), 400

    # Run the asynchronous agent function synchronously via asyncio
    try:
        response_text = asyncio.run(run_scrum_agent(query, scrum_agent2))
        return jsonify({"success": True, "response": response_text})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run()
