import os

base_path = r"C:\Users\Myrian\Downloads\projectihc\Attendance-Management-system-using-face-recognition"

folders = [
    "epp_model",
    "epp_model\\weights"
]

for folder in folders:
    path = os.path.join(base_path, folder)
    os.makedirs(path, exist_ok=True)
    print(f"✅ Carpeta creada o existente: {path}")

# Crear archivos vacíos para empezar
open(os.path.join(base_path, "epp_model", "__init__.py"), "a").close()
print("✅ Archivo __init__.py creado")
