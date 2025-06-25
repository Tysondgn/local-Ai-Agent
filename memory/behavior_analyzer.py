# memory/behavior_analyzer.py

import json
from typing import List, Dict, Optional
from utils.logger import log_event
from llm.engine import LLMEngine
from config.settings import load_config
from datetime import datetime

class BehaviorAnalyzer:
    """
    Uses offline LLM to infer user behavior patterns—tone, mood, goals, habits, preferences, etc.—from conversation.
    Maintains previous state to detect changes if desired.
    """

    def __init__(self,
                 llm_engine: Optional[LLMEngine] = None,
                 max_history_messages: int = 10,
                 temperature: float = 0.0):
        """
        :param llm_engine: an instance of LLMEngine; if None, create one via config
        :param max_history_messages: how many recent user/assistant messages to include for behavior inference
        :param temperature: sampling temperature for behavior LLM calls (0.0 for deterministic)
        """
        if llm_engine is None:
            config = load_config()
            self.llm = LLMEngine(config)
        else:
            self.llm = llm_engine
        self.max_history = max_history_messages
        self.temperature = temperature
        # Store last inferred behavior state
        self.last_behavior: Dict = {}

    async def analyze(self, messages: List[Dict]) -> Dict:
        """
        Analyze the conversation messages to infer behavior patterns.
        :param messages: list of {"role": "user" or "assistant", "content": str}, in chronological order.
        :return: dict of inferred behavior attributes.
        """
        # 1. Collect recent messages (user + assistant) up to limit. Here include both roles so LLM can see context.
        #    But if you prefer only user messages, adjust accordingly.
        recent = messages[-self.max_history*2:]  # take roughly last N turns (user+assistant)
        # Format them into a small text block
        convo_snippet = ""
        for msg in recent:
            role = msg.get("role", "")
            content = msg.get("content", "").replace("\n", " ")
            # Prefix roles to help LLM:
            if role == "user":
                convo_snippet += f"User: {content}\n"
            elif role == "assistant":
                convo_snippet += f"Assistant: {content}\n"
        if not convo_snippet.strip():
            return {}  # nothing to analyze

        # 2. Build a prompt to ask LLM for behavior inference in JSON.
        #    We instruct the LLM to respond with a JSON object only, with keys we define.
        #    For example: {"mood": "...", "tone": "...", "goals": [...], "habits": [...], "preferences": [...], "emotional_state": "..."}
        #    You can adjust the schema as you like.
        prompt = self._build_behavior_prompt(convo_snippet)
        try:
            # 3. Call LLMEngine to get a response
            raw = await self.llm.get_response(prompt)
            # 4. Parse JSON from raw
            behavior = self._parse_json(raw)
            if not isinstance(behavior, dict):
                raise ValueError("Parsed behavior is not a dict")
            # log_event("BehaviorAnalyzer Inferred", behavior)  # Commented out for performance
            return behavior
        except Exception as e:
            log_event("BehaviorAnalyzer Error", f"{e}; raw response: {raw if 'raw' in locals() else 'N/A'}")
            return None

    def _build_behavior_prompt(self, convo_snippet: str) -> str:
        """
        Constructs a prompt instructing the LLM to analyze the user behavior from the conversation snippet.
        We ask for a JSON-only response.
        """
        # You can refine instructions to your style/model.
        # Here we explicitly ask for JSON output, no extra text.
        prompt = (
            "You are a system that analyzes user behavior and emotional context from conversation. "
            "Given the following recent conversation between the user and assistant, infer the user's:\n"
            "  - mood or emotional state (e.g., happy, sad, anxious, neutral)\n"
            "  - tone (e.g., polite, frustrated, curious)\n"
            "  - goals or intentions (if any apparent)\n"
            "  - habits or routine hints (e.g., mentions waking times, study habits, work styles)\n"
            "  - preferences or interests mentioned (e.g., likes/dislikes)\n"
            "Respond ONLY as a JSON object, with keys among: "
            "\"mood\", \"tone\", \"goals\", \"habits\", \"preferences\", \"emotional_cues\". "
            "For keys with multiple items, use a JSON array; for single values, use string. "
            "If you cannot infer something, omit that key. Do NOT output any explanation—only the JSON.\n\n"
            "Conversation:\n"
            f"{convo_snippet}\n\n"
            "JSON:"
        )
        return prompt

    def _parse_json(self, text: str) -> Optional[Dict]:
        """
        Parse JSON object from text. The LLM might include whitespace; we try to locate the JSON substring.
        """
        # Strategy: find first '{' and last '}', then json.loads.
        try:
            start = text.index('{')
            end = text.rindex('}') + 1
            json_str = text[start:end]
            data = json.loads(json_str)
            return data
        except Exception as e:
            # If parsing fails, log and return None
            log_event("BehaviorAnalyzer JSON parse error", f"{e}; text: {text}")
            return None
