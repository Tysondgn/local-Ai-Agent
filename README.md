# Offline AI Agent

This project is a desktop AI assistant that runs entirely offline, leveraging the power of local large language models (LLMs) through Ollama. It features a modern, user-friendly interface and a memory system that allows it to learn from your conversations.

![UI Screenshot](placeholder.png) <!-- You can replace placeholder.png with a real screenshot -->

## Features

- **100% Offline**: All components, from the LLM to the user interface, run locally on your machine.
- **Local LLM Integration**: Powered by Ollama, allowing you to use various open-source models like OpenHermes, Llama 3, etc.
- **Persistent Memory**: The agent remembers key facts, user preferences, and previous conversations to provide contextual responses.
- **Semantic Search**: You can search the agent's memory using natural language (e.g., "search memory for...").
- **Modern UI**: A clean, responsive interface built with Tkinter, featuring:
    - Dark and Light themes.
    - Real-time status indicators for the LLM, Memory, and Agent.
    - Live-streaming responses with a "typing" animation.
    - Spell-checking and suggestions.
- **Extensible Architecture**: The code is organized into modules (`agent`, `llm`, `memory`, `tools`), making it easy to add new tools, models, or memory systems.

## How It Works

The agent processes user input through a core loop:
1.  **Input Handling**: The UI captures user input.
2.  **Command Routing**: It first checks if the input is a special command (e.g., for a tool).
3.  **Prompt Engineering**: If it's a regular chat message, it builds a detailed prompt using your profile, chat history, and semantic memory.
4.  **LLM Interaction**: It sends the prompt to the locally-running Ollama model.
5.  **Response Streaming**: The response is streamed back to the UI in real-time.
6.  **Memory Update**: After the conversation turn, the agent processes the interaction, extracts key facts, and updates its memory for future use.

## Setup and Installation

Follow these steps to get the AI agent running on your local machine.

### 1. Prerequisites
- Python 3.8 or newer.
- A computer with a decent CPU/GPU capable of running local LLMs.

### 2. Download and Set Up Ollama
Ollama is required to run the local LLM.

- Download and install Ollama from the official website: [https://ollama.com/](https://ollama.com/)
- After installation, run the following command in your terminal to download the `openhermes` model (around 5 GB). This only needs to be done once.
  ```sh
  ollama run openhermes
  ```
- Make sure Ollama is running in the background before starting the AI agent.

### 3. Clone the Repository
Clone this project to your local machine.
```sh
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```
*(Replace `your-username/your-repo-name` with the actual URL after you upload it to GitHub.)*

### 4. Install Dependencies
Install the required Python packages using the `requirements.txt` file.
```sh
pip install -r requirements.txt
```

### 5. Run the Application
Once Ollama is running and the dependencies are installed, you can start the agent.
```sh
python run.py
```
The application window should appear, and you can start chatting with your offline AI assistant!

## Project Structure

The codebase is organized into the following directories:

- `/agent`: The core logic of the AI agent, including the main loop and command routing.
- `/config`: Configuration files for settings and prompts.
- `/data`: Stores logs and the user's profile.
- `/interface`: The Tkinter-based graphical user interface.
- `/llm`: Handles all communication with the Ollama LLM engine.
- `/memory`: Manages the agent's short-term and long-term memory, including the vector-based semantic search.
- `/tools`: Extensible modules for specific tasks (e.g., file search, web downloads).
- `/utils`: Helper scripts and utilities, like the event logger. 