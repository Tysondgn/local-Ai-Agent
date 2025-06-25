# run.py

# import sys
# import os
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # Add project root

# from interface.ui_pygame import AssistantPygameUI  # 👉 Updated to use Pygame UI

# if __name__ == "__main__":
#     ui = AssistantPygameUI()
#     ui.run()

# =========================================================to use ui_tk use below code==============================================================

import sys
import os
from pathlib import Path
from agent.profile_form import ProfileForm
sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # Add project root

from interface.ui_tk import AssistantUI

if __name__ == "__main__":

        # Show form on first run
    if not Path("data/profile.json").exists():
        form = ProfileForm()
        form.run()
    ui = AssistantUI()
    print("🚀 Launching UI...")
    ui.run()
