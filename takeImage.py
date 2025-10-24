# takeImage.py
import csv
import os
import cv2
import numpy as np
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
haarcasecade_path = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")
trainimage_path = os.path.join(BASE_DIR, "TrainingImage")
studentdetail_path = os.path.join(BASE_DIR, "StudentDetails", "studentdetails.csv")

def TakeImage(l1, l2, haar_path, train_path, message, err_screen, text_to_speech):
    # l1 = Enrollment, l2 = Name
    if (l1 == "") and (l2 == ""):
        t = "Por favor, ingrese su código y nombre."
        text_to_speech(t)
        err_screen()
        return
    if l1 == "":
        t = "Por favor, ingrese su número de matrícula."
        text_to_speech(t)
        err_screen()
        return
    if l2 == "":
        t = "Por favor, ingrese su nombre."
        text_to_speech(t)
        err_screen()
        return

    Enrollment = l1.strip()
    Name = l2.strip()

    try:
        if not os.path.exists(studentdetail_path):
            os.makedirs(os.path.dirname(studentdetail_path), exist_ok=True)
            with open(studentdetail_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Enrollment", "Name"])

        already_registered = False
        with open(studentdetail_path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 1 and row[0] == Enrollment:
                    already_registered = True
                    break

        if already_registered:
            res = f"El usuario {Name} ({Enrollment}) ya está registrado."
            message.configure(text=res)
            text_to_speech(res)
            return

        directory = f"{Enrollment}_{Name}"
        path = os.path.join(train_path, directory)
        if os.path.exists(path) and any(os.scandir(path)):
            res = f"Las imágenes de {Name} ya existen."
            message.configure(text=res)
            text_to_speech(res)
            return

        os.makedirs(path, exist_ok=True)

        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            text_to_speech("No se pudo acceder a la cámara.")
            return

        detector = cv2.CascadeClassifier(haar_path)
        sampleNum = 0

        while True:
            ret, img = cam.read()
            if not ret:
                break
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                sampleNum += 1
                face_img = gray[y:y+h, x:x+w]
                filename = os.path.join(path, f"{Name}_{Enrollment}_{sampleNum}.jpg")
                cv2.imwrite(filename, face_img)
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.imshow("Capturando rostro...", img)

            # esperar poco para no saturar CPU
            if cv2.waitKey(100) & 0xFF == ord("q"):
                break
            if sampleNum >= 50:
                break

        cam.release()
        cv2.destroyAllWindows()

        with open(studentdetail_path, "a", newline="", encoding="utf-8-sig") as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow([Enrollment, Name])

        res = f"Imágenes guardadas para ER No: {Enrollment} Nombre: {Name}"
        message.configure(text=res)
        text_to_speech(res)

    except Exception as e:
        err = f"Error capturando imágenes: {str(e)}"
        message.configure(text=err)
        text_to_speech(err)
