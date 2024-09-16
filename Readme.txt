README - Silica Map Screenshot Tool
====================================

1. Overview
------------
The Silica Map Screenshot Tool is a Python-based utility designed to capture periodic screenshots from the Silica game map. It can extract in-game details such as chat status and time, and generate a GIF from the collected screenshots. The GUI interface allows easy control of the session, and screenshots are saved in a specified sessions folder.

2. Installation Instructions
------------------------------
To prepare and run the Silica Map Screenshot Tool, follow the steps below:

Step 1: Clone or download the project
--------------------------------------
- If using git, you can clone the repository using:
    git clone <repository-link>

Step 2: Set up a virtual environment (optional but recommended)
---------------------------------------------------------------
- Open a terminal or command prompt.
- Navigate to the project directory.
- Create a virtual environment:
      python -m venv venv

- Activate the virtual environment:
      venv\Scripts\activate

Step 3: Install dependencies
-----------------------------
- Ensure your virtual environment is activated.
- Install the required Python libraries using the provided `requirements.txt` file:
    pip install -r requirements.txt

Step 4: Ensure Tesseract-OCR is installed
------------------------------------------
- The tool relies on Tesseract-OCR for text extraction. You need to install it separately:

        1. Download Tesseract from https://github.com/tesseract-ocr/tesseract and install it.
        2. You might need to manually add the installation path (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`) to the system's PATH.


Step 5: Run the application
-----------------------------
- With the environment set up, you can start the application by running the following command:
    python silica_session_capture.py

3. How to Use the Tool
----------------------
1. **Change Sessions Folder (optional)**:
    - By default, screenshots are saved to the "Silica Sessions" folder in your Pictures directory. You can change the folder by clicking the "Change Sessions Folder" button.

2. **Set Screenshot Interval**:
    - Enter the desired interval (in seconds) between screenshots in the "Screenshot Interval" field. The default is 10 seconds.

3. **Start a Session**:
    - Click "Start Session" to begin capturing screenshots. A new folder will be created for each session within the selected sessions folder.

4. **Stop a Session**:
    - Click "Stop Session" to end the screenshot capture.

5. **Generate a GIF**:
    - After a session ends, you can generate a GIF of the captured screenshots by clicking the "Generate GIF" button.

6. **Open the Last Screenshot Folder**:
    - Click the "Open Last Screenshot Folder" button to open the folder containing the latest screenshots.

4. Important Notices
---------------------
- **Distraction Warning**: The tool interacts with the keyboard (for toggling the in-game map) and takes screenshots during gameplay. This may briefly interfere with gameplay by causing minor distractions, especially during critical in-game moments.
- **Session Folder Management**: Ensure that the folder where screenshots are stored has enough space to accommodate multiple images and GIF files.

5. Troubleshooting
-------------------
- **Tesseract not found**: Ensure Tesseract-OCR is installed and added to your system's PATH.
- **Permission issues with folder**: Make sure the selected sessions folder is writable.

For any further issues, please check the logs (stored in the `screenshot_tool.log` file).

6. License
-----------
This tool is provided for personal use. Please modify and share with proper attribution if you find it useful.
