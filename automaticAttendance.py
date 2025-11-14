from epp_detector_integrado import verify_epp, draw_results
from interfaz_asistencia_epp import InterfazAsistenciaEPP
import tkinter as tk
import os, cv2
import pandas as pd
import datetime
import time
import subprocess
import platform

# ==============================
# RUTAS BASE
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
haarcasecade_path = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")
trainimagelabel_path = os.path.join(BASE_DIR, "TrainingImageLabel", "Trainner.yml")
studentdetail_path = os.path.join(BASE_DIR, "StudentDetails", "studentdetails.csv")
attendance_base = os.path.join(BASE_DIR, "Attendance")

os.makedirs(attendance_base, exist_ok=True)

# ==============================
# PALETA DE COLORES (COHERENTE CON attendance.py)
# ==============================

PRIMARY_BG = "#020617"        # Fondo principal
SECONDARY_BG = "#0f172a"      # Tarjetas / panel
ACCENT = "#22c55e"            # Verde principal
ACCENT_SECONDARY = "#38bdf8"  # Azul cian
TEXT_PRIMARY = "#e5e7eb"
TEXT_SECONDARY = "#9ca3af"
WARNING_COLOR = "#facc15"
ERROR_COLOR = "#f97373"


# ==============================
# UTILIDADES
# ==============================

def text_to_speech(message):
    """Función de texto a voz simple"""
    print(f"[TTS] {message}")
    try:
        if platform.system() == "Linux":
            subprocess.run(
                ["espeak", message],
                check=False,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )
    except Exception:
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
    except Exception:
        print(f"Archivo guardado en: {filepath}")


def fade_in_window(win):
    """Animación de aparición suave (alpha de 0 a 1) para Tk/Toplevel."""
    try:
        win.attributes("-alpha", 0.0)
    except Exception:
        return

    def _fade(alpha=0.0):
        if alpha < 1.0:
            try:
                win.attributes("-alpha", alpha)
            except Exception:
                return
            win.after(25, _fade, alpha + 0.08)

    _fade()


# ==============================
# VENTANA DE ASISTENCIA
# ==============================

