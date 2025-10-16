import tkinter as tk
from typing import Dict, Tuple, Optional
import logging
import platform
import subprocess

logger = logging.getLogger(__name__)

class WindowManager:
    def __init__(self, parent_media_manager, window_config: Dict, window_manager_config: Dict = None):
        if parent_media_manager:
            root = tk.Toplevel(parent_media_manager.root)
        else:
            root = tk.Tk()
        self.root = root
        self.window_config = window_config
        self.window_manager_config = window_manager_config or {}
        self.has_resize_grips = False
        self.fullscreen = self.window_config.get("fullscreen", False)
        self.set_window_config(window_config)
        self._drag_data = {"x": 0, "y": 0}

    def _toggle_fullscreen_event(self, event=None):
        """Toggle fullscreen mode."""
        self.fullscreen = not self.fullscreen
        self.toggle_fullscreen(self.fullscreen)

    def get_root(self) -> tk.Tk:
        """Return the root Tkinter window."""
        return self.root

    def set_window_config(self, window_config: Dict) -> None:
        """Apply the window configuration to the root window."""
        if "height" in window_config and "width" in window_config:
            self.resize((window_config["width"], window_config["height"]))
        if "title" in window_config:
            self.set_title(window_config["title"])
        if "show_menubar" in window_config:
            self.toggle_menubar(window_config["show_menubar"])
        if "fullscreen" in window_config:
            self.toggle_fullscreen(window_config["fullscreen"])
        if "borderless" in window_config:
            self.toggle_borderless(window_config["borderless"])
        if "always_on_top" in window_config:
            self.toggle_always_on_top(window_config["always_on_top"])

        if window_config.get("exit_on_escape", False):
            self.root.bind("<Escape>", lambda e: self.close_window())
            self.root.focus_force()
        if window_config.get("fullscreen_on_f11", False):
            self.root.bind("<F11>", lambda e: self.toggle_fullscreen(not self.fullscreen))
            self.root.focus_force()

    def close_window(self) -> None:
        """Close the root window."""
        self.root.destroy()

    def resize(self, dimensions: Tuple[int, int]) -> None:
        """Resize the window to the specified dimensions (width, height)."""
        self.root.geometry(f"{dimensions[0]}x{dimensions[1]}")

    def set_title(self, value: str) -> None:
        """Set the title of the window."""
        self.root.title(value)
        if hasattr(self, "title_bar"):
            self.title_bar.config(text=value)

    def toggle_menubar(self, value: bool) -> None:
        """Show or hide the menubar based on the boolean value."""
        if value:
            self.add_menu_items()
        else:
            self.root.config(menu="")

    def add_menu_items(self) -> None:
        """Add default menu items to the menubar."""
        menu_config = self.window_manager_config.get("menu_items", {})

        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(
            label=menu_config.get("file_menu", {}).get("exit_label", "Exit"),
            command=self.root.quit
        )
        menubar.add_cascade(
            label=menu_config.get("file_menu", {}).get("label", "File"),
            menu=file_menu
        )
        self.root.config(menu=menubar)

    def toggle_fullscreen(self, value: bool) -> None:
        """Toggle fullscreen mode based on the boolean value."""
        self.root.attributes("-fullscreen", value)
        self.fullscreen = value

    def toggle_always_on_top(self, value: bool) -> None:
        """Toggle whether the window stays on top of others."""
        self.root.attributes("-topmost", value)

    def toggle_borderless(self, value: bool) -> None:
        """Toggle borderless mode."""
        self.root.overrideredirect(value)
        if value:
            self.root.bind("<ButtonPress-1>", self.on_drag_start)
            self.root.bind("<ButtonRelease-1>", self.on_drag_stop)
            self.root.bind("<B1-Motion>", self.on_drag_motion)
            show_custom = self.window_config.get("show_custom_titlebar", False)
            if show_custom:
                self.create_custom_title_bar()
            else:
                self._mouse_inside = False
                self.root.bind("<Enter>", self._on_root_enter)
                self.root.bind("<Leave>", self._on_root_leave)
            if not self.has_resize_grips:
                self.create_resize_grips()
        else:
            self.root.unbind("<ButtonPress-1>")
            self.root.unbind("<ButtonRelease-1>")
            self.root.unbind("<B1-Motion>")
            self.root.unbind("<Enter>")
            self.root.unbind("<Leave>")
            if hasattr(self, "title_bar_frame"):
                self.title_bar_frame.destroy()
            if self.has_resize_grips:
                self.delete_resize_grips()

    def create_resize_grips(self):
        """Create resize grips at the bottom corners of the window."""
        if not ("borderless" in self.window_config and self.window_config["borderless"]):
            return

        grip_config = self.window_manager_config.get("resize_grips", {})
        self.grips = []
        grip_size = grip_config.get("width", 7)

        # Bottom right grip
        grip = tk.Frame(
            self.root,
            bg=grip_config.get("bg", "#333333"),
            width=grip_size,
            height=grip_size,
            cursor=grip_config.get("bottom_right_cursor", "bottom_right_corner")
        )
        grip.place(relx=1.0, rely=1.0, anchor="se")
        grip.bind("<ButtonPress-1>", lambda e: self.on_resize_start(e, "se"))
        grip.bind("<B1-Motion>", lambda e: self.on_resize_motion(e, "se"))
        self.grips.append(grip)

        # Bottom left grip
        grip = tk.Frame(
            self.root,
            bg=grip_config.get("bg", "#333333"),
            width=grip_size,
            height=grip_size,
            cursor=grip_config.get("bottom_left_cursor", "bottom_left_corner")
        )
        grip.place(relx=0.0, rely=1.0, anchor="sw")
        grip.bind("<ButtonPress-1>", lambda e: self.on_resize_start(e, "sw"))
        grip.bind("<B1-Motion>", lambda e: self.on_resize_motion(e, "sw"))
        self.grips.append(grip)

        self.has_resize_grips = True

    def delete_resize_grips(self):
        """Delete the resize grips."""
        if hasattr(self, "grips"):
            for grip in self.grips:
                grip.destroy()
            del self.grips
        self.has_resize_grips = False

    def on_resize_start(self, event, anchor):
        """Store the starting position of the resize."""
        self._resize_anchor = anchor
        self._resize_start_x = event.x_root
        self._resize_start_y = event.y_root
        self._resize_start_width = self.root.winfo_width()
        self._resize_start_height = self.root.winfo_height()

    def on_resize_motion(self, event, anchor):
        """Move the window during resize."""
        dx = event.x_root - self._resize_start_x
        dy = event.y_root - self._resize_start_y
        new_width = self._resize_start_width
        new_height = self._resize_start_height
        if anchor == "se":
            new_width += dx
            new_height += dy
        elif anchor == "sw":
            new_width -= dx
            new_height += dy
        new_width = max(200, new_width)
        new_height = max(100, new_height)
        self.root.geometry(f"{new_width}x{new_height}")

    def _on_root_enter(self, event=None):
        """Handle mouse entering the root window."""
        self._mouse_inside = True
        self._show_temp_titlebar()
        if not self.has_resize_grips:
            self.create_resize_grips()

    def _on_root_leave(self, event=None):
        """Handle mouse leaving the root window."""
        self.root.after(1000, self._maybe_hide_UI)

    def _on_titlebar_enter(self, event=None):
        """Handle mouse entering the titlebar."""
        self._mouse_inside = True

    def _on_titlebar_leave(self, event=None):
        """Handle mouse leaving the titlebar."""
        self._mouse_inside = False
        self.root.after(1000, self._maybe_hide_UI)

    def _maybe_hide_UI(self):
        """Hide UI elements if the mouse is not inside the window."""
        x_root = self.root.winfo_rootx()
        y_root = self.root.winfo_rooty()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        try:
            mouse_x = self.root.winfo_pointerx()
            mouse_y = self.root.winfo_pointery()
        except Exception:
            mouse_x, mouse_y = 0, 0
        inside = (x_root <= mouse_x < x_root + width) and (y_root <= mouse_y < y_root + height)
        if not inside:
            self._hide_temp_titlebar()
            self.delete_resize_grips()

    def _show_temp_titlebar(self, event=None):
        """Show a temporary titlebar."""
        if not hasattr(self, "title_bar_frame"):
            self.create_custom_title_bar()
            self.title_bar_frame.bind("<Enter>", self._on_titlebar_enter)
            self.title_bar_frame.bind("<Leave>", self._on_titlebar_leave)

    def _hide_temp_titlebar(self, event=None):
        """Hide the temporary titlebar."""
        if self.window_config.get("show_custom_titlebar", False):
            return
        if hasattr(self, "title_bar_frame"):
            self.title_bar_frame.destroy()
            del self.title_bar_frame
            if hasattr(self, "title_bar"):
                del self.title_bar
            if hasattr(self, "close_button"):
                del self.close_button

    def create_custom_title_bar(self):
        """Create a custom title bar with a close button."""
        if hasattr(self, "title_bar_frame") or (self.fullscreen and self.window_config.get("show_custom_titlebar", False)):
            return

        title_bar_config = self.window_manager_config.get("custom_title_bar", {})
        title_label_config = title_bar_config.get("title_label", {})
        close_button_config = title_bar_config.get("close_button", {})

        self.title_bar_frame = tk.Frame(
            self.root,
            bg=title_bar_config.get("bg", "#333333"),
            relief=title_bar_config.get("relief", "raised"),
            bd=title_bar_config.get("bd", 0)
        )
        self.title_bar_frame.pack(fill=tk.X)

        self.title_bar = tk.Label(
            self.title_bar_frame,
            text=self.root.title(),
            bg=title_label_config.get("bg", "#333333"),
            fg=title_label_config.get("fg", "white"),
            anchor=title_label_config.get("anchor", "w"),
            padx=title_label_config.get("padx", 10)
        )
        self.title_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.close_button = tk.Button(
            self.title_bar_frame,
            text=close_button_config.get("text", "✕"),
            bg=close_button_config.get("bg", "#333333"),
            fg=close_button_config.get("fg", "white"),
            bd=close_button_config.get("bd", 0),
            command=self.root.quit,
            padx=close_button_config.get("padx", 10),
            pady=close_button_config.get("pady", 2)
        )
        self.close_button.pack(side=tk.RIGHT)

        self.title_bar_frame.bind("<ButtonPress-1>", self.on_drag_start)
        self.title_bar_frame.bind("<ButtonRelease-1>", self.on_drag_stop)
        self.title_bar_frame.bind("<B1-Motion>", self.on_drag_motion)

    def on_drag_start(self, event):
        """Store the starting position of the drag."""
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_drag_stop(self, event):
        """Reset the drag data."""
        self._drag_data["x"] = 0
        self._drag_data["y"] = 0

    def on_drag_motion(self, event):
        """Move the window during drag."""
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]
        x = self.root.winfo_x() + delta_x
        y = self.root.winfo_y() + delta_y
        self.root.geometry(f"+{x}+{y}")
