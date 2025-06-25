# llm/template_formatter.py

import yaml
from pathlib import Path

class PromptTemplate:
    def __init__(self, model="openhermes", config_path="config/templates.yaml"):
        self.model = model.lower()
        self.templates = self.load_templates(config_path)
        self.template = self.templates.get(self.model, self.templates.get("openhermes"))

    def load_templates(self, path):
        with open(Path(path), "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def format(self, system, history, user_input):
        history_str = self.format_history(history)
        final_prompt = self.template["format"].format(
            system=system.strip(),
            history=history_str.strip(),
            user=user_input.strip()
        )
        return final_prompt

    def format_history(self, history):
        pattern = self.template["history_format"]

        lines = []
        for msg in history:
            content = msg["content"].strip()
            role = msg["role"]

            # Special syntax parsing (handle 'if role == ...' cases)
            if "if role == \"user\"" in pattern:
                if role == "user":
                    lines.append(pattern.split("if")[0].strip().format(role=role, content=content))
                elif role == "assistant":
                    lines.append(pattern.split("if")[-1].strip().format(role=role, content=content))
            else:
                lines.append(pattern.format(role=role, content=content))

        return "\n".join(lines)
