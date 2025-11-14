# attendance.py (main) - UI REDISEÑADA CON ANIMACIONES Y DASHBOARD MODERNO

import tkinter as tk
from tkinter import *
import os, cv2, csv
from PIL import ImageTk, Image
import pyttsx3

import show_attendance
import takeImage
import trainImage
import automaticAttendance
from epp_detector_integrado import generar_codigo_epp  # ✅ IMPORT EPP

# ==============================
# CONFIGURACIÓN GLOBAL / ESTILO
# ==============================

# Paleta de colores (tema oscuro moderno)
PRIMARY_BG = "#020617"      # Fondo principal (casi negro)
SECONDARY_BG = "#0f172a"    # Tarjetas / paneles
ACCENT = "#22c55e"          # Verde principal
ACCENT_HOVER = "#4ade80"    # Verde claro hover
ACCENT_SECONDARY = "#38bdf8"  # Azul cian
TEXT_PRIMARY = "#e5e7eb"    # Texto principal
TEXT_SECONDARY = "#9ca3af"  # Texto secundario
WARNING_COLOR = "#facc15"   # Amarillo
ERROR_COLOR = "#f97373"     # Rojo suave
BTN_BG = "#111827"          # Fondo de botones
BTN_FG = TEXT_PRIMARY

DEFAULT_STATUS = "Coloca el cursor sobre un botón para ver su descripción."

# ==============================
# UTILIDAD: TEXTO A VOZ
# ==============================

def text_to_speech(user_text):
    """Texto a voz con manejo de errores"""
    try:
        engine = pyttsx3.init()
        engine.say(user_text)
        engine.runAndWait()
    except Exception:
        # Si falla, solo imprime en consola
        print(f"[TTS] {user_text}")

# ==============================
# RUTAS Y PREPARACIÓN DE CARPETAS
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
haarcasecade_path = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")
trainimagelabel_path = os.path.join(BASE_DIR, "TrainingImageLabel", "Trainner.yml")
trainimage_path = os.path.join(BASE_DIR, "TrainingImage")
studentdetail_path = os.path.join(BASE_DIR, "StudentDetails", "studentdetails.csv")
attendance_path = os.path.join(BASE_DIR, "Attendance")

# Crear directorios necesarios
os.makedirs(trainimage_path, exist_ok=True)
os.makedirs(os.path.dirname(trainimagelabel_path), exist_ok=True)
os.makedirs(os.path.dirname(studentdetail_path), exist_ok=True)
os.makedirs(attendance_path, exist_ok=True)

# Crear CSV si no existe
if not os.path.exists(studentdetail_path):
    with open(studentdetail_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Enrollment", "Name"])

# ==============================
# FUNCIONES DE APOYO UI
# ==============================

def err_screen():
    """Ventana de error básica para campos vacíos"""
    sc1 = tk.Toplevel()
    sc1.title("Advertencia")
    sc1.geometry("420x140")
    sc1.configure(background=PRIMARY_BG)
    sc1.resizable(0, 0)
    # Animación fade-in
    sc1.attributes("-alpha", 0.0)

    def fade_in(alpha=0.0):
        if alpha < 1.0:
            sc1.attributes("-alpha", alpha)
            sc1.after(25, fade_in, alpha + 0.08)

    fade_in()

    tk.Label(
        sc1,
        text="⚠ Código y nombre son requeridos",
        fg=WARNING_COLOR,
        bg=PRIMARY_BG,
        font=("Segoe UI", 13, "bold")
    ).pack(pady=(20, 10))

    tk.Button(
        sc1,
        text="Entendido",
        command=sc1.destroy,
        fg=TEXT_PRIMARY,
        bg=BTN_BG,
        activebackground=ACCENT,
        activeforeground="black",
        bd=0,
        relief="flat",
        cursor="hand2",
        font=("Segoe UI", 11, "bold"),
        padx=20,
        pady=6
    ).pack()


def testVal(inStr, acttyp):
    """Validación para solo números en entradas de ID"""
    if acttyp == "1":  # insert
        return inStr.isdigit() or inStr == ""
    return True


def apply_button_hover_effect(btn, status_label, text_status):
    """
    Aplica efecto hover a un botón y actualiza la barra de estado.
    """
    def on_enter(e):
        btn.config(bg=ACCENT, fg="black")
        status_label.config(text=text_status, fg=ACCENT_SECONDARY)

    def on_leave(e):
        btn.config(bg=BTN_BG, fg=BTN_FG)
        status_label.config(text=DEFAULT_STATUS, fg=TEXT_SECONDARY)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)


