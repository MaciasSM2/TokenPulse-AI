import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Known root directories to avoid classifying as a project
SYSTEM_ROOTS = {
    "users", "documents", "0. programacion", "programacion", 
    "nueva carpeta", "desktop", "downloads", "appdata", "local",
    "roaming", "c:", "d:", "e:", "workspace", "projects"
}

# Project indicator files and their associated tech stacks
INDICATORS = {
    ".git": ("Git Repository", 10),
    ".tokenpulse": ("TokenPulse Config", 10),
    "package.json": ("Node.js / Web", 8),
    "pyproject.toml": ("Python (Poetry/Flit/UV)", 8),
    "requirements.txt": ("Python", 7),
    "setup.py": ("Python Package", 7),
    "Cargo.toml": ("Rust", 8),
    "go.mod": ("Go", 8),
    "pom.xml": ("Java (Maven)", 8),
    "build.gradle": ("Java / Kotlin (Gradle)", 8),
    "CMakeLists.txt": ("C / C++ (CMake)", 7),
    "Makefile": ("C / Make Build", 6),
    "composer.json": ("PHP (Composer)", 7),
    "Gemfile": ("Ruby (Bundler)", 7),
    "tsconfig.json": ("TypeScript", 7),
    "game/options.rpy": ("Ren'Py Visual Novel", 9),
    "game/script.rpy": ("Ren'Py Visual Novel", 9),
}

def clean_candidate_name(folder_name: str) -> str:
    """Cleans up raw folder name removing common trailing extensions if it's a file."""
    name = re.sub(r'\.(md|py|js|ts|json|txt|db|rpy)$', '', folder_name, flags=re.IGNORECASE)
    return name.strip()

def resolve_canonical_project(path_str: Optional[str]) -> Tuple[Optional[str], Optional[str], str]:
    """
    Given any arbitrary path (file, deep subfolder, or directory),
    traverses up to find the true project root folder.
    
    Returns:
        (canonical_name, canonical_path_str, detection_reason)
    """
    if not path_str or len(path_str.strip()) == 0:
        return "General", None, "no_path"

    # Normalize path
    clean_p = path_str.strip('\"\'')
    try:
        p = Path(clean_p).resolve()
    except Exception:
        return "General", None, "invalid_path"

    # If it's a file, take its directory
    if p.is_file() or re.search(r'\.[a-zA-Z0-9]+$', p.name):
        p = p.parent

    # Check if inside an Antigravity brain / conversation folder or scratch
    p_str_norm = str(p).replace('\\', '/').lower()
    if "antigravity-ide/brain" in p_str_norm:
        return "General (Antigravity)", str(p), "antigravity_brain"
    if "antigravity-ide/scratch" in p_str_norm:
        return "General (Scratch)", str(p), "antigravity_scratch"

    # Traverse upwards looking for highest quality project root (.git takes highest priority)
    git_root = None
    package_root = None
    
    curr = p
    max_depth = 8
    depth = 0
    
    while curr and depth < max_depth:
        c_name = curr.name.lower()
        # If we reached system root or empty, break
        if not c_name or c_name in SYSTEM_ROOTS or len(curr.parts) <= 1:
            break
        
        # Check git first (definitive project root)
        if (curr / ".git").is_dir():
            git_root = curr
            break  # Found git root, don't traverse higher than git root
            
        # Check tokenpulse
        if (curr / ".tokenpulse").exists():
            git_root = curr
            break

        # Check Ren'Py
        if (curr / "game" / "options.rpy").exists() or (curr / "game" / "script.rpy").exists():
            package_root = curr

        # Check language descriptors
        for ind in ["package.json", "pyproject.toml", "Cargo.toml", "go.mod"]:
            if (curr / ind).is_file() and not package_root:
                package_root = curr
                break

        curr = curr.parent
        depth += 1

    canonical_dir = git_root or package_root or p
    
    # Check if canonical_dir name is a system root, if so, fallback to p or General
    if canonical_dir.name.lower() in SYSTEM_ROOTS:
        return "General", str(p), "system_root_fallback"

    reason = "git_root" if git_root else ("package_root" if package_root else "folder_fallback")
    return canonical_dir.name, str(canonical_dir), reason

