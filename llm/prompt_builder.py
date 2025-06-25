# llm/prompt_builder.py

from datetime import datetime
from llm.instructions import get_instruction
from llm.template_formatter import PromptTemplate
import json
import re

class PromptBuilder:
    def __init__(self, mode="default", model="openhermes:latest", exclude_profile_keys=None):
        """
        :param mode: instruction mode, passed to get_instruction(mode)
        :param model: model name for PromptTemplate
        :param exclude_profile_keys: iterable of profile keys to exclude or mask, e.g. ["password", "token"]
        """
        self.system_instruction = get_instruction(mode).strip()
        self.formatter = PromptTemplate(model=model)
        # default exclude sensitive keys
        if exclude_profile_keys is None:
            exclude_profile_keys = ["password", "token", "auth", "ssn"]
        # normalize to set of lowercase keys
        self.exclude_profile_keys = set(k.lower() for k in exclude_profile_keys)

    def _prettify_key(self, key: str) -> str:
        """
        Turn a snake_case or camelCase key into human-friendly phrase.
        E.g. "pet_name" -> "Pet name", "favoriteColor" -> "Favorite color".
        """
        pretty = key.replace("_", " ")
        pretty = re.sub(r"(?<!^)(?=[A-Z])", " ", pretty)  # camelCase split
        pretty = pretty.strip().lower().capitalize()
        return pretty

    def _format_profile_lines(self, profile: dict) -> list:
        """
        Iterate profile dict and generate lines like "User's <prettified key> is <value>."
        Skip keys in exclude list, and skip None or empty-string values.
        If value is list or dict, convert to JSON-string or a joined string for readability.
        """
        lines = []
        for raw_key, value in profile.items():
            if raw_key is None:
                continue
            key_lower = str(raw_key).lower()
            if key_lower in self.exclude_profile_keys:
                continue
            # Skip empty or null
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue

            pretty_key = self._prettify_key(str(raw_key))
            # Convert value to a readable string
            if isinstance(value, list):
                # join items if simple; else JSON-dump
                try:
                    # If all items are primitive and short, join by comma
                    if all(isinstance(item, (str, int, float, bool)) for item in value) and len(value) <= 5:
                        val_str = ", ".join(str(item) for item in value)
                    else:
                        val_str = json.dumps(value, ensure_ascii=False)
                except Exception:
                    val_str = str(value)
            elif isinstance(value, dict):
                try:
                    # Optionally flatten small dicts or JSON-dump
                    val_str = json.dumps(value, ensure_ascii=False)
                except Exception:
                    val_str = str(value)
            else:
                val_str = str(value)

            # Construct sentence. E.g., "User's pet name is Fluffy."
            # For boolean flags, you could adjust: e.g., if value is True: "User ..."? But here generic.
            line = f"User's {pretty_key.lower()} is {val_str}."
            lines.append(line)
        return lines

    def build_prompt(self, user_input: str, profile: dict, chat_history: list) -> str:
        """
        Build prompt string combining:
         1. system instruction
         2. dynamic profile facts (all keys except excluded)
         3. timestamp
         4. chat history (list of {"role":..., "content":...})
         5. current user_input
        """
        # 1. Format profile lines
        profile_lines = self._format_profile_lines(profile)

        # 2. Optionally handle nested behavior or other structured fields specially:
        #    But since behavior stored as dict under profile["behavior"], _format_profile_lines
        #    will JSON-dump it; if you want nicer, you can handle "behavior" key separately:
        # Example: if "behavior" in profile, pull out sub-keys for prettier sentences:
        behavior = profile.get("behavior")
        behavior_lines = []
        if isinstance(behavior, dict):
            # Remove the raw JSON-dumped behavior if included in profile_lines
            # We skip the "behavior" key in _format_profile_lines by excluding or post-filter:
            # Here we simply generate more human-friendly lines:
            for bkey, bval in behavior.items():
                if bval is None:
                    continue
                pretty_bkey = bkey.replace("_", " ").lower()
                if isinstance(bval, list):
                    items = ", ".join(str(item) for item in bval)
                    behavior_lines.append(f"User's {pretty_bkey} include: {items}.")
                else:
                    behavior_lines.append(f"User's {pretty_bkey} is {bval}.")
        # If we wish to remove the raw behavior JSON line from profile_lines, ensure exclude_profile_keys
        # or filter out raw "behavior" key before calling _format_profile_lines.

        # 3. Timestamp
        date_time = datetime.now().strftime("%A, %d %B %Y %I:%M %p")
        timestamp_line = f"Current date and time: {date_time}."

        # 4. Combine system instruction + timestamp + profile lines + behavior lines
        system_parts = [self.system_instruction, timestamp_line]
        if profile_lines:
            system_parts.extend(profile_lines)
        if behavior_lines:
            system_parts.extend(behavior_lines)
        system_block = "\n".join(system_parts)

        # 5. Pass to template formatter
        # The PromptTemplate.format expects (system, history, user_input)
        prompt = self.formatter.format(system_block, chat_history, user_input.strip())
        return prompt
