import tkinter as tk
from tkinter import messagebox
import json
from pathlib import Path

PROFILE_PATH = Path("data/profile.json")

class ProfileForm:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Create Your Profile")
        self.entries = {}

        fields = [
            ("Name*", "name"),
            ("Pet Name", "pet_name"),
            ("Phone", "phone"),
            ("Email", "email"),
            ("Password", "password"),
            ("Job Title", "job"),
            ("Organization", "organization"),
            ("Gender", "gender"),
            ("Religion", "religion"),
        ]

        for idx, (label, key) in enumerate(fields):
            tk.Label(self.root, text=label).grid(row=idx, column=0, sticky="w", padx=10, pady=5)
            entry = tk.Entry(self.root, width=40, show="*" if "password" in key else None)
            entry.grid(row=idx, column=1, padx=10, pady=5)
            self.entries[key] = entry

        tk.Button(self.root, text="Save", command=self.save_profile).grid(columnspan=2, pady=10)

    def save_profile(self):
        profile = {key: entry.get().strip() for key, entry in self.entries.items()}

        if not profile["name"]:
            messagebox.showerror("Missing Name", "Name is required.")
            return

        PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)

        messagebox.showinfo("Profile Saved", "Your profile has been saved.")
        self.root.destroy()

    def run(self):
        self.root.mainloop()
