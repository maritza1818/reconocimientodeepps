# attendance.py (main) - versión IHC estilada

import os
import csv
import datetime
import tkinter as tk
from PIL import ImageTk, Image
import pyttsx3

import show_attendance
import takeImage
import trainImage
import automaticAttendance
import dashboard
from epp_detector_integrado import generar_codigo_epp  # ⬅️ IMPORT PARA ASIGNAR EPP


# ---------------- PALETA Y ANIMACIONES ----------------
PRIMARY_BG = "#020617"        # Fondo raíz muy oscuro
TOPBAR_BG = "#0f172a"         # Barra superior
SIDEBAR_BG = "#111827"        # Sidebar
CONTENT_BG = "#f8fafc"        # Área principal clara
CARD_BG = "#ffffff"           # Tarjetas
ACCENT = "#22c55e"            # Verde principal
ACCENT_SECONDARY = "#38bdf8"  # Azul cian
TEXT_PRIMARY = "#e5e7eb"
TEXT_SECONDARY = "#9ca3af"
WARNING_COLOR = "#facc15"
ERROR_COLOR = "#f97373"


def fade_in_window(win):
    """Animación de aparición suave para ventanas Tk/Toplevel."""
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


# ---------------- UTILIDADES BÁSICAS ----------------
def text_to_speech(user_text):
    """TTS simple (usa pyttsx3 si está disponible, si no solo imprime)."""
    try:
        engine = pyttsx3.init()
        engine.say(user_text)
        engine.runAndWait()
    except Exception:
        print(f"[TTS] {user_text}")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
haarcasecade_path = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")
trainimagelabel_path = os.path.join(BASE_DIR, "TrainingImageLabel", "Trainner.yml")
trainimage_path = os.path.join(BASE_DIR, "TrainingImage")
studentdetail_path = os.path.join(BASE_DIR, "StudentDetails", "studentdetails.csv")
attendance_path = os.path.join(BASE_DIR, "Attendance")

# crear carpetas mínimas
os.makedirs(trainimage_path, exist_ok=True)
os.makedirs(os.path.dirname(trainimagelabel_path), exist_ok=True)
os.makedirs(os.path.dirname(studentdetail_path), exist_ok=True)
os.makedirs(attendance_path, exist_ok=True)

