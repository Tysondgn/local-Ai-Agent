# interface/ui_tk.py

import tkinter as tk
from tkinter import scrolledtext, ttk
import asyncio
import threading
import time
from interface.event_dispatcher import EventDispatcher
from spellchecker import SpellChecker  # pip install pyspellchecker
from datetime import datetime
import platform

class ModernButton(tk.Canvas):
    """Modern button with rounded corners and hover effects"""
    def __init__(self, parent, text, command=None, bg="#4CAF50", fg="white", width=80, height=35, **kwargs):
        super().__init__(parent, width=width, height=height, bg=parent.cget("bg"), highlightthickness=0, **kwargs)
        self.command = command
        self.bg = bg
        self.fg = fg
        self.text = text
        self.hover = False
        
        # Bind events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)
        
        self._draw()
    
    def _draw(self):
        self.delete("all")
        # Draw rounded rectangle
        radius = 8
        color = "#45a049" if self.hover else self.bg
        
        # Create rounded rectangle
        self.create_rounded_rectangle(2, 2, self.winfo_reqwidth()-2, self.winfo_reqheight()-2, 
                                    radius, fill=color, outline="")
        
        # Add text
        self.create_text(self.winfo_reqwidth()//2, self.winfo_reqheight()//2, 
                        text=self.text, fill=self.fg, font=("Segoe UI", 10, "bold"))
    
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        """Create a rounded rectangle"""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def _on_enter(self, event):
        self.hover = True
        self._draw()
    
    def _on_leave(self, event):
        self.hover = False
        self._draw()
    
    def _on_click(self, event):
        self.configure(cursor="hand2")
    
    def _on_release(self, event):
        self.configure(cursor="")
        if self.command:
            self.command()

class ModernEntry(tk.Frame):
    """Modern entry with rounded corners and placeholder"""
    def __init__(self, parent, placeholder="", font=("Segoe UI", 12), **kwargs):
        super().__init__(parent, bg=parent.cget("bg"))
        # Remove font from kwargs if present to avoid duplicate
        kwargs.pop("font", None)
        # Create canvas for rounded background
        self.canvas = tk.Canvas(self, height=40, bg=parent.cget("bg"), highlightthickness=0)
        self.canvas.pack(fill="x", padx=5)
        # Create entry widget
        self.entry = tk.Entry(self.canvas, font=font, bd=0, 
                            bg="#f0f0f0", fg="#333333", insertbackground="#333333",
                            relief="flat", **kwargs)
        
        # Position entry in canvas
        self.canvas.create_window(10, 20, anchor="w", window=self.entry, width=self.canvas.winfo_reqwidth()-20)
        
        self.placeholder = placeholder
        self.placeholder_color = "#999999"
        self.text_color = "#333333"
        
        # Bind events
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<KeyRelease>", self._on_key_release)
        
        # Set initial placeholder
        self._set_placeholder()
    
    def _on_focus_in(self, event):
        if self.entry.get() == self.placeholder:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=self.text_color)
    
    def _on_focus_out(self, event=None):
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=self.placeholder_color)
    
    def _set_placeholder(self):
        """Set initial placeholder without requiring event"""
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=self.placeholder_color)
    
    def _on_key_release(self, event):
        if self.entry.get() != self.placeholder:
            self.entry.config(fg=self.text_color)
    
    def get(self):
        text = self.entry.get()
        return "" if text == self.placeholder else text
    
    def delete(self, first, last):
        self.entry.delete(first, last)
    
    def insert(self, index, string):
        self.entry.insert(index, string)
    
    def bind(self, sequence, func):
        self.entry.bind(sequence, func)

