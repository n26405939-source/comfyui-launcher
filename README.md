# Modular ComfyUI Launcher

A unified, Git-based launcher for running ComfyUI on **Google Colab** and **Kaggle**.

## Features
-   **Config-Driven**: Switch projects (e.g., SDXL, Video, Z-Image) by changing a JSON file.
-   **Platform Agnostic**: Works on Colab, Kaggle, and Local.
-   **Fast**: Uses `aria2c` for rapid model downloads.
-   **Clean**: Keeps your config separate from the engine.

## Quick Start (Colab)

1.  **Fork/Clone** this repo to your GitHub.
2.  **Upload** `launcher.ipynb` to Google Colab.
3.  **Edit the Cell**: 
    - Change `REPO_URL` to point to your repository.
    - Change `CONFIG_PATH` to select your project:
        - `templates/z_image_project.json`: Fast Custom Gradio UI for Z-Image-Turbo.
        - `templates/comfyui_server.json`: Standard ComfyUI Server interface.
4.  **Run**: The notebook will clone your repo, set up the environment, and launch the selected mode.

## Project Modes
- **Script Mode**: Launches a custom Python script (like `app.py`) for a streamlined UI.
- **Server Mode**: Launches the full ComfyUI backend with standard UI access.
-   **Workflows**: Save your ComfyUI workflows (drag-and-drop JSONs) into the `workflows/` folder.
    -   *To Run*: Just drag them from your local folder into the ComfyUI browser window after it launches.
    -   *Automation*: If running headless, referencing `workflows/my_workflow_api.json` in the config.
-   **Prompts**:
    -   **Gradio (Z-Image)**: Enter directly in the UI.
    -   **Standard ComfyUI**: Inside your Workflow nodes (CLIP Text Encode).
-   **Outputs**:
    -   Found in the `ComfyUI/output` folder (in the Colab file browser).
    -   *Note*: Download them before closing the tab!
