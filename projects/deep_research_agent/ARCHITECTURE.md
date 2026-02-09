# Deep Research Agent — Architecture

## System Overview

The Deep Research Agent is a multi-agent system that autonomously researches any topic by searching real external APIs, extracting full-page content, evaluating source credibility, cross-referencing claims, and synthesizing a comprehensive report with citations and confidence scores. It uses a pipeline architecture where 7 specialized agents collaborate through structured handoffs to produce a research report — like a human researcher.

Unlike the other projects in this repository, this agent uses **real external APIs** (no simulated data). It queries live web search engines, academic databases, news feeds, forums, and code repositories.

## Design Philosophy

The system follows **"functional core; imperative shell"** — internal data models are frozen/immutable dataclasses, tools are pure functions that return JSON, and the agent orchestration layer (main.py) handles the imperative coordination. The system embraces **composition over inheritance** with agents composed from tools, handoffs, and guardrails rather than class hierarchies.

## Agentic Design Patterns Applied

| # | Pattern | How It's Applied |
|---|---------|-----------------|
| 2 | **Default Agent Loop** | Each agent follows: goal intake → context gathering (tools) → planning (instructions) → action execution (tool calls) → reflection (handoff decision) |
| 3 | **Prompt Chaining** | Sequential handoff chain: Planner → Researcher → Extractor → Synthesizer → Writer. Each agent's output feeds the next agent's context. |
| 4 | **Routing** | Research Planner classifies query type (factual/comparison/analysis/current_events/technical/general) and routes to the appropriate specialist researcher via handoff. |
| 5 | **Parallelization** | Web, Academic, and News Researcher agents are independent specialists that can operate on different sub-questions (fan-out from Planner). |
| 7 | **Tool Use** | 24 function tools with strict input/output schemas. Every tool has clear descriptions, typed parameters, and validated outputs. Tools span 11 external APIs. |
| 9 | **Multi-Agent** | 7 agents with single responsibility each. Communication via structured handoff messages. No circular dependencies. |
| 10 | **Reflection** | Synthesizer Agent evaluates source credibility, extracts claims, cross-references findings, and identifies knowledge gaps before passing to Report Writer. |
| 13 | **Exception Handling** | Tools return JSON error objects instead of raising exceptions. Agents see errors and adapt strategy (e.g., fallback from Jina Reader to BeautifulSoup scraper). |
| 19 | **Guardrails & Safety** | Input guardrail validates query is substantive (≥15 chars, not harmful). Output guardrail ensures report has structure, citations, and no hallucinated URLs. |
| 20 | **Evaluation & Monitoring** | Confidence scoring evaluates research quality (0-100). AgentHooks provide real-time observability of all agent actions and handoffs. |

## Agent Architecture

### Agent Responsibilities

#### 1. Research Planner Agent (Entry Point)
- **Role**: Query decomposition, classification, and routing
- **Tools**: `tavily_web_search` (initial broad search)
- **Handoffs**: Web Researcher, Academic Researcher, News Researcher
- **Guardrails**: Input validation (query length ≥15 chars, no harmful content)
- **Decision Logic**: Classifies query into factual/comparison/analysis/current_events/technical/general, decomposes into 3-5 sub-questions, routes to appropriate specialist

#### 2. Web Researcher Agent
- **Role**: Broad web search across general sources
- **Tools**: `tavily_web_search`, `duckduckgo_text_search`, `duckduckgo_news_search`
- **Handoffs**: Content Extractor
- **Capabilities**: General factual lookups, comparative searches, current event summaries

#### 3. Academic Researcher Agent
- **Role**: Scholarly and encyclopedic research
- **Tools**: `wikipedia_search`, `wikipedia_get_page`, `arxiv_search`, `semantic_scholar_search`, `semantic_scholar_get_paper`
- **Handoffs**: Content Extractor
- **Capabilities**: Foundational knowledge, peer-reviewed literature, citation analysis