def fade_in_window(win):
    """Animación de aparición suave (alpha de 0 a 1) para Toplevel."""
    try:
        win.attributes("-alpha", 0.0)
    except Exception:
        return  # Puede fallar en algunos sistemas; ignorar

    def _fade(alpha=0.0):
        if alpha < 1.0:
            try:
                win.attributes("-alpha", alpha)
            except Exception:
                return
            win.after(25, _fade, alpha + 0.08)

    _fade()


# ==============================
# SUBVENTANA: REGISTRO DE TRABAJADOR
# ==============================

def TakeImageUI(parent):
    """Interfaz para registrar trabajador con diseño modernizado"""
    ImageUI = tk.Toplevel(parent)
    ImageUI.title("Registrar nuevo trabajador")
    ImageUI.geometry("780x520")
    ImageUI.configure(background=PRIMARY_BG)
    ImageUI.resizable(0, 0)
    fade_in_window(ImageUI)

    # Contenedor principal
    container = tk.Frame(ImageUI, bg=PRIMARY_BG)
    container.pack(expand=True, fill="both", padx=30, pady=30)

    # Header
    header = tk.Frame(container, bg=PRIMARY_BG)
    header.pack(fill="x", pady=(0, 20))

    tk.Label(
        header,
        text="Registro de trabajador",
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 22)
    ).pack(anchor="w")

    tk.Label(
        header,
        text="Captura de rostro y datos básicos para el control de asistencia.",
        bg=PRIMARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10)
    ).pack(anchor="w", pady=(5, 0))

    # Tarjeta central
    card = tk.Frame(container, bg=SECONDARY_BG, bd=0, relief="flat")
    card.pack(expand=True, fill="both", pady=(5, 10))

    # Campos dentro de la tarjeta
    form = tk.Frame(card, bg=SECONDARY_BG)
    form.pack(padx=40, pady=40, fill="x")

    # Código
    tk.Label(
        form,
        text="Código (ID) del trabajador",
        bg=SECONDARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI", 11, "bold")
    ).grid(row=0, column=0, sticky="w", pady=(0, 3))

    txt1 = tk.Entry(
        form,
        width=18,
        bd=0,
        font=("Segoe UI", 14, "bold"),
        validate="key",
        validatecommand=(ImageUI.register(testVal), "%P", "%d"),
        bg="#020617",
        fg=TEXT_PRIMARY,
        insertbackground=TEXT_PRIMARY,
        relief="flat"
    )
    txt1.grid(row=1, column=0, sticky="w", pady=(0, 15), ipadx=5, ipady=5)

    # Línea decorativa debajo del Entry
    tk.Frame(form, bg=ACCENT, height=2).grid(row=2, column=0, sticky="we", pady=(0, 20))

    # Nombre
    tk.Label(
        form,
        text="Nombre completo",
        bg=SECONDARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI", 11, "bold")
    ).grid(row=3, column=0, sticky="w", pady=(0, 3))

    txt2 = tk.Entry(
        form,
        width=24,
        bd=0,
        font=("Segoe UI", 14),
        bg="#020617",
        fg=TEXT_PRIMARY,
        insertbackground=TEXT_PRIMARY,
        relief="flat"
    )
    txt2.grid(row=4, column=0, sticky="we", pady=(0, 15), ipadx=5, ipady=5)
    tk.Frame(form, bg=ACCENT_SECONDARY, height=2).grid(row=5, column=0, sticky="we", pady=(0, 10))

    # Mensaje
    message = tk.Label(
        card,
        text="",
        bg=SECONDARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10, "bold"),
        wraplength=620,
        justify="left"
    )
    message.pack(fill="x", padx=40, pady=(10, 10))

    # Funciones de los botones
    def take_image():
        l1 = txt1.get().strip()
        l2 = txt2.get().strip()
        takeImage.TakeImage(
            l1,
            l2,
            haarcasecade_path,
            trainimage_path,
            message,
            err_screen,
            text_to_speech
        )
        txt1.delete(0, "end")
        txt2.delete(0, "end")

    def train_image():
        trainImage.TrainImage(
            haarcasecade_path,
            trainimage_path,
            trainimagelabel_path,
            message,
            text_to_speech
        )

    # Barra de botones
    button_bar = tk.Frame(container, bg=PRIMARY_BG)
    button_bar.pack(fill="x", pady=(5, 0))

    btn_take = tk.Button(
        button_bar,
        text="Tomar imagen",
        command=take_image,
        bg=ACCENT,
        fg="black",
        activebackground=ACCENT_HOVER,
        activeforeground="black",
        font=("Segoe UI Semibold", 11),
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=18,
        pady=10
    )
    btn_take.pack(side="left", padx=(0, 10))

    btn_train = tk.Button(
        button_bar,
        text="Entrenar modelo",
        command=train_image,
        bg=ACCENT_SECONDARY,
        fg="black",
        activebackground="#0ea5e9",
        activeforeground="black",
        font=("Segoe UI Semibold", 11),
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=18,
        pady=10
    )
    btn_train.pack(side="left")

    btn_close = tk.Button(
        button_bar,
        text="Cerrar",
        command=ImageUI.destroy,
        bg=BTN_BG,
        fg=TEXT_PRIMARY,
        activebackground="#1f2937",
        activeforeground=TEXT_PRIMARY,
        font=("Segoe UI", 11),
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=18,
        pady=10
    )
    btn_close.pack(side="right")


