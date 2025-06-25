# interface/ui_pygame.py

import pygame
import sys
import asyncio
import threading
from queue import Queue
from interface.event_dispatcher import EventDispatcher

# UI Settings
WIDTH, HEIGHT = 800, 600
BG_COLOR = (30, 30, 30)
TEXT_COLOR = (255, 255, 255)
INPUT_BG = (50, 50, 50)
FONT_SIZE = 20
CURSOR_BLINK_INTERVAL = 500  # milliseconds

class AssistantPygameUI:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Offline AI Assistant")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, FONT_SIZE)

        self.chat_lines = []
        self.input_text = ""
        self.cursor_visible = True
        self.last_cursor_toggle = pygame.time.get_ticks()

        self.input_rect = pygame.Rect(10, HEIGHT - 40, WIDTH - 20, 30)

        # Queue for thread-safe streamed chunks
        self.response_queue = Queue()

        # Event dispatcher for async response
        self.dispatcher = EventDispatcher(on_response_chunk=self.handle_chunk)
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()

    def handle_chunk(self, chunk):
        self.response_queue.put(chunk)

    def submit_input(self):
        text = self.input_text.strip()
        if text:
            self.chat_lines.append(f"You: {text}")
            self.chat_lines.append("🤖: ")  # Placeholder for response
            self.input_text = ""
            asyncio.run_coroutine_threadsafe(
                self.dispatcher.handle_input(text, stream=True),
                self.loop
            )

    def update_response_from_queue(self):
        while not self.response_queue.empty():
            chunk = self.response_queue.get()
            if self.chat_lines and self.chat_lines[-1].startswith("🤖:"):
                self.chat_lines[-1] += chunk

    def draw_ui(self):
        self.screen.fill(BG_COLOR)

        # Draw chat lines
        y = 10
        for line in self.chat_lines[-25:]:
            rendered = self.font.render(line, True, TEXT_COLOR)
            self.screen.blit(rendered, (10, y))
            y += FONT_SIZE + 4

        # Draw input box
        pygame.draw.rect(self.screen, INPUT_BG, self.input_rect)
        input_display = self.input_text

        # Handle blinking cursor
        if self.cursor_visible:
            input_display += "|"

        input_surface = self.font.render(input_display, True, TEXT_COLOR)
        self.screen.blit(input_surface, (self.input_rect.x + 5, self.input_rect.y + 5))

        pygame.display.flip()

    def toggle_cursor(self):
        now = pygame.time.get_ticks()
        if now - self.last_cursor_toggle >= CURSOR_BLINK_INTERVAL:
            self.cursor_visible = not self.cursor_visible
            self.last_cursor_toggle = now

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.submit_input()
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                else:
                    self.input_text += event.unicode

    def run(self):
        while True:
            self.handle_events()
            self.toggle_cursor()
            self.update_response_from_queue()
            self.draw_ui()
            self.clock.tick(30)
