# Deep Research Agent -- Code Guide

## AI Agent Concepts

### What is a Deep Research Agent?

A Deep Research Agent is an autonomous system that mimics how a human researcher works:
1. **Understand the question** -- decompose a complex query into answerable sub-questions
2. **Search broadly** -- query multiple sources (web, academic, news, forums)
3. **Read deeply** -- extract full content from the most relevant pages
4. **Evaluate critically** -- assess source credibility and cross-reference claims
5. **Synthesize** -- combine findings into a coherent narrative
6. **Report** -- produce a structured document with citations

Unlike a simple chatbot that generates answers from training data, this agent retrieves real-time information from live APIs and grounds its responses in cited sources.

### Multi-Agent Orchestration

The system uses 7 specialized agents in a pipeline:

| Agent | Responsibility | Handoff Target |
|-------|---------------|----------------|
| Research Planner | Decompose query, route to researcher | Web/Academic/News Researcher |
| Web Researcher | Search Tavily + DuckDuckGo | Content Extractor |
| Academic Researcher | Search Wikipedia + arXiv + Semantic Scholar | Content Extractor |
| News Researcher | Search Google News + Reddit + GitHub + SE | Content Extractor |
| Content Extractor | Deep-read URLs via Jina/scraping/YouTube | Synthesizer |
| Synthesizer | Evaluate sources, cross-reference claims | Report Writer |
| Report Writer | Generate final report with citations | (terminal) |

Each agent has a single responsibility and communicates through handoffs.

---

## OpenAI Agents SDK Constructs

### Agent

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Research Planner Agent",
    instructions="...",           # System prompt
    tools=[tool1, tool2],         # Function tools
    handoffs=[agent_a, agent_b],  # Agents to hand off to
    input_guardrails=[guard],     # Validate input
    output_guardrails=[guard],    # Validate output
    hooks=hooks,                  # Lifecycle callbacks
    model_settings=ModelSettings(temperature=0.3),
)
```

The `Agent` class wraps an LLM with instructions, tools, and handoffs. The SDK automatically generates `transfer_to_<agent_name>` functions for each handoff target.

### Function Tools

```python
from agents import RunContextWrapper, function_tool

@function_tool
def tavily_web_search(
    ctx: RunContextWrapper[ResearchContext],
    query: str,
    max_results: int = 5,
) -> str:
    """Search the web using Tavily."""
    # The SDK auto-generates the JSON schema from type hints + docstring
    ...
    return json.dumps(result)
```

Key points:
- `@function_tool` decorator registers the function as an agent tool
- First parameter `ctx: RunContextWrapper[T]` provides shared context
- Return type must be `str` (JSON-serialized)
- The docstring becomes the tool description for the LLM
- Type hints become the JSON schema parameters

### Handoffs

When an agent is added to another agent's `handoffs` list, the SDK creates a transfer function:
```python
# If handoffs=[content_extractor], the SDK creates:
# transfer_to_content_extractor_agent(message: str) -> None
```

The LLM calls this function to transfer control and context to the next agent.

### RunContextWrapper

```python
@dataclass
class ResearchContext:
    query: str
    config: dict[str, str | None]
    findings: list[ResearchFinding] = field(default_factory=list)
    raw_contents: dict[str, str] = field(default_factory=dict)
```

The context is shared across all agents and tools via `ctx.context`. Tools can read config (API keys) and write accumulated findings.

### Guardrails

```python
from agents import InputGuardrail, OutputGuardrail, GuardrailFunctionOutput

async def validate_input(ctx, agent, input_data) -> GuardrailFunctionOutput:
    if invalid:
        return GuardrailFunctionOutput(
            output_info="Error message",
            tripwire_triggered=True,  # Stops pipeline
        )
    return GuardrailFunctionOutput(
        output_info="OK",
        tripwire_triggered=False,
    )

guardrail = InputGuardrail(guardrail_function=validate_input, name="...")
```

- `InputGuardrail`: Attached to the entry agent, validates the research query
- `OutputGuardrail`: Attached to the terminal agent, validates the final report
- `tripwire_triggered=True` halts the pipeline immediately

### Runner

```python
from agents import Runner, RunConfig

