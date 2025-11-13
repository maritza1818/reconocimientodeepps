# attendance.py (main) - versión IHC
import tkinter as tk
from tkinter import *
import os, cv2, csv
from PIL import ImageTk, Image
import pyttsx3
import datetime

import show_attendance
import takeImage
import trainImage
import automaticAttendance
import dashboard

# ---------------- UTILIDADES BÁSICAS ----------------
def text_to_speech(user_text):
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
window = Tk()
window.title("Control de Asistencia con EPP")
window.geometry("1280x720")
window.minsize(1180, 660)
window.configure(bg="#111827")  # gris azulado tipo panel

# ---------------- BARRA SUPERIOR ----------------
topbar = tk.Frame(window, bg="#0f172a", height=60)
topbar.pack(side="top", fill="x")

# logo + título
logo_label = tk.Label(topbar, bg="#0f172a")
logo_label.pack(side="left", padx=15)
try:
    logo = Image.open(os.path.join(BASE_DIR, "UI_Image", "0001.png"))
    logo = logo.resize((45, 42), Image.LANCZOS)
    logo1 = ImageTk.PhotoImage(logo)
    logo_label.configure(image=logo1)
except Exception:
    logo_label.configure(text="EPP", fg="white", font=("Verdana", 16, "bold"))

title_header = tk.Label(
    topbar,
    text="Sistema de Control de Asistencia + EPP",
    bg="#0f172a",
    fg="white",
    font=("Verdana", 17, "bold"),
)
title_header.pack(side="left", padx=10)

# reloj global
clock_label = tk.Label(
    topbar,
    text="",
    bg="#0f172a",
    fg="#e2e8f0",
    font=("Verdana", 11, "bold"),
)
clock_label.pack(side="right", padx=20)

def update_clock():
    if not clock_label.winfo_exists():
        return
    now = datetime.datetime.now()
    # sin emojis para evitar errores de consola
    clock_label.config(text=now.strftime("%d/%m/%Y   %H:%M:%S"))
    window.after(1000, update_clock)

update_clock()

# ---------------- LAYOUT PRINCIPAL ----------------
# left sidebar
sidebar = tk.Frame(window, bg="#111827", width=250)
sidebar.pack(side="left", fill="y")

# content area
content = tk.Frame(window, bg="#f8fafc")
content.pack(side="right", fill="both", expand=True)

# ---------------- CABECERA DEL CONTENT ----------------
welcome_title = tk.Label(
    content,
    text="Panel principal",
    bg="#f8fafc",
    fg="#0f172a",
    font=("Verdana", 20, "bold"),
    anchor="w",
)
welcome_title.pack(fill="x", padx=30, pady=(25, 5))

welcome_sub = tk.Label(
    content,
    text="Elija una de las acciones del menú para continuar.",
    bg="#f8fafc",
    fg="#475569",
    font=("Verdana", 11),
    anchor="w",
)
welcome_sub.pack(fill="x", padx=30, pady=(0, 10))

# ---------------- TARJETAS (IHC: información agrupada) ----------------
cards_frame = tk.Frame(content, bg="#f8fafc")
cards_frame.pack(fill="x", padx=30, pady=10)

def make_card(parent, title, desc, color):
    frame = tk.Frame(parent, bg="white", bd=0, highlightthickness=0)
    frame.pack(side="left", padx=10, pady=5, fill="x", expand=True)
    head = tk.Label(frame, text=title, bg="white", fg=color, font=("Verdana", 11, "bold"))
    head.pack(anchor="w", pady=(8, 0), padx=10)
    body = tk.Label(frame, text=desc, bg="white", fg="#475569", font=("Verdana", 9), wraplength=180, justify="left")
    body.pack(anchor="w", pady=(2, 10), padx=10)
    return frame

make_card(cards_frame, "Asistencia por rostro", "Reconoce al trabajador y valida EPP.", "#0f766e")
make_card(cards_frame, "Registro de personal", "Capture rostro y entrene el modelo.", "#1d4ed8")
make_card(cards_frame, "Dashboard", "Vea totales, intentos y zonas activas.", "#b45309")

# ---------------- FUNCIONES DE LAS VENTANAS ----------------
def err_screen():
    sc1 = tk.Toplevel(window)
    sc1.geometry("400x110")
    sc1.title("Advertencia")
    sc1.configure(background="#1f2937")
    sc1.resizable(0, 0)
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
    ).pack()

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
        fg="#cbd5f5" if False else "#cbd5f5",
        font=("Verdana", 9),
    )
    subt.place(x=40, y=55)

    lbl1 = tk.Label(ImageUI, text="Código (ID):", bg="#0f172a", fg="#e2e8f0", font=("Verdana", 12))
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
        insertbackground="white"
    )
    txt1.place(x=200, y=105)

    lbl2 = tk.Label(ImageUI, text="Nombre:", bg="#0f172a", fg="#e2e8f0", font=("Verdana", 12))
    lbl2.place(x=40, y=165)
    
    txt2 = tk.Entry(
        ImageUI,
        width=17,
        bd=2,
        font=("Verdana", 18, "bold"),
        bg="#0f172a",
        fg="white",
        insertbackground="white"
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
        takeImage.TakeImage(l1, l2, haarcasecade_path, trainimage_path, message, err_screen, text_to_speech)
        txt1.delete(0, "end")
        txt2.delete(0, "end")

    def train_image():
        trainImage.TrainImage(haarcasecade_path, trainimage_path, trainimagelabel_path, message, text_to_speech)

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
        activebackground="#115e59"
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
        activebackground="#1e40af"
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
        activebackground="#991b1b"
    )
    closeBtn.place(x=520, y=450)

# ---------------- BOTONES DEL SIDEBAR (IHC) ----------------
def make_side_button(parent, text, subtext, command, color="#f8fafc"):
    frame = tk.Frame(parent, bg="#111827")
    frame.pack(fill="x", pady=4, padx=8)

    btn = tk.Button(
        frame,
        text=text,
        command=command,
        anchor="w",
        bg="#1f2937",
        fg=color,
        activebackground="#0f766e",
        activeforeground="white",
        bd=0,
        font=("Verdana", 12, "bold"),
        padx=12,
        pady=4,
    )
    btn.pack(fill="x")

    if subtext:
        lbl = tk.Label(
            frame,
            text=subtext,
            bg="#111827",
            fg="#94a3b8",
            font=("Verdana", 8),
            anchor="w",
        )
        lbl.pack(fill="x", padx=12)
    return btn

make_side_button(
    sidebar,
    "➕ Registrar trabajador",
    "Captura de rostro y entrenamiento",
    TakeImageUI,
)

make_side_button(
    sidebar,
    "📷 Tomar asistencia",
    "Rostro + EPP + Código de barras",
    lambda: automaticAttendance.subjectChoose(),
)

make_side_button(
    sidebar,
    "📄 Ver asistencia",
    "Históricos, CSV del día",
    lambda: show_attendance.subjectchoose(text_to_speech),
)

make_side_button(
    sidebar,
    "📊 Dashboard",
    "Totales, intentos, zonas",
    dashboard.build_dashboard,
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
