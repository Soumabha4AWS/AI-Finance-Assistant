# aiFinanceWorkflow.py Overview

`src/workflow/aiFinanceWorkflow.py` defines the main LangGraph workflow for the AI Finance Assistant. It is the orchestration layer that receives a user question, routes it to the correct specialist agent, and returns the final response.

## Purpose

This file builds the workflow graph that powers the assistant. Instead of handling finance logic directly, it coordinates the work between:
- a router node
- multiple specialist agents
- a default fallback agent
- a managed MCP server lifecycle

## Workflow state

The workflow uses a `FinanceWorkflowState` TypedDict with these fields:
- `user_input`: the original question from the user
- `selected_agent`: the route selected by the router
- `response`: the final answer returned by the selected agent

This gives the workflow a consistent structure for passing data from node to node.

## Graph structure

The workflow is created using `StateGraph`, then nodes are added for:
- `router`
- `default`
- `finance_qa`
- `portfolio_analysis`
- `market_analysis`
- `goal_planning`
- `news_synthesizer`
- `tax_education`

The graph starts at `START` and routes into the `router` node.

## Routing behavior

The `router` node calls `router_node`, and then the workflow uses `route_decision` to choose the next step. The router can send the request to:
- `finance qa`
- `portfolio analysis`
- `market analysis`
- `goal planning`
- `news synthesizer`
- `tax education`
- `default`

These edges are defined in `add_conditional_edges(...)`, so the workflow dynamically selects the best specialist based on the user input.

## Specialist execution

Each specialist node corresponds to a finance domain-specific handler, such as:
- `finance_qa_node`
- `portfolio_analysis_node`
- `market_analysis_node`
- `goal_planning_node`
- `news_synthesizer_node`
- `tax_education_node`

Each of these agents is responsible for producing the final response for that domain. After the relevant specialist completes its work, the graph ends at `END`.

## Default handling

If the router cannot confidently determine the best domain, it sends the request to the `default` node. This provides a fallback answer path so the application continues working even when a request is unclear or unsupported by the specialist routes.

## MCP lifecycle management

This workflow also integrates with MCP server lifecycle management through:
- `begin_workflow()`
- `end_workflow()`

The `ManagedFinanceApp` wrapper ensures that each workflow invocation starts the required MCP service lifecycle before processing begins and shuts it down afterward in a `finally` block. This helps ensure external tool access is available when needed.

## App wrapper

The file defines:
- `compiled_finance_app = financeWorkflow.compile()`
- `ManagedFinanceApp`
- `financeApp = ManagedFinanceApp()`

`financeApp` is the main runtime object used by the UI and other callers. It exposes the compiled graph and wraps `invoke` and `ainvoke` calls so they run with the proper MCP lifecycle handling.

## Overall functionality

In summary, `aiFinanceWorkflow.py` is the central orchestrator for the AI Finance Assistant. It:
1. receives a user question,
2. routes it to the right domain specialist,
3. executes the selected agent,
4. returns the final response in the workflow state,
5. manages the MCP service lifecycle required for tool-based operations.

This makes it the core execution path for the application’s question-answering system.
