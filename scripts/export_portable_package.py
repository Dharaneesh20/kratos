"""
Exports all trained model weights (roadnet.pt) and persistent vector database (vector.db)
into a portable ZIP package (kratos_laptop_deploy_package.zip) for offline deployment on laptops.
"""

import os
import sys
import zipfile
from pathlib import Path

def create_portable_package():
    root = Path(__file__).resolve().parents[1]
    output_zip = root / "kratos_laptop_deploy_package.zip"

    files_to_pack = [
        ("vision-service/weights/roadnet.pt", root / "vision-service" / "weights" / "roadnet.pt"),
        ("agentverse-platform/backend/vector.db", root / "agentverse-platform" / "backend" / "vector.db"),
        ("agentverse-platform/backend/kratos.db", root / "agentverse-platform" / "backend" / "kratos.db"),
    ]

    print("===============================================================================")
    print("      KRATOS PORTABLE MODEL WEIGHTS & VECTOR.DB EXPORTER")
    print("===============================================================================")
    print(f"Target Zip Package: {output_zip}\n")

    packed_count = 0
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for arcname, filepath in files_to_pack:
            if filepath.exists():
                zipf.write(filepath, arcname)
                size_mb = round(os.path.getsize(filepath) / (1024 * 1024), 2)
                print(f"  [+] Packed: {arcname} ({size_mb} MB)")
                packed_count += 1
            else:
                print(f"  [-] Skipped (Not found): {arcname}")

    if packed_count > 0:
        print("\n===============================================================================")
        print("  PORTABLE PACKAGE CREATED SUCCESSFULLY!")
        print("===============================================================================")
        print("  To deploy on your laptop:")
        print("  1. Copy 'kratos_laptop_deploy_package.zip' to your laptop.")
        print("  2. Extract it into your laptop's project workspace.")
        print("  3. Run '.\\run_kratos.bat' - model inference & vector DB will run offline instantly!")
        print("===============================================================================")
    else:
        print("\n[!] Warning: No model weights or vector.db were found to pack.")
        print("    Run 'vision-service\\train.bat' first to generate weights/roadnet.pt.")

if __name__ == "__main__":
    create_portable_package()
