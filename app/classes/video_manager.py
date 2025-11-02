import tkinter as tk
from tkinter import ttk, Menu
from typing import Optional, Callable, Dict, Any
import os
import logging
import vlc
import sys

logger = logging.getLogger(__name__)

class VideoManager:
    """Manages video playback in the application using python-vlc."""
    def __init__(self, frame: tk.Frame, config: Optional[Dict[str, Any]] = None, content_frame = None):
        """Initialize the VideoManager with a frame to display videos."""
        self.frame = frame
        self.config = config or {}
        self.content_frame = content_frame
        self.current_video_path: Optional[str] = None
        self.on_video_error: Optional[Callable] = None
        self.instance: Optional[vlc.Instance] = None
        self.player: Optional[vlc.MediaPlayer] = None
        self.canvas: Optional[tk.Canvas] = None
        self.controls_visible = True
        self.controls_frame: Optional[ttk.Frame] = None
        self.play_pause_btn: Optional[ttk.Button] = None
        self.stop_btn: Optional[ttk.Button] = None
        self.seek_slider: Optional[ttk.Scale] = None
        self.time_lbl: Optional[ttk.Label] = None
        self.vol_slider: Optional[ttk.Scale] = None
        self.placeholder_label: Optional[ttk.Label] = None
        self._create_placeholder()
        self._setup_vlc()
        self._setup_controls()

    def _setup_vlc(self):
        """Initialize VLC instance and player."""
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.canvas = tk.Canvas(self.frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self._set_video_window()

    def _set_video_window(self):
        """Set the VLC video output window to the canvas."""
        if sys.platform.startswith("win"):
            self.player.set_hwnd(self.canvas.winfo_id())
        elif sys.platform == "darwin":
            self.player.set_nsobject(self.canvas.winfo_id())
        else:  # Linux/X11
            self.player.set_xwindow(self.canvas.winfo_id())

    def _create_placeholder(self):
        """Create a placeholder label for when no video is loaded."""
        config = self.config.get("video_manager", {})
        if hasattr(self, "placeholder_label"):
            if self.placeholder_label:
                self.placeholder_label.destroy()
        self.placeholder_label = ttk.Label(
            self.frame,
            text=config.get("placeholder_text", "Select a video file to play"),
            borderwidth=config.get("placeholder_borderwidth", 0),
            relief=config.get("placeholder_relief", "flat"),
            anchor=config.get("placeholder_anchor", "center"),
            background=config.get("placeholder_bg", "black"),
            foreground=config.get("placeholder_fg", "white")
        )
        self.placeholder_label.place(
            relx=config.get("placeholder_place_relx", 0.5),
            rely=config.get("placeholder_place_rely", 0.5),
            anchor=config.get("placeholder_place_anchor", "center")
        )

    def _setup_controls(self):
        """Set up playback controls."""
        # Controls frame
        self.controls_frame = ttk.Frame(self.frame)
        self.controls_frame.pack(fill="x", side="bottom")

        # Play/Pause toggle button
        self.play_pause_btn = ttk.Button(
            self.controls_frame,
            text="▶",
            command=self.toggle_play_pause,
            width=3,
        )
        self.play_pause_btn.pack(side="left", padx=2, pady=2)

        # Stop button
        self.stop_btn = ttk.Button(
            self.controls_frame,
            text="⏹",
            command=self.stop,
            width=3,
        )
        self.stop_btn.pack(side="left", padx=2, pady=2)

        # Seek bar + time label
        seek_frame = ttk.Frame(self.controls_frame)
        seek_frame.pack(side="right", fill="x", expand=True, padx=2, pady=2)

        self.time_lbl = ttk.Label(seek_frame, text="00:00 / 00:00", relief="sunken", borderwidth=1)
        self.time_lbl.pack(side="right")

        self.seek_slider = ttk.Scale(
            seek_frame,
            from_=0,
            to=1000,
            orient="horizontal",
            command=self._on_seek_move,
        )
        self.seek_slider.pack(side="left", fill="x", expand=True)

        # Volume control
        vol_frame = ttk.Frame(seek_frame)
        vol_frame.pack(side="right", padx=5, pady=2)

        ttk.Label(vol_frame, text="🔊").pack(side="left")

        self.vol_slider = ttk.Scale(
            vol_frame,
            from_=0,
            to=100,
            orient="horizontal",
            command=self._on_volume_change,
        )
        self.vol_slider.set(80)
        self.vol_slider.pack(side="left")

        # Right-click menu
        self.right_click_menu = Menu(self.frame, tearoff=0)
        self.show_controls_var = tk.BooleanVar(value=True)
        self.right_click_menu.add_checkbutton(
            label="Show Controls",
            variable=self.show_controls_var,
            command=self.toggle_controls,
        )
        self.canvas.bind("<Button-3>", self.show_right_click_menu)

        # Bind press, motion, and release for the seek slider
        self.seek_slider.bind("<ButtonPress-1>", self._on_seek_press)
        self.seek_slider.bind("<B1-Motion>", self._on_seek_move)
        self.seek_slider.bind("<ButtonRelease-1>", self._on_seek_release)

    def load_video(self, file_path: str):
        """Load and play a video file embedded in the canvas."""
        if not os.path.exists(file_path):
            self._create_placeholder()
            if self.on_video_error:
                self.on_video_error("File not found")
            return
        try:
            if self.player:
                media = self.instance.media_new(file_path)
                self.player.set_media(media)
                if hasattr(self, "placeholder_label"):
                    self.placeholder_label.destroy()
                self.canvas.pack(fill="both", expand=True)
                self.player.play()
                self.current_video_path = file_path
                self._update_seek_bar()
        except Exception as e:
            logger.error(f"Error loading video: {e}")
            self._create_placeholder()
            if self.on_video_error:
                self.on_video_error(str(e))

    def toggle_play_pause(self):
        """Toggle play/pause for the current video."""
        if self.player:
            if self.player.is_playing():
                self.player.pause()
                self.play_pause_btn.config(text="▶")
            else:
                self.player.play()
                self.play_pause_btn.config(text="⏸")

    def stop(self):
        """Stop the current video and reset to start."""
        if self.player:
            self.player.stop()
            self.player.set_time(0)
            self.play_pause_btn.config(text="▶")

    def _on_seek_press(self, event):
        """Handle press on the seek bar."""
        self.is_seeking = True
        self.initial_click_x = event.x

    def _on_seek_move(self, event):
        """Handle dragging the seek bar."""
        if self.is_seeking:
            width = self.seek_slider.winfo_width()
            if width == 0:
                return
            rel = event.x / width
            rel = max(0.0, min(rel, 1.0))
            self.seek_slider.set(rel * 1000)
            self._update_time_label(rel)

    def _on_seek_release(self, event):
        """Handle release of the seek bar (both click and drag)."""
        self.is_seeking = False
        width = self.seek_slider.winfo_width()
        if width == 0:
            return
        rel = event.x / width
        rel = max(0.0, min(rel, 1.0))
        self.seek_slider.set(rel * 1000)
        self._seek_to_slider_position()

    def _update_time_label(self, pos):
        """Format the label with the fractional position."""
        length = self.player.get_length()
        if length <= 0:
            self.time_lbl.config(text="00:00 / 00:00")
            return
        curr = int(pos * length)
        total = length
        self.time_lbl.config(
            text=f"{self._sec_to_mmss(curr)} / {self._sec_to_mmss(total)}"
        )

    def _seek_to_slider_position(self):
        """Tell VLC to seek to the position currently set on the slider."""
        pos = float(self.seek_slider.get()) / 1000.0
        length = self.player.get_length()
        if length > 0:
            self.player.set_time(int(pos * length))

    def _on_volume_change(self, value):
        """Set VLC volume (0-100)."""
        if self.player:
            self.player.audio_set_volume(int(float(value)))

    def _update_seek_bar(self):
        """Update the seek bar and time label."""
        if self.player and self.player.is_playing():
            length = self.player.get_length()
            if length > 0:
                current = self.player.get_time()
                pos = current / length
                self.seek_slider.set(pos * 1000)
                self.time_lbl.config(
                    text=f"{self._sec_to_mmss(current)} / {self._sec_to_mmss(length)}"
                )
        self.frame.after(500, self._update_seek_bar)

    def _sec_to_mmss(self, ms):
        """Convert milliseconds to MM:SS format."""
        s = ms // 1000
        return f"{s // 60:02}:{s % 60:02}"

    def toggle_controls(self):
        """Toggle the visibility of the controls."""
        self.controls_visible = self.show_controls_var.get()
        if self.controls_visible:
            self.controls_frame.pack(fill="x", side="bottom")
        else:
            self.controls_frame.pack_forget()

    def show_right_click_menu(self, event):
        """Show the right-click menu at the mouse position."""
        self.right_click_menu.tk_popup(event.x_root, event.y_root)

    def clear(self):
        """Clear the current video."""
        if self.player:
            self.player.stop()
        self._create_placeholder()
        self.current_video_path = None

    def set_error_handler(self, callback: Callable):
        """Set a callback for video loading errors."""
        self.on_video_error = callback

    def hide(self):
        """Hide the frame"""
        if self.frame:
            self.stop()
            self.canvas.pack_forget()
