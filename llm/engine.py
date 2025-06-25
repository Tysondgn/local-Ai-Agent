# llm/engine.py

import aiohttp
import asyncio
from utils.logger import log_event
from llm.stream_parser import StreamParser
# from llm.model_selector import get_default_model
from llm.model_selector import ModelSelector
import json

class LLMEngine:
    def __init__(self, config):
        self.base_url = config.get("ollama_url", "http://localhost:11434")
        # self.model = config.get("model", "llama3")  //hardcode Default llm model
        # self.model = config.get("model", get_default_model())
        selector = ModelSelector(config)
        self.model = config.get("model", selector.get_active_model())

    async def get_response(self, prompt: str) -> str:
        """
        Send a prompt and get a complete response.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        output = data.get("response", "").strip()
                        log_event("LLM response", output)
                        return output
                    else:
                        error = await resp.text()
                        log_event("LLM error", error)
                        return "Sorry, I couldn't process that request."
        except Exception as e:
            log_event("LLM connection error", str(e))
            return "Error: LLM is not responding. Is Ollama running?"

    async def stream_response(self, prompt: str):
        """
        Stream the response from the Ollama LLM (chunk by chunk).
        Yields strings for each 'response' field in the streamed JSON lines.
        """
        url = f"{self.base_url}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": True}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    async for line in resp.content:
                        if not line:
                            continue
                        decoded = line.decode("utf-8").strip()
                        # print("📡 Raw Line:", decoded)  # Debug: see raw line
                        # Try parsing JSON directly
                        try:
                            data = json.loads(decoded)
                            # Ollama returns a JSON object with "response" key for each chunk
                            chunk = data.get("response", "")
                            if chunk is not None:
                                # Some responses may be empty strings; yield only non-empty
                                if chunk != "":
                                    # print("🔹 Chunk to yield:", chunk)  # Debug
                                    yield chunk
                        except json.JSONDecodeError:
                            # Not a JSON line? Skip or log
                            # Some streams may send partial or keep-alive lines; skip them
                            continue
        except Exception as e:
            # On error, yield an error message so UI can show it
            error_msg = f"[Error streaming: {e}]"
            # print("❌ LLM stream error:", e)
            yield error_msg

    async def complete(self, prompt: str, model: str = None, stream: bool = False) -> str:
            """
            Async wrapper to get a response; if model override needed, temporarily override self.model.
            """
            orig_model = self.model
            if model:
                self.model = model
            try:
                resp = await self.get_response(prompt)
            finally:
                self.model = orig_model
            return resp
# EOC=================================================================================================================

# ✅ Features Summary
# Method	Function
# get_response()	Full single-shot response (fast + simple)
# stream_response()	Token/chunk-based streaming response
# 💥 Error handling	Returns graceful errors when model is unreachable
# 🔌 Configurable	You can plug in LM Studio or other backends later