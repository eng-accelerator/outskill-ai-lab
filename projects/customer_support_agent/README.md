# Customer Support Agent

A production-grade, multi-agent AI customer support system built with the **OpenAI Agents SDK** and **OpenRouter**. The system acts as an autonomous customer support representative, capable of classifying customer intents, looking up orders and billing, searching knowledge bases, processing refunds/returns, escalating complex cases, and generating resolution summaries with CSAT predictions.

## Key Features

- **6 Specialized Agents** — Intake & Router, Order Support, Billing Support, Technical Support, Escalation, Resolution & CSAT
- **18 Function Tools** — CRM lookup, sentiment analysis, order tracking, refund processing, subscription management, knowledge base search, diagnostics, escalation management, CSAT prediction
- **5 Pre-built Scenarios** — Delayed order, refund request, billing dispute, technical issue, complex multi-issue escalation
- **Simulated Data Stack** — Self-contained with realistic customer profiles, orders, billing data, and knowledge base articles
- **Input & Output Guardrails** — Validates queries have actionable context; prevents PII leakage, caps unauthorized refunds, blocks inappropriate language
- **CSAT Prediction** — Predicts customer satisfaction score (1-5) based on resolution quality, response time, and customer tier

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- OpenRouter API key

### Installation

1. Clone the repository and navigate to the project root:

```bash
cd outskill-ai-lab
```

2. Install dependencies:

```bash
uv sync
```

3. Create a `.env` file in the project root with your OpenRouter API key:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-5-mini
```

## Usage

### Interactive Mode

Run the agent with interactive scenario selection:

```bash
PYTHONPATH=projects uv run python -m customer_support_agent.main
```

This presents a menu of 5 scenarios to choose from.

### Programmatic Mode

Run a specific scenario programmatically:

```python
import asyncio
from customer_support_agent.main import run_customer_support

async def main():
    report = await run_customer_support("billing_dispute")
    print(report)

asyncio.run(main())
```

### Available Scenarios

| Scenario | Description |
|----------|-------------|
| `delayed_order` | Customer with order stuck in transit for 5 days, no tracking updates |
| `refund_request` | Customer received defective Smart Watch Pro X, wants full refund |
| `billing_dispute` | Enterprise customer double-charged, wants refund + plan downgrade |
| `technical_issue` | Customer can't log in, API authentication failures, blocking work |
| `complex_escalation` | Angry platinum customer: wrong item + billing overcharge + product bug |

## Project Structure

```
projects/customer_support_agent/
├── __init__.py
├── main.py                          # Entry point, pipeline orchestration
├── utils/
│   └── config.py                    # OpenRouter configuration
├── models/
│   ├── customer.py                  # CustomerProfile, SentimentScore
│   ├── orders.py                    # Order, OrderItem, Shipment, Return
│   ├── billing.py                   # Subscription, Invoice, Payment, Refund
│   └── support.py                   # SupportTicket, Resolution, CSATScore, KBArticle
├── simulators/
│   ├── customer_simulator.py        # 10 diverse customer profiles
│   ├── order_simulator.py           # Orders, shipments, returns per scenario
│   ├── billing_simulator.py         # Subscriptions, invoices, payments per scenario
│   ├── knowledge_base_simulator.py  # 15 FAQ and documentation articles
│   └── scenario_engine.py           # Orchestrates all simulators for 5 scenarios
├── tools/
│   ├── customer_tools.py            # fetch_customer_profile, analyze_sentiment
│   ├── order_tools.py               # lookup_order, track_shipment, process_return, modify_order
│   ├── billing_tools.py             # get_billing_info, process_refund, update_subscription, check_payment_status
│   ├── knowledge_tools.py           # search_knowledge_base, get_system_status, run_diagnostics
│   ├── escalation_tools.py          # escalate_to_human, get_agent_availability, create_escalation_ticket
│   └── resolution_tools.py          # generate_resolution_summary, predict_csat_score
├── guardrails/
│   ├── input_validation.py          # Validates customer query has actionable content
│   └── response_safety.py           # PII protection, refund caps, language safety
└── agents/
    ├── intake_router.py             # Intake & Router Agent (entry point)
    ├── order_support.py             # Order Support Agent
    ├── billing_support.py           # Billing Support Agent
    ├── technical_support.py         # Technical Support Agent
    ├── escalation.py                # Escalation Agent
    └── resolution.py                # Resolution & CSAT Agent (terminal)
```

## Agent Pipeline

```
Customer Query
      │
      ▼
┌─────────────────┐
│  Intake & Router │──── classifies intent, analyzes sentiment, fetches customer profile
│     Agent        │     routes to specialist based on intent
└──┬──────┬───────┘
   │      │      │      │
   ▼      ▼      ▼      ▼
┌──────┐┌──────┐┌─────────┐┌───────────┐
│Order ││Billing││Technical││Escalation │
│Support││Support││ Support ││  Agent    │
│Agent ││Agent ││ Agent   ││           │
└──┬───┘└──┬───┘└──┬─────┘└─────┬─────┘
   │       │       │             │
   ├───────┴───────┴─────────────┤
   ▼                             ▼
┌─────────────────┐    ┌─────────────────┐
│  Escalation     │    │ Resolution &    │
│     Agent       │───>│   CSAT Agent    │
└─────────────────┘    │  (terminal)     │
                       └─────────────────┘
```

## Tools Reference

| Module | Tool | Description |
|--------|------|-------------|
| customer_tools | `fetch_customer_profile` | Fetch CRM profile by customer ID |
| customer_tools | `analyze_sentiment` | Keyword-based sentiment analysis |
| order_tools | `lookup_order` | Full order details with items and status |
| order_tools | `track_shipment` | Real-time shipment tracking with delay analysis |
| order_tools | `process_return` | Initiate return with RMA number |
| order_tools | `modify_order` | Cancel, expedite, or update orders |
| billing_tools | `get_billing_info` | Subscription, invoices, payment history |
| billing_tools | `process_refund` | Issue refund (auto-approve ≤$500) |
| billing_tools | `update_subscription` | Change subscription plan |
| billing_tools | `check_payment_status` | Verify specific payment details |
| knowledge_tools | `search_knowledge_base` | Search FAQ and documentation |
| knowledge_tools | `get_system_status` | Check service health and incidents |
| knowledge_tools | `run_diagnostics` | Account health diagnostics |
| escalation_tools | `escalate_to_human` | Create human escalation request |
| escalation_tools | `get_agent_availability` | Check human team availability |
| escalation_tools | `create_escalation_ticket` | Formal escalation ticket |
| resolution_tools | `generate_resolution_summary` | Compile interaction summary |
| resolution_tools | `predict_csat_score` | Predict customer satisfaction (1-5) |
