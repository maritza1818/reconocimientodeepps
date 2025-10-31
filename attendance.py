# attendance.py (main) - CORREGIDO
import tkinter as tk
from tkinter import *
import os, cv2, csv
from PIL import ImageTk, Image
import pyttsx3
import datetime   # 👈👈 para el reloj

import show_attendance
import takeImage
import trainImage
import automaticAttendance

# 👇👇 👇 NUEVO: importa tu dashboard
import dashboard   # <-- asegúrate de tener dashboard.py en la misma carpeta

def text_to_speech(user_text):
    """Texto a voz con manejo de errores"""
    try:
        engine = pyttsx3.init()
        engine.say(user_text)
        engine.runAndWait()
    except Exception as e:
        print(f"[TTS] {user_text}")

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

# Ventana principal
window = Tk()
window.title("Reconocimiento de cara")
window.geometry("1280x720")
window.configure(background="#1c1c1c")

# Logo (opcional)
try:
    logo = Image.open(os.path.join(BASE_DIR, "UI_Image", "0001.png"))
    logo = logo.resize((50, 47), Image.LANCZOS)
    logo1 = ImageTk.PhotoImage(logo)
    l1 = tk.Label(window, image=logo1, bg="#1c1c1c")
    l1.place(x=470, y=10)
except Exception:
    pass

# Títulos
titl = tk.Label(window, text="CONTROL DE ASISTENCIA", bg="#1c1c1c", fg="yellow", font=("Verdana", 27, "bold"))
titl.place(x=450, y=90)

a = tk.Label(window, text="BIENVENIDO AL CONTROL DE ASISTENCIA", bg="#1c1c1c", fg="yellow", bd=10, font=("Verdana", 32, "bold"))
a.pack()

# 👇👇 RELOJ EN VIVO EN LA VENTANA PRINCIPAL
clock_label = tk.Label(window, text="", bg="#1c1c1c", fg="white", font=("Verdana", 12, "bold"))
clock_label.place(x=1030, y=4)

def update_clock():
    now = datetime.datetime.now()
    # formato: 31/10/2025  14:33:22
    clock_label.config(text=now.strftime(" %d/%m/%Y    %H:%M:%S"))
    window.after(1000, update_clock)

update_clock()
# 👆👆 fin del reloj

def err_screen():
    """Ventana de error"""
    sc1 = tk.Toplevel()
    sc1.geometry("400x110")
    sc1.title("Advertencia")
    sc1.configure(background="#1c1c1c")
    sc1.resizable(0, 0)
    tk.Label(sc1, text="¡Código y nombre requeridos!", fg="yellow", bg="#1c1c1c", font=("Verdana", 16, "bold")).pack()
    tk.Button(sc1, text="OK", command=sc1.destroy, fg="yellow", bg="#333333", width=9, height=1, activebackground="red", font=("Verdana", 16, "bold")).place(x=110, y=50)

def testVal(inStr, acttyp):
    """Validación para solo números"""
    if acttyp == "1":  # insert
        return inStr.isdigit() or inStr == ""
    return True

def TakeImageUI():
    """Interfaz para registrar trabajador"""
    ImageUI = tk.Toplevel()
    ImageUI.title("Captura de rostro")
    ImageUI.geometry("780x520")
    ImageUI.configure(background="#1c1c1c")
    ImageUI.resizable(0, 0)

    titl = tk.Label(ImageUI, text="Registrando su rostro", bg="#1c1c1c", fg="green", font=("Verdana", 30, "bold"))
    titl.place(x=150, y=20)

    lbl1 = tk.Label(ImageUI, text="Código (ID):", bg="#1c1c1c", fg="yellow", font=("Verdana", 14))
    lbl1.place(x=120, y=100)
    
    txt1 = tk.Entry(ImageUI, width=17, bd=5, font=("Verdana", 18, "bold"), validate="key", validatecommand=(ImageUI.register(testVal), "%P", "%d"))
    txt1.place(x=250, y=95)

    lbl2 = tk.Label(ImageUI, text="Nombre:", bg="#1c1c1c", fg="yellow", font=("Verdana", 14))
    lbl2.place(x=120, y=165)
    
    txt2 = tk.Entry(ImageUI, width=17, bd=5, font=("Verdana", 18, "bold"))
    txt2.place(x=250, y=160)

    message = tk.Label(ImageUI, text="", bg="#1c1c1c", fg="yellow", width=50, font=("Verdana", 12, "bold"), wraplength=600)
    message.place(x=50, y=230)

    def take_image():
        l1 = txt1.get()
        l2 = txt2.get()
        takeImage.TakeImage(l1, l2, haarcasecade_path, trainimage_path, message, err_screen, text_to_speech)
        txt1.delete(0, "end")
        txt2.delete(0, "end")

    def train_image():
        trainImage.TrainImage(haarcasecade_path, trainimage_path, trainimagelabel_path, message, text_to_speech)

    takeImg = tk.Button(
        ImageUI, 
        text="Tomar Imagen", 
        command=take_image, 
        bg="#2ecc71",
        fg="white", 
        font=("Verdana", 16, "bold"),
        width=18,
        height=2
    )
    takeImg.place(x=100, y=350)

    trainImg = tk.Button(
        ImageUI, 
        text="Entrenar Imagen", 
        command=train_image, 
        bg="#3498db",
        fg="white", 
        font=("Verdana", 16, "bold"),
        width=18,
        height=2
    )
    trainImg.place(x=400, y=350)

    closeBtn = tk.Button(
        ImageUI,
        text="Cerrar",
        command=ImageUI.destroy,
        bg="#e74c3c",
        fg="white",
        font=("Verdana", 14, "bold"),
        width=15
    )
    closeBtn.place(x=280, y=450)


# ═══════════════════════════════════════════════════════
# BOTONES PRINCIPALES
# ═══════════════════════════════════════════════════════

btn_register = tk.Button(
    window, 
    text="Registrar nuevo trabajador", 
    command=TakeImageUI, 
    bg="black", 
    fg="yellow", 
    font=("Verdana", 16)
)
btn_register.place(x=100, y=520)

btn_attendance = tk.Button(
    window, 
    text="Tomar Asistencia", 
    command=lambda: automaticAttendance.subjectChoose(),
    bg="black", 
    fg="yellow", 
    font=("Verdana", 16)
)
btn_attendance.place(x=600, y=520)

btn_view = tk.Button(
    window, 
    text="Ver Asistencia", 
    command=lambda: show_attendance.subjectchoose(text_to_speech), 
    bg="black", 
    fg="yellow", 
    font=("Verdana", 16)
)
btn_view.place(x=1000, y=520)

# 👇👇👇 NUEVO BOTÓN DASHBOARD
btn_dashboard = tk.Button(
    window,
    text="Ver Dashboard",
    command=dashboard.build_dashboard,   # llama a la función del archivo nuevo
    bg="black",
    fg="yellow",
    font=("Verdana", 16)
)
btn_dashboard.place(x=1000, y=600)

btn_exit = tk.Button(
    window, 
    text="SALIR", 
    command=quit, 
    bg="black", 
    fg="yellow", 
    font=("Verdana", 16)
)
btn_exit.place(x=600, y=660)

# Iniciar aplicación
window.mainloop()
