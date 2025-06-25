# memory/memory_manager.py

import os
import json
from datetime import datetime, timezone, date
from typing import List, Dict, Optional
from memory.fact_extractor import FactExtractor
from utils.logger import log_event
from memory.vector_memory import VectorMemory
from memory.behavior_analyzer import BehaviorAnalyzer
from memory.summarizer import Summarizer
from llm.engine import LLMEngine
from config.settings import load_config


# Optional future imports (vector memory, summarizer, etc.)
# from memory.vector_memory import VectorMemory
# from memory.behavior_analyzer import BehaviorAnalyzer
# from memory.summarizer import Summarizer


class ProfileStore:
    """Simple JSON key-value store."""
    def __init__(self, path: str):
        self.path = path
        self.data = self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            log_event("ProfileStore JSON error", f"Corrupted profile file: {e}. Creating new profile.")
            return {}
        except Exception as e:
            log_event("ProfileStore load error", f"Error loading profile: {e}. Creating new profile.")
            return {}

    def get(self, key: str):
        return self.data.get(key)

    def get_all(self) -> Dict:
        return self.data

    def set(self, key: str, value):
        self.data[key] = value
        self._save()

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)


class SessionLogger:
    """Logs user/assistant turns in JSONL by day."""
    def __init__(self, log_dir: str):
        self.dir = log_dir
        os.makedirs(self.dir, exist_ok=True)

    def log(self, role: str, text: str):
        now = datetime.now(timezone.utc).isoformat()
        entry = {"time": now, "role": role, "text": text}
        filename = os.path.join(self.dir, f"{date.today()}.jsonl")
        # ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")



class MemoryManager:
    """Master memory manager: logs chat, extracts facts, updates profile, semantic memory."""
    def __init__(self, profile_path="data/profile.json", log_dir="data/logs/", llm_engine: Optional[LLMEngine] = None):
        self.profile = ProfileStore(profile_path)
        self.logger = SessionLogger(log_dir)
        self.fact_extractor = FactExtractor()
        self.vector = VectorMemory()
        
        # Use provided LLM engine or create one
        if llm_engine is None:
            config = load_config()
            llm_engine = LLMEngine(config)
        
        self.behavior = BehaviorAnalyzer(llm_engine=llm_engine)
        self.summarizer = Summarizer()

        # Future integrations:
        # self.vector = VectorMemory(...)
        # self.summarizer = Summarizer(...)
        # self.behavior = BehaviorAnalyzer(...)

    async def process_turn(self, user_msg: str, assistant_msg: str):
        """
        Called after every user-assistant exchange.
        Must be awaited by caller.
        """
        # 1. Log raw turns
        # self.logger.log("user", user_msg)  # Commented out for performance
        # self.logger.log("assistant", assistant_msg)  # Commented out for performance

        # 2. Extract facts to profile
        messages = [
            {"role": "user", "content": user_msg}
            # ,
            # {"role": "assistant", "content": assistant_msg}
        ]
        facts = self.fact_extractor.extract(messages)
        for k, v in facts:
            self.profile.set(k, v)
            # log_event("🧠 MemoryManager: Saved fact", f"{k}: {v}")  # Commented out for performance

        # 3. Behavior analysis
        patterns = await self.behavior.analyze(messages)
        if patterns:
            # store under a "behavior" key or break out subkeys
            self.profile.set("behavior", patterns)
            # log_event("🧠 MemoryManager: Saved behavior", str(patterns))  # Commented out for performance

        # 4. Summarize & add to vector memory
        now = datetime.now(timezone.utc).isoformat()
        snippet = f"User: {user_msg} Assistant: {assistant_msg}"
        # if very long, summarize; else use snippet directly
        if len(snippet) > 500:
            try:
                summary = await self.summarizer.summarize(snippet)
            except Exception as e:
                log_event("MemoryManager: Summarizer failed", str(e))
                summary = snippet
        else:
            summary = snippet
        try:
            self.vector.add_memory(summary, metadata={"timestamp": now})
            # log_event("🧠 MemoryManager: Added to vector memory", summary[:80] + ("..." if len(summary)>80 else ""))  # Commented out for performance
        except Exception as e:
            log_event("MemoryManager: VectorMemory add failed", str(e))

        # OPTIONAL:
        # - analyze behavior
        # - generate vector summary
        # - semantic store using vector memory

    def get_profile(self) -> Dict:
        # Return current in-memory profile dict
        return self.profile.get_all()

    def get_fact(self, key: str):
        return self.profile.get(key)

    def retrieve_memory(self, query: str, top_k: int = 3) -> List[str]:
        """
        Return top memory snippets relevant to `query`.
        """
        try:
            hits = self.vector.query(query, top_k=top_k)
            # each hit is a dict with "text" and metadata
            return [hit.get("text", "") for hit in hits]
        except Exception as e:
            log_event("MemoryManager: retrieve_memory error", str(e))
            return []