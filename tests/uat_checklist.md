# User Acceptance Testing Checklist

## Core workflow checks
- [ ] A user can enter a finance question in the Gradio UI.
- [ ] The UI accepts a query and starts the workflow.
- [ ] The workflow selects the expected specialist agent.
- [ ] The response field displays the final answer.
- [ ] The selected agent field updates correctly.

## Domain validation scenarios
- [ ] Finance basics question routes to `finance_qa`.
- [ ] Portfolio allocation question routes to `portfolio_analysis`.
- [ ] Market trend question routes to `market_analysis`.
- [ ] Retirement or goal-planning question routes to `goal_planning`.
- [ ] News summary question routes to `news_synthesizer`.
- [ ] Tax question routes to `tax_education`.
- [ ] Unclear or unsupported question falls back to `default`.

## Data and integration checks
- [ ] The workflow handles missing or empty input gracefully.
- [ ] The workflow does not crash when tool access is unavailable.
- [ ] The MCP server starts and stops correctly during workflow execution.
- [ ] The app still works when API-backed features are not configured.

## UX and reliability checks
- [ ] The page remains usable on a standard desktop browser.
- [ ] The user sees a clear response even when the agent is not certain.
- [ ] Errors are not silently swallowed; they appear as plain output or fallback handling.
- [ ] The interface remains responsive for short queries.

## Exit criteria
- [ ] All smoke-test scenarios pass.
- [ ] No critical workflow errors occur during repeated use.
- [ ] The app returns understandable answers for common finance prompts.