# crear csv base si no existe
if not os.path.exists(studentdetail_path):
    with open(studentdetail_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Enrollment", "Name"])


# ---------------- VENTANA PRINCIPAL ----------------
window = tk.Tk()
window.title("Control de Asistencia con EPP")
window.geometry("1280x720")
window.minsize(1180, 660)
window.configure(bg=PRIMARY_BG)
fade_in_window(window)

# ---------------- BARRA SUPERIOR ----------------
topbar = tk.Frame(window, bg=TOPBAR_BG, height=60)
topbar.pack(side="top", fill="x")

# logo + título
logo_label = tk.Label(topbar, bg=TOPBAR_BG)
logo_label.pack(side="left", padx=15)

try:
    logo = Image.open(os.path.join(BASE_DIR, "UI_Image", "0001.png"))
    logo = logo.resize((45, 42), Image.LANCZOS)
    logo1 = ImageTk.PhotoImage(logo)
    logo_label.configure(image=logo1)
    logo_label.image = logo1
except Exception:
    logo_label.configure(text="EPP", fg="white", font=("Verdana", 16, "bold"))

title_header = tk.Label(
    topbar,
    text="Sistema de Control de Asistencia + EPP",
    bg=TOPBAR_BG,
    fg="white",
    font=("Verdana", 17, "bold"),
)
title_header.pack(side="left", padx=10)

# reloj global
clock_label = tk.Label(
    topbar,
    text="",
    bg=TOPBAR_BG,
    fg="#e2e8f0",
    font=("Verdana", 11, "bold"),
)
clock_label.pack(side="right", padx=20)


def update_clock():
    if not clock_label.winfo_exists():
        return
    now = datetime.datetime.now()
    clock_label.config(text=now.strftime("%d/%m/%Y   %H:%M:%S"))
    window.after(1000, update_clock)


update_clock()

# ---------------- LAYOUT PRINCIPAL ----------------
# left sidebar
sidebar = tk.Frame(window, bg=SIDEBAR_BG, width=250)
sidebar.pack(side="left", fill="y")

# content area
content = tk.Frame(window, bg=CONTENT_BG)
content.pack(side="right", fill="both", expand=True)

# ---------------- CABECERA DEL CONTENT ----------------
welcome_title = tk.Label(
    content,
    text="Panel principal",
    bg=CONTENT_BG,
    fg="#0f172a",
    font=("Verdana", 20, "bold"),
    anchor="w",
)
welcome_title.pack(fill="x", padx=30, pady=(25, 5))

welcome_sub = tk.Label(
    content,
    text="Elija una de las acciones del menú para continuar.",
    bg=CONTENT_BG,
    fg="#475569",
    font=("Verdana", 11),
    anchor="w",
)
welcome_sub.pack(fill="x", padx=30, pady=(0, 10))

# ---------------- TARJETAS (IHC: información agrupada) ----------------
cards_frame = tk.Frame(content, bg=CONTENT_BG)
cards_frame.pack(fill="x", padx=30, pady=10)


def make_card(parent, title, desc, color):
    frame = tk.Frame(parent, bg=CARD_BG, bd=0, highlightthickness=0)
    frame.pack(side="left", padx=10, pady=5, fill="x", expand=True)

    head = tk.Label(
        frame,
        text=title,
        bg=CARD_BG,
        fg=color,
        font=("Verdana", 11, "bold"),
    )
    head.pack(anchor="w", pady=(8, 0), padx=10)

    body = tk.Label(
        frame,
        text=desc,
        bg=CARD_BG,
        fg="#475569",
        font=("Verdana", 9),
        wraplength=180,
        justify="left",
    )
    body.pack(anchor="w", pady=(2, 10), padx=10)

    def on_enter(_event):
        frame.configure(bg="#e2f3ff")
        head.configure(bg="#e2f3ff")
        body.configure(bg="#e2f3ff")

    def on_leave(_event):
        frame.configure(bg=CARD_BG)
        head.configure(bg=CARD_BG)
        body.configure(bg=CARD_BG)

    for widget in (frame, head, body):
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    return frame


make_card(
    cards_frame,
    "Asistencia por rostro",
    "Reconoce al trabajador y valida EPP.",
    "#0f766e",
)
make_card(
    cards_frame,
    "Registro de personal",
    "Capture rostro y entrene el modelo.",
    "#1d4ed8",
)
make_card(
    cards_frame,
    "Dashboard",
    "Vea totales, intentos y zonas activas.",
    "#b45309",
)

# ---------------- FUNCIONES DE LAS VENTANAS ----------------
def err_screen():
    sc1 = tk.Toplevel(window)
    sc1.geometry("400x110")
    sc1.title("Advertencia")
    sc1.configure(background="#1f2937")
    sc1.resizable(0, 0)
    fade_in_window(sc1)
    tk.Label(
        sc1,
        text="¡Código y nombre requeridos!",
        fg="#fde68a",
        bg="#1f2937",
        font=("Verdana", 14, "bold"),
    ).pack(pady=(15, 5))
    tk.Button(
        sc1,
        text="OK",
        command=sc1.destroy,
        fg="white",
        bg="#0f766e",
        activebackground="#0f766e",
        bd=0,
        font=("Verdana", 12, "bold"),
        width=10,
        cursor="hand2",
    ).pack(pady=(0, 6))


def testVal(inStr, acttyp):
    if acttyp == "1":
        return inStr.isdigit() or inStr == ""
    return True


def TakeImageUI():
    ImageUI = tk.Toplevel(window)
    ImageUI.title("Captura de rostro")
    ImageUI.geometry("780x520")
    ImageUI.configure(background="#0f172a")
    ImageUI.resizable(0, 0)
    fade_in_window(ImageUI)

    titl = tk.Label(
        ImageUI,
        text="Registrar nuevo trabajador",
        bg="#0f172a",
        fg="white",
        font=("Verdana", 20, "bold"),
    )
    titl.place(x=40, y=20)

    subt = tk.Label(
        ImageUI,
        text="Capture 50–70 imágenes del rostro para un mejor entrenamiento.",
        bg="#0f172a",
        fg="#cbd5f5",
        font=("Verdana", 9),
    )
    subt.place(x=40, y=55)

    lbl1 = tk.Label(
        ImageUI,
        text="Código (ID):",
        bg="#0f172a",
        fg="#e2e8f0",
        font=("Verdana", 12),
    )
    lbl1.place(x=40, y=110)

    txt1 = tk.Entry(
        ImageUI,
        width=17,
        bd=2,
        font=("Verdana", 18, "bold"),
        validate="key",
        validatecommand=(ImageUI.register(testVal), "%P", "%d"),
        bg="#0f172a",
        fg="white",
        insertbackground="white",
    )
    txt1.place(x=200, y=105)

    lbl2 = tk.Label(
        ImageUI,
        text="Nombre:",
        bg="#0f172a",
        fg="#e2e8f0",
        font=("Verdana", 12),
    )
    lbl2.place(x=40, y=165)

    txt2 = tk.Entry(
        ImageUI,
        width=17,
        bd=2,
        font=("Verdana", 18, "bold"),
        bg="#0f172a",
        fg="white",
        insertbackground="white",
    )
    txt2.place(x=200, y=160)

    message = tk.Label(
        ImageUI,
        text="",
        bg="#0f172a",
        fg="#fcd34d",
        width=60,
        font=("Verdana", 10, "bold"),
        wraplength=600,
        justify="left",
    )
    message.place(x=40, y=220)

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
            text_to_speech,
        )
        txt1.delete(0, "end")
        txt2.delete(0, "end")

    def train_image():
        trainImage.TrainImage(
            haarcasecade_path,
            trainimage_path,
            trainimagelabel_path,
            message,
            text_to_speech,
        )

    takeImg = tk.Button(
        ImageUI,
        text="1. Tomar imágenes",
        command=take_image,
        bg="#0f766e",
        fg="white",
        font=("Verdana", 13, "bold"),
        width=18,
        height=2,
        bd=0,
        activebackground="#115e59",
        cursor="hand2",
    )
    takeImg.place(x=40, y=320)

    trainImg = tk.Button(
        ImageUI,
        text="2. Entrenar modelo",
        command=train_image,
        bg="#1d4ed8",
        fg="white",
        font=("Verdana", 13, "bold"),
        width=18,
        height=2,
        bd=0,
        activebackground="#1e40af",
        cursor="hand2",
    )
    trainImg.place(x=275, y=320)

    closeBtn = tk.Button(
        ImageUI,
        text="Cerrar",
        command=ImageUI.destroy,
        bg="#b91c1c",
        fg="white",
        font=("Verdana", 12, "bold"),
        width=15,
        bd=0,
        activebackground="#991b1b",
        cursor="hand2",
    )
    closeBtn.place(x=520, y=450)


