# llm/stream_parser.py

import json
from utils.logger import log_event

class StreamParser:
    def __init__(self):
        self.buffer = ""

    def parse_chunk(self, raw_line: bytes) -> str:
        """
        Takes a raw streamed byte line from Ollama and extracts the token.
        Returns clean token or empty string.
        """
        try:
            text = raw_line.decode("utf-8").strip()

            if not text.startswith("data:"):
                return ""

            # Remove "data:" and parse JSON
            data_str = text.replace("data:", "").strip()
            if data_str == "[DONE]":
                return ""

            data = json.loads(data_str)
            token = data.get("response", "")
            return token

        except Exception as e:
            # log_event("StreamParser error", str(e))  # Comment out for performance
            return ""

    def reset(self):
        self.buffer = ""


# EOC=============================================================================================================

# ✅ How to Use in engine.py (already partially done)

# In stream_response() from engine.py, you use:

# from llm.stream_parser import StreamParser

# parser = StreamParser()

# async for line in resp.content:
#     token = parser.parse_chunk(line)
#     if token:
#         yield token

# 🚀 Optional (for UI Typing Delay Effect)

# If you want artificial typing delay in UI (like ChatGPT):

# import asyncio
# await asyncio.sleep(0.01)

# Add it inside your UI update loop.