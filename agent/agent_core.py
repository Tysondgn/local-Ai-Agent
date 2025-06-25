# agent/agent_core.py

import asyncio
from agent.memory_bus import MemoryBus
from agent.command_router import CommandRouter
from agent.session_state import SessionState
from llm.engine import LLMEngine
from llm.prompt_builder import PromptBuilder
from llm.model_selector import ModelSelector
from utils.logger import log_event
from config.settings import load_config
from memory.behavior_analyzer import BehaviorAnalyzer

# ✅ NEW MEMORY SYSTEM
from memory.memory_manager import MemoryManager  # <-- Create this in next steps

class AgentCore:
    def __init__(self, session: SessionState):
        self.session_state = session
        self.config = load_config()

        # Load model dynamically using selector
        model = ModelSelector(self.config).get_active_model()

        # Core components
        # self.memory = MemoryBus(self.config)
        self.llm = LLMEngine(self.config)
        self.memory_manager = MemoryManager(               # <-- ✅ NEW
            profile_path=self.config.get("profile_path", "data/profile.json"),
            log_dir=self.config.get("log_dir", "data/logs/"),
            llm_engine=self.llm  # Pass the LLM engine
            # ,

            # vector_memory=None  # <- placeholder, we'll implement in later steps
        )
        self.router = CommandRouter()
        self.behavior_analyzer = BehaviorAnalyzer(llm_engine=self.llm, max_history_messages=10)
        self.prompt_builder = PromptBuilder(mode="default", model=model)

    async def handle_input(self, user_input: str) -> str:
        log_event("Received input", user_input)

         # 1. Tool command routing
        if self.router.is_tool_command(user_input):
            result = await self.router.route_command(user_input, self.session_state)
            log_event("Tool handled", result)
            return result

        # ✅ 2. Manual memory search
        if user_input.lower().startswith("search memory for"):
            query = user_input.replace("search memory for", "").strip()
            memory_hits = self.memory_manager.retrieve_memory(query)
            return "\n".join(memory_hits) if memory_hits else "No matching memory found."

        # 3. Load profile & recent chat from MemoryManager
        profile = self.memory_manager.get_profile()
        context = self.session_state.get_recent_messages()

        # 4. Construct prompt
        prompt = self.prompt_builder.build_prompt(user_input, profile, context)

        # 5. Query the LLM (full response)
        response = await self.llm.get_response(prompt)

        # 6. Update chat state and memory
        self.session_state.append_message("user", user_input)
        self.session_state.append_message("assistant", response)
        # self.memory.log_conversation(user_input, response)

        # # Log conversation & extract facts via MemoryManager
        # self.memory_manager.process_turn(user_input, response)

        # ✅ Await the async memory update
        await self.memory_manager.process_turn(user_input, response)

        # Now infer behavior:
        # Pass the full recent chat history (or a subset) for analysis
        chat_history = self.session_state.get_recent_messages()
        behavior = await self.behavior_analyzer.analyze(chat_history)
        # You can store this behavior in profile or memory_manager as well:
        if behavior:
            # e.g., store under a key in ProfileStore or MemoryManager
            # Example: memory_manager.profile.set("behavior", behavior)
            self.memory_manager.profile.set("behavior", behavior)
        
        return response


    async def stream_input(self, user_input: str):
        log_event("Streaming input", user_input)

        if self.router.is_tool_command(user_input):
            result = await self.router.route_command(user_input, self.session_state)
            yield result
            return

        # 2. Load profile from MemoryManager
        profile = self.memory_manager.get_profile()
        context = self.session_state.get_recent_messages()
        prompt = self.prompt_builder.build_prompt(user_input, profile, context)

        collected_response = ""
        # Log start of streaming only
        # log_event("LLM streaming started", prompt)
        async for chunk in self.llm.stream_response(prompt):
            # log_event("LLM chunk", chunk)  # <-- Remove or comment out this line
            collected_response += chunk
            yield chunk
        # Log end of streaming only
        # log_event("LLM streaming ended", collected_response[:80] + ("..." if len(collected_response)>80 else ""))

        # After streaming, update session & memory
        self.session_state.append_message("user", user_input)
        self.session_state.append_message("assistant", collected_response)
        await self.memory_manager.process_turn(user_input, collected_response)

        print(f"[AgentCore] Logging conversation to memory: {user_input} -> {collected_response}")


    async def respond(self, user_input: str, stream: bool = False):
        print(f"🤖 AgentCore called with stream={stream}")
        if stream:
            async for chunk in self.stream_input(user_input):
                yield chunk
        else:
            result = await self.handle_input(user_input)
            # Instead of return (not allowed in generator), yield once
            yield result

    def reset_session(self):
        self.session_state.reset()

# EOC=================================================================================================================

# 🧠 What This Handles:

# Feature	Included
# Uses ModelSelector	✅
# Fully async I/O	✅
# Dynamic prompt builder	✅
# Shared session state	✅
# Real-time streaming support	✅
# Logs everything via logger.py	✅
# Easy to expand with new tools	✅