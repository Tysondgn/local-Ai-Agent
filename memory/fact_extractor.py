# memory/fact_extractor.py

import re
from typing import List, Dict, Tuple
from utils.logger import log_event

class FactExtractor:
    def __init__(self):
        pass

    def extract(self, messages: List[Dict]) -> List[Tuple[str, str]]:
        """
        Given a list of messages (each {'role': 'user'/'assistant', 'content': ...}),
        only inspect the latest user message for structured facts.
        """
        # Find the last user message:
        last_user = None
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = m.get("content", "").strip()
                break
        if not last_user:
            return []

        user_input = last_user  # only examine this
        facts = []

        # Example patterns:

        # 1. Name: "my name is X"
        if match := re.search(r"\bmy name is ([A-Za-z ]+)", user_input, re.I):
            name = match.group(1).strip().title()
            facts.append(("name", name))
            # log_event("🧠 FactExtractor: name", name)  # Commented out for performance

        # 2. Preferred name: "just call me X"
        if match := re.search(r"\bjust call me ([A-Za-z]+)", user_input, re.I):
            pref = match.group(1).strip().title()
            facts.append(("preferred_name", pref))
            # log_event("🧠 FactExtractor: preferred_name", pref)  # Commented out for performance

        # 3. Friend's name: "my friend's name is X"
        if match := re.search(r"\bmy friend(?:'s)? name is ([A-Za-z ]+)", user_input, re.I):
            friend = match.group(1).strip().title()
            facts.append(("friend_name", friend))
            # log_event("🧠 FactExtractor: friend_name", friend)  # Commented out for performance

        # 4. Favorite food: "I like/enjoy/love X"
        if match := re.search(r"\b(?:i like|i love|i enjoy|my favorite food is) ([A-Za-z ]+)", user_input, re.I):
            food = match.group(1).strip().lower()
            facts.append(("fav_food", food))
            # log_event("🧠 FactExtractor: fav_food", food)  # Commented out for performance

        # 5. Location: "I live in X"
        if match := re.search(r"\bi live in ([A-Za-z ]+)", user_input, re.I):
            loc = match.group(1).strip().title()
            facts.append(("location", loc))
            # log_event("🧠 FactExtractor: location", loc)  # Commented out for performance

        # 6. Job: "I work as X" or "I am a/an X"
        if match := re.search(r"\bi (?:work as|am a|am an) ([A-Za-z ]+)", user_input, re.I):
            job = match.group(1).strip().title()
            facts.append(("job", job))
            # log_event("🧠 FactExtractor: job", job)  # Commented out for performance

        # ... add more user-only patterns as needed ...

        return facts
