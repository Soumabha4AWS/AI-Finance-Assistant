import os
import sys

# Ensure UTF-8 output on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure 'src' is on sys.path so we can import 'workflow'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from workflow.aiFinanceWorkflow import financeApp

test_queries = [
    "What is the difference between a mutual fund and an exchange-traded fund (ETF)?",
    "Can you review my current asset allocation and tell me if my portfolio is too tech-heavy?",
    "What is the current stock trend for Apple (AAPL) today, and how are the major indices trading?",
    "How much should I save monthly if I want to retire in 25 years with a $2 million nest egg, given a moderate risk appetite?",
    "Can you summarize the main takeaways and market impact from today's Federal Reserve rate decision announcement?",
    "What are the contribution limits and tax advantages of a Roth IRA compared to a Traditional IRA?",
    "Can you explain how compound interest works with a simple example?",
    "Evaluate my stock holdings and check if my portfolio is properly diversified across different sectors.",
    "What are analysts saying in today's financial headlines about the recent surge in oil prices?",
    "Help me map out a milestone plan to save for a house down payment over the next 4 years.",
    "My portfolio consists of 60% US stocks, 20% bonds, 10% gold, and 10% cash. Is it well diversified?",
	"Analyze my investment portfolio and identify sectors where I'm overexposed.",
	"What is happening with NVIDIA stock today, and why is it moving?",
	"Give me today's market outlook for the S&P 500 and Nasdaq",
	"I want to save ₹20 lakh in 8 years for my daughter's education. How much should I invest every month?"
	"Help me create an investment plan based on my moderate risk appetite and retirement goal."
	"Summarize today's biggest financial news and explain how it might affect investors.",
	"What is the difference between tax deductions and tax credits?",
    "What is Locus of Control (Internal vs External) in goal ownership?",
    "What is a Golden Cross vs Death Cross moving average signal?",
    "What is NEWTS (NEWS Topic-focused Summarization) Benchmark?",
    "How are Cryptocurrencies and Digital Assets taxed?"
]

for query in test_queries:
    print(f"\nUser Query: {query}")
    final_state = financeApp.invoke({"user_input": query, "selected_agent": "", "response": ""})
    print("AI Response:", final_state.get("response", "<no response>"))