#### 4. News Researcher Agent
- **Role**: Current events, community discussions, and technical insights
- **Tools**: `google_news_rss`, `reddit_search`, `github_search_repos`, `stackexchange_search`
- **Handoffs**: Content Extractor
- **Capabilities**: Recent news, community sentiment, code repositories, technical Q&A

#### 5. Content Extractor Agent
- **Role**: Deep content extraction from URLs
- **Tools**: `jina_read_url`, `scrape_webpage`, `youtube_get_transcript`
- **Handoffs**: Synthesizer
- **Capabilities**: Clean markdown extraction (Jina), HTML scraping fallback (BeautifulSoup), video transcripts (YouTube)

#### 6. Synthesizer Agent
- **Role**: Source evaluation, claim extraction, cross-referencing, gap identification
- **Tools**: `evaluate_source_credibility`, `extract_key_claims`, `cross_reference_findings`, `identify_knowledge_gaps`
- **Handoffs**: Report Writer
- **Capabilities**: Domain-based credibility scoring, claim extraction, agreement/contradiction detection, unanswered sub-question identification

#### 7. Report Writer Agent (Terminal)
- **Role**: Final report generation with citations and confidence scoring
- **Tools**: `generate_report_outline`, `generate_citation`, `format_report_section`, `compile_bibliography`, `calculate_confidence_score`
- **Handoffs**: None (terminal agent)
- **Guardrails**: Output quality (minimum length, markdown structure, citations present, no hallucinated URLs)
- **Capabilities**: APA-style citations, structured sections, bibliography compilation, confidence scoring

### Handoff Topology

```
                    ┌──────────────┐
                    │   Research   │
                    │   Planner    │
                    └──┬──┬──┬────┘
                       │  │  │
           ┌───────────┘  │  └───────────┐
           ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │   Web    │   │ Academic │   │   News   │
    │Researcher│   │Researcher│   │Researcher│
    └────┬─────┘   └────┬─────┘   └────┬─────┘
         │              │              │
         └──────────┬───┘──────────────┘
                    ▼
             ┌──────────┐
             │ Content  │
             │Extractor │
             └────┬─────┘
                  ▼
             ┌──────────┐
             │Synthesizer│
             └────┬─────┘
                  ▼
             ┌──────────┐
             │  Report  │
             │  Writer  │
             │(terminal)│
             └──────────┘
```

## Data Architecture

### Domain Models

The data layer uses **dataclasses** organized by domain:

- **`models/research.py`** — `ResearchPlan`, `SubQuestion`, `ResearchFinding`, `ResearchContext` with `QueryType` and `SourceType` literal types
- **`models/sources.py`** — `Source`, `SourceCredibility`, `Citation` with `SourceType` and `CredibilityLevel` literal types
- **`models/report.py`** — `ReportSection`, `ConfidenceScore`, `ResearchReport`

### Context Object (ResearchContext)

The `ResearchContext` dataclass serves as the **run context** passed to all agents and tools via `RunContextWrapper[ResearchContext]`. It accumulates data as the pipeline progresses:

- `query` — Original research query
- `config` — API keys and model settings
- `research_plan` — Decomposed sub-questions and search strategy (set by Planner)
- `findings` — List of `ResearchFinding` objects (accumulated by Researchers + Extractor)
- `sources` — List of `Source` and `SourceCredibility` objects (accumulated by all agents)
- `citations` — List of `Citation` objects (generated by Report Writer)
- `confidence` — `ConfidenceScore` (calculated by Report Writer)

### External API Architecture

Unlike the simulator-based projects, this agent calls real external APIs:

