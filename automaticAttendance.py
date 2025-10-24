from epp_detector_integrado import verify_epp, draw_results
from interfaz_asistencia_epp import InterfazAsistenciaEPP
import tkinter as tk
import os, cv2
import pandas as pd
import datetime
import time
import subprocess
import platform

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
haarcasecade_path = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")
trainimagelabel_path = os.path.join(BASE_DIR, "TrainingImageLabel", "Trainner.yml")
studentdetail_path = os.path.join(BASE_DIR, "StudentDetails", "studentdetails.csv")
attendance_base = os.path.join(BASE_DIR, "Attendance")

def text_to_speech(message):
    """Funcion de texto a voz simple"""
    print(f"[TTS] {message}")
    try:
        if platform.system() == "Linux":
            subprocess.run(["espeak", message], check=False, 
                         stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except:
        pass

def open_file(filepath):
    """Abre archivo multiplataforma"""
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(filepath)
        elif system == "Darwin":
            subprocess.run(["open", filepath], check=False)
        else:
            subprocess.run(["xdg-open", filepath], check=False)
    except:
        print(f"Archivo guardado en: {filepath}")

def subjectChoose():
    def FillAttendance():
        trabajador_buscado = tx.get().strip()
        if trabajador_buscado == "":
            text_to_speech("Ingrese el nombre del trabajador.")
            return

        if not os.path.exists(trainimagelabel_path):
            text_to_speech("Modelo no encontrado. Entrena primero.")
            return

        try:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.read(trainimagelabel_path)
            face_cascade = cv2.CascadeClassifier(haarcasecade_path)

            if not os.path.exists(studentdetail_path):
                text_to_speech("No hay trabajadores registrados.")
                return

            df_students = pd.read_csv(studentdetail_path, dtype=str)
            df_students["Enrollment"] = df_students["Enrollment"].astype(str)

            # ===== VALIDAR QUE EL TRABAJADOR EXISTE =====
            trabajador_existe = df_students['Name'].str.lower().str.contains(trabajador_buscado.lower()).any()
            if not trabajador_existe:
                msg = f"Trabajador '{trabajador_buscado}' no encontrado en la base de datos."
                text_to_speech(msg)
                print(f"\n❌ {msg}")
                print("\nTrabajadores registrados:")
                for idx, row in df_students.iterrows():
                    print(f"  - {row['Name']} (ID: {row['Enrollment']})")
                return

            os.makedirs(attendance_base, exist_ok=True)
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            today_file = os.path.join(attendance_base, f"asistencia_{today}.csv")

            if os.path.exists(today_file):
                prev_attendance = pd.read_csv(today_file, dtype=str)
            else:
                prev_attendance = pd.DataFrame(columns=["Enrollment", "Name", "Date", "Time", "Status"])

            cam = cv2.VideoCapture(0)
            if not cam.isOpened():
                text_to_speech("No se pudo abrir la camara.")
                return

            cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            interfaz = InterfazAsistenciaEPP()
            start_time = time.time()
            capture_duration = 10
            new_rows = []

            print("\n" + "="*60)
            print("INICIANDO CAPTURA DE ASISTENCIA")
            print("="*60)
            print(f"Trabajador buscado: {trabajador_buscado}")
            print(f"Duracion: {capture_duration} segundos")
            print(f"Detector EPP: ACTIVO (Color + Forma)")
            print(f"Solo se registrara: {trabajador_buscado}")
            print("="*60 + "\n")

            window_name = "Sistema de Asistencia con EPP"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, 1280, 720)

            trabajador_registrado = False

            while True:
                ret, frame = cam.read()
                if not ret:
                    break

                tiempo_restante = int(capture_duration - (time.time() - start_time))
                info_trabajador = None
                epp_results = []

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.2, 5)

                for (x, y, w, h) in faces:
                    Id, conf = recognizer.predict(gray[y:y+h, x:x+w])
                    if conf < 70:
                        Id_str = str(Id)
                        match = df_students.loc[df_students["Enrollment"] == Id_str, "Name"]
                        if not match.empty:
                            name = match.values[0]

                            # ===== FILTRO: SOLO PROCESAR SI ES EL TRABAJADOR BUSCADO =====
                            if trabajador_buscado.lower() not in name.lower():
                                # Mostrar que se detectó otro trabajador pero no se registra
                                info_trabajador = {
                                    'nombre': f"{name} (NO ES {trabajador_buscado})",
                                    'id': Id_str,
                                    'tiene_rostro': True,
                                    'bbox_rostro': (x, y, w, h)
                                }
                                print(f"⚠️  Detectado: {name} - NO es el trabajador buscado")
                                continue  # Saltar al siguiente rostro

                            # Es el trabajador correcto
                            info_trabajador = {
                                'nombre': name,
                                'id': Id_str,
                                'tiene_rostro': True,
                                'bbox_rostro': (x, y, w, h)
                            }

                            # Verificar EPP
                            epp_results = verify_epp(frame)
                            tiene_casco = any('casco' in str(r[0]).lower() for r in epp_results)
                            tiene_chaleco = any('chaleco' in str(r[0]).lower() for r in epp_results)
                            has_epp = tiene_casco and tiene_chaleco

                            if has_epp:
                                timeStamp = datetime.datetime.now().strftime("%H:%M:%S")
                                today = datetime.datetime.now().strftime("%Y-%m-%d")
                                records_today = prev_attendance.loc[prev_attendance["Enrollment"] == Id_str]
                                records_today = pd.concat([records_today, pd.DataFrame(new_rows)], ignore_index=True) if len(new_rows) else records_today

                                if records_today.empty:
                                    status = "Entrada"
                                elif len(records_today) == 1 and records_today.iloc[0]["Status"] == "Entrada":
                                    status = "Salida"
                                else:
                                    status = None

                                if status:
                                    already_in_new = any(
                                        r["Enrollment"] == Id_str and r["Status"] == status
                                        for r in new_rows
                                    )
                                    
                                    if not already_in_new:
                                        row = {
                                            "Enrollment": Id_str, 
                                            "Name": name, 
                                            "Date": today, 
                                            "Time": timeStamp, 
                                            "Status": status
                                        }
                                        new_rows.append(row)
                                        print(f"✅ {name} - {status} - {timeStamp}")
                                        text_to_speech(f"{name} {status} registrada")
                                        trabajador_registrado = True
                            else:
                                print(f"⚠️  {name} detectado pero sin EPP completo")

                frame = interfaz.dibujar_interfaz_completa(
                    frame, 
                    info_trabajador,
                    epp_results,
                    tiempo_restante=tiempo_restante
                )

                cv2.imshow(window_name, frame)

                if time.time() - start_time > capture_duration:
                    break
                if cv2.waitKey(1) & 0xFF == 27:
                    break

            cam.release()
            cv2.destroyAllWindows()

            if len(new_rows):
                appended = pd.concat([prev_attendance, pd.DataFrame(new_rows)], ignore_index=True)
            else:
                appended = prev_attendance

            appended.drop_duplicates(subset=["Enrollment", "Date", "Status"], keep="first", inplace=True)
            appended.to_csv(today_file, index=False)

            print("\n" + "="*60)
            if trabajador_registrado:
                print(f"✅ ASISTENCIA REGISTRADA")
                print(f"Trabajador: {trabajador_buscado}")
                print(f"Registros: {len(new_rows)}")
            else:
                print(f"⚠️  NO SE REGISTRO ASISTENCIA")
                print(f"Trabajador '{trabajador_buscado}' no detectado o sin EPP")
            print(f"Archivo: {today_file}")
            print("="*60 + "\n")

            msg = f"Asistencia: {len(new_rows)} registros para {trabajador_buscado}"
            Notifica.configure(text=msg, bg="black", fg="yellow" if trabajador_registrado else "red", 
                             width=50, relief=tk.RIDGE, bd=5, font=("times", 15, "bold"))
            Notifica.place(x=20, y=250)
            text_to_speech(msg)
            
            if trabajador_registrado:
                open_file(today_file)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            text_to_speech(error_msg)
            print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            try:
                cam.release()
                cv2.destroyAllWindows()
            except:
                pass

    subject = tk.Tk()
    subject.title("Registrar Asistencia con EPP")
    subject.geometry("600x340")
    subject.resizable(0, 0)
    subject.configure(background="black")

    titl = tk.Label(subject, text="Registrar asistencia individual", bg="black", 
                   fg="green", font=("arial", 25))
    titl.pack(pady=20)

    Notifica = tk.Label(subject, text="", bg="black", fg="yellow", 
                       font=("times", 15, "bold"))
    Notifica.pack()

    sub_label = tk.Label(subject, text="Nombre del trabajador:", bg="black", fg="yellow", 
                        font=("times new roman", 15))
    sub_label.place(x=60, y=120)

    tx = tk.Entry(subject, width=15, bd=5, bg="black", fg="yellow", 
                 font=("times", 30, "bold"))
    tx.place(x=200, y=110)

    fill_a = tk.Button(subject, text="Registrar Asistencia", command=FillAttendance, 
                      bd=7, font=("times new roman", 15), bg="black", fg="yellow", 
                      height=2, width=16)
    fill_a.place(x=190, y=220)

    subject.mainloop()

if __name__ == "__main__":
    subjectChoose()