# Modular ComfyUI Launcher

A unified, Git-based launcher for running ComfyUI on **Google Colab** and **Kaggle**.

## Features
-   **Config-Driven**: Switch projects (e.g., SDXL, Video, Z-Image) by changing a JSON file.
-   **Platform Agnostic**: Works on Colab, Kaggle, and Local.
-   **Fast**: Uses `aria2c` for rapid model downloads.
-   **Clean**: Keeps your config separate from the engine.

## Quick Start

## Quick Start (Colab)

1.  **Fork/Clone** this repo to your GitHub.
2.  **Upload** `launcher.ipynb` to Google Colab.
3.  **Edit the Cell**: Change `REPO_URL` to point to your new repository.
4.  **Run**: The notebook will clone your repo, set up the environment, and launch the App.

## Where to Put Files?
-   **Workflows**: Save your ComfyUI workflows (drag-and-drop JSONs) into the `workflows/` folder.
    -   *To Run*: Just drag them from your local folder into the ComfyUI browser window after it launches.
    -   *Automation*: If running headless, referencing `workflows/my_workflow_api.json` in the config.
-   **Prompts**:
    -   **Gradio (Z-Image)**: Enter directly in the UI.
    -   **Standard ComfyUI**: Inside your Workflow nodes (CLIP Text Encode).
-   **Outputs**:
    -   Found in the `ComfyUI/output` folder (in the Colab file browser).
    -   *Note*: Download them before closing the tab!
