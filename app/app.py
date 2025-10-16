import os
import json
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv
import logging
from classes import MediaManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load app configuration from JSON
with open("appconfig.json", "r") as f:
    app_config = json.load(f)

class MediaManagerApp:
    def __init__(self):
        # Database configuration from .env
        conn_config = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "retries": int(os.getenv("DB_RETRIES")),
            "delay": int(os.getenv("DB_DELAY")),
        }

        # Window configuration from appconfig.json
        window_config = app_config["window"]

        # Window manager configuration from appconfig.json
        window_manager_config = app_config.get("window_manager", {})

        # Grid configuration from appconfig.json
        grid_config = app_config["grid"]

        # Initialize MediaManager
        self.media_manager = MediaManager(conn_config, window_config, grid_config, window_manager_config=window_manager_config)

if __name__ == "__main__":
    try:
        app = MediaManagerApp()
        app.media_manager.root.mainloop()
    except Exception as e:
        logger.exception("Failed to start application")
        messagebox.showerror("Error", f"Failed to start application: {e}")