# ==============================
# SUBVENTANA: ASIGNAR EPP
# ==============================

def AssignEPPUI(parent):
    """Ventana para asignar códigos de EPP (casco / chaleco) a un trabajador"""
    assign_win = tk.Toplevel(parent)
    assign_win.title("Asignar EPP a trabajador")
    assign_win.geometry("800x450")
    assign_win.configure(background=PRIMARY_BG)
    assign_win.resizable(0, 0)
    fade_in_window(assign_win)

    seleccionado = {"enrollment": None, "name": None}

    # Contenedor
    container = tk.Frame(assign_win, bg=PRIMARY_BG)
    container.pack(expand=True, fill="both", padx=30, pady=30)

    # Header
    header = tk.Frame(container, bg=PRIMARY_BG)
    header.pack(fill="x", pady=(0, 15))

    tk.Label(
        header,
        text="Asignar EPP a trabajador",
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 20)
    ).pack(anchor="w")

    tk.Label(
        header,
        text="Busque al trabajador por su código y genere un código único para su casco o chaleco.",
        bg=PRIMARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10),
        wraplength=560,
        justify="left"
    ).pack(anchor="w", pady=(5, 0))

    # Tarjeta
    card = tk.Frame(container, bg=SECONDARY_BG)
    card.pack(fill="both", expand=True, pady=(5, 10))

    # Campo de búsqueda
    field_frame = tk.Frame(card, bg=SECONDARY_BG)
    field_frame.pack(padx=30, pady=(25, 10), fill="x")

    tk.Label(
        field_frame,
        text="Código (ID) del trabajador",
        bg=SECONDARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI", 11, "bold")
    ).grid(row=0, column=0, sticky="w")

    vcmd = (assign_win.register(testVal), "%P", "%d")
    entry_id = tk.Entry(
        field_frame,
        width=10,
        bd=0,
        font=("Segoe UI", 14, "bold"),
        validate="key",
        validatecommand=vcmd,
        bg="#020617",
        fg=TEXT_PRIMARY,
        insertbackground=TEXT_PRIMARY,
        relief="flat"
    )
    entry_id.grid(row=1, column=0, sticky="w", pady=(3, 5), ipadx=5, ipady=5)
    tk.Frame(field_frame, bg=ACCENT_SECONDARY, height=2).grid(row=2, column=0, sticky="we", pady=(0, 5))

    # Botón buscar
    def buscar_trabajador():
        enrollment = entry_id.get().strip()
        if enrollment == "":
            lbl_info.config(
                text="⚠ Ingrese un código (ID) primero.",
                fg=WARNING_COLOR
            )
            text_to_speech("Ingrese un código de trabajador.")
            return

        if not os.path.exists(studentdetail_path):
            lbl_info.config(
                text="⚠ No se encontró el archivo studentdetails.csv.",
                fg=ERROR_COLOR
            )
            text_to_speech("No se encontró la base de trabajadores.")
            return

        encontrado = None
        try:
            with open(studentdetail_path, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Enrollment", "").strip() == enrollment:
                        encontrado = row
                        break
        except Exception as e:
            lbl_info.config(text=f"⚠ Error leyendo CSV: {e}", fg=ERROR_COLOR)
            return

        if not encontrado:
            lbl_trabajador.config(text="Trabajador: ---")
            lbl_info.config(
                text=f"⚠ No se encontró trabajador con ID {enrollment}.",
                fg=ERROR_COLOR
            )
            text_to_speech("Trabajador no encontrado.")
            seleccionado["enrollment"] = None
            seleccionado["name"] = None
            btn_casco.config(state="disabled")
            btn_chaleco.config(state="disabled")
        else:
            nombre = encontrado.get("Name", "").strip()
            seleccionado["enrollment"] = enrollment
            seleccionado["name"] = nombre
            lbl_trabajador.config(
                text=f"Trabajador: {nombre}  (ID: {enrollment})"
            )
            lbl_info.config(
                text="Seleccione si desea generar un código para el CASCO o para el CHALECO.",
                fg=TEXT_SECONDARY
            )
            btn_casco.config(state="normal")
            btn_chaleco.config(state="normal")
            text_to_speech(f"Trabajador {nombre} encontrado.")

    btn_buscar = tk.Button(
        field_frame,
        text="Buscar",
        command=buscar_trabajador,
        bg=ACCENT_SECONDARY,
        fg="black",
        activebackground="#0ea5e9",
        activeforeground="black",
        font=("Segoe UI Semibold", 10),
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=14,
        pady=7
    )
    btn_buscar.grid(row=1, column=1, padx=(10, 0), pady=(3, 0))

    # Información de trabajador
    lbl_trabajador = tk.Label(
        card,
        text="Trabajador: ---",
        bg=SECONDARY_BG,
        fg=ACCENT_SECONDARY,
        font=("Segoe UI", 11, "bold")
    )
    lbl_trabajador.pack(anchor="w", padx=30, pady=(5, 5))

    # Mensaje de estado
    lbl_info = tk.Label(
        card,
        text="Ingrese el código del trabajador y presione 'Buscar'.",
        bg=SECONDARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 9),
        wraplength=540,
        justify="left"
    )
    lbl_info.pack(anchor="w", padx=30, pady=(0, 10))

    # Botones EPP
    frame_epp = tk.Frame(card, bg=SECONDARY_BG)
    frame_epp.pack(padx=30, pady=(10, 25), anchor="w")

    def asignar_epp(tipo):
        enrollment = seleccionado["enrollment"]
        name = seleccionado["name"]
        if not enrollment:
            lbl_info.config(
                text="⚠ Primero busque y seleccione un trabajador.",
                fg=WARNING_COLOR
            )
            text_to_speech("Primero seleccione un trabajador.")
            return

        # Generar código de EPP
        codigo = generar_codigo_epp(enrollment, tipo_epp=tipo)

        # Leer CSV, actualizar fila, asegurar columnas
        try:
            with open(studentdetail_path, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                filas = list(reader)
                campos = reader.fieldnames or []

            col_casco = "EPPCodeCasco"
            col_chaleco = "EPPCodeChaleco"
            if col_casco not in campos:
                campos.append(col_casco)
            if col_chaleco not in campos:
                campos.append(col_chaleco)

            if tipo.lower() == "casco":
                col_objetivo = col_casco
            else:
                col_objetivo = col_chaleco

            for fila in filas:
                if fila.get("Enrollment", "").strip() == str(enrollment):
                    fila[col_objetivo] = codigo

            with open(studentdetail_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=campos)
                writer.writeheader()
                writer.writerows(filas)

            lbl_info.config(
                text=(
                    f"✅ Código generado para {tipo.upper()} del trabajador "
                    f"{name}:\n{codigo}"
                ),
                fg=ACCENT
            )
            text_to_speech(f"Código de {tipo} asignado.")
        except Exception as e:
            lbl_info.config(text=f"⚠ Error actualizando CSV: {e}", fg=ERROR_COLOR)

    btn_casco = tk.Button(
        frame_epp,
        text="Asignar código a CASCO",
        command=lambda: asignar_epp("casco"),
        bg=ACCENT,
        fg="black",
        font=("Segoe UI Semibold", 10),
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=15,
        pady=9,
        state="disabled"
    )
    btn_casco.grid(row=0, column=0, padx=(0, 10))

    btn_chaleco = tk.Button(
        frame_epp,
        text="Asignar código a CHALECO",
        command=lambda: asignar_epp("chaleco"),
        bg="#f97316",
        fg="black",
        font=("Segoe UI Semibold", 10),
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=15,
        pady=9,
        state="disabled"
    )
    btn_chaleco.grid(row=0, column=1)

    # Barra inferior
    bottom_bar = tk.Frame(container, bg=PRIMARY_BG)
    bottom_bar.pack(fill="x", pady=(5, 0))

    tk.Button(
        bottom_bar,
        text="Cerrar",
        command=assign_win.destroy,
        bg=BTN_BG,
        fg=TEXT_PRIMARY,
        activebackground="#1f2937",
        activeforeground=TEXT_PRIMARY,
        font=("Segoe UI", 10),
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=18,
        pady=8
    ).pack(side="right")


# ==============================
# VENTANA PRINCIPAL
# ==============================

window = Tk()
window.title("Sistema de Asistencia - Reconocimiento Facial + EPP")
window.geometry("1280x720")
window.minsize(1024, 640)
window.configure(background=PRIMARY_BG)

# Intentar colocar icono (opcional)
try:
    window.iconbitmap(os.path.join(BASE_DIR, "UI_Image", "icono.ico"))
except Exception:
    pass

# ---- HEADER SUPERIOR ----
top_bar = tk.Frame(window, bg=SECONDARY_BG, height=70)
top_bar.pack(side="top", fill="x")

# Logo / avatar circular
logo_frame = tk.Frame(top_bar, bg=SECONDARY_BG)
logo_frame.pack(side="left", padx=25)

try:
    logo = Image.open(os.path.join(BASE_DIR, "UI_Image", "0001.png"))
    logo = logo.resize((46, 46), Image.LANCZOS)
    logo1 = ImageTk.PhotoImage(logo)
    logo_label = tk.Label(logo_frame, image=logo1, bg=SECONDARY_BG)
    logo_label.pack()
except Exception:
    tk.Label(
        logo_frame,
        text="👷",
        bg=SECONDARY_BG,
        fg=ACCENT,
        font=("Segoe UI", 32)
    ).pack()

# Título principal
title_frame = tk.Frame(top_bar, bg=SECONDARY_BG)
title_frame.pack(side="left", padx=10)

title_label = tk.Label(
    title_frame,
    text="Control de Asistencia",
    bg=SECONDARY_BG,
    fg=TEXT_PRIMARY,
    font=("Segoe UI Semibold", 22)
)
title_label.pack(anchor="w")

subtitle_label = tk.Label(
    title_frame,
    text="Reconocimiento facial y verificación de EPP",
    bg=SECONDARY_BG,
    fg=TEXT_SECONDARY,
    font=("Segoe UI", 10)
)
subtitle_label.pack(anchor="w")

# Indicador de “sistema activo”
status_dot_frame = tk.Frame(top_bar, bg=SECONDARY_BG)
status_dot_frame.pack(side="right", padx=25)

dot = tk.Label(
    status_dot_frame,
    text="●",
    bg=SECONDARY_BG,
    fg=ACCENT,
    font=("Segoe UI", 18)
)
dot.pack(side="left")

dot_label = tk.Label(
    status_dot_frame,
    text="Sistema activo",
    bg=SECONDARY_BG,
    fg=TEXT_SECONDARY,
    font=("Segoe UI", 9)
)
dot_label.pack(side="left", padx=(5, 0))

def animate_dot():
    """Pequeña animación para el punto de estado (parpadeo suave)."""
    current = dot.cget("fg")
    dot.config(fg=ACCENT if current != ACCENT else "#16a34a")
    window.after(600, animate_dot)

animate_dot()

# ---- CONTENIDO CENTRAL ----
main_container = tk.Frame(window, bg=PRIMARY_BG)
main_container.pack(expand=True, fill="both", padx=40, pady=30)

# LADO IZQUIERDO: MENSAJE / INFO
left_panel = tk.Frame(main_container, bg=PRIMARY_BG)
left_panel.pack(side="left", fill="both", expand=True, padx=(0, 20))

welcome_label = tk.Label(
    left_panel,
    text="Bienvenido al panel de asistencia",
    bg=PRIMARY_BG,
    fg=TEXT_PRIMARY,
    font=("Segoe UI Semibold", 20)
)
welcome_label.pack(anchor="w", pady=(0, 10))

welcome_text = tk.Label(
    left_panel,
    text=(
        "Desde aquí puedes registrar nuevos trabajadores, asignar sus EPP y "
        "gestionar la asistencia diaria de forma rápida y segura.\n\n"
        "Usa los botones del panel derecho para acceder a las funciones "
        "principales del sistema."
    ),
    bg=PRIMARY_BG,
    fg=TEXT_SECONDARY,
    justify="left",
    wraplength=460,
    font=("Segoe UI", 10)
)
welcome_text.pack(anchor="w")

# Pequeñas viñetas de ayuda
tips_frame = tk.Frame(left_panel, bg=PRIMARY_BG)
tips_frame.pack(anchor="w", pady=(25, 0))

tk.Label(
    tips_frame,
    text="Consejos rápidos:",
    bg=PRIMARY_BG,
    fg=ACCENT_SECONDARY,
    font=("Segoe UI Semibold", 11)
).pack(anchor="w", pady=(0, 5))

for tip in [
    "• Registra primero el rostro y datos del trabajador.",
    "• Asigna el código de EPP a su casco y chaleco.",
    "• Usa 'Tomar asistencia' para registrar la jornada.",
    "• Consulta el historial en 'Ver asistencia'."
]:
    tk.Label(
        tips_frame,
        text=tip,
        bg=PRIMARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 9)
    ).pack(anchor="w")

