import subprocess

OLLAMA_MODELS_URL = "https://ollama.com/library"

def list_local_models():
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()
        models = []

        for line in lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 1:
                models.append(parts[0])

        return models
    except Exception as e:
        return [f"Error getting model list: {e}"]

def get_ollama_library_url():
    return OLLAMA_MODELS_URL


# ✅ Now add this class
class ModelSelector:
    def __init__(self, config: dict):
        self.config = config
        self.local_models = list_local_models()

    def get_active_model(self) -> str:
        # 1. Prefer user-defined config
        if "default_model" in self.config:
            return self.config["default_model"]

        # 2. Otherwise, pick a safe model
        for preferred in ["openhermes:latest", "llama3", "mistral", "gemma"]:
            for model in self.local_models:
                if preferred in model:
                    return model

        return self.local_models[0] if self.local_models else "openhermes:latest"
