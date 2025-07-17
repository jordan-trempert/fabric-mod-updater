import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import subprocess
import threading
import queue
import platform
import os
import json

# --- Constants ---
APP_NAME = "Fabric Mod Builder"
APP_WIDTH = 1200
APP_HEIGHT = 850
SUCCESS_COLOR = "#2ECC71"
ERROR_COLOR = "#E74C3C"
PENDING_COLOR = "#F1C40F"
PROCESSING_COLOR = "#3498DB"
DEFAULT_TEXT_COLOR = "#DCE4EE" # Default text color for CTk themes

class ModBuilderApp(ctk.CTk):
    """
    A GUI application to automate the process of updating versions
    and building multiple Minecraft Fabric mods using a central gradlew file.
    It remembers paths and versions between sessions.
    """
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(800, 650)

        self.mod_entries = []
        self.build_queue = queue.Queue()
        self.is_processing = False
        self.gradlew_path = None
        self.config_file = os.path.join(os.path.expanduser("~"), "mod_builder_config.json")

        self._setup_ui()
        self.load_config()
        self.check_queue_for_updates()
        
        # --- Handle window closing ---
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_ui(self):
        """Initializes and places all the UI components."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Top Frame for Controls ---
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.top_frame.grid_columnconfigure(1, weight=1)

        # Row 0: gradlew selection
        self.select_gradlew_button = ctk.CTkButton(self.top_frame, text="Select gradlew File", command=self.select_gradlew_path)
        self.select_gradlew_button.grid(row=0, column=0, padx=10, pady=(10,5), sticky="w")
        self.gradlew_path_label = ctk.CTkLabel(self.top_frame, text="Path to gradlew file not set.", text_color=PENDING_COLOR, anchor="w")
        self.gradlew_path_label.grid(row=0, column=1, columnspan=3, padx=10, pady=(10,5), sticky="ew")

        # Row 1: Global Gradle Properties
        self.yarn_mappings_label = ctk.CTkLabel(self.top_frame, text="Yarn Mappings:")
        self.yarn_mappings_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.yarn_mappings_entry = ctk.CTkEntry(self.top_frame, placeholder_text="e.g., 1.20.1+build.10")
        self.yarn_mappings_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        self.fabric_version_label = ctk.CTkLabel(self.top_frame, text="Fabric Version:")
        self.fabric_version_label.grid(row=1, column=2, padx=10, pady=5, sticky="w")
        self.fabric_version_entry = ctk.CTkEntry(self.top_frame, placeholder_text="e.g., 0.14.22")
        self.fabric_version_entry.grid(row=1, column=3, padx=10, pady=5, sticky="ew")

        # Row 2: Mod controls
        self.add_dir_button = ctk.CTkButton(self.top_frame, text="Add Mod Directory", command=self.add_directory)
        self.add_dir_button.grid(row=2, column=0, padx=10, pady=(10,10), sticky="w")
        self.start_button = ctk.CTkButton(self.top_frame, text="Process All Mods", command=self.start_processing, state="disabled")
        self.start_button.grid(row=2, column=1, padx=10, pady=(10,10), sticky="w")

        # --- Main Content Frame ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # --- Scrollable Frame for Mod Entries ---
        self.scrollable_mods_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="Selected Mod Projects")
        self.scrollable_mods_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.scrollable_mods_frame.grid_columnconfigure(0, weight=1)

        # --- Console Output Textbox ---
        self.console_frame = ctk.CTkFrame(self.main_frame)
        self.console_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.console_frame.grid_columnconfigure(0, weight=1)

        self.console_label = ctk.CTkLabel(self.console_frame, text="Build Progress Output", font=ctk.CTkFont(weight="bold"))
        self.console_label.grid(row=0, column=0, padx=10, pady=(5,0), sticky="w")
        
        self.console_output = ctk.CTkTextbox(self.console_frame, height=250, state="disabled", wrap="word")
        self.console_output.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    def on_closing(self):
        """Saves config and closes the application."""
        self.save_config()
        self.destroy()

    def save_config(self):
        """Saves current paths and versions to a JSON file."""
        config_data = {
            "gradlew_path": self.gradlew_path,
            "yarn_mappings": self.yarn_mappings_entry.get(),
            "fabric_version": self.fabric_version_entry.get(),
            "mods": []
        }
        for mod in self.mod_entries:
            config_data["mods"].append({
                "path": mod["path"],
                "mc_version": mod["mc_version_entry"].get(),
                "mod_version": mod["mod_version_entry"].get()
            })
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def load_config(self):
        """Loads paths and versions from the JSON config file on startup."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                if config_data.get("gradlew_path"):
                    self.gradlew_path = config_data["gradlew_path"]
                    self.gradlew_path_label.configure(text=f"Using: {self.gradlew_path}", text_color=DEFAULT_TEXT_COLOR)

                self.yarn_mappings_entry.insert(0, config_data.get("yarn_mappings", ""))
                self.fabric_version_entry.insert(0, config_data.get("fabric_version", ""))

                for mod_info in config_data.get("mods", []):
                    if os.path.isdir(mod_info.get("path")):
                        self.add_directory(
                            directory_path=mod_info.get("path"),
                            mc_version=mod_info.get("mc_version", ""),
                            mod_version=mod_info.get("mod_version", "")
                        )
        except (json.JSONDecodeError, TypeError) as e:
            self.log_to_console(f"WARNING: Could not read config file. It might be corrupted. Error: {e}")
        except Exception as e:
            self.log_to_console(f"ERROR: An unexpected error occurred while loading config: {e}")
        
        self._update_start_button_state()

    def _update_start_button_state(self):
        """Enables or disables the start button based on current state."""
        if self.gradlew_path and self.mod_entries and not self.is_processing:
            self.start_button.configure(state="normal")
        else:
            self.start_button.configure(state="disabled")

    def select_gradlew_path(self):
        """Opens a dialog to select the gradlew executable."""
        filetypes = [("Gradle Wrapper", "gradlew*"), ("All files", "*.*")]
        if platform.system() == "Windows":
            filetypes = [("Gradle Wrapper Batch", "gradlew.bat"), ("All files", "*.*")]
        
        filepath = filedialog.askopenfilename(
            title="Select your central gradlew executable",
            filetypes=filetypes
        )
        if filepath:
            self.gradlew_path = filepath
            self.gradlew_path_label.configure(text=f"Using: {filepath}", text_color=DEFAULT_TEXT_COLOR)
            self._update_start_button_state()

    def add_directory(self, directory_path=None, mc_version="", mod_version=""):
        """Adds a directory to the list of mods. Can be called with a path or from a dialog."""
        if directory_path is None:
            directory_path = filedialog.askdirectory(title="Select a Fabric Mod Project Directory")
        
        if not directory_path:
            return

        for mod in self.mod_entries:
            if mod['path'] == directory_path:
                self.log_to_console(f"INFO: Directory '{directory_path}' is already in the list.")
                return

        mod_frame = ctk.CTkFrame(self.scrollable_mods_frame)
        mod_frame.grid(sticky="ew", pady=5)
        mod_frame.grid_columnconfigure(1, weight=1)

        status_label = ctk.CTkLabel(mod_frame, text="Pending", text_color=PENDING_COLOR, width=80)
        status_label.grid(row=0, column=0, padx=10, pady=5)
        path_label = ctk.CTkLabel(mod_frame, text=directory_path, anchor="w")
        path_label.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        mc_version_label = ctk.CTkLabel(mod_frame, text="MC Version:", width=90)
        mc_version_label.grid(row=0, column=2, padx=(10, 0), pady=5)
        mc_version_entry = ctk.CTkEntry(mod_frame, placeholder_text="e.g., 1.20.1", width=120)
        mc_version_entry.grid(row=0, column=3, padx=(0, 10), pady=5)
        mc_version_entry.insert(0, mc_version)
        mod_version_label = ctk.CTkLabel(mod_frame, text="Mod Version:", width=90)
        mod_version_label.grid(row=0, column=4, padx=(10, 0), pady=5)
        mod_version_entry = ctk.CTkEntry(mod_frame, placeholder_text="e.g., 1.0.0", width=120)
        mod_version_entry.grid(row=0, column=5, padx=(0, 10), pady=5)
        mod_version_entry.insert(0, mod_version)
        remove_button = ctk.CTkButton(mod_frame, text="Remove", width=50, fg_color=ERROR_COLOR, hover_color="#C0392B")
        remove_button.grid(row=0, column=6, padx=10, pady=5)

        mod_data = {
            "path": directory_path, "frame": mod_frame, "status_label": status_label,
            "mc_version_entry": mc_version_entry, "mod_version_entry": mod_version_entry,
        }
        remove_button.configure(command=lambda m=mod_data: self.remove_mod(m))
        self.mod_entries.append(mod_data)
        self._update_start_button_state()

    def remove_mod(self, mod_to_remove):
        """Removes a mod entry from the UI and the internal list."""
        mod_to_remove['frame'].destroy()
        self.mod_entries.remove(mod_to_remove)
        self._update_start_button_state()

    def log_to_console(self, message):
        """Safely appends a message to the console textbox."""
        self.console_output.configure(state="normal")
        self.console_output.insert(tk.END, message + "\n")
        self.console_output.configure(state="disabled")
        self.console_output.see(tk.END)

    def check_queue_for_updates(self):
        """Periodically checks the queue for messages from worker threads."""
        try:
            while True:
                message = self.build_queue.get_nowait()
                self.log_to_console(message)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.check_queue_for_updates)

    def start_processing(self):
        """Starts the main processing thread."""
        if self.is_processing:
            messagebox.showwarning("In Progress", "A build process is already running.")
            return
            
        if not self.gradlew_path:
            messagebox.showerror("Missing Gradle Path", "Please select the path to your 'gradlew' or 'gradlew.bat' file first.")
            return

        for mod in self.mod_entries:
            if not mod['mc_version_entry'].get() or not mod['mod_version_entry'].get():
                messagebox.showerror("Missing Information", f"Please provide both Minecraft and Mod versions for all projects.\n\nProblem with: {mod['path']}")
                return

        self.is_processing = True
        self._update_start_button_state()
        self.add_dir_button.configure(state="disabled")
        self.select_gradlew_button.configure(state="disabled")
        
        processing_thread = threading.Thread(target=self.process_all_mods_thread, daemon=True)
        processing_thread.start()

    def process_all_mods_thread(self):
        """Worker thread that iterates through each mod and processes it."""
        for mod_data in self.mod_entries:
            self.process_single_mod(mod_data)

        self.is_processing = False
        self.add_dir_button.configure(state="normal")
        self.select_gradlew_button.configure(state="normal")
        self._update_start_button_state()
        self.build_queue.put("\n===== ALL BUILDS COMPLETE =====")

    def process_single_mod(self, mod_data):
        """Handles the logic for updating and building a single mod."""
        path = mod_data['path']
        mc_version = mod_data['mc_version_entry'].get()
        mod_version = mod_data['mod_version_entry'].get()
        status_label = mod_data['status_label']
        
        # Get global values
        yarn_mappings = self.yarn_mappings_entry.get()
        fabric_version = self.fabric_version_entry.get()

        self.build_queue.put(f"\n--- Processing: {os.path.basename(path)} ---")
        status_label.configure(text="Processing...", text_color=PROCESSING_COLOR)

        if not self.update_gradle_properties(path, mc_version, mod_version, yarn_mappings, fabric_version):
            status_label.configure(text="Failed", text_color=ERROR_COLOR)
            return

        self.build_queue.put(f"Starting Gradle build for {os.path.basename(path)}...")
        status_label.configure(text="Building...", text_color=PROCESSING_COLOR)
        
        command = [self.gradlew_path, 'build', '--no-daemon']
        
        try:
            process = subprocess.Popen(
                command, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace', bufsize=1
            )
            for line in iter(process.stdout.readline, ''):
                self.build_queue.put(line.strip())
            
            process.stdout.close()
            return_code = process.wait()

            if return_code == 0:
                self.build_queue.put(f"SUCCESS: Build for {os.path.basename(path)} completed successfully.")
                status_label.configure(text="Success", text_color=SUCCESS_COLOR)
            else:
                self.build_queue.put(f"ERROR: Build for {os.path.basename(path)} failed with exit code {return_code}.")
                status_label.configure(text="Failed", text_color=ERROR_COLOR)
        except FileNotFoundError:
            self.build_queue.put(f"ERROR: '{self.gradlew_path}' not found. Please verify the path is correct.")
            status_label.configure(text="Failed", text_color=ERROR_COLOR)
        except Exception as e:
            self.build_queue.put(f"ERROR: An unexpected error occurred during build: {e}")
            status_label.configure(text="Failed", text_color=ERROR_COLOR)

    def update_gradle_properties(self, path, mc_version, mod_version, yarn_mappings, fabric_version):
        """Finds and updates the version properties in the gradle.properties file."""
        properties_file = os.path.join(path, 'gradle.properties')
        if not os.path.exists(properties_file):
            self.build_queue.put(f"ERROR: gradle.properties not found in '{path}'")
            return False

        try:
            with open(properties_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            # Flags to check if properties were found and updated
            flags = {
                "mc_version": False, "mod_version": False,
                "yarn_mappings": False, "fabric_version": False
            }

            for line in lines:
                stripped_line = line.strip()
                if stripped_line.startswith('minecraft_version='):
                    new_lines.append(f'minecraft_version={mc_version}\n')
                    flags["mc_version"] = True
                elif stripped_line.startswith('mod_version='):
                    new_lines.append(f'mod_version={mod_version}\n')
                    flags["mod_version"] = True
                elif stripped_line.startswith('yarn_mappings='):
                    new_lines.append(f'yarn_mappings={yarn_mappings}\n')
                    flags["yarn_mappings"] = True
                elif stripped_line.startswith('fabric_version='):
                    new_lines.append(f'fabric_version={fabric_version}\n')
                    flags["fabric_version"] = True
                else:
                    new_lines.append(line)
            
            # Append any properties that were not found in the file
            if not flags["mc_version"]: new_lines.append(f'minecraft_version={mc_version}\n')
            if not flags["mod_version"]: new_lines.append(f'mod_version={mod_version}\n')
            if not flags["yarn_mappings"]: new_lines.append(f'yarn_mappings={yarn_mappings}\n')
            if not flags["fabric_version"]: new_lines.append(f'fabric_version={fabric_version}\n')
            
            with open(properties_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            self.build_queue.put(f"Updated gradle.properties for {os.path.basename(path)}.")
            return True
        except Exception as e:
            self.build_queue.put(f"ERROR: Failed to write to gradle.properties in '{path}': {e}")
            return False

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = ModBuilderApp()
    app.mainloop()
