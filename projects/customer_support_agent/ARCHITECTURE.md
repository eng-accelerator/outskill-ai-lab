# Customer Support Agent — Architecture

## System Overview

The Customer Support Agent is a multi-agent system that autonomously handles customer support interactions. It uses a pipeline architecture where specialized agents handle different domains (orders, billing, technical) and collaborate through structured handoffs to resolve customer issues end-to-end.

## Design Philosophy

The system follows **"functional core; imperative shell"** — internal data models and tool logic are pure functions with immutable dataclasses, while the agent orchestration layer (main.py) handles the imperative coordination. The system embraces **composition over inheritance** with agents composed from tools, handoffs, and guardrails rather than class hierarchies.

## Agentic Design Patterns Applied

| # | Pattern | How It's Applied |
|---|---------|-----------------|
| 2 | **Default Agent Loop** | Each agent follows: goal intake → context gathering (tools) → planning (instructions) → action execution (tool calls) → reflection (handoff decision) |
| 3 | **Prompt Chaining** | Sequential handoff chain: Intake → Specialist → [Escalation] → Resolution. Each agent's output feeds the next agent's context. |
| 4 | **Routing** | Intake agent classifies intent (ORDER/BILLING/TECHNICAL/COMPLEX) and routes to the appropriate specialist via handoff. Decision is explicit and logged. |
| 5 | **Parallelization** | Order, Billing, and Technical Support agents are independent specialists that can operate in parallel (fan-out from Intake). |
| 7 | **Tool Use** | 18 function tools with strict input/output schemas. Every tool has clear descriptions, typed parameters, and validated outputs. |
| 9 | **Multi-Agent** | 6 agents with single responsibility each. Communication via structured handoff messages. No circular dependencies. |
| 13 | **Exception Handling** | All specialist agents can escalate to the Escalation Agent when they cannot resolve an issue. Graceful degradation. |
| 14 | **Human-in-the-Loop** | Escalation Agent creates formal tickets for human review with full context, priority, and team assignment. |
| 19 | **Guardrails & Safety** | Input guardrail validates query has actionable data. Output guardrail prevents PII leakage, caps refunds, blocks inappropriate language. |
| 20 | **Evaluation & Monitoring** | CSAT prediction evaluates resolution quality. AgentHooks provide real-time observability of all agent actions and handoffs. |

## Agent Architecture

### Agent Responsibilities

#### 1. Intake & Router Agent (Entry Point)
- **Role**: Initial triage and routing
- **Tools**: `fetch_customer_profile`, `analyze_sentiment`
- **Handoffs**: Order Support, Billing Support, Technical Support, Escalation
- **Guardrails**: Input validation (ensures customer data and query exist)
- **Decision Logic**: Classifies intent into ORDER/BILLING/TECHNICAL/COMPLEX categories

#### 2. Order Support Agent
- **Role**: Investigate and resolve order-related issues
- **Tools**: `lookup_order`, `track_shipment`, `process_return`, `modify_order`
- **Handoffs**: Escalation (complex cases), Resolution (resolved cases)
- **Capabilities**: Track packages, initiate returns with RMA, cancel/modify orders, detect shipping delays

#### 3. Billing Support Agent
- **Role**: Investigate and resolve billing issues
- **Tools**: `get_billing_info`, `process_refund`, `update_subscription`, `check_payment_status`
- **Handoffs**: Escalation (complex cases), Resolution (resolved cases)
- **Capabilities**: Identify duplicate charges, process refunds (auto-approve ≤$500), change subscription plans

#### 4. Technical Support Agent
- **Role**: Diagnose and resolve technical issues
- **Tools**: `search_knowledge_base`, `get_system_status`, `run_diagnostics`
- **Handoffs**: Escalation (complex cases), Resolution (resolved cases)
- **Capabilities**: Search KB for solutions, check system incidents, run account diagnostics

#### 5. Escalation Agent
- **Role**: Handle complex cases requiring human intervention
- **Tools**: `escalate_to_human`, `get_agent_availability`, `create_escalation_ticket`
- **Handoffs**: Resolution (always forwards to terminal agent)
- **Capabilities**: Check team availability, create formal escalation tickets, estimate response times based on priority and customer tier

#### 6. Resolution & CSAT Agent (Terminal)
- **Role**: Compile final resolution report and predict satisfaction
- **Tools**: `generate_resolution_summary`, `predict_csat_score`
- **Handoffs**: None (terminal agent)
- **Capabilities**: Generate structured resolution summaries, predict CSAT (1-5), recommend follow-up actions

### Handoff Topology

```
                    ┌──────────────┐
                    │  Intake &    │
                    │  Router      │
                    └──┬─┬─┬─┬────┘
                       │ │ │ │
           ┌───────────┘ │ │ └───────────┐
           ▼             │ │             ▼
    ┌──────────┐         │ │      ┌──────────────┐
    │  Order   │         │ │      │  Escalation  │◄──┐
    │  Support │─────┐   │ │   ┌──│    Agent     │   │
    └──────────┘     │   │ │   │  └──────┬───────┘   │
                     │   │ │   │         │            │
           ┌─────────┼───┘ └───┼─────────┼────────┐  │
           ▼         │         │         │        │  │
    ┌──────────┐     │         │         │        │  │
    │ Billing  │─────┤         │         │        │  │
    │  Support │──┐  │         │         │        │  │
    └──────────┘  │  │         │         │        │  │
                  │  │  ┌──────┘         │        │  │
           ┌──────┼──┼──┘               │        │  │
           ▼      │  │                   │        │  │
    ┌──────────┐  │  │                   │        │  │
    │Technical │──┤  │                   │        │  │
    │  Support │──┼──┤                   │        │  │
    └──────────┘  │  │                   │        │  │
                  │  │                   │        │  │
                  ▼  ▼                   ▼        │  │
              ┌──────────────────────────────┐    │  │
              │     Resolution & CSAT        │    │  │
              │       (Terminal Agent)       │    │  │
              └──────────────────────────────┘    │  │
                                                  │  │
              Specialist agents can escalate ──────┘  │
              Escalation agent can be reached ────────┘
              directly from Intake for COMPLEX cases
```

