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
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in process.stdout:
            print(line, end="")
        
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)

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
        # Install aria2 if needed
        self.run_command("apt -y install -qq aria2 || true")

        models = self.config.get("models", [])
        for model in models:
            url = model.get("url")
            filename = model.get("filename")
            dest_path = model.get("dest_path")
            method = model.get("method", "aria2c")
            
            # Check if this is an external path (absolute path like /tmp)
            is_external = dest_path.startswith("/")
            
            # For relative paths, make them relative to ComfyUI root
            if not is_external:
                dest_path = os.path.join(self.root_dir, dest_path)
            
            os.makedirs(dest_path, exist_ok=True)
            full_path = os.path.join(dest_path, filename)
            
            if os.path.exists(full_path):
                print(f"Model {filename} already exists at {full_path}")
            else:
                print(f"Downloading {filename}...")
                if method == "aria2c":
                    cmd = f"aria2c --console-log-level=error -c -x 16 -s 16 -k 1M '{url}' -d '{dest_path}' -o '{filename}'"
                    self.run_command(cmd)
                elif method == "symlink":
                    source_path = model.get("source_path")
                    if source_path and os.path.exists(source_path):
                        self.run_command(f"ln -s '{source_path}' '{full_path}'")
                    else:
                        print(f"Error: Source path for symlink not found: {source_path}")
            
            # Create symlink inside ComfyUI for external paths
            if is_external and os.path.exists(full_path):
                # Determine the ComfyUI model subdirectory based on dest_path
                # e.g., /tmp/comfy_models/clip -> models/clip
                subdir = os.path.basename(dest_path)  # "clip", "vae", "diffusion_models"
                comfy_model_dir = os.path.join(self.root_dir, "models", subdir)
                os.makedirs(comfy_model_dir, exist_ok=True)
                
                symlink_path = os.path.join(comfy_model_dir, filename)
                if not os.path.exists(symlink_path):
                    print(f"Creating symlink: {symlink_path} -> {full_path}")
                    os.symlink(full_path, symlink_path)


    def install_requirements(self):
        req_file = self.config.get("execution", {}).get("requirements", "requirements.txt")
        # For now, standard ComfyUI requirements
        self.run_command(f"pip install -r requirements.txt", cwd=self.root_dir)
        
        # Ensure gradio is installed for script-based UI
        if self.config.get("execution", {}).get("mode") == "script":
            print("Ensuring gradio is installed...")
            self.run_command("pip install gradio")

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
            # Use -u for unbuffered output so logs appear immediately in Colab
            self.run_command(f"python -u {script_name}", cwd=self.root_dir)
            
        else:
            print("\n" + "="*60)
            print("  VERSION: V.2.2-FIXED | ComfyUI Server Mode")
            print("="*60 + "\n")
            
            args = execution.get("args", "") 
            
            # Extract port
            import re
            import time
            import threading
            
            port_match = re.search(r'--port\s+(\d+)', args)
            port = int(port_match.group(1)) if port_match else 8188

            # Step 1: Download Cloudflared binary first
            print("[1/3] Downloading Cloudflared...")
            os.system("wget -q -nc https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /tmp/cloudflared_bin")
            os.system("chmod +x /tmp/cloudflared_bin")
            
            # Step 2: Start ComfyUI Server in background
            print(f"[2/3] Starting ComfyUI server on port {port}...")
            server_cmd = f"python -u main.py {args}"
            server_proc = subprocess.Popen(
                server_cmd,
                shell=True,
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Wait for server to start (check for "Starting server" message)
            print("Waiting for server to initialize...")
            server_ready = False
            startup_lines = []
            for _ in range(120):  # Wait up to 60 seconds for server startup
                line = server_proc.stdout.readline()
                if line:
                    startup_lines.append(line)
                    print(line, end="")
                    if "Starting server" in line or "To see the GUI" in line:
                        server_ready = True
                        break
                time.sleep(0.5)
            
            if not server_ready:
                print("\nWarning: Server may not have started correctly. Continuing anyway...")
            
            # Step 3: Start Cloudflared Tunnel
            print("\n[3/3] Starting Cloudflared tunnel...")
            tunnel_proc = subprocess.Popen(
                ["/tmp/cloudflared_bin", "tunnel", "--url", f"http://127.0.0.1:{port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Capture the public URL from Cloudflared
            print("Waiting for public URL (this takes ~10-15 seconds)...")
            cf_url_found = False
            for _ in range(30):  # Wait up to 15 seconds
                line = tunnel_proc.stdout.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                
                if "trycloudflare.com" in line:
                    match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                    if match:
                        print("\n" + "="*60)
                        print(f"  PUBLIC URL: {match.group(0)}")
                        print("="*60 + "\n")
                        cf_url_found = True
                        break
                time.sleep(0.5)

            if not cf_url_found:
                print("\nWarning: Could not capture Cloudflared URL automatically.")
                print("The tunnel may still be starting. Look for 'trycloudflare.com' in the logs below.\n")

            # Colab Proxy Fallback (only on Colab, skip on Kaggle)
            is_colab = os.path.exists('/content')
            if is_colab:
                try:
                    from google.colab.output import eval_js
                    proxy_url = eval_js(f"google.colab.kernel.proxyPort({port})")
                    print(f"[Colab Fallback URL]: {proxy_url}\n")
                except Exception:
                    pass


            # Continue streaming server output
            print("\n--- ComfyUI Server Logs ---\n")
            try:
                for line in server_proc.stdout:
                    print(line, end="")
            except KeyboardInterrupt:
                print("\nShutting down...")
                server_proc.terminate()
                tunnel_proc.terminate()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python comfy_launcher.py <config_path>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    launcher = ComfyLauncher(config_path)
    launcher.launch()