# --------------- ASIGNAR CÓDIGOS DE EPP ---------------
def AssignEPPUI():
    """Ventana para asignar códigos de EPP (casco / chaleco) a un trabajador."""
    assign_win = tk.Toplevel(window)
    assign_win.title("Asignar EPP a trabajador")
    assign_win.geometry("620x380")
    assign_win.configure(background="#020617")
    assign_win.resizable(0, 0)
    fade_in_window(assign_win)

    seleccionado = {"enrollment": None, "name": None}

    tk.Label(
        assign_win,
        text="Asignar EPP a trabajador",
        bg="#020617",
        fg="white",
        font=("Verdana", 20, "bold"),
    ).pack(pady=(18, 5))

    tk.Label(
        assign_win,
        text="Busque al trabajador por código (ID) y genere códigos para casco o chaleco.",
        bg="#020617",
        fg="#94a3b8",
        font=("Verdana", 9),
        wraplength=560,
        justify="center",
    ).pack(pady=(0, 10))

    frame_input = tk.Frame(assign_win, bg="#020617")
    frame_input.pack(pady=5)

    tk.Label(
        frame_input,
        text="Código (ID):",
        bg="#020617",
        fg="#e5e7eb",
        font=("Verdana", 11),
    ).grid(row=0, column=0, padx=8)

    entry_id = tk.Entry(
        frame_input,
        width=10,
        bd=2,
        font=("Verdana", 18, "bold"),
        validate="key",
        validatecommand=(assign_win.register(testVal), "%P", "%d"),
        bg="#020617",
        fg="white",
        insertbackground="white",
    )
    entry_id.grid(row=0, column=1, padx=8)

    lbl_info = tk.Label(
        assign_win,
        text="Ingrese el código del trabajador y presione 'Buscar'.",
        bg="#020617",
        fg="#facc15",
        font=("Verdana", 9),
        wraplength=560,
        justify="center",
    )
    lbl_info.pack(pady=4)

    lbl_trabajador = tk.Label(
        assign_win,
        text="Trabajador: ---",
        bg="#020617",
        fg="#22c55e",
        font=("Verdana", 13, "bold"),
    )
    lbl_trabajador.pack(pady=6)

    def buscar_trabajador():
        enrollment = entry_id.get().strip()
        if enrollment == "":
            lbl_info.config(text="⚠ Ingrese un código (ID) primero.", fg=ERROR_COLOR)
            text_to_speech("Ingrese un código de trabajador.")
            return

        if not os.path.exists(studentdetail_path):
            lbl_info.config(
                text="⚠ No se encontró el archivo de trabajadores (studentdetails.csv).",
                fg=ERROR_COLOR,
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
                fg=ERROR_COLOR,
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
            lbl_trabajador.config(text=f"Trabajador: {nombre} (ID: {enrollment})")
            lbl_info.config(
                text="Seleccione si desea generar código para CASCO o para CHALECO.",
                fg="#facc15",
            )
            btn_casco.config(state="normal")
            btn_chaleco.config(state="normal")
            text_to_speech(f"Trabajador {nombre} encontrado.")

    btn_buscar = tk.Button(
        assign_win,
        text="Buscar",
        command=buscar_trabajador,
        bg="#1d4ed8",
        fg="white",
        font=("Verdana", 11, "bold"),
        width=10,
        bd=0,
        activebackground="#1e40af",
        cursor="hand2",
    )
    btn_buscar.pack(pady=(2, 10))

    frame_epp = tk.Frame(assign_win, bg="#020617")
    frame_epp.pack(pady=5)

    def asignar_epp(tipo):
        enrollment = seleccionado["enrollment"]
        name = seleccionado["name"]
        if not enrollment:
            lbl_info.config(
                text="⚠ Primero busque y seleccione un trabajador.",
                fg=ERROR_COLOR,
            )
            text_to_speech("Primero seleccione un trabajador.")
            return

        codigo = generar_codigo_epp(enrollment, tipo_epp=tipo)

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
                text=f"✅ Código generado para {tipo.upper()} del trabajador {name}: {codigo}",
                fg=ACCENT,
            )
            text_to_speech(f"Código de {tipo} asignado.")
        except Exception as e:
            lbl_info.config(text=f"⚠ Error actualizando CSV: {e}", fg=ERROR_COLOR)

    btn_casco = tk.Button(
        frame_epp,
        text="Asignar código a CASCO",
        command=lambda: asignar_epp("casco"),
        bg="#0f766e",
        fg="white",
        font=("Verdana", 11, "bold"),
        width=22,
        bd=0,
        activebackground="#115e59",
        cursor="hand2",
        state="disabled",
    )
    btn_casco.grid(row=0, column=0, padx=8)

    btn_chaleco = tk.Button(
        frame_epp,
        text="Asignar código a CHALECO",
        command=lambda: asignar_epp("chaleco"),
        bg="#ea580c",
        fg="white",
        font=("Verdana", 11, "bold"),
        width=22,
        bd=0,
        activebackground="#c2410c",
        cursor="hand2",
        state="disabled",
    )
    btn_chaleco.grid(row=0, column=1, padx=8)

    tk.Button(
        assign_win,
        text="Cerrar",
        command=assign_win.destroy,
        bg="#b91c1c",
        fg="white",
        font=("Verdana", 11, "bold"),
        width=12,
        bd=0,
        activebackground="#991b1b",
        cursor="hand2",
    ).pack(pady=15)


