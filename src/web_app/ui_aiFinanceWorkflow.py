import sys
from pathlib import Path
from typing import Any

import gradio as gr


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from workflow.aiFinanceWorkflow import financeApp


dark_theme = gr.themes.Base(
    primary_hue="emerald",
    neutral_hue="slate",
).set(
    body_background_fill="#0b1120",
    body_text_color="#e2f0e7",
    background_fill_primary="#111827",
    background_fill_secondary="#1e293b",
    block_background_fill="#111827",
    block_border_color="#334155",
    input_background_fill="#0f172a",
    input_border_color="#334155",
    button_primary_background_fill="#10b981",
    button_primary_background_fill_hover="#059669",
    button_primary_text_color="#052e24",
)


def run_workflow(user_query: str) -> tuple[str, str]:
    result: dict[str, Any] = financeApp.invoke(
        {"user_input": user_query, "selected_agent": "", "response": ""}
    )
    return result.get("selected_agent", "<no agent selected>"), result.get(
        "response", "<no response>"
    )


with gr.Blocks(title="AI Finance Workflow Tester") as demo:
    gr.Markdown("# AI Finance Workflow Tester")
    gr.Markdown("Enter a finance question to run it through the finance workflow.")

    user_query = gr.Textbox(
        label="Your question",
        placeholder="For example: How does compound interest work?",
        lines=4,
    )
    run_button = gr.Button("Run workflow", variant="primary")
    selected_agent = gr.Textbox(label="Selected agent", interactive=False)
    response = gr.Textbox(label="Workflow response", lines=12, interactive=False)

    run_button.click(
        fn=run_workflow,
        inputs=user_query,
        outputs=[selected_agent, response],
    )
    user_query.submit(
        fn=run_workflow,
        inputs=user_query,
        outputs=[selected_agent, response],
    )


if __name__ == "__main__":
    demo.launch(theme=dark_theme)
