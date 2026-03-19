"""
Agent Generator — self-spawning engine that creates new agents.

Uses meta-reasoning to identify system gaps and automatically
generates new agent definitions to fill them.
"""

from __future__ import annotations

import logging
import json
from typing import TYPE_CHECKING

from openai import AsyncOpenAI

from config import OPENAI_API_KEY
from core.agent_dna import AgentDNA

if TYPE_CHECKING:
    from core.coordinator import Coordinator

logger = logging.getLogger("hydranet.generator")

META_REASONING_PROMPT = """You are the meta-reasoning engine of HydraNet, a self-evolving multi-agent AI system.

Your job is to analyze the current system state and decide if new agents are needed.

Current system state:
- Active agents: {agent_list}
- Recent events: {recent_events}
- System gaps: {gaps}
- Performance summary: {performance}

Questions to answer:
1. What capability is currently missing from the system?
2. What agent would improve overall system performance?
3. Are there bottlenecks that a new agent could solve?
4. What new data source or analysis type would add value?

If a new agent is needed, output JSON:
{{
  "create_agent": true,
  "name": "AgentName",
  "purpose": "what this agent does",
  "agent_type": "scanner|analyzer|detector|advisor|executor",
  "input_sources": ["channel1", "channel2"],
  "decision_prompt": "the full system prompt for this agent",
  "output_actions": ["emit_event", "store_memory"],
  "tags": ["tag1", "tag2"],
  "reasoning": "why this agent is needed"
}}

If no new agent is needed, output:
{{
  "create_agent": false,
  "reasoning": "explanation"
}}
"""

AGENT_VALIDATION_PROMPT = """Validate this agent definition for a crypto/blockchain intelligence system.

Agent:
{agent_json}

Check:
1. Is the purpose clear and non-redundant with existing agents?
2. Is the decision prompt well-structured?
3. Are input/output channels reasonable?
4. Will this agent add value to the system?

Respond with JSON:
{{
  "valid": true/false,
  "issues": ["list of issues if any"],
  "improvements": ["suggested improvements"]
}}
"""


class AgentGenerator:
    """Meta-reasoning engine that spawns new agents."""

    def __init__(self, coordinator: Coordinator):
        self.coordinator = coordinator
        self.llm = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self._generation_count = 0

    async def analyze_gaps(self) -> dict:
        """Analyze the current system for capability gaps."""
        active = self.coordinator.get_active_agents()
        agent_list = [
            {"name": a.name, "type": a.agent_type, "purpose": a.purpose}
            for a in active
        ]

        # Get recent history
        recent = await self.coordinator.history.query(limit=20)
        recent_summary = [
            {"type": e["event_type"], "agent": e["agent_id"]}
            for e in recent
        ]

        # Identify gaps
        existing_types = {a.agent_type for a in active}
        all_types = {"scanner", "analyzer", "detector", "advisor", "executor"}
        missing_types = all_types - existing_types

        gaps = []
        if missing_types:
            gaps.append(f"Missing agent types: {missing_types}")
        if len(active) < 3:
            gaps.append("System has fewer than 3 active agents")

        prompt = META_REASONING_PROMPT.format(
            agent_list=json.dumps(agent_list, indent=2),
            recent_events=json.dumps(recent_summary[:10]),
            gaps=json.dumps(gaps),
            performance=json.dumps(self.coordinator.get_system_status()),
        )

        try:
            response = await self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=2000,
            )
            content = response.choices[0].message.content
            # Try to parse JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
        except Exception as e:
            logger.error(f"Gap analysis failed: {e}")
            return {"create_agent": False, "reasoning": f"Error: {e}"}

    async def validate_agent(self, dna: AgentDNA) -> dict:
        """Validate a proposed agent before deployment."""
        prompt = AGENT_VALIDATION_PROMPT.format(
            agent_json=dna.to_json()
        )

        try:
            response = await self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=500,
            )
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {"valid": False, "issues": [str(e)]}

    async def generate(self) -> AgentDNA | None:
        """Run the full generation pipeline: analyze → create → validate."""
        self._generation_count += 1
        logger.info(f"Agent generation attempt #{self._generation_count}")

        # Step 1: Analyze gaps
        analysis = await self.analyze_gaps()

        if not analysis.get("create_agent"):
            logger.info(f"No new agent needed: {analysis.get('reasoning', 'N/A')}")
            return None

        # Step 2: Create DNA from analysis
        dna = AgentDNA(
            name=analysis.get("name", f"AutoAgent_{self._generation_count}"),
            purpose=analysis.get("purpose", ""),
            agent_type=analysis.get("agent_type", "generic"),
            input_sources=analysis.get("input_sources", []),
            decision_prompt=analysis.get("decision_prompt", ""),
            output_actions=analysis.get("output_actions", []),
            tags=analysis.get("tags", ["auto-generated"]),
        )

        # Step 3: Validate
        validation = await self.validate_agent(dna)
        if not validation.get("valid", False):
            logger.warning(f"Agent validation failed: {validation.get('issues', [])}")
            return None

        # Log generation
        await self.coordinator.history.log(
            agent_id="agent_generator",
            event_type="agent_generated",
            payload={
                "name": dna.name,
                "reasoning": analysis.get("reasoning"),
                "validation": validation,
            },
        )

        logger.info(f"Generated new agent: {dna.name} ({dna.agent_type})")
        return dna
