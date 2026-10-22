import os
import argparse
import requests
from pathlib import Path

# Configuración de URLs para descargar los modelos (PLACEHOLDER)
# Debes subir tus modelos a un Bucket S3 público o privado (con presigned URL),
# Google Drive, o cualquier servidor HTTP y poner los links aquí.
MODELS = {
    "sentinel2-model.keras": "https://tu-bucket-s3.s3.amazonaws.com/models/sentinel2-model.keras",
    # Agrega otros si son necesarios
}

def download_file(url: str, dest_path: Path):
    if dest_path.exists():
        print(f"[SKIP] {dest_path.name} ya existe.")
        return

    print(f"[DOWNLOADING] {dest_path.name} desde {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"[OK] Descarga completada: {dest_path.name}")
    except Exception as e:
        print(f"[ERROR] Falló la descarga de {dest_path.name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Descargar modelos para Sentinel MVP")
    parser.add_argument("--output-dir", default="models", help="Carpeta destino")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Iniciando descarga de modelos en '{args.output_dir}'...")
    for filename, url in MODELS.items():
        download_file(url, Path(args.output_dir) / filename)

if __name__ == "__main__":
    main()