def subjectChoose():
    """
    Ventana para registrar la asistencia de UN trabajador,
    usando reconocimiento facial + verificación de EPP (casco + chaleco).
    """

    def FillAttendance():
        trabajador_buscado = tx.get().strip()
        if trabajador_buscado == "":
            msg = "Ingrese el nombre del trabajador antes de continuar."
            Notifica.config(text=msg, fg=WARNING_COLOR, bg=SECONDARY_BG)
            text_to_speech("Ingrese el nombre del trabajador.")
            return

        if not os.path.exists(trainimagelabel_path):
            msg = (
                "Modelo de reconocimiento no encontrado.\n"
                "Primero debe entrenar el modelo desde el módulo de registro."
            )
            Notifica.config(text=msg, fg=ERROR_COLOR, bg=SECONDARY_BG)
            text_to_speech("Modelo no encontrado. Entrena primero.")
            return

        try:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.read(trainimagelabel_path)
            face_cascade = cv2.CascadeClassifier(haarcasecade_path)

            if not os.path.exists(studentdetail_path):
                msg = "No hay trabajadores registrados. Registre al menos uno primero."
                Notifica.config(text=msg, fg=ERROR_COLOR, bg=SECONDARY_BG)
                text_to_speech("No hay trabajadores registrados.")
                return

            df_students = pd.read_csv(studentdetail_path, dtype=str)
            df_students["Enrollment"] = df_students["Enrollment"].astype(str)

            # Asegurar columnas por si el CSV es antiguo
            for col in ["EPP_CASCO_CODE", "EPP_CHALECO_CODE"]:
                if col not in df_students.columns:
                    df_students[col] = ""

            # Verificar que el trabajador existe por nombre
            trabajador_existe = df_students["Name"].str.lower().str.contains(
                trabajador_buscado.lower()
            ).any()
            if not trabajador_existe:
                msg = (
                    f"Trabajador '{trabajador_buscado}' no encontrado en la base de datos.\n"
                    "Verifique el nombre y vuelva a intentarlo."
                )
                Notifica.config(text=msg, fg=ERROR_COLOR, bg=SECONDARY_BG)
                text_to_speech(msg)
                print("\n❌", msg)
                print("\nTrabajadores registrados:")
                for idx, row in df_students.iterrows():
                    print(f"  - {row['Name']} (ID: {row['Enrollment']})")
                return

            today = datetime.datetime.now().strftime("%Y-%m-%d")
            today_file = os.path.join(attendance_base, f"asistencia_{today}.csv")

            if os.path.exists(today_file):
                prev_attendance = pd.read_csv(today_file, dtype=str)
            else:
                prev_attendance = pd.DataFrame(
                    columns=["Enrollment", "Name", "Date", "Time", "Status"]
                )

            cam = cv2.VideoCapture(0)
            if not cam.isOpened():
                msg = "No se pudo abrir la cámara. Verifique la conexión."
                Notifica.config(text=msg, fg=ERROR_COLOR, bg=SECONDARY_BG)
                text_to_speech("No se pudo abrir la cámara.")
                return

            cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            interfaz = InterfazAsistenciaEPP()
            start_time = time.time()
            capture_duration = 10  # segundos
            new_rows = []

            print("\n" + "=" * 60)
            print("INICIANDO CAPTURA DE ASISTENCIA")
            print("=" * 60)
            print(f"Trabajador buscado: {trabajador_buscado}")
            print(f"Duración: {capture_duration} segundos")
            print(f"Detector EPP: ACTIVO (Color + Forma)")
            print(f"Solo se registrará: {trabajador_buscado}")
            print("=" * 60 + "\n")

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

                # Detectar EPP SIEMPRE en cada frame
                epp_results = verify_epp(frame)

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

                            # Si no es el trabajador que buscamos, solo mostramos info
                            if trabajador_buscado.lower() not in name.lower():
                                info_trabajador = {
                                    "nombre": f"{name} (NO ES {trabajador_buscado})",
                                    "id": Id_str,
                                    "tiene_rostro": True,
                                    "bbox_rostro": (x, y, w, h),
                                }
                                print(
                                    f"⚠️  Detectado: {name} - NO es el trabajador buscado"
                                )
                                continue

                            # Es el trabajador correcto
                            info_trabajador = {
                                "nombre": name,
                                "id": Id_str,
                                "tiene_rostro": True,
                                "bbox_rostro": (x, y, w, h),
                            }

                            # Verificar EPP usando el resultado calculado arriba
                            tiene_casco = any(
                                "casco" in str(r[0]).lower() for r in epp_results
                            )
                            tiene_chaleco = any(
                                "chaleco" in str(r[0]).lower() for r in epp_results
                            )
                            has_epp = tiene_casco and tiene_chaleco

                            if has_epp:
                                timeStamp = datetime.datetime.now().strftime("%H:%M:%S")
                                today = datetime.datetime.now().strftime("%Y-%m-%d")

                                records_today = prev_attendance.loc[
                                    prev_attendance["Enrollment"] == Id_str
                                ]
                                if len(new_rows):
                                    records_today = pd.concat(
                                        [records_today, pd.DataFrame(new_rows)],
                                        ignore_index=True,
                                    )

                                # Lógica Entrada / Salida
                                if records_today.empty:
                                    status = "Entrada"
                                elif (
                                    len(records_today) == 1
                                    and records_today.iloc[0]["Status"] == "Entrada"
                                ):
                                    status = "Salida"
                                else:
                                    status = None

                                if status:
                                    already_in_new = any(
                                        r["Enrollment"] == Id_str
                                        and r["Status"] == status
                                        for r in new_rows
                                    )
                                    if not already_in_new:
                                        row = {
                                            "Enrollment": Id_str,
                                            "Name": name,
                                            "Date": today,
                                            "Time": timeStamp,
                                            "Status": status,
                                        }
                                        new_rows.append(row)
                                        print(
                                            f"✅ {name} - {status} - {timeStamp} (EPP OK)"
                                        )
                                        text_to_speech(
                                            f"{name} {status} registrada correctamente"
                                        )
                                        trabajador_registrado = True
                            else:
                                print(
                                    f"⚠️  {name} detectado pero sin EPP completo (casco+chaleco)"
                                )

                # Dibujar overlay de interfaz (barra inferior, estado, etc.)
                frame = interfaz.dibujar_interfaz_completa(
                    frame,
                    info_trabajador,
                    epp_results,
                    tiempo_restante=tiempo_restante,
                )

                cv2.imshow(window_name, frame)

                if time.time() - start_time > capture_duration:
                    break
                if cv2.waitKey(1) & 0xFF == 27:   # ESC para salir
                    break

            cam.release()
            cv2.destroyAllWindows()

            # Guardar asistencia
            if len(new_rows):
                appended = pd.concat(
                    [prev_attendance, pd.DataFrame(new_rows)], ignore_index=True
                )
            else:
                appended = prev_attendance

            appended.drop_duplicates(
                subset=["Enrollment", "Date", "Status"], keep="first", inplace=True
            )
            appended.to_csv(today_file, index=False)

            print("\n" + "=" * 60)
            if trabajador_registrado:
                print("✅ ASISTENCIA REGISTRADA")
                print(f"Trabajador: {trabajador_buscado}")
                print(f"Registros: {len(new_rows)}")
            else:
                print("⚠️  NO SE REGISTRÓ ASISTENCIA")
                print(
                    f"Trabajador '{trabajador_buscado}' no detectado o sin EPP completo"
                )
            print(f"Archivo: {today_file}")
            print("=" * 60 + "\n")

            msg = f"Asistencia: {len(new_rows)} registro(s) para {trabajador_buscado}"
            if trabajador_registrado:
                Notifica.config(text=msg, fg=ACCENT, bg=SECONDARY_BG)
                text_to_speech(msg)
                open_file(today_file)
            else:
                Notifica.config(text=msg, fg=WARNING_COLOR, bg=SECONDARY_BG)
                text_to_speech(
                    f"No se registró asistencia para {trabajador_buscado}."
                )

        except Exception as e:
            error_msg = f"Error en la captura de asistencia: {str(e)}"
            Notifica.config(text=error_msg, fg=ERROR_COLOR, bg=SECONDARY_BG)
            text_to_speech(error_msg)
            print("ERROR:", error_msg)
            try:
                cam.release()
                cv2.destroyAllWindows()
            except Exception:
                pass

    # =============================
    # CREACIÓN DE VENTANA (Toplevel o Tk)
    # =============================

    root = tk._default_root
    if root is None:
        subject = tk.Tk()
        is_standalone = True
    else:
        subject = tk.Toplevel(root)
        is_standalone = False

    subject.title("Registrar asistencia con EPP")
    subject.geometry("800x480")
    subject.minsize(720, 420)
    subject.configure(background=PRIMARY_BG)
    fade_in_window(subject)

    # CONTENEDOR PRINCIPAL
    container = tk.Frame(subject, bg=PRIMARY_BG)
    container.pack(expand=True, fill="both", padx=30, pady=30)

    # HEADER
    header = tk.Frame(container, bg=PRIMARY_BG)
    header.pack(fill="x", pady=(0, 15))

    tk.Label(
        header,
        text="Registrar asistencia individual",
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 22),
    ).pack(anchor="w")

    tk.Label(
        header,
        text=(
            "Escriba el nombre del trabajador tal como está registrado.\n"
            "El sistema solo registrará asistencia si detecta al trabajador correcto "
            "con casco y chaleco."
        ),
        bg=PRIMARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10),
        justify="left",
        wraplength=720,
    ).pack(anchor="w", pady=(6, 0))

    # TARJETA CENTRAL
    card = tk.Frame(container, bg=SECONDARY_BG, bd=0, relief="flat")
    card.pack(fill="both", expand=True, pady=(10, 0))

    form = tk.Frame(card, bg=SECONDARY_BG)
    form.pack(fill="x", padx=30, pady=(25, 10))

    tk.Label(
        form,
        text="Nombre del trabajador",
        bg=SECONDARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI", 11, "bold"),
    ).grid(row=0, column=0, sticky="w", pady=(0, 3))

    tx = tk.Entry(
        form,
        width=24,
        bd=0,
        font=("Segoe UI", 16, "bold"),
        bg="#020617",
        fg=TEXT_PRIMARY,
        insertbackground=TEXT_PRIMARY,
        relief="flat",
    )
    tx.grid(row=1, column=0, sticky="we", pady=(0, 8), ipady=4)
    tk.Frame(form, bg=ACCENT_SECONDARY, height=2).grid(
        row=2, column=0, sticky="we", pady=(0, 5)
    )

    tk.Label(
        form,
        text="Ejemplo: Juan Pérez / María López (no es sensible a mayúsculas).",
        bg=SECONDARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 9),
    ).grid(row=3, column=0, sticky="w")

    # Breve texto de ayuda
    status_text = tk.Label(
        card,
        text="El sistema realizará una captura de 10 segundos usando la cámara.",
        bg=SECONDARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 9),
        justify="left",
        wraplength=720,
    )
    status_text.pack(anchor="w", padx=30, pady=(10, 0))

    # Mensaje de notificación (errores / resumen)
    Notifica = tk.Label(
        card,
        text="",
        bg=SECONDARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10, "bold"),
        justify="left",
        wraplength=720,
    )
    Notifica.pack(anchor="w", padx=30, pady=(8, 5))

    # BOTONES INFERIORES
    buttons_frame = tk.Frame(card, bg=SECONDARY_BG)
    buttons_frame.pack(fill="x", padx=30, pady=(20, 25))

    btn_registrar = tk.Button(
        buttons_frame,
        text="▶ Iniciar captura de asistencia",
        command=FillAttendance,
        bg=ACCENT,
        fg="black",
        activebackground="#4ade80",
        activeforeground="black",
        font=("Segoe UI Semibold", 12),
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=24,
        pady=10,
    )
    btn_registrar.pack(side="left")

    def cerrar_ventana():
        subject.destroy()

    btn_cerrar = tk.Button(
        buttons_frame,
        text="Cerrar",
        command=cerrar_ventana,
        bg=SECONDARY_BG,
        fg=TEXT_SECONDARY,
        activebackground="#111827",
        activeforeground=TEXT_PRIMARY,
        font=("Segoe UI", 10),
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=18,
        pady=8,
    )
    btn_cerrar.pack(side="right")

    if is_standalone:
        subject.mainloop()


# ==============================
# EJECUCIÓN DIRECTA
# ==============================

if __name__ == "__main__":
    subjectChoose()
