# web_app Overview

The `web_app` component is the Gradio-based user interface for the AI Finance Assistant. It gives users a simple way to enter a finance-related question and run it through the project’s LangGraph workflow.

## Purpose

The app serves as the front-end layer for the assistant. It does not directly answer questions by itself; instead, it passes the user input to the workflow engine, which decides how to handle the request.

## Main functionality

1. Accepts a finance question from the user.
2. Sends the question to `financeApp.invoke(...)`.
3. The workflow routes the query to the most appropriate specialist agent.
4. The selected agent may use:
   - external API/tool data
   - retrieval-augmented generation (RAG)
   - or a combined approach using both
5. Returns the final response and the selected agent name to the UI.

## Interface

The web interface includes:
- a text box for entering the user question
- a `Run workflow` button
- a read-only field showing the selected agent
- a read-only field showing the workflow response

## Workflow flow

When the user submits a question:
- the UI collects the text
- it invokes the finance workflow with the input
- the top-level router classifies the question
- one of the specialist agents processes it
- the workflow returns the final answer and agent selection
- the interface displays both to the user

## Agents supported by the workflow

The underlying workflow can route to specialist agents such as:
- Finance Q&A
- Market analysis
- Portfolio analysis
- Goal planning
- News synthesis
- Tax education

## Notes

This is a lightweight interface for testing and interacting with the AI Finance workflow. It is intended to help users ask finance questions and view the workflow’s chosen specialist and generated response.
