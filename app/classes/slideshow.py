import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from PIL import Image, ImageTk
import os
import random

class SlideshowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Slideshow Application")

        self.csv_path = None
        self.image_paths = []

        # Create buttons and place them using grid
        self.load_csv_button = tk.Button(root, text="Load CSV", command=self.load_csv)
        self.load_csv_button.grid(row=0, column=0, columnspan=4, pady=10)

        self.scan_button = tk.Button(root, text="Scan and Save Images as CSV", command=self.scan_and_save)
        self.scan_button.grid(row=1, column=0, columnspan=4, pady=10)

        self.start_slideshow_button = tk.Button(root, text="Start Slideshows", command=self.start_slideshows)
        self.start_slideshow_button.grid(row=2, column=0, columnspan=4, pady=10)

    def load_csv(self):
        # Start the file dialog at the root folder or home directory
        initial_dir = os.path.expanduser("~")  # Use "~" for the home directory
        self.csv_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            filetypes=[("CSV Files", "*.csv")]
        )
        if self.csv_path:
            try:
                df = pd.read_csv(self.csv_path)
                self.image_paths = df['image_path'].tolist()
                messagebox.showinfo("Success", "CSV loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV: {e}")

    def scan_and_save(self):
        # Start the directory dialog at the root folder or home directory
        initial_dir = os.path.expanduser("~")  # Use "~" for the home directory
        folder_path = filedialog.askdirectory(initialdir=initial_dir)
        if folder_path:
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
            image_paths = []
            for root_dir, _, files in os.walk(folder_path):
                for file in files:
                    if os.path.splitext(file)[1].lower() in image_extensions:
                        image_paths.append(os.path.join(root_dir, file))

            if image_paths:
                save_path = filedialog.asksaveasfilename(
                    initialdir=initial_dir,
                    defaultextension=".csv",
                    filetypes=[("CSV Files", "*.csv")]
                )
                if save_path:
                    df = pd.DataFrame(image_paths, columns=['image_path'])
                    df.to_csv(save_path, index=False)
                    messagebox.showinfo("Success", "Images scanned and saved as CSV successfully!")
            else:
                messagebox.showwarning("Warning", "No images found in the selected folder.")

    def start_slideshows(self):
        if not self.image_paths:
            messagebox.showwarning("Warning", "No images loaded. Please load a CSV first.")
            return

        # Create a new window for the slideshows
        slideshow_window = tk.Toplevel(self.root)
        slideshow_window.title("Slideshows")

        # Set the default resolution to 3840x2160
        primary_screen_width = 3840
        primary_screen_height = 2160

        # Set the geometry of the slideshow window to match the default resolution
        slideshow_window.geometry(f"{primary_screen_width}x{primary_screen_height}+0+0")

        # Create a grid of canvases for the slideshows
        num_rows, num_cols = 2, 4
        canvas_width = primary_screen_width // num_cols
        canvas_height = primary_screen_height // num_rows

        self.canvases = []
        self.image_indices = []

        for row in range(num_rows):
            for col in range(num_cols):
                canvas = tk.Canvas(slideshow_window, width=canvas_width, height=canvas_height, bg="black", highlightthickness=0)
                canvas.grid(row=row, column=col, padx=0, pady=0, sticky="nsew")
                self.canvases.append(canvas)

                # Randomize the image sequence for each slideshow
                randomized_paths = self.image_paths.copy()
                random.shuffle(randomized_paths)
                self.image_indices.append([randomized_paths, 0])

        # Configure grid rows and columns to expand with the window
        for i in range(num_rows):
            slideshow_window.grid_rowconfigure(i, weight=1)
        for j in range(num_cols):
            slideshow_window.grid_columnconfigure(j, weight=1)

        # Start the synchronized slideshow
        self.show_images(slideshow_window)

    def show_images(self, slideshow_window):
        for canvas, (image_paths, current_index) in zip(self.canvases, self.image_indices):
            if image_paths:
                image_path = image_paths[current_index]
                try:
                    image = Image.open(image_path)

                    # Get the dimensions of the original image
                    original_width, original_height = image.size

                    # Calculate the new dimensions while maintaining the aspect ratio
                    canvas_width = canvas.winfo_width()
                    canvas_height = canvas.winfo_height()
                    aspect_ratio = min(canvas_width / original_width, canvas_height / original_height)
                    new_width = int(original_width * aspect_ratio)
                    new_height = int(original_height * aspect_ratio)

                    # Resize the image with the calculated dimensions
                    image = image.resize((new_width, new_height), Image.LANCZOS)

                    photo = ImageTk.PhotoImage(image)
                    canvas.create_image((canvas_width - new_width) // 2, (canvas_height - new_height) // 2, anchor=tk.NW, image=photo)
                    canvas.image = photo  # Keep a reference to avoid garbage collection

                    # Update the current index
                    #current_index = (current_index + 1) % len(image_paths)
                    #self.image_indices[self.canvases.index(canvas)][1] = current_index
                except Exception as e:
                    # Log the error and skip the problematic image
                    print(f"Failed to load image {image_path}: {e}")
                # Update the current index
                current_index = (current_index + 1) % len(image_paths)
                self.image_indices[self.canvases.index(canvas)][1] = current_index
        # Schedule the next update after 8 seconds
        slideshow_window.after(8000, lambda: self.show_images(slideshow_window))

if __name__ == "__main__":
    root = tk.Tk()
    app = SlideshowApp(root)
    root.mainloop()
