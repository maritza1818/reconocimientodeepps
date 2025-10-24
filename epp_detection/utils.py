# epp_detection/utils.py

# Anchors por defecto para la detección de objetos (YOLO)
default_anchors = [
    [10,13, 16,30, 33,23],
    [30,61, 62,45, 59,119],
    [116,90, 156,198, 373,326]
]

def load_class_names(file_path='epp_detection/class_names.txt'):
    """
    Carga los nombres de las clases desde un archivo de texto.
    Cada línea del archivo debe contener un nombre de clase.
    """
    try:
        with open(file_path, 'r') as f:
            class_names = [line.strip() for line in f.readlines() if line.strip()]
        return class_names
    except FileNotFoundError:
        print(f"[Error] No se encontró el archivo de clases: {file_path}")
        return ["Unknown"]
