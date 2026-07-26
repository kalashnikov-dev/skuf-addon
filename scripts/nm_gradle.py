#!/usr/bin/env python3
import os
import sys
import subprocess
import re
import glob

def get_java_major_version(java_path):
    try:
        res = subprocess.run([java_path, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        output = res.stderr or res.stdout
        match = re.search(r'version "(\d+)(?:\.(\d+))?', output)
        if match:
            major = int(match.group(1))
            if major == 1 and match.group(2):
                return int(match.group(2))
            return major
    except Exception:
        pass
    return 0

def find_jdk():
    # 1. Try default java on path
    if get_java_major_version("java") >= 17:
        return None  # Already OK
    
    # 2. Try JAVA_HOME
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        java_exe = os.path.join(java_home, "bin", "java.exe" if os.name == "nt" else "java")
        if os.path.exists(java_exe) and get_java_major_version(java_exe) >= 17:
            return java_home

    # 3. Scan common paths
    paths_to_check = []
    if os.name == "nt":
        # Get current drive letter of this script (e.g. "E:")
        drive = os.path.splitdrive(os.path.abspath(__file__))[0] or "C:"
        program_files_roots = [
            f"{drive}\\Program Files",
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        ]
        # De-duplicate
        program_files_roots = list(dict.fromkeys(program_files_roots))
        
        patterns = [
            "Microsoft/jdk-21*",
            "Eclipse Adoptium/jdk-21*",
            "Java/jdk-21*",
            "Microsoft/jdk-17*",
            "Eclipse Adoptium/jdk-17*",
            "Java/jdk-17*"
        ]
        
        for root in program_files_roots:
            if not root:
                continue
            for pattern in patterns:
                full_pattern = os.path.join(root, pattern)
                for path in glob.glob(full_pattern):
                    paths_to_check.append(path)
    else:
        # Linux/macOS
        patterns = [
            "/usr/lib/jvm/*21*",
            "/usr/lib/jvm/*17*",
            "/Library/Java/JavaVirtualMachines/*21*/Contents/Home",
            "/Library/Java/JavaVirtualMachines/*17*/Contents/Home"
        ]
        for pattern in patterns:
            for path in glob.glob(pattern):
                paths_to_check.append(path)

    for path in paths_to_check:
        java_exe = os.path.join(path, "bin", "java.exe" if os.name == "nt" else "java")
        if os.path.exists(java_exe) and get_java_major_version(java_exe) >= 17:
            return path
            
    return None

def main():
    jdk_path = find_jdk()
    env = os.environ.copy()
    if jdk_path:
        env["JAVA_HOME"] = jdk_path
        # Add bin directory to PATH
        bin_dir = os.path.join(jdk_path, "bin")
        env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
        print(f"[nm_gradle.py] Found JDK 17+ at: {jdk_path}", file=sys.stderr)
    else:
        print("[nm_gradle.py] Using system/default java version...", file=sys.stderr)
        
    # Find gradlew / gradlew.bat
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gradle_cmd = os.path.join(project_root, "gradlew.bat" if os.name == "nt" else "gradlew")
    
    if not os.path.exists(gradle_cmd):
        print(f"[nm_gradle.py] Error: Gradle wrapper not found at {gradle_cmd}", file=sys.stderr)
        sys.exit(1)
        
    args = [gradle_cmd] + sys.argv[1:]
    
    # Run the gradle command
    try:
        res = subprocess.run(args, env=env, check=False)
        sys.exit(res.returncode)
    except Exception as e:
        print(f"[nm_gradle.py] Failed to run Gradle: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