| API | Tool(s) | Auth | Rate Limits |
|-----|---------|------|-------------|
| Tavily | `tavily_web_search` | API key | 1000/month (free) |
| DuckDuckGo | `duckduckgo_text_search`, `duckduckgo_news_search` | None | Unlimited |
| Wikipedia | `wikipedia_search`, `wikipedia_get_page` | None | Unlimited |
| arXiv | `arxiv_search` | None | Unlimited |
| Semantic Scholar | `semantic_scholar_search`, `semantic_scholar_get_paper` | None | 100 req/5min |
| Jina Reader | `jina_read_url` | None | Free |
| YouTube Transcripts | `youtube_get_transcript` | None | Unlimited |
| Google News RSS | `google_news_rss` | None | Unlimited |
| Reddit JSON API | `reddit_search` | None | Rate-limited |
| GitHub Search | `github_search_repos` | None | 10 req/min |
| StackExchange | `stackexchange_search` | None | 300 req/day |

## Pipeline Flow

### Execution Model

```
1. Query Input
   └── User provides research query string

2. Pipeline Construction
   └── build_agent_pipeline(model, hooks) → research_planner
       ├── Report Writer (terminal, output guardrail)
       ├── Synthesizer → Report Writer
       ├── Content Extractor → Synthesizer
       ├── Web Researcher → Content Extractor
       ├── Academic Researcher → Content Extractor
       ├── News Researcher → Content Extractor
       └── Research Planner → [Web, Academic, News] (input guardrail)

3. Execution
   └── Runner.run(planner, input=query, context=ResearchContext, max_turns=50)
       ├── Input guardrail validates query
       ├── Planner decomposes query and routes to specialist
       ├── Researcher searches external APIs, gathers findings
       ├── Extractor deep-reads top URLs via Jina/scraper/YouTube
       ├── Synthesizer evaluates credibility, cross-references claims
       ├── Report Writer generates structured report with citations
       └── Output guardrail validates report quality

4. Output
   └── Final markdown research report with sections, citations, bibliography, and confidence score
```

### Query Routing Examples

| Query Type | Planner Classification | Route | Pipeline Path |
|------------|----------------------|-------|---------------|
| "Latest quantum computing breakthroughs" | `current_events` | News Researcher | Planner → News → Extractor → Synthesizer → Writer |
| "Compare TCP vs UDP protocols" | `comparison` | Web Researcher | Planner → Web → Extractor → Synthesizer → Writer |
| "Transformer architecture in deep learning" | `technical` | Academic Researcher | Planner → Academic → Extractor → Synthesizer → Writer |
| "Environmental impact of cryptocurrency" | `analysis` | Web Researcher | Planner → Web → Extractor → Synthesizer → Writer |
| "What is the capital of France?" | `factual` | Web Researcher | Planner → Web → Extractor → Synthesizer → Writer |

## Guardrails Architecture

### Input Guardrail (`input_validation.py`)

Applied to the Research Planner Agent. Validates:
- Query is not empty or too short (minimum 15 characters)
- Query does not contain harmful or irrelevant content keywords

Tripwire triggered → pipeline stops with validation error.

### Output Guardrail (`output_quality.py`)

Applied to the Report Writer Agent. Validates:
- Report meets minimum length (≥500 characters)
- Report has structured sections (markdown `##` headers)
- Report contains citations or bibliography
- Report does not contain hallucinated URLs (e.g., `example.com`, `placeholder.com`)

Tripwire triggered → report blocked with quality error.

## Observability

### AgentHooks

The `DeepResearchHooks` class provides real-time visibility into:
- **on_start** — Agent activation (which agent is processing)
- **on_end** — Agent completion
- **on_tool_start** — Tool invocation (which tool, by which agent)
- **on_tool_end** — Tool completion
- **on_handoff** — Agent-to-agent transfers (source → target)

### Logging

All tools use Python's `logging` module with structured messages:
- Tool invocations log input parameters and result counts
- API errors are logged with status codes and response bodies
- Pipeline logs routing decisions and configuration

## Configuration

The system uses OpenRouter as the LLM provider, configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | (required) | API key for OpenRouter |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter API endpoint |
| `OPENROUTER_MODEL` | `openai/gpt-4.1-mini` | Model to use via OpenRouter |
| `TAVILY_API_KEY` | (required) | Tavily search API key |

All agents share the same model instance, with `ModelSettings(temperature=0.2)` for consistent, deterministic outputs across the pipeline.
