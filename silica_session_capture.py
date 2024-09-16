import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import ImageGrab, Image, ImageDraw, ImageFont
import pyautogui
from threading import Thread
import pytesseract
from pynput.keyboard import Controller
import subprocess
import cv2
import numpy as np
import logging
import re

# Setup the logger
logging.basicConfig(
    level=logging.DEBUG,  # Set the default log level to DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("screenshot_tool.log"),
        logging.StreamHandler()
    ]
)

keyboard = Controller()

class ScreenshotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Silica Map Screenshot Tool")
        self.root.geometry("400x550")
        self.root.resizable(False, False)  # Disable window resizing

        # Apply a style theme
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('TLabel', font=('Arial', 10))
        self.style.configure('TButton', font=('Arial', 10))
        self.style.configure('TEntry', font=('Arial', 10))
        self.style.configure('Header.TLabel', font=('Arial', 12, 'bold'))

        self.screenshot_interval_var = tk.StringVar(value="10")  # Variable for real-time interval adjustment
        self.screenshot_count = 0
        self.is_running = False
        self.start_time = None
        self.session_folder = ""

        # Set default parent folder to user's Pictures directory / "Silica Sessions"
        pictures_folder = os.path.join(os.path.expanduser("~"), "Pictures")
        silica_sessions_folder = os.path.join(pictures_folder, "Silica Sessions")

        if os.path.exists(pictures_folder):
            try:
                # Attempt to create the "Silica Sessions" subfolder
                os.makedirs(silica_sessions_folder, exist_ok=True)
                self.parent_folder = silica_sessions_folder
                logging.info(f"Using sessions folder: {self.parent_folder}")
            except Exception as e:
                logging.error(f"Error creating Silica Sessions folder: {e}")
                logging.info("Falling back to Pictures folder.")
                self.parent_folder = pictures_folder
        else:
            # Pictures folder does not exist
            logging.warning("Pictures folder does not exist.")
            # Prompt user to select a sessions folder
            messagebox.showwarning("Folder Not Found", "Pictures folder not found. Please select a sessions folder.")
            new_folder = filedialog.askdirectory(initialdir=os.path.expanduser("~"), title="Select Sessions Folder")
            if new_folder:
                self.parent_folder = new_folder
                logging.info(f"User selected sessions folder: {self.parent_folder}")
            else:
                # User canceled the dialog
                logging.warning("User did not select a sessions folder. Using home directory.")
                self.parent_folder = os.path.expanduser("~")

        # Get current screen resolution
        self.screen_width, self.screen_height = pyautogui.size()

        # Scaling factors based on 1920x1080 resolution
        self.x_scale = self.screen_width / 1920
        self.y_scale = self.screen_height / 1080

        # Adjustable initial delay before starting the session
        self.initial_delay = 5  # seconds

        # Adjustable frame duration for the GIF
        self.gif_frame_duration = 0.5  # seconds per frame

        # GUI Elements
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Sessions Folder
        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill=tk.X, pady=5)
        self.parent_folder_label = ttk.Label(folder_frame, text=f"Sessions Folder:", style='Header.TLabel')
        self.parent_folder_label.pack(side=tk.LEFT)
        self.folder_path_label = ttk.Label(folder_frame, text=self.parent_folder, wraplength=300)
        self.folder_path_label.pack(side=tk.LEFT, padx=5)
        self.change_folder_button = ttk.Button(main_frame, text="Change Sessions Folder", command=self.change_parent_folder)
        self.change_folder_button.pack(fill=tk.X, pady=5)

        # Interval Setting
        interval_frame = ttk.Frame(main_frame)
        interval_frame.pack(fill=tk.X, pady=5)
        interval_label = ttk.Label(interval_frame, text="Screenshot Interval (seconds):")
        interval_label.pack(side=tk.LEFT)
        self.interval_entry = ttk.Entry(interval_frame, textvariable=self.screenshot_interval_var, width=10)
        self.interval_entry.pack(side=tk.LEFT, padx=5)

        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        self.start_button = ttk.Button(button_frame, text="Start Session", command=self.start_session)
        self.start_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.stop_button = ttk.Button(button_frame, text="Stop Session", command=self.stop_session, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Generate GIF Button
        self.generate_gif_button = ttk.Button(main_frame, text="Generate GIF", command=self.generate_gif)
        self.generate_gif_button.pack(fill=tk.X, pady=5)

        # Open Folder Button
        self.open_folder_button = ttk.Button(main_frame, text="Open Last Screenshot Folder", command=self.open_last_screenshot_folder)
        self.open_folder_button.pack(fill=tk.X, pady=5)

        # Status Labels
        self.count_label = ttk.Label(main_frame, text="Screenshots Taken: 0")
        self.count_label.pack(pady=5)

        self.elapsed_time_label = ttk.Label(main_frame, text="Elapsed Time: 0s")
        self.elapsed_time_label.pack(pady=5)

    def change_parent_folder(self):
        new_folder = filedialog.askdirectory(initialdir=self.parent_folder, title="Select Sessions Folder")
        if new_folder:
            self.parent_folder = new_folder
            self.folder_path_label.config(text=self.parent_folder)
            logging.info(f"Changed sessions folder to: {self.parent_folder}")
        else:
            logging.info("User canceled folder selection.")

    def start_session(self):
        try:
            self.screenshot_interval = int(self.screenshot_interval_var.get())
        except ValueError:
            logging.error("Invalid interval input by user.")
            messagebox.showerror("Invalid Input", "Please enter a valid number for the interval.")
            return
        
        self.screenshot_count = 0
        self.start_time = time.time()
        self.session_folder = os.path.join(self.parent_folder, time.strftime("%Y%m%d_%H%M%S"))
        os.makedirs(self.session_folder, exist_ok=True)
        logging.info(f"Session folder created: {self.session_folder}")
        # Create the debug folder
        self.debug_folder = os.path.join(self.session_folder, "debug")
        os.makedirs(self.debug_folder, exist_ok=True)
        
        self.is_running = True
        self.update_ui()
        self.screenshot_thread = Thread(target=self.take_screenshots)
        self.screenshot_thread.start()
        logging.info("Screenshot session started.")


    def preprocess_image(self, image):
        logging.debug("Preprocessing image for text extraction.")
        # Convert the screenshot to grayscale
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
        
        # Resize the image to enlarge the text
        scale_percent = 300  # Enlarge the image by 300%
        width = int(gray.shape[1] * scale_percent / 100)
        height = int(gray.shape[0] * scale_percent / 100)
        dim = (width, height)
        resized = cv2.resize(gray, dim, interpolation=cv2.INTER_CUBIC)
        
        # Apply Gaussian Blur to reduce noise
        blurred = cv2.GaussianBlur(resized, (5, 5), 0)
        
        # Apply a binary threshold to make the text stand out more
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Apply dilation to make text thicker
        kernel = np.ones((2, 2), np.uint8)
        dilated = cv2.dilate(binary, kernel, iterations=1)
        
        # Convert back to PIL Image
        processed_image = Image.fromarray(dilated)
        return processed_image

    def extract_time(self, image):
        """Attempt to extract time from the preprocessed image."""
        logging.debug("Attempting to extract time from the image.")
        try:
            elapsed_time_text = pytesseract.image_to_string(image, config='--psm 7').strip()
            logging.debug(f"Raw extracted time text: {elapsed_time_text}")
            
            if "CURRENT MATCH" in elapsed_time_text:
                # Extract the last part which should contain the time in MM:SS format
                time_parts = elapsed_time_text.split()[-1]
                
                # Validate the time format using regular expression: MM:SS where MM can be > 60 but SS <= 60
                if re.match(r"^\d{2,3}:\d{2}$", time_parts):
                    minutes, seconds = map(int, time_parts.split(":"))
                    if seconds < 60:  # Ensure the seconds are valid
                        logging.info(f"Successfully extracted time: {time_parts}")
                        return time_parts.replace(":", "_")  # Convert MM:SS to MM_SS for filename
                    else:
                        logging.warning(f"Invalid time format with seconds > 60: {time_parts}")
            else:
                logging.warning("Failed to find 'CURRENT MATCH' in extracted text.")
        except Exception as e:
            logging.error(f"Exception occurred during time extraction: {e}")
        return None

    def extract_chat_status(self, image):
        """Check if 'Team' or 'All' is present in the chat region."""
        logging.debug("Checking chat status from the image.")
        try:
            # Extract text from the image using Tesseract OCR
            chat_text = pytesseract.image_to_string(image, config='--psm 7').strip().lower()
            logging.debug(f"Extracted chat text: {chat_text}")

            # Check if 'team' or 'all' is in the chat text (case-insensitive)
            if "team" in chat_text or "all" in chat_text:
                logging.info(f"Detected chat activity: {chat_text}")
                return True
            else:
                logging.debug("No relevant chat activity detected ('team' or 'all').")
        except Exception as e:
            logging.error(f"Exception occurred during chat extraction: {e}")

        # Return False if neither 'team' nor 'all' is found, or an error occurs
        return False

    def take_screenshots(self):
        logging.info(f"Waiting {self.initial_delay} seconds before starting the session.")
        time.sleep(self.initial_delay)

        while self.is_running:
            try:
                self.screenshot_interval = int(self.screenshot_interval_var.get())
            except ValueError:
                logging.error("Invalid screenshot interval, using default 10 seconds.")
                self.screenshot_interval = 10  # Default to 10 seconds if the input is invalid
            
            # Take an initial screenshot without toggling the map
            initial_screenshot = pyautogui.screenshot()

            # Define the chat region
            chat_area = (
                int(20 * self.x_scale),  # Controls the x-coordinate of the left edge.
                int(700 * self.y_scale),  # Controls the y-coordinate of the top edge.
                int(75 * self.x_scale),  # Controls the x-coordinate of the right edge.
                int(725 * self.y_scale)   # Controls the y-coordinate of the bottom edge.
            )

            chat_screenshot = initial_screenshot.crop(chat_area)
            processed_chat_image = self.preprocess_image(chat_screenshot)
            chat_active = self.extract_chat_status(processed_chat_image)

            # Save the chat region to debug folder
            chat_debug_filename = f"chat_region_{self.screenshot_count + 1}.png"
            chat_debug_path = os.path.join(self.debug_folder, chat_debug_filename)
            chat_screenshot.save(chat_debug_path)
            logging.info(f"Saved chat region to {chat_debug_path}")

            # If the player is chatting, skip the rest of the process
            if chat_active:
                logging.info("Player is typing in the chat. Skipping map toggle.")
                time.sleep(self.screenshot_interval)
                logging.info('========================================================')
                continue

            # Attempt to extract the time from the initial screenshot
            time_area = (
                int(300 * self.x_scale), int(50 * self.y_scale), 
                int((300 + 300) * self.x_scale), int((50 + 42) * self.y_scale)
            )
            time_screenshot = initial_screenshot.crop(time_area)
            processed_time_image = self.preprocess_image(time_screenshot)
            elapsed_time = self.extract_time(processed_time_image)

            # Save the time region to debug folder
            time_debug_filename = f"time_region_{self.screenshot_count + 1}.png"
            time_debug_path = os.path.join(self.debug_folder, time_debug_filename)
            time_screenshot.save(time_debug_path)
            logging.info(f"Saved time region to {time_debug_path}")

            map_toggled = False

            # Check if the time was detected
            if elapsed_time:
                logging.info(f"Detected time in initial screenshot: {elapsed_time}")
                map_screenshot = initial_screenshot
            else:
                logging.info("Map is not activated, toggling the map on.")
                
                # Toggle the map on by pressing 'M'
                keyboard.press('m')
                keyboard.release('m')
                map_toggled = True  # Track that we manually toggled the map
                
                # Wait a brief moment to ensure the map is fully displayed
                time.sleep(0.2)
                
                # Take another screenshot with the map activated
                map_screenshot = pyautogui.screenshot()
                
                # Extract the time from the new screenshot
                time_screenshot = map_screenshot.crop(time_area)
                processed_time_image = self.preprocess_image(time_screenshot)
                elapsed_time = self.extract_time(processed_time_image)
                
                if not elapsed_time:
                    logging.warning("Failed to extract time, using 'unknown_time'.")
                    elapsed_time = "unknown_time"

            # Extract the map from the screenshot
            map_area = (
                int(638 * self.x_scale), int(53 * self.y_scale), 
                int((638 + 974) * self.x_scale), int((53 + 974) * self.y_scale)
            )
            map_cropped = map_screenshot.crop(map_area)

            # Validate the cropped map image before saving
            if map_cropped.size[0] > 0 and map_cropped.size[1] > 0:
                screenshot_filename = f"map_{self.screenshot_count + 1}_{elapsed_time}.png"
                screenshot_path = os.path.join(self.session_folder, screenshot_filename)
                try:
                    map_cropped.save(screenshot_path)
                    logging.info(f"Saved screenshot: {screenshot_filename}")
                except Exception as e:
                    logging.error(f"Failed to save screenshot {screenshot_filename}: {e}")
            else:
                logging.warning(f"Map screenshot was invalid or empty, skipping save. Size: {map_cropped.size}")

            # Update screenshot count
            self.screenshot_count += 1
            self.count_label.config(text=f"Screenshots Taken: {self.screenshot_count}")
            
            # If we manually toggled the map, deactivate it by pressing 'M' again
            if map_toggled:
                logging.info("Deactivating the map.")
                keyboard.press('m')
                keyboard.release('m')

            # Wait for the specified interval before the next screenshot
            time.sleep(self.screenshot_interval)
            logging.info('========================================================')

    def stop_session(self):
        self.is_running = False
        logging.info("Screenshot session stopped.")
        self.update_ui()
        # GIF generation is now manual via the "Generate GIF" button

    def generate_gif(self):
        if not self.session_folder or not os.path.exists(self.session_folder):
            logging.warning("No session folder found to generate GIF.")
            messagebox.showwarning("No Session", "No session folder found to generate GIF.")
            return

        # After the session stops, merge images into a GIF
        try:
            # Collect image files, excluding those with 'unknown_time' in the filename
            image_files = [
                f for f in os.listdir(self.session_folder)
                if f.endswith('.png') and 'map_' in f and 'unknown_time' not in f
            ]

            if not image_files:
                logging.warning("No valid images found to create GIF.")
                messagebox.showwarning("No Images", "No valid images found to create GIF.")
                return

            # Define the sorting key function
            def get_sort_key(filename):
                match = re.match(r"map_(\d+)_(\d+)_(\d+)\.png", filename)
                if match:
                    # You can choose to sort by screenshot count or in-game time
                    # For sorting by in-game time:
                    minutes = int(match.group(2))
                    seconds = int(match.group(3))
                    total_seconds = minutes * 60 + seconds
                    return total_seconds
                else:
                    logging.warning(f"Filename does not match expected pattern: {filename}")
                    return float('inf')  # Push invalid filenames to the end

            # Sort the image files using the sorting key
            image_files.sort(key=get_sort_key)

            images = []

            for filename in image_files:
                filepath = os.path.join(self.session_folder, filename)

                # Extract the elapsed_time from the filename
                match = re.match(r"map_\d+_(\d+)_(\d+)\.png", filename)
                if match:
                    elapsed_time = f"{match.group(1)}:{match.group(2)}"  # MM:SS format
                else:
                    logging.warning(f"Filename does not match expected pattern: {filename}")
                    continue  # Skip files with unexpected names

                # Open the image
                image = Image.open(filepath).convert('RGBA')

                # Create a transparent overlay
                overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(overlay)

                # Choose a font
                try:
                    font = ImageFont.truetype("arial.ttf", 40)
                except IOError:
                    font = ImageFont.load_default()

                # Calculate position for the text (bottom left)
                bbox = font.getbbox(elapsed_time)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                text_position = (10, image.size[1] - text_height - 10)

                # Draw the text onto the overlay
                draw.text(text_position, elapsed_time, font=font, fill=(255, 0, 0, 128))

                # Composite the overlay onto the image
                combined = Image.alpha_composite(image, overlay)

                images.append(combined)

            if images:
                gif_filename = os.path.join(self.session_folder, 'session.gif')
                images[0].save(
                    gif_filename,
                    save_all=True,
                    append_images=images[1:],
                    format='GIF',
                    duration=int(self.gif_frame_duration * 1000),
                    loop=0
                )
                logging.info(f"Saved GIF animation: {gif_filename}")
                messagebox.showinfo("GIF Created", f"GIF saved as {gif_filename}")
            else:
                logging.warning("No valid images found to create GIF.")
                messagebox.showwarning("No Images", "No valid images found to create GIF.")
        except Exception as e:
            logging.error(f"Failed to create GIF: {e}")
            messagebox.showerror("Error", f"Failed to create GIF: {e}")

    def open_last_screenshot_folder(self):
        if os.path.exists(self.session_folder):
            # Use subprocess to open the folder in the file explorer
            logging.info(f"Opening folder: {self.session_folder}")
            subprocess.run(['explorer', os.path.normpath(self.session_folder)])
        else:
            logging.info("No screenshots have been taken yet.")
            messagebox.showinfo("No Session", "No screenshots have been taken yet.")

    def update_ui(self):
        if self.is_running:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.change_folder_button.config(state=tk.DISABLED)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.change_folder_button.config(state=tk.NORMAL)
        self.update_elapsed_time()

    def update_elapsed_time(self):
        if self.start_time:
            elapsed_time = int(time.time() - self.start_time)
            self.elapsed_time_label.config(text=f"Elapsed Time: {elapsed_time}s")
        if self.is_running:
            self.root.after(1000, self.update_elapsed_time)

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenshotApp(root)
    root.mainloop()
