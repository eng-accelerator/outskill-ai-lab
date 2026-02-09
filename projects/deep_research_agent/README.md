# Deep Research Agent

An autonomous research system that searches the web, evaluates sources, retrieves facts, and synthesizes long, multi-step answers. It produces comprehensive reports with citations, cross-references, and confidence assessments -- like a human researcher.

Unlike other projects in this repository, the Deep Research Agent uses **real external APIs** to search the live web, academic databases, news sources, and more. No simulated data.

## Key Features

- **7 Specialized Agents**: Research Planner, Web Researcher, Academic Researcher, News Researcher, Content Extractor, Synthesizer, Report Writer
- **24 Real-World Tools**: Tavily, DuckDuckGo, Wikipedia, arXiv, Semantic Scholar, Jina Reader, YouTube Transcripts, Google News, Reddit, GitHub, StackExchange, and more
- **Multi-Source Research**: Searches web, academic papers, news, forums, and code repositories simultaneously
- **Source Credibility Evaluation**: Scores sources based on domain reputation and content quality
- **Cross-Reference Analysis**: Identifies agreement and conflict across multiple sources
- **Confidence Scoring**: Calculates overall research confidence (0-100) based on source quality and coverage
- **Structured Reports**: Generates formatted reports with sections, citations, and bibliography
- **Input/Output Guardrails**: Validates queries and ensures report quality

## Setup Instructions

### 1. Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### 2. Install Dependencies

From the repository root:

```bash
uv add duckduckgo-search arxiv wikipedia-api beautifulsoup4 feedparser youtube-transcript-api
```

The following are already included:
- `openai-agents` (OpenAI Agents SDK)
- `tavily-python` (Tavily Search API)
- `python-dotenv` (Environment variable loading)

### 3. Configure API Keys

Create or update the `.env` file in the repository root:

```env
# Required: OpenRouter API key for LLM access
OPENROUTER_API_KEY=your_openrouter_key_here

# Required: Tavily API key for web search (free tier: 1000 searches/month)
TAVILY_API_KEY=your_tavily_key_here

# Optional: Override the default model
OPENROUTER_MODEL=openai/gpt-4.1-mini
```

**Free API Keys:**
- OpenRouter: [https://openrouter.ai/](https://openrouter.ai/)
- Tavily: [https://tavily.com/](https://tavily.com/) (1000 free searches/month)
- All other APIs (DuckDuckGo, Wikipedia, arXiv, Semantic Scholar, Jina Reader, Google News, Reddit, GitHub, StackExchange) require **no API key**.

### 4. Run the Agent

```bash
cd projects
PYTHONPATH=. uv run python -m deep_research_agent.main
```

Or programmatically:

```python
import asyncio
from deep_research_agent.main import run_deep_research

async def research():
    report = await run_deep_research("What are the latest advancements in quantum computing?")
    print(report)

asyncio.run(research())
```

## Usage

### Interactive Mode

```bash
PYTHONPATH=projects uv run python -c "
import asyncio
from deep_research_agent.main import main
asyncio.run(main())
"
```

You'll be prompted to enter a research query. The agent will:
1. Analyze and decompose your query into sub-questions
2. Route to the appropriate researcher (Web, Academic, or News)
3. Search multiple sources in parallel
4. Extract full content from the most promising URLs
5. Evaluate source credibility and cross-reference findings
6. Generate a structured report with citations and confidence score

### Example Queries

- "What are the latest advancements in quantum computing in 2025?"
- "Compare React, Vue, and Svelte for building large-scale web applications"
- "What is the current state of nuclear fusion research and when might it become commercially viable?"
- "How does retrieval-augmented generation (RAG) work and what are the best practices?"
- "What are the environmental impacts of cryptocurrency mining?"

## External APIs Used

| API | Purpose | Key Required | Free Tier |
|-----|---------|-------------|-----------|
| Tavily | AI-optimized web search | Yes | 1000/month |
| DuckDuckGo | Web + news search | No | Unlimited |
| Wikipedia | Encyclopedic knowledge | No | Unlimited |
| arXiv | Academic papers | No | Unlimited |
| Semantic Scholar | Paper citations | No | 100 req/5min |
| Jina Reader | URL content extraction | No | Free |
| YouTube Transcripts | Video transcripts | No | Unlimited |
| Google News RSS | News headlines | No | Unlimited |
| Reddit JSON API | Community discussions | No | Rate-limited |
| GitHub Search | Repository search | No | 10 req/min |
| StackExchange | Technical Q&A | No | 300 req/day |

## Project Structure

```
deep_research_agent/
├── main.py                    # Entry point, pipeline orchestration
├── utils/config.py            # API keys and model configuration
├── models/
│   ├── research.py            # ResearchPlan, SubQuestion, ResearchFinding, ResearchContext
│   ├── sources.py             # Source, SourceCredibility, Citation
│   └── report.py              # ReportSection, ConfidenceScore, ResearchReport
├── tools/
│   ├── web_search_tools.py    # Tavily, DuckDuckGo text, DuckDuckGo news
│   ├── academic_tools.py      # Wikipedia, arXiv, Semantic Scholar
│   ├── content_tools.py       # Jina Reader, BeautifulSoup scraper, YouTube
│   ├── news_tools.py          # Google News RSS, Reddit
│   ├── code_search_tools.py   # GitHub, StackExchange
│   ├── analysis_tools.py      # Credibility, claims, cross-reference, gaps, confidence
│   └── report_tools.py        # Citations, sections, bibliography, outline
├── guardrails/
│   ├── input_validation.py    # Research query validation
│   └── output_quality.py      # Report quality validation
└── agents/
    ├── research_planner.py    # Query decomposition and routing
    ├── web_researcher.py      # General web search specialist
    ├── academic_researcher.py # Scholarly and encyclopedic specialist
    ├── news_researcher.py     # News, Reddit, GitHub, StackExchange
    ├── content_extractor.py   # Deep URL content extraction
    ├── synthesizer.py         # Source evaluation and synthesis
    └── report_writer.py       # Final report generation (terminal)
```
