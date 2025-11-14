# trainImage.py - VERSION MEJORADA
import os
import cv2
import numpy as np
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
trainimage_path = os.path.join(BASE_DIR, "TrainingImage")
trainimagelabel_path = os.path.join(BASE_DIR, "TrainingImageLabel", "Trainner.yml")
haarcasecade_path = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")

def getImagesAndLabels(path):
    """Obtiene imágenes y labels con preprocesamiento mejorado"""
    faces = []
    Ids = []
    
    print("\n" + "="*60)
    print("CARGANDO IMÁGENES PARA ENTRENAMIENTO")
    print("="*60)
    
    total_images = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.lower().endswith(".jpg") or file.lower().endswith(".png"):
                total_images += 1
    
    print(f"Total de imágenes encontradas: {total_images}")
    processed = 0
    
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.lower().endswith(".jpg") or file.lower().endswith(".png"):
                imagePath = os.path.join(root, file)
                try:
                    # Abrir imagen
                    PIL_img = Image.open(imagePath).convert('L')
                    img_numpy = np.array(PIL_img, 'uint8')
                    
                    # ===== MEJORA 1: NORMALIZACIÓN =====
                    # Ecualizar histograma para mejor consistencia
                    img_numpy = cv2.equalizeHist(img_numpy)
                    
                    # Extraer ID del nombre del archivo
                    parts = os.path.basename(imagePath).split("_")
                    Id = int(parts[1])
                    
                    faces.append(img_numpy)
                    Ids.append(Id)
                    
                    processed += 1
                    if processed % 50 == 0:
                        print(f"Procesadas: {processed}/{total_images}")
                    
                except Exception as e:
                    print(f"⚠️  Error procesando {file}: {e}")
                    continue
    
    print(f"✅ Imágenes procesadas correctamente: {len(faces)}")
    print("="*60 + "\n")
    return faces, Ids

def TrainImage(haarcasecade_path_input, trainimage_path_input, trainimagelabel_path, message, text_to_speech):
    try:
        # ===== MEJORA 2: LBPH CON PARÁMETROS OPTIMIZADOS =====
        # radius: radio del patrón LBP (default 1)
        # neighbors: número de puntos de muestra (default 8)
        # grid_x, grid_y: división de la imagen en celdas (default 8x8)
        # threshold: umbral de confianza (más alto = más estricto)
        
        recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=2,        # Mayor radio captura más contexto
            neighbors=8,     # Puntos de muestreo
            grid_x=8,        # División horizontal
            grid_y=8,        # División vertical
            threshold=50.0   # Umbral más estricto (default 123.0)
        )
        
        if not os.path.exists(haarcasecade_path_input):
            msg = f"Haarcascade no encontrado en {haarcasecade_path_input}"
            message.configure(text=msg)
            text_to_speech(msg)
            return

        print("="*60)
        print("ENTRENANDO MODELO DE RECONOCIMIENTO FACIAL")
        print("="*60)
        
        faces, Ids = getImagesAndLabels(trainimage_path_input)
        
        if len(faces) == 0:
            msg = "No hay imágenes para entrenar. Registra primero."
            message.configure(text=msg)
            text_to_speech(msg)
            return
        
        # Estadísticas
        unique_ids = len(set(Ids))
        print(f"\nEstadísticas:")
        print(f"  - Total de rostros: {len(faces)}")
        print(f"  - Trabajadores únicos: {unique_ids}")
        print(f"  - Promedio por trabajador: {len(faces)//unique_ids}")
        
        print("\nIniciando entrenamiento...")
        recognizer.train(faces, np.array(Ids))
        
        os.makedirs(os.path.dirname(trainimagelabel_path), exist_ok=True)
        recognizer.save(trainimagelabel_path)
        
        print("\n" + "="*60)
        print("✅ ENTRENAMIENTO COMPLETADO")
        print("="*60)
        print(f"Modelo guardado en: {trainimagelabel_path}")
        print(f"Parámetros del modelo:")
        print(f"  - Radius: 2")
        print(f"  - Neighbors: 8")
        print(f"  - Grid: 8x8")
        print(f"  - Threshold: 50.0 (más estricto)")
        print("="*60 + "\n")
        
        res = f"✅ Modelo entrenado: {len(faces)} imágenes, {unique_ids} trabajadores"
        message.configure(text=res)
        text_to_speech(res)
        
    except Exception as e:
        err = f"Error al entrenar: {e}"
        message.configure(text=err)
        text_to_speech(err)
        import traceback
        traceback.print_exc()