## Data Architecture

### Domain Models

The data layer uses **frozen dataclasses** (immutable products in the algebra of types) organized by domain:

- **`models/customer.py`** — `CustomerProfile`, `SentimentScore` with `CustomerTier` and `SentimentLevel` literal types
- **`models/orders.py`** — `Order`, `OrderItem`, `Shipment`, `Return` with `OrderStatus`, `ShipmentStatus`, `ReturnStatus` literal types
- **`models/billing.py`** — `Subscription`, `Invoice`, `Payment`, `Refund` with `SubscriptionPlan`, `PaymentStatus`, `RefundStatus` literal types
- **`models/support.py`** — `SupportTicket`, `EscalationTicket`, `Resolution`, `CSATScore`, `KBArticle` with `TicketPriority`, `TicketCategory` literal types

### Scenario Data (Context Object)

The `ScenarioData` dataclass serves as the **run context** passed to all agents and tools via `RunContextWrapper[ScenarioData]`. It contains:

- Customer profile and all customer profiles
- Orders and returns
- Subscriptions, invoices, payments, refunds
- Knowledge base articles
- Support ticket
- Scenario metadata (type, description, customer query)

### Simulator Architecture

Four specialized simulators generate correlated data:

1. **Customer Simulator** — 10 diverse profiles across all tiers
2. **Order Simulator** — Scenario-specific orders with shipment tracking and returns
3. **Billing Simulator** — Subscriptions, invoices, and payments with scenario-specific issues (double charges, wrong rates)
4. **Knowledge Base Simulator** — 15 articles across 6 categories (orders, billing, technical, troubleshooting, account, general)

The **Scenario Engine** orchestrates all simulators for each of the 5 pre-built scenarios, producing a complete `ScenarioData` object with correlated data.

## Pipeline Flow

### Execution Model

```
1. Scenario Generation
   └── scenario_engine.generate_scenario(type) → ScenarioData

2. Pipeline Construction
   └── build_agent_pipeline(model, hooks) → intake_agent
       ├── Resolution (terminal, no handoffs)
       ├── Escalation → Resolution
       ├── Order Support → [Escalation, Resolution]
       ├── Billing Support → [Escalation, Resolution]
       ├── Technical Support → [Escalation, Resolution]
       └── Intake & Router → [Order, Billing, Technical, Escalation]

3. Execution
   └── Runner.run(intake_agent, input, context=ScenarioData, max_turns=40)
       ├── Input guardrail validates query
       ├── Intake classifies and routes
       ├── Specialist investigates and acts
       ├── [Optional] Escalation creates ticket
       ├── Resolution compiles report + CSAT
       └── Output guardrail validates response

4. Output
   └── Final resolution report with CSAT prediction
```

### Scenario Routing Examples

| Scenario | Intake Classification | Route | Resolution Path |
|----------|----------------------|-------|-----------------|
| `delayed_order` | ORDER | Order Support | Order Support → Resolution |
| `refund_request` | ORDER | Order Support | Order Support → Resolution |
| `billing_dispute` | BILLING | Billing Support | Billing Support → Resolution |
| `technical_issue` | TECHNICAL | Technical Support | Technical Support → Resolution |
| `complex_escalation` | COMPLEX | Escalation | Escalation → Resolution |

## Guardrails Architecture

### Input Guardrail (`input_validation.py`)

Applied to the Intake & Router Agent. Validates:
- Customer profile exists in scenario data
- Customer query is substantive (≥10 characters)
- At least one data source available (orders, billing, or knowledge base)

Tripwire triggered → pipeline stops with validation error.

### Output Guardrail (`response_safety.py`)

Applied to the Resolution & CSAT Agent. Validates:
- No credit card numbers (regex: `\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b`)
- No SSN exposure (with context-aware false positive filtering)
- No inappropriate language (10 blocked phrases)
- Refunds >$500 must mention "approval" or "manager" or "review"

Tripwire triggered → response blocked with safety message.

## Observability

### AgentHooks

The `CustomerSupportHooks` class provides real-time visibility into:
- **on_start** — Agent activation (which agent is processing)
- **on_end** — Agent completion
- **on_tool_start** — Tool invocation (which tool, by which agent)
- **on_tool_end** — Tool completion
- **on_handoff** — Agent-to-agent transfers (source → target)

### Logging

All tools and simulators use Python's `logging` module with structured messages:
- Tool invocations log input parameters and results
- Simulators log generation counts
- Pipeline logs routing decisions and configuration

## Configuration

The system uses OpenRouter as the LLM provider, configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | (required) | API key for OpenRouter |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter API endpoint |
| `OPENROUTER_MODEL` | `openai/gpt-5-mini` | Model to use via OpenRouter |

All agents share the same model instance, with individual `ModelSettings` controlling temperature (0.2 for routing/billing, 0.3 for support/resolution).
