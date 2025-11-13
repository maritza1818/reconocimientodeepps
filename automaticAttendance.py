# automaticAttendance.py
# versión con:
# - zona
# - forzado (demo)
# - intentos compactados
# - MODO EPP ESTRICTO: SOLO CÓDIGO DE CHALECO DEL DUEÑO
# - reloj
# - lectura de códigos de barras
# - fix csv vacíos
# - fix after cuando se cierra la ventana

from epp_detector_integrado import verify_epp
from interfaz_asistencia_epp import InterfazAsistenciaEPP
import tkinter as tk
from tkinter import ttk
import os, cv2
import pandas as pd
import datetime
import time
import subprocess
import platform
from pyzbar.pyzbar import decode

# rutas base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
haarcasecade_path = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")
trainimagelabel_path = os.path.join(BASE_DIR, "TrainingImageLabel", "Trainner.yml")
studentdetail_path = os.path.join(BASE_DIR, "StudentDetails", "studentdetails.csv")
attendance_base = os.path.join(BASE_DIR, "Attendance")
epp_registry_path = os.path.join(BASE_DIR, "EPP", "epp_registry.csv")


def text_to_speech(message: str):
    print(f"[TTS] {message}")
    try:
        if platform.system() == "Linux":
            subprocess.run(
                ["espeak", message],
                check=False,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )
    except:
        pass


def open_file(filepath):
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


def leer_csv_seguro(path, columnas):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame(columns=columnas)
    try:
        df = pd.read_csv(path, dtype=str)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=columnas)
    for c in columnas:
        if c not in df.columns:
            df[c] = ""
    return df


def load_epp_registry():
    carpeta_epp = os.path.join(BASE_DIR, "EPP")
    os.makedirs(carpeta_epp, exist_ok=True)
    cols = ["Barcode", "EPP_Type", "Enrollment", "Name", "Active"]
    df = leer_csv_seguro(epp_registry_path, cols)
    df["Barcode"] = df["Barcode"].fillna("").str.upper().str.replace(" ", "")
    return df


def save_attempt_log(row_dict):
    os.makedirs(attendance_base, exist_ok=True)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    intentos_file = os.path.join(attendance_base, f"intentos_{today}.csv")
    df_row = pd.DataFrame([row_dict])
    if not os.path.exists(intentos_file):
        df_row.to_csv(intentos_file, index=False, encoding="utf-8-sig")
    else:
        df_row.to_csv(
            intentos_file,
            mode="a",
            header=False,
            index=False,
            encoding="utf-8-sig",
        )


def save_attempts_batch(rows):
    for r in rows:
        save_attempt_log(r)


def compact_attempts(rows, max_per_person=2):
    compacted = []
    seen = set()
    for r in rows:
        enroll = r.get("Enrollment", "")
        minute_bucket = r.get("Time", "")[:5]
        reason_short = (r.get("Reason", "") or "")[:40]
        key = (enroll, minute_bucket, reason_short)
        if key in seen:
            continue
        seen.add(key)
        compacted.append(r)

    if max_per_person is not None:
        final = []
        count_by_person = {}
        for r in compacted:
            p = r.get("Enrollment", "")
            count_by_person.setdefault(p, 0)
            if count_by_person[p] < max_per_person:
                final.append(r)
                count_by_person[p] += 1
        return final
    return compacted


def parse_epp_results(epp_results, min_casco=0.65, min_chaleco=0.65):
    tiene_casco = False
    tiene_chaleco = False
    for r in epp_results:
        if not r:
            continue
        label = str(r[0]).lower()
        score = 1.0
        if len(r) > 1:
            try:
                score = float(r[1])
            except:
                score = 1.0
        if ("casco" in label or "helmet" in label) and score >= min_casco:
            tiene_casco = True
        if ("chaleco" in label or "vest" in label) and score >= min_chaleco:
            tiene_chaleco = True
    return tiene_casco, tiene_chaleco


