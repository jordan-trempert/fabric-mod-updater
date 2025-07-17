# **Fabric Mod Builder GUI**

A Python-based graphical user interface to simplify and automate the process of updating and building multiple Minecraft Fabric mods simultaneously.

This tool is perfect for developers managing several mods who need to update versions and build them for new Minecraft releases without manually editing each project's gradle.properties file and running builds one by one.

## **Features**

- **Graphical User Interface:** Easy-to-use interface built with customtkinter.
- **Batch Processing:** Add multiple Fabric mod projects and process them all with a single click.
- **Centralized gradlew:** Use a single gradlew executable for all your projects.
- **Individual Version Control:** Set minecraft_version and mod_version for each mod individually.
- **Global Version Control:** Set global properties like yarn_mappings and fabric_version that apply to all mods.
- **Real-time Console:** Monitor the gradlew build output for each mod in real-time to catch errors immediately.
- **Persistent Configuration:** The application automatically saves your gradlew path, mod list, and version settings, so you don't have to re-enter them every time.
- **Cross-Platform:** Works on Windows, macOS, and Linux.

## **Prerequisites**

Before you run the script, you need to have the following installed:

1. **Python 3:** Make sure Python 3.x is installed on your system. You can download it from [python.org](https://www.python.org/downloads/).
2. **customtkinter:** This is a Python library for creating modern GUIs. You can install it via pip:  
    pip install customtkinter  

## **How to Run the Script**

1. **Save the Code:** Save the script's code into a file named mod_builder_gui.py.
2. **Open a Terminal:** Open a command prompt (on Windows) or a terminal (on macOS/Linux).
3. **Navigate to the Directory:** Use the cd command to go to the folder where you saved mod_builder_gui.py.
4. **Run the Script:** Execute the following command:  
    python mod_builder_gui.py  

## **How to Use the Application**

1. **Select gradlew File:**
    - The first step is to tell the application where your Gradle Wrapper executable is.
    - Click the **"Select gradlew File"** button and navigate to your gradlew.bat (on Windows) or gradlew (on macOS/Linux) file. This can be a single file you use for all your projects.
2. **Set Global Properties (Optional):**
    - In the **"Yarn Mappings"** field, enter the mapping version you want to build against (e.g., 1.20.1+build.10).
    - In the **"Fabric Version"** field, enter the Fabric API version you need (e.g., 0.14.22).
    - These values will be applied to every mod you process.
3. **Add Mod Directories:**
    - Click the **"Add Mod Directory"** button.
    - In the dialog, select the root folder of a Fabric mod project (the folder that contains the src directory and a gradle.properties file).
    - The project will appear in the list.
4. **Set Mod-Specific Versions:**
    - For each mod in the list, enter the specific **"MC Version"** (e.g., 1.20.1) and **"Mod Version"** (e.g., 2.1.0) you want to set for that build.
5. **Process and Build:**
    - Once you have everything configured, click the **"Process All Mods"** button.
    - The application will lock the controls and begin processing each mod sequentially.
    - You can watch the status change from "Pending" to "Processing...", "Building...", and finally to "Success" or "Failed".
    - The **"Build Progress Output"** console at the bottom will show the live output from Gradle, which is essential for debugging.

## **Configuration File**

The application automatically creates a configuration file at C:\\Users\\YourUser\\mod_builder_config.json (path will vary based on your OS).

This file stores:

- The path to your gradlew file.
- The global yarn_mappings and fabric_version.
- The list of all your added mod projects and their specific versions.

The application loads this file on startup and saves it when you close the window, so your setup is always remembered.

## **Troubleshooting**

### **Build Fails with "cannot find symbol" Error**

If the console shows a Java compilation error like cannot find symbol for a Minecraft or Fabric class, it means there is a version mismatch.

**Example:**

error: cannot find symbol  
import net.minecraft.particle.EntityEffectParticleEffect;  

**Cause:** The class EntityEffectParticleEffect was renamed in a newer version of Minecraft. This error indicates that your mod's Java code was written for an older version, but you are trying to build it with newer yarn_mappings.

**Solution:**

1. **Update Code (Recommended):** Update your Java source code to use the new class names and APIs for the Minecraft version you are targeting.
2. **Use Older Versions:** Change the minecraft_version, yarn_mappings, and fabric_version in the GUI to match the older versions that your code is compatible with.
