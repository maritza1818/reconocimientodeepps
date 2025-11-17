# automaticAttendance.py
# Versión integrada:
# - Zona / área seleccionable
# - Modo forzado (demo)
# - MODO EPP ESTRICTO:
#     • rostro reconocido
#     • casco + chaleco detectados (color)
#     • código de chaleco asignado al trabajador
# - Historial de intentos en la UI
# - Registro de asistencia e intentos en CSV
# - Reloj en ventana
# - Lectura de códigos de barras / QR

from epp_detector_integrado import verify_epp
from interfaz_asistencia_epp import InterfazAsistenciaEPP

import tkinter as tk
from tkinter import ttk

import os
import cv2
import pandas as pd
import datetime
import time
import subprocess
import platform

from pyzbar.pyzbar import decode

# ==============================
# RUTAS Y CARPETAS
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

haarcasecade_path = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")
trainimagelabel_path = os.path.join(BASE_DIR, "TrainingImageLabel", "Trainner.yml")
studentdetail_path = os.path.join(BASE_DIR, "StudentDetails", "studentdetails.csv")
attendance_base = os.path.join(BASE_DIR, "Attendance")
epp_registry_path = os.path.join(BASE_DIR, "EPP", "epp_registry.csv")

os.makedirs(attendance_base, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "EPP"), exist_ok=True)


# ==============================
# PALETA DE COLORES
# ==============================

PRIMARY_BG = "#020617"        # Fondo principal ventana
CARD_BG = "#0f172a"           # Tarjeta interior
TEXT_PRIMARY = "#e5e7eb"
TEXT_SECONDARY = "#9ca3af"
ACCENT = "#22c55e"
ACCENT_SECONDARY = "#38bdf8"
WARNING_COLOR = "#facc15"
ERROR_COLOR = "#f97373"


# ==============================
# UTILIDADES
# ==============================

def text_to_speech(message: str):
    """Texto a voz simple en Linux (espeak) + print de respaldo."""
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


def open_file(filepath: str):
    """Abre un archivo con la aplicación por defecto según el sistema operativo."""
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(filepath)  # type: ignore[attr-defined]
        elif system == "Darwin":
            subprocess.run(["open", filepath], check=False)
        else:
            subprocess.run(["xdg-open", filepath], check=False)
    except Exception:
        print(f"[INFO] Archivo guardado en: {filepath}")


def leer_csv_seguro(path, columnas=None):
    """
    Lee un CSV y si no existe o está vacío, devuelve un DataFrame con las columnas dadas.
    """
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        if columnas is None:
            return pd.DataFrame()
        return pd.DataFrame(columns=columnas)
    try:
        df = pd.read_csv(path, dtype=str)
        if columnas is not None:
            for c in columnas:
                if c not in df.columns:
                    df[c] = ""
            df = df[columnas]
        return df
    except Exception:
        if columnas is None:
            return pd.DataFrame()
        return pd.DataFrame(columns=columnas)


def load_epp_registry():
    """
    Carga el registro de EPP (chalecos, cascos, etc.).
    Espera columnas: Barcode, EPP_Type, Enrollment, Name, Active
    """
    cols = ["Barcode", "EPP_Type", "Enrollment", "Name", "Active"]
    df = leer_csv_seguro(epp_registry_path, cols)
    if df.empty:
        return df
    df["Barcode"] = df["Barcode"].fillna("").str.upper().str.replace(" ", "")
    df["Enrollment"] = df["Enrollment"].astype(str)
    df["Active"] = df["Active"].fillna("1").astype(str)
    return df


def save_attempt_log(row_dict):
    """
    Guarda un intento (exitoso o fallido) en intentos_YYYY-MM-DD.csv
    """
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    intentos_file = os.path.join(attendance_base, f"intentos_{today}.csv")

    cols = [
        "Enrollment",
        "Name",
        "Date",
        "Time",
        "Status",
        "Reason",
        "Zone",
        "EPP_Color",
        "EPP_Code",
        "EPP_Code_Source",
    ]

    df = leer_csv_seguro(intentos_file, cols)
    df = pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)
    df.to_csv(intentos_file, index=False)