# Animación suave de color en el título principal
def animate_title_pulse(step=0):
    colors = [TEXT_PRIMARY, ACCENT_SECONDARY, TEXT_PRIMARY]
    title_label.config(fg=colors[step % len(colors)])
    window.after(1500, animate_title_pulse, step + 1)

animate_title_pulse()

# LADO DERECHO: TARJETA DE BOTONES
right_panel = tk.Frame(main_container, bg=PRIMARY_BG)
right_panel.pack(side="right", fill="y")

card_actions = tk.Frame(right_panel, bg=SECONDARY_BG)
card_actions.pack(fill="both", padx=(0, 0), pady=(0, 0))

card_header = tk.Frame(card_actions, bg=SECONDARY_BG)
card_header.pack(fill="x", padx=25, pady=20)

tk.Label(
    card_header,
    text="Acciones rápidas",
    bg=SECONDARY_BG,
    fg=TEXT_PRIMARY,
    font=("Segoe UI Semibold", 14)
).pack(anchor="w")

tk.Label(
    card_header,
    text="Selecciona una opción para comenzar:",
    bg=SECONDARY_BG,
    fg=TEXT_SECONDARY,
    font=("Segoe UI", 9)
).pack(anchor="w", pady=(2, 0))

buttons_frame = tk.Frame(card_actions, bg=SECONDARY_BG)
buttons_frame.pack(fill="both", padx=25, pady=(10, 25))

