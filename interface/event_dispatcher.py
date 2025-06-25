# interface/event_dispatcher.py
# import asyncio
# from agent.agent_core import AgentCore
# from agent.session_state import SessionState
# from utils.logger import log_event

# class EventDispatcher:
#     def __init__(self, on_response_chunk=None):
#         self.session = SessionState()
#         self.agent = AgentCore(self.session)
#         self.on_response_chunk = on_response_chunk  # callback for UI
#         print("[DEBUG] Dispatcher initialized with callback:", self.on_response_chunk)

#     async def handle_input(self, user_input: str, stream: bool = False) -> str:
#         print(f"[DEBUG] handle_input called with: '{user_input}', stream={stream}")
#         self.session.append_message("user", user_input)
#         log_event("User input", user_input)

#         if stream:
#             full_response = ""
#             try:
#                 async for chunk in self.agent.respond(user_input, stream=True):
#                     print(f"🟢 Sending chunk to UI: '{chunk}'")
#                     full_response += chunk
#                     if self.on_response_chunk:
#                         try:
#                             print(f"[DEBUG] Invoking on_response_chunk with: '{chunk}'")
#                             self.on_response_chunk(chunk)
#                         except Exception as e:
#                             print("[ERROR] on_response_chunk raised:", e)
#                 self.session.append_message("assistant", full_response)
#             except Exception as e:
#                 print("[ERROR] Exception in handle_input stream loop:", e)
#             return full_response
#         else:
#             # Non-stream path
#             try:
#                 chunks = []
#                 async for chunk in self.agent.respond(user_input, stream=False):
#                     print(f"[DEBUG] Non-stream chunk: '{chunk}'")
#                     chunks.append(chunk)
#                 response = "".join(chunks)
#                 self.session.append_message("assistant", response)
#                 if self.on_response_chunk:
#                     self.on_response_chunk(response)
#                 return response
#             except Exception as e:
#                 print("[ERROR] Exception in handle_input non-stream:", e)
#                 return "Error occurred."
#     def get_history(self):
#         return self.session.get_recent_messages()
# =============================================================================================================================

# interface/event_dispatcher.py

import asyncio
from agent.agent_core import AgentCore
from agent.session_state import SessionState
from utils.logger import log_event

class EventDispatcher:
    def __init__(
        self,
        on_response_chunk=None,
        on_start=None,
        on_end=None,
        on_error=None
    ):
        """
        :param on_response_chunk: callback(chunk: str) called for each streamed chunk or full response.
        :param on_start: optional callback() called once just before streaming begins.
        :param on_end: optional callback() called once after streaming completes successfully.
        :param on_error: optional callback(error_msg: str) called if an exception/error occurs.
        """
        self.session = SessionState()
        self.agent = AgentCore(self.session)
        self.on_response_chunk = on_response_chunk
        self.on_start = on_start
        self.on_end = on_end
        self.on_error = on_error

    async def handle_input(self, user_input: str, stream: bool = False) -> str:
        """
        Handles input from UI, routes through agent core, returns full response.
        If stream=True, calls UI callback with each token chunk.
        Lifecycle callbacks:
          - on_start(): before first chunk is requested
          - on_response_chunk(chunk): for each chunk (or full response in non-stream mode)
          - on_end(): after streaming completes successfully
          - on_error(error_msg): on exception during processing
        """
        # Append user turn to session state
        self.session.append_message("user", user_input)
        log_event("User input", user_input)

        # Tool commands or special routing can be in AgentCore
        try:
            if stream:
                # Notify UI: streaming is about to start
                if self.on_start:
                    try:
                        self.on_start()
                    except Exception as e:
                        log_event("EventDispatcher on_start callback error", str(e))

                full_response = ""
                # Stream mode: yield chunks as they arrive
                async for chunk in self.agent.respond(user_input, stream=True):
                    # deliver chunk to UI
                    if self.on_response_chunk:
                        try:
                            self.on_response_chunk(chunk)
                        except Exception as e:
                            log_event("EventDispatcher on_response_chunk error", str(e))
                    full_response += chunk
                # Streaming complete
                if self.on_end:
                    try:
                        self.on_end()
                    except Exception as e:
                        log_event("EventDispatcher on_end callback error", str(e))

                # After streaming completes, store assistant turn
                self.session.append_message("assistant", full_response)
                return full_response

            else:
                # Non-streaming: gather chunks (if any) and send once
                # Notify start as well, optionally
                if self.on_start:
                    try:
                        self.on_start()
                    except Exception as e:
                        log_event("EventDispatcher on_start callback error", str(e))

                response = ""
                async for chunk in self.agent.respond(user_input, stream=False):
                    if self.on_response_chunk:
                        try:
                            self.on_response_chunk(chunk)
                        except Exception as e:
                            log_event("EventDispatcher on_response_chunk error", str(e))
                    response += chunk

                # Notify end
                if self.on_end:
                    try:
                        self.on_end()
                    except Exception as e:
                        log_event("EventDispatcher on_end callback error", str(e))

                self.session.append_message("assistant", response)
                return response

        except Exception as exc:
            # Log and notify error callback
            err_msg = f"Error handling input: {exc}"
            log_event("EventDispatcher error", err_msg)
            if self.on_error:
                try:
                    self.on_error(err_msg)
                except Exception as e:
                    log_event("EventDispatcher on_error callback error", str(e))
            # Return a fallback error message
            return "Sorry, something went wrong while processing your request."

    def get_history(self):
        return self.session.get_recent_messages()


# EOC=========================================================================================================================

# 💡 Notes
# Feature	Description
# on_response_chunk	Function pointer from UI (e.g., update_output_text())
# stream=True	Supports live typing effect in GUI
# get_history()	UI can use this to show full chat so far