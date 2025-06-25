# memory/summarizer.py

from typing import Optional
from llm.engine import LLMEngine
from config.settings import load_config
from utils.logger import log_event

class Summarizer:
    """
    Uses local LLM (e.g. Ollama) to summarize long conversation turns
    for vector memory storage or fact compression.
    """

    def __init__(self, model_name: Optional[str] = None):
        config = load_config()
        self.llm = LLMEngine(config)
        self.model = model_name or config.get("default_model", "openhermes")

    async def summarize(self, text: str) -> str:
        prompt = self._build_summary_prompt(text)
        try:
            # Use LLMEngine.get_response (async)
            response = await self.llm.get_response(prompt)
            if isinstance(response, str):
                return response.strip()
            else:
                return ""
        except Exception as e:
            print("[Summarizer Error]", e)
            return text  # fallback to original

    def _build_summary_prompt(self, text: str) -> str:
        return (
            "Please summarize the following conversation exchange into 1-2 concise sentences "
            "focusing on important personal facts, goals, or interests mentioned:\n\n"
            f"{text}\n\nSummary:"
        )