# ---- BARRA DE ESTADO INFERIOR ----
status_bar = tk.Label(
    window,
    text=DEFAULT_STATUS,
    bg="#020617",
    fg=TEXT_SECONDARY,
    bd=1,
    relief="flat",
    anchor="w",
    font=("Segoe UI", 9)
)
status_bar.pack(side="bottom", fill="x", padx=20, pady=(0, 10))


# ==============================
# ACCIONES PRINCIPALES (BOTONES)
# ==============================

# Botón: Registrar nuevo trabajador
btn_register = tk.Button(
    buttons_frame,
    text="Registrar nuevo trabajador",
    command=lambda: TakeImageUI(window),
    bg=BTN_BG,
    fg=BTN_FG,
    activebackground="#1f2937",
    activeforeground=TEXT_PRIMARY,
    font=("Segoe UI", 11),
    bd=0,
    relief="flat",
    cursor="hand2",
    padx=16,
    pady=12
)
btn_register.grid(row=0, column=0, sticky="we", pady=(0, 10))

# Botón: Asignar EPP
btn_assign_epp = tk.Button(
    buttons_frame,
    text="Asignar EPP (casco / chaleco)",
    command=lambda: AssignEPPUI(window),
    bg=BTN_BG,
    fg=BTN_FG,
    activebackground="#1f2937",
    activeforeground=TEXT_PRIMARY,
    font=("Segoe UI", 11),
    bd=0,
    relief="flat",
    cursor="hand2",
    padx=16,
    pady=12
)
btn_assign_epp.grid(row=1, column=0, sticky="we", pady=(0, 10))