# ---------------- BOTONES DEL SIDEBAR (IHC) ----------------
def make_side_button(parent, text, subtext, command, color="#f8fafc"):
    frame = tk.Frame(parent, bg=SIDEBAR_BG)
    frame.pack(fill="x", pady=4, padx=8)

    base_btn_bg = "#1f2937"
    hover_btn_bg = "#0f172a"
    base_frame_bg = SIDEBAR_BG
    hover_frame_bg = "#020617"

    btn = tk.Button(
        frame,
        text=text,
        command=command,
        anchor="w",
        bg=base_btn_bg,
        fg=color,
        activebackground="#0f766e",
        activeforeground="white",
        bd=0,
        font=("Verdana", 12, "bold"),
        padx=12,
        pady=4,
        cursor="hand2",
    )
    btn.pack(fill="x")

    lbl = None
    if subtext:
        lbl = tk.Label(
            frame,
            text=subtext,
            bg=base_frame_bg,
            fg="#94a3b8",
            font=("Verdana", 8),
            anchor="w",
        )
        lbl.pack(fill="x", padx=12)

    def on_enter(_event):
        frame.configure(bg=hover_frame_bg)
        btn.configure(bg=hover_btn_bg)
        if lbl is not None:
            lbl.configure(bg=hover_frame_bg)

    def on_leave(_event):
        frame.configure(bg=base_frame_bg)
        btn.configure(bg=base_btn_bg)
        if lbl is not None:
            lbl.configure(bg=base_frame_bg)

    widgets = [frame, btn]
    if lbl is not None:
        widgets.append(lbl)
    for w in widgets:
        w.bind("<Enter>", on_enter)
        w.bind("<Leave>", on_leave)

    return btn


