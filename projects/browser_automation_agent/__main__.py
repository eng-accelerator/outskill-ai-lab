"""Allow running the Browser Automation Agent as a module.

Usage:
    uv run python -m browser_automation_agent
"""

import asyncio

from browser_automation_agent.main import main

asyncio.run(main())
