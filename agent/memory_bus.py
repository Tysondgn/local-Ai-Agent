# agent/memory_bus.py

import json
import os
from datetime import datetime
from utils.logger import log_event
from pathlib import Path

PROFILE_PATH = Path("data/profile.json")

class MemoryBus:
    def __init__(self, config):
        self.profile_path = config.get("profile_path", "data/profile.json")
        self.log_dir = config.get("log_dir", "data/logs/")
        self.profile = {}
        self.chat_log_buffer = []
        self.load_profile()

    def load_profile(self):
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    self.profile = json.load(f)
                log_event("Profile loaded", self.profile)
            except Exception as e:
                log_event("Error loading profile", str(e))
                self.profile = {}
        else:
            self.profile = {}

    def get_profile(self):
        return self.profile

    def update_profile(self, key, value):
        self.profile[key] = value
        self.save_profile()

    def save_profile(self):
        try:
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(self.profile, f, indent=2)
            log_event("Profile saved", self.profile)
        except Exception as e:
            log_event("Error saving profile", str(e))

    def log_conversation(self, user_input, response):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "time": timestamp,
            "user": user_input,
            "assistant": response
        }
        self.chat_log_buffer.append(log_entry)

        # Write to disk after every 5 messages for performance
        if len(self.chat_log_buffer) >= 5:
            self.flush_log_to_disk()

    def flush_log_to_disk(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        filename = datetime.now().strftime("%Y-%m-%d") + ".jsonl"
        full_path = os.path.join(self.log_dir, filename)
        try:
            with open(full_path, "a", encoding="utf-8") as f:
                for entry in self.chat_log_buffer:
                    f.write(json.dumps(entry) + "\n")
            log_event("Log flushed to disk", full_path)
        except Exception as e:
            log_event("Error writing logs", str(e))
        self.chat_log_buffer = []

# EOC===============================================================================================================

# 🧠 Features Supported
# Feature	Description
# get_profile()	Fast profile access in RAM
# update_profile()	Change name, age, mood, etc.
# log_conversation()	Log user & assistant turns
# flush_log_to_disk()	Writes in chunks to avoid IO overload
# save_profile()	Called only on changes