# Botón: Tomar asistencia
btn_attendance = tk.Button(
    buttons_frame,
    text="Tomar asistencia",
    command=lambda: automaticAttendance.subjectChoose(),
    bg=BTN_BG,
    fg=BTN_FG,
    activebackground="#1f2937",
    activeforeground=TEXT_PRIMARY,
    font=("Segoe UI", 11),
    bd=0,
    relief="flat",
    cursor="hand2",
    padx=16,
    pady=12
)
btn_attendance.grid(row=2, column=0, sticky="we", pady=(0, 10))

# Botón: Ver asistencia
btn_view = tk.Button(
    buttons_frame,
    text="Ver asistencia",
    command=lambda: show_attendance.subjectchoose(text_to_speech),
    bg=BTN_BG,
    fg=BTN_FG,
    activebackground="#1f2937",
    activeforeground=TEXT_PRIMARY,
    font=("Segoe UI", 11),
    bd=0,
    relief="flat",
    cursor="hand2",
    padx=16,
    pady=12
)
btn_view.grid(row=3, column=0, sticky="we", pady=(0, 10))

# Botón: Salir
btn_exit = tk.Button(
    buttons_frame,
    text="Salir del sistema",
    command=quit,
    bg="#b91c1c",
    fg="white",
    activebackground="#ef4444",
    activeforeground="white",
    font=("Segoe UI Semibold", 11),
    bd=0,
    relief="flat",
    cursor="hand2",
    padx=16,
    pady=12
)
btn_exit.grid(row=4, column=0, sticky="we", pady=(10, 0))

# Expandir en ancho
buttons_frame.grid_columnconfigure(0, weight=1)

# Hover + barra de estado
apply_button_hover_effect(
    btn_register,
    status_bar,
    "Registrar un nuevo trabajador: captura de rostro y datos básicos."
)
apply_button_hover_effect(
    btn_assign_epp,
    status_bar,
    "Asignar códigos de EPP (casco / chaleco) a un trabajador registrado."
)
apply_button_hover_effect(
    btn_attendance,
    status_bar,
    "Tomar asistencia con reconocimiento facial y verificación de EPP."
)
apply_button_hover_effect(
    btn_view,
    status_bar,
    "Visualizar y exportar registros de asistencia existentes."
)
apply_button_hover_effect(
    btn_exit,
    status_bar,
    "Cerrar la aplicación de control de asistencia."
)

# ==============================
# INICIAR APLICACIÓN
# ==============================

window.mainloop()