def verify_project_folder(folder_path_str: str) -> Dict[str, Any]:
    """
    Examines a target directory to determine if it is a legitimate programming project.
    Returns validity, tech stack, detected indicators, and canonical root.
    """
    if not folder_path_str or not folder_path_str.strip():
        return {
            "is_valid": False,
            "confidence": "invalid",
            "name": "",
            "root_path": "",
            "tech_stack": "",
            "indicators": [],
            "reasons": ["Ruta vacía o no especificada"]
        }

    p = Path(folder_path_str.strip('\"\''))
    if not p.exists():
        return {
            "is_valid": False,
            "confidence": "invalid",
            "name": p.name,
            "root_path": str(p),
            "tech_stack": "",
            "indicators": [],
            "reasons": ["La carpeta no existe en el sistema"]
        }

    if p.is_file():
        # User picked a file instead of a folder
        parent_p = p.parent
        canonical_name, canonical_path, reason = resolve_canonical_project(str(parent_p))
        return {
            "is_valid": True,
            "is_file": True,
            "confidence": "medium",
            "name": canonical_name or parent_p.name,
            "root_path": canonical_path or str(parent_p),
            "tech_stack": "Archivo individual en proyecto",
            "indicators": [p.name],
            "reasons": [f"Se seleccionó un archivo ({p.name}); la raíz del proyecto es {canonical_name}"]
        }

    # Detect indicators
    detected_indicators = []
    stacks = []
    score = 0

    for filename, (stack_desc, weight) in INDICATORS.items():
        check_path = p / filename
        if check_path.exists():
            detected_indicators.append(filename)
            stacks.append(stack_desc)
            score += weight

    # Check for presence of code files
    code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".rpy", ".rs", ".go", ".java", ".cpp", ".c"}
    found_code_files = 0
    try:
        for entry in os.scandir(str(p)):
            if entry.is_file() and Path(entry.name).suffix.lower() in code_extensions:
                found_code_files += 1
                if found_code_files >= 3:
                    break
    except Exception:
        pass

    if found_code_files > 0:
        score += 5
        stacks.append(f"{found_code_files}+ archivos de código")

    # Determine confidence
    canonical_name, canonical_path, root_reason = resolve_canonical_project(str(p))
    
    is_valid = score >= 5 or ".git" in detected_indicators or found_code_files > 0
    confidence = "high" if score >= 10 else ("medium" if is_valid else "low")
    
    unique_stacks = list(dict.fromkeys(stacks))
    tech_stack_str = " • ".join(unique_stacks) if unique_stacks else "Carpeta de archivos"

    reasons = []
    if ".git" in detected_indicators:
        reasons.append("Repositorio Git activo detectado (.git)")
    if ".tokenpulse" in detected_indicators:
        reasons.append("Configuración previa de TokenPulse vinculada (.tokenpulse)")
    if any(k in detected_indicators for k in ["package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "game/options.rpy"]):
        reasons.append(f"Archivos de configuración encontrados: {', '.join(detected_indicators)}")
    if found_code_files > 0:
        reasons.append(f"Contiene código fuente ({found_code_files}+ archivos)")
    if not is_valid:
        reasons.append("No se detectaron repositorios Git, archivos de configuración ni código fuente")

    return {
        "is_valid": is_valid,
        "confidence": confidence,
        "score": score,
        "name": canonical_name or p.name,
        "original_name": p.name,
        "root_path": canonical_path or str(p),
        "is_subfolder": (str(canonical_path).lower() != str(p).lower()) if canonical_path else False,
        "tech_stack": tech_stack_str,
        "indicators": detected_indicators,
        "reasons": reasons
    }

def scan_directory_candidates(browse_path_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Browses a directory and returns its subfolders with real-time project verification,
    allowing developers to visually pick projects and see their validity.
    """
    if not browse_path_str or not browse_path_str.strip():
        # Default starting point: User Documents/0. Programacion or user home
        user_home = Path.home()
        prog_path = user_home / "Documents" / "0. Programacion"
        if prog_path.exists():
            target_path = prog_path
        else:
            target_path = user_home / "Documents"
    else:
        target_path = Path(browse_path_str.strip('\"\''))

    if not target_path.exists():
        target_path = Path.home()

    current_path_str = str(target_path.resolve())
    parent_path_str = str(target_path.parent.resolve()) if target_path.parent != target_path else None

    subfolders = []
    try:
        with os.scandir(current_path_str) as entries:
            for entry in entries:
                if entry.is_dir() and not entry.name.startswith('.'):
                    sub_p = Path(entry.path)
                    v = verify_project_folder(str(sub_p))
                    subfolders.append({
                        "name": entry.name,
                        "path": str(sub_p),
                        "is_valid_project": v["is_valid"],
                        "confidence": v["confidence"],
                        "tech_stack": v["tech_stack"],
                        "indicators": v["indicators"]
                    })
    except PermissionError:
        pass
    except Exception:
        pass

    # Sort: Valid projects first, then alphabetically
    subfolders.sort(key=lambda x: (not x["is_valid_project"], x["name"].lower()))

    return {
        "current_path": current_path_str,
        "parent_path": parent_path_str,
        "folders": subfolders
    }