def subjectChoose():
    subject = tk.Tk()
    subject.title("Registrar Asistencia con EPP")
    subject.geometry("650x500")
    subject.resizable(0, 0)
    subject.configure(background="black")

    titulo = tk.Label(
        subject,
        text="Registrar asistencia individual",
        bg="black",
        fg="green",
        font=("arial", 25),
    )
    titulo.pack(pady=5)

    lbl_clock = tk.Label(
        subject,
        text="",
        bg="black",
        fg="white",
        font=("arial", 11, "bold"),
    )
    lbl_clock.pack(pady=2)

    def actualizar_reloj():
        if not subject.winfo_exists():
            return
        ahora = datetime.datetime.now()
        lbl_clock.config(text=ahora.strftime(" %d/%m/%Y   %H:%M:%S"))
        try:
            subject.after(1000, actualizar_reloj)
        except tk.TclError:
            pass

    actualizar_reloj()

    estado_label = tk.Label(
        subject,
        text="Listo",
        bg="black",
        fg="white",
        font=("arial", 16, "bold"),
        width=30,
    )
    estado_label.place(x=70, y=70)

    motivo_label = tk.Label(
        subject,
        text="",
        bg="black",
        fg="yellow",
        font=("arial", 12),
        wraplength=520,
        justify="left",
    )
    motivo_label.place(x=40, y=110)

    name_lbl = tk.Label(
        subject,
        text="Nombre del trabajador:",
        bg="black",
        fg="yellow",
        font=("times new roman", 15),
    )
    name_lbl.place(x=40, y=160)

    tx = tk.Entry(
        subject,
        width=15,
        bd=5,
        bg="black",
        fg="yellow",
        font=("times", 30, "bold"),
    )
    tx.place(x=40, y=190)

    zone_lbl = tk.Label(
        subject,
        text="Zona / área:",
        bg="black",
        fg="yellow",
        font=("times new roman", 15),
    )
    zone_lbl.place(x=360, y=160)

    zonas_disponibles = [
        "Portón principal",
        "Almacén",
        "Taller",
        "Oficina",
        "Laboratorio",
        "General",
    ]
    zona_var = tk.StringVar(value="Portón principal")
    zona_combo = ttk.Combobox(
        subject,
        textvariable=zona_var,
        values=zonas_disponibles,
        state="readonly",
        font=("times", 12),
    )
    zona_combo.place(x=360, y=190, width=200)
    zona_combo.current(0)

    force_var = tk.BooleanVar(value=False)
    force_chk = tk.Checkbutton(
        subject,
        text="Permitir registro aunque falte EPP (demo)",
        variable=force_var,
        bg="black",
        fg="yellow",
        selectcolor="black",
        activebackground="black",
        font=("times", 11),
    )
    force_chk.place(x=40, y=240)

    historial_title = tk.Label(
        subject,
        text="Últimos intentos:",
        bg="black",
        fg="white",
        font=("arial", 12, "bold"),
    )
    historial_title.place(x=40, y=300)

    historial_list = tk.Listbox(subject, width=80, height=8, bg="black", fg="white")
    historial_list.place(x=40, y=330)

    def set_estado(titulo, detalle="", color="green"):
        estado_label.config(text=titulo, bg=color)
        motivo_label.config(text=detalle)

    def agregar_historial(nombre, texto):
        ahora = datetime.datetime.now().strftime("%H:%M:%S")
        historial_list.insert(0, f"{ahora} | {nombre} | {texto}")

    def FillAttendance():
        trabajador_buscado = tx.get().strip()
        zona_actual = zona_var.get().strip() or "General"

        set_estado("Procesando...", "Abriendo cámara...", "orange")

        if trabajador_buscado == "":
            set_estado("NO REGISTRADO", "Ingrese el nombre del trabajador", "red")
            return

        if not os.path.exists(trainimagelabel_path):
            set_estado("NO REGISTRADO", "Modelo no encontrado. Entrene primero.", "red")
            return

        cam = None
        try:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.read(trainimagelabel_path)
            face_cascade = cv2.CascadeClassifier(haarcasecade_path)

            if not os.path.exists(studentdetail_path) or os.path.getsize(studentdetail_path) == 0:
                set_estado("NO REGISTRADO", "No hay trabajadores registrados.", "red")
                return

            df_students = leer_csv_seguro(studentdetail_path, ["Enrollment", "Name"])
            df_students["Enrollment"] = df_students["Enrollment"].astype(str)

            existe = df_students["Name"].str.lower().str.contains(
                trabajador_buscado.lower()
            ).any()
            if not existe:
                set_estado(
                    "NO REGISTRADO",
                    f"Trabajador '{trabajador_buscado}' no existe en la base.",
                    "red",
                )
                return

            os.makedirs(attendance_base, exist_ok=True)
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            today_file = os.path.join(attendance_base, f"asistencia_{today}.csv")

            cols_asistencia = [
                "Enrollment",
                "Name",
                "Date",
                "Time",
                "Status",
                "Reason",
                "Zone",
                "EPP_Detected",
                "CaptureSeconds",
            ]
            prev_attendance = leer_csv_seguro(today_file, cols_asistencia)

            cam = cv2.VideoCapture(0)
            if not cam.isOpened():
                set_estado("ERROR", "No se pudo abrir la cámara", "red")
                return

            cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            interfaz = InterfazAsistenciaEPP()
            start_time = time.time()
            capture_duration = 10
            new_rows = []
            attempts_buffer = []
            trabajador_registrado = False
            motivo_fallo = "No se detectó al trabajador"

            window_name = "Sistema de Asistencia con EPP"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, 1280, 720)

            epp_registry_df = load_epp_registry()
            salir_ya = False

            while True:
                ret, frame = cam.read()
                if not ret:
                    motivo_fallo = "No se pudo leer la cámara"
                    break

                ahora_txt = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                cv2.putText(
                    frame,
                    ahora_txt,
                    (850, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

                tiempo_restante = int(capture_duration - (time.time() - start_time))
                info_trabajador = None
                epp_results = []

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.2, 5)

                for (x, y, w, h) in faces:
                    Id, conf = recognizer.predict(gray[y:y + h, x:x + w])
                    if conf < 70:
                        Id_str = str(Id)
                        match = df_students.loc[
                            df_students["Enrollment"] == Id_str, "Name"
                        ]
                        if not match.empty:
                            name = match.values[0]

                            # validar que sea el trabajador buscado
                            if trabajador_buscado.lower() not in name.lower():
                                info_trabajador = {
                                    "nombre": f"{name} (NO ES {trabajador_buscado})",
                                    "id": Id_str,
                                    "tiene_rostro": True,
                                    "bbox_rostro": (x, y, w, h),
                                }
                                motivo_fallo = "Se detectó otra persona"
                                attempts_buffer.append(
                                    {
                                        "Enrollment": Id_str,
                                        "Name": name,
                                        "Date": today,
                                        "Time": datetime.datetime.now().strftime("%H:%M:%S"),
                                        "Status": "NO_REGISTRADO",
                                        "Reason": "No era el trabajador solicitado",
                                        "Zone": zona_actual,
                                        "EPP_Detected": "",
                                        "CaptureSeconds": str(int(time.time() - start_time)),
                                    }
                                )
                                continue

                            info_trabajador = {
                                "nombre": name,
                                "id": Id_str,
                                "tiene_rostro": True,
                                "bbox_rostro": (x, y, w, h),
                            }

                            # modo demo
                            if force_var.get():
                                timeStamp = datetime.datetime.now().strftime("%H:%M:%S")
                                row = {
                                    "Enrollment": Id_str,
                                    "Name": name,
                                    "Date": today,
                                    "Time": timeStamp,
                                    "Status": "Entrada",
                                    "Reason": "REGISTRO DEMO (sin EPP)",
                                    "Zone": zona_actual,
                                    "EPP_Detected": "",
                                    "CaptureSeconds": str(int(time.time() - start_time)),
                                }
                                new_rows.append(row)
                                trabajador_registrado = True

                                attempts_buffer.append(
                                    {
                                        "Enrollment": Id_str,
                                        "Name": name,
                                        "Date": today,
                                        "Time": timeStamp,
                                        "Status": "REG_FORZADO",
                                        "Reason": "REGISTRO DEMO (sin EPP)",
                                        "Zone": zona_actual,
                                        "EPP_Detected": "",
                                        "CaptureSeconds": str(int(time.time() - start_time)),
                                    }
                                )
                                salir_ya = True
                                break

                            # detección por color (solo para mostrar en pantalla)
                            epp_results = verify_epp(frame)
                            _, tiene_chaleco_color = parse_epp_results(epp_results)
                            epp_detected_str = ";".join([str(r[0]) for r in epp_results])

                            # lectura de códigos de barras
                            barcodes = decode(frame)

                            code_has_chaleco = False

                            for b in barcodes:
                                code = b.data.decode("utf-8").strip()
                                code_norm = code.upper().replace(" ", "")

                                (bx, by, bw, bh) = b.rect
                                cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 255, 255), 2)
                                cv2.putText(
                                    frame,
                                    code,
                                    (bx, by - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5,
                                    (0, 255, 255),
                                    1,
                                )

                                match_code = epp_registry_df[
                                    epp_registry_df["Barcode"] == code_norm
                                ]
                                # si no existe el código, lo ignoramos (no lo marcamos como fallo aquí)
                                if match_code.empty:
                                    continue

                                epp_owner = str(match_code.iloc[0]["Enrollment"]).strip()
                                epp_type = str(match_code.iloc[0]["EPP_Type"]).lower()
                                epp_active = str(match_code.iloc[0].get("Active", "1")).lower()

                                if epp_active not in ["1", "true", "yes", "si", "sí"]:
                                    continue

                                # SOLO chaleco del mismo trabajador
                                if epp_type == "chaleco" and epp_owner == Id_str:
                                    code_has_chaleco = True

                            # REGLA FINAL (ESTRICTO):
                            # SOLO se registra si hay código de chaleco del dueño
                            has_epp = code_has_chaleco

                            if not has_epp:
                                motivo_fallo = "Falta: código de CHALECO del dueño (no se acepta solo casco ni color)"
                                attempts_buffer.append(
                                    {
                                        "Enrollment": Id_str,
                                        "Name": name,
                                        "Date": today,
                                        "Time": datetime.datetime.now().strftime("%H:%M:%S"),
                                        "Status": "NO_REGISTRADO",
                                        "Reason": motivo_fallo,
                                        "Zone": zona_actual,
                                        "EPP_Detected": epp_detected_str,
                                        "CaptureSeconds": str(int(time.time() - start_time)),
                                    }
                                )
                                continue

                            # si llegó hasta aquí → registrar
                            timeStamp = datetime.datetime.now().strftime("%H:%M:%S")
                            row = {
                                "Enrollment": Id_str,
                                "Name": name,
                                "Date": today,
                                "Time": timeStamp,
                                "Status": "Entrada",
                                "Reason": "OK",
                                "Zone": zona_actual,
                                "EPP_Detected": epp_detected_str,
                                "CaptureSeconds": str(int(time.time() - start_time)),
                            }
                            new_rows.append(row)
                            trabajador_registrado = True

                frame = interfaz.dibujar_interfaz_completa(
                    frame,
                    info_trabajador,
                    epp_results,
                    tiempo_restante=tiempo_restante,
                )
                cv2.imshow(window_name, frame)

                try:
                    subject.update_idletasks()
                    subject.update()
                except tk.TclError:
                    break

                if salir_ya:
                    break
                if time.time() - start_time > capture_duration:
                    break
                if cv2.waitKey(1) & 0xFF == 27:
                    break

            # guardar asistencia
            if len(new_rows):
                appended = pd.concat([prev_attendance, pd.DataFrame(new_rows)], ignore_index=True)
            else:
                appended = prev_attendance

            appended.drop_duplicates(
                subset=["Enrollment", "Date", "Status", "Reason"],
                keep="first",
                inplace=True,
            )
            appended.to_csv(today_file, index=False, encoding="utf-8-sig")

            # guardar intentos
            if attempts_buffer:
                compacted = compact_attempts(attempts_buffer, max_per_person=2)
                save_attempts_batch(compacted)

            if trabajador_registrado:
                set_estado("REGISTRADO", "Asistencia guardada", "green")
                agregar_historial(trabajador_buscado, "OK")
                open_file(today_file)
            else:
                set_estado("NO REGISTRADO", motivo_fallo, "red")
                agregar_historial(trabajador_buscado, "FALLÓ: " + motivo_fallo)

        except Exception as e:
            set_estado("ERROR", str(e), "red")

        finally:
            if cam is not None:
                cam.release()
            cv2.destroyAllWindows()

    btn_reg = tk.Button(
        subject,
        text="Registrar Asistencia",
        command=FillAttendance,
        bd=7,
        font=("times new roman", 15),
        bg="black",
        fg="yellow",
        height=2,
        width=18,
    )
    btn_reg.place(x=360, y=240)

    btn_retry = tk.Button(
        subject,
        text="Reintentar",
        command=FillAttendance,
        bd=4,
        font=("times new roman", 12),
        bg="gray20",
        fg="white",
        height=1,
        width=10,
    )
    btn_retry.place(x=420, y=290)

    subject.mainloop()


if __name__ == "__main__":
    subjectChoose()
