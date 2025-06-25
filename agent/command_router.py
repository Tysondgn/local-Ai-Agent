# agent/command_router.py

import re
from tools import file_search, media_downloader, schedule_manager
from utils.logger import log_event

class CommandRouter:
    def __init__(self):
        # List of available commands with their handlers
        self.commands = {
            "search file": file_search.search_files,
            "download video": media_downloader.download_media,
            "set reminder": schedule_manager.add_task_to_schedule
        }

        # Keyword triggers (can later be replaced with local intent model)
        self.patterns = {
            "search file": r"(find|search).*(file|document)",
            "download video": r"(download).*(youtube|video|mp4)",
            "set reminder": r"(remind|reminder|schedule).*"
        }

    def is_tool_command(self, user_input: str) -> bool:
        """
        Checks if the input matches any known tool command pattern.
        """
        user_input = user_input.lower()
        for pattern in self.patterns.values():
            if re.search(pattern, user_input):
                return True
        return False

    async def route_command(self, user_input: str, session_state):
        """
        Match input to a command, run it, and return the result.
        """
        user_input = user_input.lower()
        for command_name, pattern in self.patterns.items():
            if re.search(pattern, user_input):
                handler = self.commands[command_name]
                # log_event("Tool matched", command_name)  # Commented out for performance
                return await handler(user_input, session_state)

        # log_event("No tool matched", user_input)  # Commented out for performance
        return "Sorry, I couldn't understand the command."

# EOC==========================================================================================================

#  Tools Covered by Default
# Command	Tool
# "find file"	file_search.py
# "download YouTube video"	media_downloader.py
# "reminder"	schedule_manager.py

# More tools can easily be plugged in later.