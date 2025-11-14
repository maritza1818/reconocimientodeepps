# takeImage.py - VERSION MEJORADA
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

        # ===== MEJORA 1: CONFIGURAR RESOLUCIÓN =====
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        detector = cv2.CascadeClassifier(haar_path)
        sampleNum = 0
        
        # ===== MEJORA 2: MÁS FOTOS (200 en lugar de 50) =====
        MAX_SAMPLES = 200
        
        # ===== MEJORA 3: CAPTURAR CON VARIACIONES =====
        # Instrucciones para el usuario
        instrucciones = [
            "Mira al frente",
            "Gira ligeramente a la izquierda",
            "Gira ligeramente a la derecha",
            "Inclina la cabeza un poco",
            "Sonrie",
            "Expresion normal"
        ]
        instruccion_actual = 0
        cambio_instruccion_cada = MAX_SAMPLES // len(instrucciones)

        print("\n" + "="*60)
        print(f"CAPTURANDO FOTOS PARA: {Name}")
        print("="*60)
        print("INSTRUCCIONES:")
        print("  - Manten buena iluminacion")
        print("  - Sigue las instrucciones en pantalla")
        print("  - Presiona 'Q' para cancelar")
        print(f"  - Total de fotos: {MAX_SAMPLES}")
        print("="*60 + "\n")

        while True:
            ret, img = cam.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # ===== MEJORA 4: ECUALIZACIÓN DE HISTOGRAMA =====
            gray = cv2.equalizeHist(gray)
            
            faces = detector.detectMultiScale(gray, 1.3, 5, minSize=(100, 100))
            
            for (x, y, w, h) in faces:
                sampleNum += 1
                
                # ===== MEJORA 5: AUMENTAR TAMAÑO DE CAPTURA =====
                # Capturar con más contexto alrededor del rostro
                padding = 20
                y1 = max(0, y - padding)
                y2 = min(gray.shape[0], y + h + padding)
                x1 = max(0, x - padding)
                x2 = min(gray.shape[1], x + w + padding)
                
                face_img = gray[y1:y2, x1:x2]
                
                # ===== MEJORA 6: REDIMENSIONAR A TAMAÑO ESTÁNDAR =====
                face_img = cv2.resize(face_img, (200, 200))
                
                # Guardar imagen
                filename = os.path.join(path, f"{Name}_{Enrollment}_{sampleNum}.jpg")
                cv2.imwrite(filename, face_img)
                
                # Dibujar rectángulo y texto
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Mostrar progreso
                progreso = f"{sampleNum}/{MAX_SAMPLES}"
                cv2.putText(img, progreso, (x, y - 40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                # Mostrar instrucción actual
                instruccion_idx = min(sampleNum // cambio_instruccion_cada, len(instrucciones) - 1)
                instruccion = instrucciones[instruccion_idx]
                cv2.putText(img, instruccion, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
                
                # Barra de progreso
                barra_ancho = 400
                barra_progreso = int((sampleNum / MAX_SAMPLES) * barra_ancho)
                cv2.rectangle(img, (10, img.shape[0] - 30), 
                             (10 + barra_ancho, img.shape[0] - 10), (100, 100, 100), -1)
                cv2.rectangle(img, (10, img.shape[0] - 30), 
                             (10 + barra_progreso, img.shape[0] - 10), (0, 255, 0), -1)

            cv2.imshow("Capturando rostro - Sigue las instrucciones", img)

            # ===== MEJORA 7: CAPTURAR MÁS RÁPIDO =====
            if cv2.waitKey(50) & 0xFF == ord("q"):  # 50ms en lugar de 100ms
                break
            if sampleNum >= MAX_SAMPLES:
                break

        cam.release()
        cv2.destroyAllWindows()

        print("\n" + "="*60)
        print(f"✅ CAPTURA COMPLETADA")
        print(f"Fotos guardadas: {sampleNum}")
        print(f"Trabajador: {Name} (ID: {Enrollment})")
        print("="*60 + "\n")

        with open(studentdetail_path, "a", newline="", encoding="utf-8-sig") as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow([Enrollment, Name])

        res = f"✅ {sampleNum} imágenes guardadas para {Name} (ID: {Enrollment})"
        message.configure(text=res)
        text_to_speech(res)

    except Exception as e:
        err = f"Error capturando imágenes: {str(e)}"
        message.configure(text=err)
        text_to_speech(err)
        import traceback
        traceback.print_exc()