class AssistantUI:
    def __init__(self):
        self.theme = 'dark'  # default to dark theme
        self._set_theme_colors()
        self.root = tk.Tk()
        self.root.title("AI Assistant - Modern Interface")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        self.root.configure(bg=self.bg_color)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self._create_header()
        self._create_chat_area()
        self._create_input_area()
        self._create_status_bar()
        self._create_theme_toggle()
        print("[DEBUG UI] Creating EventDispatcher")
        self.dispatcher = EventDispatcher(
            on_response_chunk=self.handle_chunk,
            on_start=self._on_response_start,
            on_end=self._on_response_end,
            on_error=self._on_response_error
        )
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        try:
            self.spellchecker = SpellChecker()
        except Exception:
            self.spellchecker = None
        self._loading_job = None
        self._streaming = False
        self._set_status("Agent", "ok")
        try:
            import os
            profile_path = self.dispatcher.agent.memory_manager.profile.path \
                if hasattr(self.dispatcher.agent, "memory_manager") else None
            if profile_path and os.access(profile_path, os.W_OK):
                self._set_status("Memory", "ok")
            else:
                self._set_status("Memory", "error")
        except Exception:
            self._set_status("Memory", "unknown")
        self._set_status("LLM", "unknown")

    def _set_theme_colors(self):
        if getattr(self, 'theme', 'dark') == 'dark':
            self.bg_color = "#181c24"
            self.chat_bg = "#232936"
            self.text_color = "#f8f8f2"
            self.accent_color = "#4f8cff"
            self.success_color = "#27ae60"
            self.warning_color = "#f39c12"
            self.error_color = "#e74c3c"
            self.status_bg = "#232936"
            self.status_fg = "#b2becd"
            self.input_bg = "#232936"
            self.input_fg = "#f8f8f2"
            self.placeholder_color = "#6c7a89"
        else:
            self.bg_color = "#f8f9fa"
            self.chat_bg = "#ffffff"
            self.text_color = "#2c3e50"
            self.accent_color = "#3498db"
            self.success_color = "#27ae60"
            self.warning_color = "#f39c12"
            self.error_color = "#e74c3c"
            self.status_bg = "#ecf0f1"
            self.status_fg = "#7f8c8d"
            self.input_bg = "#f0f0f0"
            self.input_fg = "#333333"
            self.placeholder_color = "#999999"

    def _create_theme_toggle(self):
        toggle_btn = tk.Button(self.main_frame, text="🌙" if self.theme == 'light' else "☀️", 
                               command=self._toggle_theme, bg=self.status_bg, fg=self.status_fg, bd=0, font=("Segoe UI", 12))
        toggle_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)
        self._theme_toggle_btn = toggle_btn

    def _toggle_theme(self):
        self.theme = 'light' if self.theme == 'dark' else 'dark'
        self._set_theme_colors()
        self.root.configure(bg=self.bg_color)
        self.main_frame.configure(bg=self.bg_color)
        self.chat_box.configure(bg=self.chat_bg, fg=self.text_color, insertbackground=self.text_color)
        self.input_entry.entry.configure(bg=self.input_bg, fg=self.input_fg, insertbackground=self.input_fg)
        self.input_entry.placeholder_color = self.placeholder_color
        self.input_entry.text_color = self.input_fg
        self.suggestion_label.configure(bg=self.bg_color, fg=self.warning_color)
        for name, item in self.status_items.items():
            item["canvas"].configure(bg=self.status_bg)
            item["label"].configure(bg=self.status_bg, fg=self.status_fg)
        self.time_label.configure(bg=self.status_bg, fg=self.status_fg)
        self._theme_toggle_btn.configure(bg=self.status_bg, fg=self.status_fg, text=("🌙" if self.theme == 'light' else "☀️"))

    def _create_header(self):
        """Create modern header with title and subtitle"""
        header_frame = tk.Frame(self.main_frame, bg=self.bg_color, height=80)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.grid_propagate(False)
        
        # Title
        title_label = tk.Label(header_frame, text="🤖 AI Assistant", 
                              font=("Segoe UI", 24, "bold"), 
                              fg=self.text_color, bg=self.bg_color)
        title_label.pack(pady=(20, 5))
        
        # Subtitle
        subtitle_label = tk.Label(header_frame, text="Your intelligent conversation partner", 
                                 font=("Segoe UI", 12), 
                                 fg="#7f8c8d", bg=self.bg_color)
        subtitle_label.pack()

    def _create_chat_area(self):
        chat_frame = tk.Frame(self.main_frame, bg=self.chat_bg, relief="flat", bd=1)
        chat_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        chat_frame.rowconfigure(0, weight=1)
        chat_frame.columnconfigure(0, weight=1)
        self.chat_box = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            bg=self.chat_bg,
            fg=self.text_color,
            insertbackground=self.text_color,
            font=("Segoe UI Emoji", 12),  # Emoji font
            relief="flat",
            bd=0,
            padx=20,
            pady=20,
            state="disabled"
        )
        self.chat_box.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.chat_box.tag_configure("user", foreground=self.accent_color, font=("Segoe UI Emoji", 12, "bold"), spacing1=10, spacing3=10)
        self.chat_box.tag_configure("assistant", foreground=self.success_color, font=("Segoe UI Emoji", 12), spacing1=10, spacing3=10)
        self.chat_box.tag_configure("timestamp", foreground=self.status_fg, font=("Segoe UI", 9), spacing1=5)
        self.chat_box.tag_configure("error", foreground=self.error_color, font=("Segoe UI", 12, "italic"))

    def _create_input_area(self):
        input_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        input_frame.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        input_frame.columnconfigure(0, weight=1)
        input_container = tk.Frame(input_frame, bg=self.input_bg, relief="flat", bd=1)
        input_container.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        input_container.columnconfigure(0, weight=1)
        # Modern entry field with emoji font
        self.input_entry = ModernEntry(input_container, placeholder="Type your message here...", font=("Segoe UI Emoji", 12))
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
        self.input_entry.bind("<Return>", self.on_enter_pressed)
        self.input_entry.bind("<KeyRelease>", self.on_key_release)
        self.send_button = ModernButton(input_container, "Send", command=self.on_enter_pressed, bg=self.accent_color, width=100, height=40)
        self.send_button.grid(row=0, column=1, padx=(0, 15), pady=10)
        self.suggestion_label = tk.Label(input_frame, text="", fg=self.warning_color, font=("Segoe UI", 10), bg=self.bg_color, anchor="w")
        self.suggestion_label.grid(row=1, column=0, sticky="w", pady=(5, 0))

    def _create_status_bar(self):
        status_frame = tk.Frame(self.main_frame, bg=self.status_bg, relief="flat", bd=1)
        status_frame.grid(row=3, column=0, sticky="ew")
        status_frame.columnconfigure((0, 1, 2, 3), weight=1)
        self.status_items = {}
        for idx, name in enumerate(["LLM", "Memory", "Agent"]):
            frame = tk.Frame(status_frame, bg=self.status_bg)
            frame.grid(row=0, column=idx, padx=15, pady=8, sticky="w")
            canvas = tk.Canvas(frame, width=16, height=16, bg=self.status_bg, highlightthickness=0)
            oval = canvas.create_oval(2, 2, 14, 14, fill="#bdc3c7", outline="")
            canvas.pack(side=tk.LEFT)
            label = tk.Label(frame, text=name, font=("Segoe UI", 10, "bold"), fg=self.status_fg, bg=self.status_bg)
            label.pack(side=tk.LEFT, padx=(8, 0))
            self.status_items[name] = {
                "canvas": canvas,
                "oval": oval,
                "label": label,
                "state": "unknown"
            }
        self.time_label = tk.Label(status_frame, text="", font=("Segoe UI", 10), fg=self.status_fg, bg=self.status_bg)
        self.time_label.grid(row=0, column=3, sticky="e", padx=15)
        self._update_time()

    def _update_time(self):
        """Update clock in status bar"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.time_label.config(text=now)
        self.root.after(60000, self._update_time)

    def _set_status(self, name, state):
        """Update status indicator"""
        item = self.status_items.get(name)
        if not item:
            return
        
        color_map = {
            "ok": self.success_color,
            "busy": self.warning_color,
            "error": self.error_color,
            "unknown": "#bdc3c7"
        }
        
        color = color_map.get(state, "#bdc3c7")
        canvas = item["canvas"]
        canvas.itemconfig(item["oval"], fill=color)
        item["state"] = state

    def on_key_release(self, event=None):
        """Check spelling and provide suggestions"""
        if not self.spellchecker:
            return
        
        text = self.input_entry.get().strip()
        if not text:
            self.suggestion_label.config(text="")
            return
        
        # Get the last word
        words = text.split()
        if not words:
            self.suggestion_label.config(text="")
            return
            
        last = words[-1]
        if not last.isalpha():
            self.suggestion_label.config(text="")
            return
        
        # Check spelling
        misspelled = self.spellchecker.unknown([last])
        if misspelled:
            suggestions = self.spellchecker.candidates(last)
            if suggestions:
                sug_list = list(suggestions)[:3]
                self.suggestion_label.config(
                    text=f"💡 Did you mean: {', '.join(sug_list)}?"
                )
            else:
                self.suggestion_label.config(text="")
        else:
            self.suggestion_label.config(text="")

    def _on_response_start(self):
        """Called when streaming starts"""
        self._set_status("LLM", "busy")
        self._start_loading_animation()

    def _on_response_end(self):
        """Called when streaming completes"""
        self._stop_loading_animation()
        self._set_status("LLM", "ok")

    def _on_response_error(self, error_msg=None):
        """Called when an error occurs"""
        self._stop_loading_animation()
        self._set_status("LLM", "error")
        if error_msg:
            self._append_chat("System", f"❌ Error: {error_msg}", tag="error")

    def _start_loading_animation(self):
        """Start typing animation"""
        def animate():
            if not self._streaming:
                return
            try:
                self.chat_box.configure(state="normal")
                self.chat_box.insert(tk.END, "⏳")
                self.chat_box.see(tk.END)
                self.chat_box.configure(state="disabled")
            except Exception:
                pass
            self._loading_job = self.root.after(500, animate)
        
        self._loading_job = self.root.after(500, animate)

    def _stop_loading_animation(self):
        """Stop typing animation"""
        if self._loading_job:
            self.root.after_cancel(self._loading_job)
            self._loading_job = None
        
        try:
            self.chat_box.configure(state="normal")
            self.chat_box.insert(tk.END, "\n")
            self.chat_box.configure(state="disabled")
        except Exception:
            pass
        self._streaming = False

    def on_enter_pressed(self, event=None):
        user_input = self.input_entry.get().strip()
        if not user_input:
            return
        self.suggestion_label.config(text="")
        self._append_chat("You", user_input, tag="user")
        self._streaming = True
        self.chat_box.configure(state="normal")
        self.chat_box.insert(tk.END, "🤖 ", "assistant")
        self.chat_box.configure(state="disabled")
        # Only stream, do not append full response at end (fix duplicate bug)
        asyncio.run_coroutine_threadsafe(
            self.dispatcher.handle_input(user_input, stream=True),
            self.loop
        )
        self.input_entry.delete(0, tk.END)
        return "break"

    def handle_chunk(self, chunk):
        if self._loading_job:
            self._stop_loading_animation()
        # Only append streaming chunks, not the full response at end
        self.root.after(0, lambda: self._append_stream(chunk))

    def _append_stream(self, chunk):
        """Append streaming chunk to chat"""
        self.chat_box.configure(state="normal")
        self.chat_box.insert(tk.END, chunk)
        self.chat_box.see(tk.END)
        self.chat_box.configure(state="disabled")

    def _append_chat(self, sender, message, tag=None):
        """Append a new chat message"""
        self.chat_box.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M")
        
        # Create message with proper formatting
        if sender == "You":
            icon = "👤"
        elif sender == "System":
            icon = "⚙️"
        else:
            icon = "🤖"
        
        formatted_message = f"[{timestamp}] {icon} {sender}: {message}\n"
        self.chat_box.insert(tk.END, formatted_message, tag)
        self.chat_box.see(tk.END)
        self.chat_box.configure(state="disabled")

    def run(self):
        """Start the UI main loop"""
        print("[DEBUG UI] Entering mainloop")
        self.root.mainloop()

# EOC=============================================================================================================================

# ✅ Modern Features
# Component	Function
# Modern Design	Clean, rounded corners, proper spacing
# Better Colors	High contrast, readable color scheme
# Larger Fonts	Segoe UI font family, readable sizes
# Rounded Input	Modern entry field with placeholder
# Custom Button	Hover effects, rounded corners
# Better Emojis	Proper emoji rendering and spacing
# Status Indicators	Color-coded status lights
# Responsive Layout	Adapts to window resizing
# Spell Check	Real-time spelling suggestions
# Loading Animation	Smooth typing indicators