result = await Runner.run(
    starting_agent=planner_agent,
    input=research_input,
    context=research_context,      # ResearchContext instance
    max_turns=50,                  # Maximum LLM + tool turns
    run_config=RunConfig(
        workflow_name="deep_research",
        tracing_disabled=True,
    ),
)
final_report = result.final_output
```

The `Runner` executes the agent loop: LLM call → tool/handoff → repeat until a terminal agent produces output.

### AgentHooks

```python
from agents import AgentHooks

class DeepResearchHooks(AgentHooks):
    async def on_start(self, context, agent): ...
    async def on_end(self, context, agent, output): ...
    async def on_tool_start(self, context, agent, tool): ...
    async def on_tool_end(self, context, agent, tool, result): ...
    async def on_handoff(self, context, agent, source): ...
```

Hooks provide observability into the agent lifecycle without modifying agent logic.

### OpenRouter Integration

The SDK's `OpenAIChatCompletionsModel` class enables using any OpenAI-compatible API:

```python
from agents import AsyncOpenAI, OpenAIChatCompletionsModel

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_key,
)
model = OpenAIChatCompletionsModel(
    model="openai/gpt-4.1-mini",
    openai_client=client,
)
```

This allows using OpenRouter's model catalog instead of direct OpenAI API.

---

## Tool Implementation Patterns

### External API Tool Pattern

```python
@function_tool
def api_tool(ctx: RunContextWrapper[ResearchContext], query: str) -> str:
    """Tool description for the LLM."""
    logger.info("Tool action: param=%s", query)
    
    # Call external API
    with httpx.Client(timeout=15) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    
    # Structure the result
    output = {"query": query, "results": [...], "searched_at": "..."}
    
    logger.info("Tool result: %d items", len(output["results"]))
    return json.dumps(output, indent=2)
```

### Local Computation Tool Pattern

```python
@function_tool
def analysis_tool(ctx: RunContextWrapper[ResearchContext], text: str) -> str:
    """Analyze content locally."""
    logger.info("Analyzing: %s", text[:80])
    
    # Perform local computation (regex, scoring, etc.)
    score = compute_score(text)
    
    output = {"score": score, "analyzed_at": "..."}
    return json.dumps(output, indent=2)
```

### Error Handling in Tools

Tools return JSON error objects instead of raising exceptions:
```python
if not api_key:
    return json.dumps({"error": "API key not configured", "results": []})
```

The agent sees the error in the tool response and adapts its strategy.

---

## Source Credibility Model

Sources are scored on a 0-100 scale:

| Factor | Points | Description |
|--------|--------|-------------|
| Domain reputation | 0-30 | .edu, .gov, major publications = +30; medium = +15 |
| HTTPS | +5 | Secure connection |
| Content length | +5 | Substantial content (>200 chars) |
| Descriptive title | +5 | Title >10 chars |
| Contains citations | +10 | References, DOIs, ISBNs in content |

Credibility levels:
- **High** (75-100): Academic, government, major news
- **Medium** (50-74): Tech blogs, industry sites
- **Low** (25-49): Forums, unknown domains
- **Unknown** (0-24): No quality signals

---

## Confidence Score Model

Overall research confidence is scored 0-100:

| Factor | Weight | Calculation |
|--------|--------|-------------|
| Source quantity | 25% | min(sources * 5, 25) |
| Source quality | 25% | (high_credibility / total) * 25 |
| Source agreement | 25% | (agreeing / total) * 25 |
| Topic coverage | 25% | (covered_questions_pct) * 0.25 |

Confidence levels:
- **High** (80-100): Multiple high-quality, agreeing sources
- **Moderate** (60-79): Good coverage with some limitations
- **Low** (40-59): Limited sources or disagreement
- **Very Low** (0-39): Insufficient evidence

---

## Key Libraries

| Library | Purpose |
|---------|---------|
| `openai-agents` | Agent SDK (Agent, Runner, tools, handoffs, guardrails) |
| `tavily-python` | Tavily Search API client |
| `duckduckgo-search` | DuckDuckGo search (no API key) |
| `wikipedia-api` | Wikipedia article retrieval |
| `arxiv` | arXiv paper search |
| `httpx` | Async/sync HTTP client (Semantic Scholar, Reddit, GitHub, SE) |
| `beautifulsoup4` | HTML parsing for web scraping |
| `feedparser` | RSS feed parsing (Google News) |
| `youtube-transcript-api` | YouTube transcript extraction |
| `python-dotenv` | Environment variable loading |