def parse_epp_results(epp_results, min_casco=0.65, min_chaleco=0.65):
    """
    A partir de los resultados de verify_epp(frame), devuelve:
      (tiene_casco, tiene_chaleco) considerando probabilidad si está disponible.
    """
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
            except Exception:
                score = 1.0

        if ("casco" in label or "helmet" in label) and score >= min_casco:
            tiene_casco = True
        if ("chaleco" in label or "vest" in label) and score >= min_chaleco:
            tiene_chaleco = True

    return tiene_casco, tiene_chaleco


# ==============================
# VENTANA PRINCIPAL
# ==============================

def subjectChoose():
    """
    Ventana de registro de asistencia individual con:
      - selección de zona
      - modo forzado (demo)
      - verificación estricta de EPP
      - historial de intentos
    """

    # Detectamos si ya existe una raíz Tk
    root = tk._default_root
    if root is None:
        subject = tk.Tk()
        standalone = True
    else:
        subject = tk.Toplevel(root)
        standalone = False

    subject.title("Registrar Asistencia con EPP")
    subject.geometry("900x560")
    subject.minsize(840, 520)
    subject.configure(background=PRIMARY_BG)

    # ---------- CABECERA ----------
    header = tk.Frame(subject, bg=PRIMARY_BG)
    header.pack(fill="x", padx=24, pady=(18, 6))

    titulo = tk.Label(
        header,
        text="Registrar asistencia individual",
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 20),
        anchor="w",
    )
    titulo.pack(side="left", anchor="w")

    lbl_clock = tk.Label(
        header,
        text="",
        bg=PRIMARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10, "bold"),
        anchor="e",
    )
    lbl_clock.pack(side="right")

    def actualizar_reloj():
        if not subject.winfo_exists():
            return
        ahora = datetime.datetime.now()
        lbl_clock.config(text=ahora.strftime("%d/%m/%Y   %H:%M:%S"))
        try:
            subject.after(1000, actualizar_reloj)
        except tk.TclError:
            pass

    actualizar_reloj()

    # ---------- TARJETA PRINCIPAL ----------
    card = tk.Frame(subject, bg=CARD_BG, bd=0, relief="flat")
    card.pack(fill="both", expand=True, padx=24, pady=(0, 18))

    # Estado general
    estado_label = tk.Label(
        card,
        text="Listo para registrar asistencia.",
        bg=CARD_BG,
        fg=ACCENT,
        font=("Segoe UI Semibold", 12),
        anchor="w",
        wraplength=820,
        justify="left",
    )
    estado_label.pack(fill="x", padx=18, pady=(16, 2))

    motivo_label = tk.Label(
        card,
        text="",
        bg=CARD_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 9),
        anchor="w",
        wraplength=820,
        justify="left",
    )
    motivo_label.pack(fill="x", padx=18, pady=(0, 10))

    # ---------- FORMULARIO ----------
    form = tk.Frame(card, bg=CARD_BG)
    form.pack(fill="x", padx=18, pady=(8, 4))

    # Nombre del trabajador
    name_lbl = tk.Label(
        form,
        text="Nombre del trabajador:",
        bg=CARD_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI", 10, "bold"),
    )
    name_lbl.grid(row=0, column=0, sticky="w")

    tx = tk.Entry(
        form,
        width=26,
        bd=0,
        font=("Segoe UI", 15, "bold"),
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        insertbackground=TEXT_PRIMARY,
        relief="flat",
    )
    tx.grid(row=1, column=0, sticky="we", pady=(2, 4), ipady=4)
    form.columnconfigure(0, weight=1)

    underline = tk.Frame(form, bg=ACCENT_SECONDARY, height=2)
    underline.grid(row=2, column=0, sticky="we", pady=(0, 8))

    # Zona / área
    zone_lbl = tk.Label(
        form,
        text="Zona / área:",
        bg=CARD_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI", 10, "bold"),
    )
    zone_lbl.grid(row=0, column=1, sticky="w", padx=(28, 0))

    zonas_disponibles = [
        "Portón principal",
        "Almacén",
        "Taller",
        "Oficina",
        "Laboratorio",
        "General",
    ]
    zona_var = tk.StringVar(value=zonas_disponibles[0])

    zona_combo = ttk.Combobox(
        form,
        textvariable=zona_var,
        values=zonas_disponibles,
        state="readonly",
        font=("Segoe UI", 10),
    )
    zona_combo.grid(row=1, column=1, sticky="we", padx=(28, 0), pady=(2, 4))
    form.columnconfigure(1, weight=1)

    # Check de modo demo (forzado)
    force_var = tk.BooleanVar(value=False)
    force_chk = tk.Checkbutton(
        card,
        text="Permitir registro aunque falte EPP (modo demo)",
        variable=force_var,
        bg=CARD_BG,
        fg=TEXT_SECONDARY,
        activebackground=CARD_BG,
        activeforeground=TEXT_PRIMARY,
        selectcolor=PRIMARY_BG,
        font=("Segoe UI", 9),
        anchor="w",
        justify="left",
        wraplength=820,
    )
    force_chk.pack(anchor="w", padx=18, pady=(2, 6))

    # ---------- PARTE INFERIOR: HISTORIAL + BOTONES ----------
    bottom = tk.Frame(card, bg=CARD_BG)
    bottom.pack(fill="both", expand=True, padx=18, pady=(8, 12))

    # Historial
    hist_frame = tk.Frame(bottom, bg=CARD_BG)
    hist_frame.pack(side="left", fill="both", expand=True)

    historial_title = tk.Label(
        hist_frame,
        text="Últimos intentos:",
        bg=CARD_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 10),
        anchor="w",
    )
    historial_title.pack(anchor="w", pady=(0, 4))

    hist_list_frame = tk.Frame(hist_frame, bg=CARD_BG)
    hist_list_frame.pack(fill="both", expand=True)

    historial_list = tk.Listbox(
        hist_list_frame,
        width=60,
        height=9,
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        font=("Consolas", 9),
        borderwidth=0,
        highlightthickness=0,
        selectbackground="#1e293b",
        selectforeground=TEXT_PRIMARY,
    )
    historial_list.pack(side="left", fill="both", expand=True)

    hist_scroll = tk.Scrollbar(hist_list_frame, command=historial_list.yview)
    hist_scroll.pack(side="right", fill="y")
    historial_list.config(yscrollcommand=hist_scroll.set)

    # Botones
    buttons_frame = tk.Frame(bottom, bg=CARD_BG)
    buttons_frame.pack(side="right", fill="y", padx=(16, 0))

    def set_estado(titulo, detalle="", color=ACCENT):
        estado_label.config(text=titulo, fg=color)
        motivo_label.config(text=detalle)

    def agregar_historial(nombre, texto):
        ahora = datetime.datetime.now().strftime("%H:%M:%S")
        historial_list.insert(0, f"{ahora} | {nombre} | {texto}")

    # ========== LÓGICA DE ASISTENCIA ==========
    def FillAttendance():
        trabajador_buscado = tx.get().strip()
        zona_actual = zona_var.get().strip() or "General"

        set_estado("Procesando...", "Abriendo cámara y modelo...", WARNING_COLOR)

        if trabajador_buscado == "":
            set_estado(
                "NO REGISTRADO",
                "Ingrese el nombre del trabajador antes de iniciar.",
                ERROR_COLOR,
            )
            text_to_speech("Ingrese el nombre del trabajador.")
            return

        if not os.path.exists(trainimagelabel_path):
            set_estado(
                "NO REGISTRADO",
                "Modelo de reconocimiento no encontrado. Entrene primero el modelo.",
                ERROR_COLOR,
            )
            text_to_speech("Modelo no encontrado. Entrene primero.")
            return

        # Cargamos modelo y datos
        cam = None
        try:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.read(trainimagelabel_path)
            face_cascade = cv2.CascadeClassifier(haarcasecade_path)

            # Trabajadores
            df_students = leer_csv_seguro(studentdetail_path, ["Enrollment", "Name"])
            if df_students.empty:
                set_estado(
                    "NO REGISTRADO",
                    "No hay trabajadores registrados todavía.",
                    ERROR_COLOR,
                )
                text_to_speech("No hay trabajadores registrados.")
                return

            df_students["Enrollment"] = df_students["Enrollment"].astype(str)

            existe = df_students["Name"].str.lower().str.contains(
                trabajador_buscado.lower()
            ).any()
            if not existe:
                set_estado(
                    "NO REGISTRADO",
                    f"Trabajador '{trabajador_buscado}' no existe en la base de datos.",
                    ERROR_COLOR,
                )
                agregar_historial("Sistema", "Intento con trabajador inexistente")
                text_to_speech("Trabajador no encontrado.")
                return

            # Registro de EPP (chalecos, etc.)
            epp_registry_df = load_epp_registry()

            # Archivo de asistencia del día
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
                "EPP_Color",
                "EPP_Code",
                "EPP_Code_Source",
            ]
            prev_attendance = leer_csv_seguro(today_file, cols_asistencia)

            # Abrimos cámara
            cam = cv2.VideoCapture(0)
            if not cam.isOpened():
                set_estado("ERROR", "No se pudo abrir la cámara.", ERROR_COLOR)
                text_to_speech("No se pudo abrir la cámara.")
                return

            cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            interfaz = InterfazAsistenciaEPP()
            start_time = time.time()
            capture_duration = 10  # segundos

            new_rows = []
            attempts_rows = []
            trabajador_registrado = False

            window_name = "Asistencia con EPP"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, 1280, 720)

            while True:
                ret, frame = cam.read()
                if not ret:
                    break

                tiempo_restante = int(capture_duration - (time.time() - start_time))
                if tiempo_restante < 0:
                    tiempo_restante = 0

                info_trabajador = None
                epp_results = verify_epp(frame)
                tiene_casco, tiene_chaleco_color = parse_epp_results(epp_results)

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.2, 5)

                for (x, y, w, h) in faces:
                    face_roi = gray[y : y + h, x : x + w]
                    Id, conf = recognizer.predict(face_roi)
                    if conf >= 70:
                        continue

                    Id_str = str(Id)
                    match = df_students.loc[df_students["Enrollment"] == Id_str, "Name"]
                    if match.empty:
                        continue

                    name = match.values[0]

                    # Si el rostro NO es del trabajador buscado: solo lo anotamos como intento
                    if trabajador_buscado.lower() not in name.lower():
                        info_trabajador = {
                            "nombre": f"{name} (NO ES {trabajador_buscado})",
                            "id": Id_str,
                            "tiene_rostro": True,
                            "bbox_rostro": (x, y, w, h),
                        }

                        attempts_rows.append(
                            {
                                "Enrollment": Id_str,
                                "Name": name,
                                "Date": today,
                                "Time": datetime.datetime.now().strftime("%H:%M:%S"),
                                "Status": "NO_REGISTRADO",
                                "Reason": "No era el trabajador solicitado",
                                "Zone": zona_actual,
                                "EPP_Color": "",
                                "EPP_Code": "",
                                "EPP_Code_Source": "",
                            }
                        )
                        agregar_historial(name, "Detectado pero no es la persona solicitada")
                        continue

                    # Aquí SÍ es el trabajador correcto
                    info_trabajador = {
                        "nombre": name,
                        "id": Id_str,
                        "tiene_rostro": True,
                        "bbox_rostro": (x, y, w, h),
                    }

                    # Leemos códigos de barras / QR del frame
                    barcodes = decode(frame)
                    codigo_chaleco_match = None
                    epp_code_source = ""

                    for b in barcodes:
                        code_raw = b.data.decode("utf-8").strip()
                        code_norm = code_raw.upper().replace(" ", "")

                        # Dibujamos el rectángulo para feedback visual
                        (bx, by, bw, bh) = b.rect
                        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 255, 255), 2)
                        cv2.putText(
                            frame,
                            code_raw,
                            (bx, by - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 255, 255),
                            1,
                        )

                        if not epp_registry_df.empty:
                            match_code = epp_registry_df[
                                (epp_registry_df["Barcode"] == code_norm)
                                & (epp_registry_df["Active"].astype(str) != "0")
                            ]
                        else:
                            match_code = pd.DataFrame()

                        if match_code.empty:
                            # código no registrado -> no lo contamos como fallo de EPP,
                            # pero lo dejamos pasar para seguir revisando otros códigos
                            continue

                        tipo_epp = match_code["EPP_Type"].iloc[0].lower()
                        epp_owner = str(match_code["Enrollment"].iloc[0])

                        # SOLO chaleco del dueño
                        if "chaleco" in tipo_epp and epp_owner == Id_str:
                            codigo_chaleco_match = code_norm
                            epp_code_source = "barcode"

                    tiene_chaleco_codigo = codigo_chaleco_match is not None

                    # Reglas de EPP estricto
                    epp_ok = (
                        tiene_casco and tiene_chaleco_color and tiene_chaleco_codigo
                    )

                    motivos_fallo = []
                    if not tiene_casco:
                        motivos_fallo.append("sin casco")
                    if not tiene_chaleco_color:
                        motivos_fallo.append("sin chaleco visible")
                    if not tiene_chaleco_codigo:
                        motivos_fallo.append("chaleco no coincide con el trabajador")

                    reason_str = ""
                    if motivos_fallo:
                        reason_str = ", ".join(motivos_fallo)

                    # Momento actual
                    timeStamp = datetime.datetime.now().strftime("%H:%M:%S")

                    # Revisamos registros previos del día para saber si es Entrada o Salida
                    records_today = prev_attendance.loc[
                        prev_attendance["Enrollment"] == Id_str
                    ]
                    status = "Entrada"
                    if not records_today.empty:
                        # Si ya tiene una Entrada sin Salida, ahora será Salida
                        if (records_today["Status"] == "Entrada").any() and not (
                            records_today["Status"] == "Salida"
                        ).any():
                            status = "Salida"

                    # Decisión final
                    if epp_ok or force_var.get():
                        # Creamos fila de asistencia
                        row = {
                            "Enrollment": Id_str,
                            "Name": name,
                            "Date": today,
                            "Time": timeStamp,
                            "Status": status,
                            "Reason": "" if epp_ok else f"FORZADO ({reason_str})",
                            "Zone": zona_actual,
                            "EPP_Color": f"casco={tiene_casco}, chaleco={tiene_chaleco_color}",
                            "EPP_Code": codigo_chaleco_match or "",
                            "EPP_Code_Source": epp_code_source,
                        }
                        new_rows.append(row)

                        # Intento
                        attempts_rows.append(row.copy())

                        trabajador_registrado = True

                        msj_estado = f"{name} - {status} registrada en zona {zona_actual}"
                        if not epp_ok and force_var.get():
                            msj_estado += " (modo forzado)"

                        set_estado("REGISTRADO", msj_estado, ACCENT)
                        agregar_historial(name, msj_estado)
                        text_to_speech(f"Asistencia de {name} registrada correctamente.")
                    else:
                        # No cumple EPP y no estamos en modo forzado
                        attempts_rows.append(
                            {
                                "Enrollment": Id_str,
                                "Name": name,
                                "Date": today,
                                "Time": timeStamp,
                                "Status": "RECHAZADO",
                                "Reason": reason_str,
                                "Zone": zona_actual,
                                "EPP_Color": f"casco={tiene_casco}, chaleco={tiene_chaleco_color}",
                                "EPP_Code": codigo_chaleco_match or "",
                                "EPP_Code_Source": epp_code_source,
                            }
                        )
                        set_estado(
                            "EPP INCOMPLETO",
                            f"No se pudo registrar a {name}: {reason_str}",
                            ERROR_COLOR,
                        )
                        agregar_historial(name, f"Fallo EPP: {reason_str}")
                        text_to_speech(
                            f"No se pudo registrar a {name} por E P P incompleto."
                        )

                # Dibujamos interfaz overlay
                frame = interfaz.dibujar_interfaz_completa(
                    frame,
                    info_trabajador,
                    epp_results,
                    tiempo_restante=tiempo_restante,
                )
                cv2.imshow(window_name, frame)

                # Integramos con Tk
                try:
                    subject.update_idletasks()
                    subject.update()
                except tk.TclError:
                    break

                if time.time() - start_time > capture_duration:
                    break
                if cv2.waitKey(1) & 0xFF == 27:
                    break

            # Guardamos asistencia del día
            if len(new_rows):
                appended = pd.concat(
                    [prev_attendance, pd.DataFrame(new_rows)], ignore_index=True
                )
            else:
                appended = prev_attendance

            appended.drop_duplicates(
                subset=["Enrollment", "Date", "Status"],
                keep="first",
                inplace=True,
            )
            appended.to_csv(today_file, index=False)

            # Guardamos intentos
            for r in attempts_rows:
                save_attempt_log(r)

            if trabajador_registrado:
                set_estado(
                    "ASISTENCIA REGISTRADA",
                    f"Se registró al menos un evento para '{trabajador_buscado}'.",
                    ACCENT,
                )
                open_file(today_file)
            else:
                set_estado(
                    "SIN REGISTROS",
                    f"No se registró asistencia para '{trabajador_buscado}'.",
                    WARNING_COLOR,
                )

        except Exception as e:
            set_estado("ERROR", f"Error en la captura de asistencia: {str(e)}", ERROR_COLOR)
            text_to_speech("Ocurrió un error en la captura de asistencia.")
        finally:
            try:
                if cam is not None and cam.isOpened():
                    cam.release()
                cv2.destroyAllWindows()
            except Exception:
                pass

    # Botón principal
    btn_reg = tk.Button(
        buttons_frame,
        text="▶ Iniciar captura",
        command=FillAttendance,
        bg=ACCENT,
        fg="black",
        activebackground="#4ade80",
        activeforeground="black",
        font=("Segoe UI Semibold", 12),
        bd=0,
        padx=20,
        pady=10,
        cursor="hand2",
    )
    btn_reg.pack(pady=(10, 6), fill="x")

    def limpiar():
        tx.delete(0, "end")
        set_estado("Listo para registrar asistencia.", "", ACCENT)
        agregar_historial("Sistema", "Campos limpiados")

    btn_retry = tk.Button(
        buttons_frame,
        text="Limpiar / Nuevo intento",
        command=limpiar,
        bg=CARD_BG,
        fg=TEXT_SECONDARY,
        activebackground="#111827",
        activeforeground=TEXT_PRIMARY,
        font=("Segoe UI", 10),
        bd=0,
        padx=14,
        pady=8,
        cursor="hand2",
    )
    btn_retry.pack(pady=(0, 6), fill="x")

    def cerrar():
        subject.destroy()

    btn_close = tk.Button(
        buttons_frame,
        text="Cerrar",
        command=cerrar,
        bg="#b91c1c",
        fg="white",
        activebackground="#991b1b",
        activeforeground="white",
        font=("Segoe UI", 10, "bold"),
        bd=0,
        padx=14,
        pady=8,
        cursor="hand2",
    )
    btn_close.pack(pady=(6, 0), fill="x")

    if standalone:
        subject.mainloop()


# ==============================
# EJECUCIÓN DIRECTA
# ==============================

if __name__ == "__main__":
    subjectChoose()
