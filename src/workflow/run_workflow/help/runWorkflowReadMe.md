# test_aiFinanceWorkflow.py Overview

`src/workflow/run_workflow/test_aiFinanceWorkflow.py` is a script designed to exercise the main AI Finance workflow with a set of example finance questions. It is used to validate that the router, specialist agents, and final response generation work as expected across a range of financial topics.

## Purpose

This file acts as a lightweight test harness for the workflow. Instead of testing individual components one by one, it runs multiple realistic user queries through the full `financeApp` pipeline and prints each response.

## What it does

The script:
1. adds the project `src` directory to `sys.path` so the workflow modules can be imported correctly
2. imports `financeApp` from `workflow.aiFinanceWorkflow`
3. defines a list of sample finance queries covering categories such as:
   - investments and portfolio allocation
   - stock and market trends
   - retirement planning
   - tax education
   - financial news and market summaries
   - goal planning and behavioral finance concepts
   - compound interest and financial basics
4. loops through each query
5. invokes the workflow with a state like:
   - `user_input`
   - `selected_agent`
   - `response`
6. prints the final response returned by the workflow

## Example query coverage

The test script includes questions such as:
- comparing mutual funds and ETFs
- reviewing portfolio diversification
- checking current market sentiment for a stock
- planning retirement contributions
- summarizing Fed announcements
- explaining Roth vs Traditional IRAs
- describing compound interest
- reviewing stock sector exposure
- analyzing financial news headlines
- planning a house down payment strategy
- explaining tax deductions vs credits
- discussing investment risk and goals

## Why it matters

This file is useful for:
- verifying the workflow still routes to the correct agents
- checking whether specialist logic is working
- validating that LLM-based responses can be generated for multiple finance domains
- quickly running a smoke test before using the application interactively

## Output

For each query, the script prints:
- the user question
- the workflow response from `financeApp.invoke(...)`

This makes it easy to quickly inspect whether the assistant is responding correctly for a variety of financial scenarios.
