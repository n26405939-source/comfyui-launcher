import os
import json
import subprocess
import sys
import shutil

class ComfyLauncher:
    def __init__(self, config_path, root_dir="ComfyUI"):
        self.config_path = config_path
        self.root_dir = os.path.abspath(root_dir)
        self.config = self._load_config()

    def _load_config(self):
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def run_command(self, command, cwd=None):
        print(f"Executing: {command}")
        subprocess.run(command, shell=True, check=True, cwd=cwd)

    def install_comfy(self):
        if not os.path.exists(self.root_dir):
            print("Cloning ComfyUI...")
            self.run_command(f"git clone https://github.com/comfyanonymous/ComfyUI {self.root_dir}")
        
        comfy_commit = self.config.get("execution", {}).get("comfy_commit")
        if comfy_commit:
            print(f"Resetting ComfyUI to commit {comfy_commit}...")
            self.run_command(f"git fetch --all -q", cwd=self.root_dir)
            self.run_command(f"git reset --hard {comfy_commit}", cwd=self.root_dir)

    def install_custom_nodes(self):
        custom_nodes_dir = os.path.join(self.root_dir, "custom_nodes")
        nodes = self.config.get("custom_nodes", [])
        
        for url in nodes:
            repo_name = url.split("/")[-1].replace(".git", "")
            repo_path = os.path.join(custom_nodes_dir, repo_name)
            if not os.path.exists(repo_path):
                print(f"Installing Custom Node: {repo_name}")
                self.run_command(f"git clone {url}", cwd=custom_nodes_dir)
            else:
                print(f"Custom Node {repo_name} already exists.")

    def download_models(self):
        # Install aria2 if needed (colab specific usually, but good to have check)
        # We assume apt install aria2 is done in notebook or here if permissible.
        # For simplicity, we just run the command assuming it's available or use wget fallback?
        # User's notebook uses aria2c, so we stick to that.
        self.run_command("apt -y install -qq aria2 || true") # Attempt install, ignore fail if not root/apt

        models = self.config.get("models", [])
        for model in models:
            url = model.get("url")
            filename = model.get("filename")
            dest_path = model.get("dest_path")
            method = model.get("method", "aria2c")
            
            # Allow relative paths relative to ComfyUI root
            if not dest_path.startswith("/"):
                dest_path = os.path.join(self.root_dir, dest_path)
            
            os.makedirs(dest_path, exist_ok=True)
            full_path = os.path.join(dest_path, filename)
            
            if os.path.exists(full_path):
                print(f"Model {filename} already exists at {full_path}")
                continue
            
            print(f"Downloading {filename}...")
            if method == "aria2c":
                cmd = f"aria2c --console-log-level=error -c -x 16 -s 16 -k 1M '{url}' -d '{dest_path}' -o '{filename}'"
                self.run_command(cmd)
            elif method == "symlink":
                # Assumes url is a local file path in this case, or source_path field
                source_path = model.get("source_path") # Custom field for symlinks
                if source_path and os.path.exists(source_path):
                    self.run_command(f"ln -s '{source_path}' '{full_path}'")
                else:
                    print(f"Error: Source path for symlink not found: {source_path}")

    def install_requirements(self):
        req_file = self.config.get("execution", {}).get("requirements", "requirements.txt")
        # Check if it's a file in the project config directory or ComfyUI root
        # If the user provided a separate requirements file path in the config dir
        pass 
        # For now, standard ComfyUI requirements
        self.run_command(f"pip install -r requirements.txt", cwd=self.root_dir)
        
        # If there are node-specific requirements, they usually auto-install or need manual handling
        # Comfy Manager handles this, but here we might need to handle it if specified.

    def launch(self):
        self.install_comfy()
        self.install_custom_nodes()
        self.download_models()
        self.install_requirements()
        
        execution = self.config.get("execution", {})
        mode = execution.get("mode", "server")
        
        if mode == "script":
            script_path = execution.get("script_path", "main.py")
            # If script path is relative, assume it's inside ComfyUI or we need to copy it there
            # User's example: wget app.py -> run python app.py inside ComfyUI
            
            # Check if we need to download the script first
            script_url = execution.get("script_url")
            script_name = script_path.split("/")[-1]
            
            if script_url:
                 self.run_command(f"wget {script_url} -O {script_name}", cwd=self.root_dir)
            elif os.path.exists(script_path):
                 # Build a self-contained repo: Copy script from Repo Root -> ComfyUI Folder
                 print(f"Copying local script {script_path} to {self.root_dir}...")
                 shutil.copy(script_path, os.path.join(self.root_dir, script_name))
            
            print(f"Launching script: {script_path}")
            self.run_command(f"python {script_name}", cwd=self.root_dir)
            
        else:
            print("Launching ComfyUI Server...")
            args = execution.get("args", "") # e.g. "--listen --enable-cors-header"
            self.run_command(f"python main.py {args}", cwd=self.root_dir)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python comfy_launcher.py <config_path>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    launcher = ComfyLauncher(config_path)
    launcher.launch()