# wrappers para actualizar el texto del panel cuando se hace clic
def open_take_image_ui():
    welcome_title.config(text="Registrar trabajador")
    welcome_sub.config(
        text="Capture el rostro del trabajador y entrene el modelo de reconocimiento."
    )
    TakeImageUI()


def open_assign_epp_ui():
    welcome_title.config(text="Asignar EPP")
    welcome_sub.config(
        text="Busque al trabajador por ID y genere códigos de casco y chaleco para imprimir en el EPP."
    )
    AssignEPPUI()


def open_automatic_attendance():
    welcome_title.config(text="Tomar asistencia")
    welcome_sub.config(
        text="Se abrirá la cámara para reconocer rostro, validar EPP y leer el código del chaleco."
    )
    automaticAttendance.subjectChoose()


def open_show_attendance():
    welcome_title.config(text="Histórico de asistencias")
    welcome_sub.config(
        text="Consulte registros de asistencia e intentos, con filtros por nombre y fecha."
    )
    show_attendance.subjectchoose(text_to_speech)


def open_dashboard():
    welcome_title.config(text="Dashboard de asistencia")
    welcome_sub.config(
        text="Visualice totales del día, intentos por zona y personas con más intentos."
    )
    dashboard.build_dashboard()


make_side_button(
    sidebar,
    "➕ Registrar trabajador",
    "Captura de rostro y entrenamiento",
    open_take_image_ui,
)

make_side_button(
    sidebar,
    "🦺 Asignar EPP",
    "Generar códigos para casco y chaleco",
    open_assign_epp_ui,
)

make_side_button(
    sidebar,
    "📷 Tomar asistencia",
    "Rostro + EPP + Código de barras",
    open_automatic_attendance,
)

make_side_button(
    sidebar,
    "📄 Ver asistencia",
    "Históricos, CSV del día",
    open_show_attendance,
)

make_side_button(
    sidebar,
    "📊 Dashboard",
    "Totales, intentos, zonas",
    open_dashboard,
)

make_side_button(
    sidebar,
    "⏻ Salir",
    "Cerrar el sistema",
    window.destroy,
    color="#fecaca",
)

# ---------------- LOOP ----------------
window.mainloop()
