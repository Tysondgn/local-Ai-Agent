# agent/session_state.py

from collections import deque
from datetime import datetime

class SessionState:
    def __init__(self, max_messages=10):
        self.chat_history = deque(maxlen=max_messages)

    def append_message(self, role: str, content: str):
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.chat_history.append(message)

    def get_recent_messages(self):
        return list(self.chat_history)

    def reset(self):
        self.chat_history.clear()

    def get_last_user_message(self):
        for message in reversed(self.chat_history):
            if message["role"] == "user":
                return message["content"]
        return None

    def __len__(self):
        return len(self.chat_history)

# EOC==========================================================================================================

# 💡 Features
# Method	Purpose
# append_message(role, content)	Adds a new message (e.g., user input or LLM reply)
# get_recent_messages()	Returns a list of the last N messages
# reset()	Clears the session history (useful for “new chat”)
# get_last_user_message()	Handy for tools or repeating the last command