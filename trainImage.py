# trainImage.py
import os
import cv2
import numpy as np
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
trainimage_path = os.path.join(BASE_DIR, "TrainingImage")
trainimagelabel_path = os.path.join(BASE_DIR, "TrainingImageLabel", "Trainner.yml")
haarcasecade_path = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")

def getImagesAndLabels(path):
    faces = []
    Ids = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.lower().endswith(".jpg") or file.lower().endswith(".png"):
                imagePath = os.path.join(root, file)
                try:
                    PIL_img = Image.open(imagePath).convert('L')
                    img_numpy = np.array(PIL_img, 'uint8')
                    parts = os.path.basename(imagePath).split("_")
                    # nombre_ER_num.jpg -> index 1 is id
                    Id = int(parts[1])
                    faces.append(img_numpy)
                    Ids.append(Id)
                except Exception:
                    continue
    return faces, Ids

def TrainImage(haarcasecade_path_input, trainimage_path_input, trainimagelabel_path, message, text_to_speech):
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        # comprobar cascade
        if not os.path.exists(haarcasecade_path_input):
            msg = f"Haarcascade no encontrado en {haarcasecade_path_input}"
            message.configure(text=msg)
            text_to_speech(msg)
            return

        faces, Ids = getImagesAndLabels(trainimage_path_input)
        if len(faces) == 0:
            msg = "No hay imágenes para entrenar. Registra primero."
            message.configure(text=msg)
            text_to_speech(msg)
            return

        recognizer.train(faces, np.array(Ids))
        os.makedirs(os.path.dirname(trainimagelabel_path), exist_ok=True)
        recognizer.save(trainimagelabel_path)
        res = "Imágenes entrenadas correctamente."
        message.configure(text=res)
        text_to_speech(res)
    except Exception as e:
        err = f"Error al entrenar: {e}"
        message.configure(text=err)
        text_to_speech(err)
