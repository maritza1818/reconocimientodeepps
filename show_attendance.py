import os
import pandas as pd
import tkinter as tk
from tkinter import ttk
from glob import glob
import datetime

# ==============================
# CONFIGURACIÓN GLOBAL / RUTAS
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ATTENDANCE_BASE = os.path.join(BASE_DIR, "Attendance")

# Crear carpeta si no existe
os.makedirs(ATTENDANCE_BASE, exist_ok=True)

# Paleta de colores (igual que en attendance.py / automaticAttendance.py)
PRIMARY_BG = "#020617"        # Fondo principal
SECONDARY_BG = "#0f172a"      # Tarjeta
ACCENT = "#22c55e"            # Verde principal
ACCENT_SECONDARY = "#38bdf8"  # Azul cian
TEXT_PRIMARY = "#e5e7eb"
TEXT_SECONDARY = "#9ca3af"
WARNING_COLOR = "#facc15"
ERROR_COLOR = "#f97373"


# ==============================
# HELPERS
# ==============================

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


def load_all_attendance_frames():
    """
    Carga TODOS los CSV de asistencia del patrón:
        Attendance/asistencia_YYYY-MM-DD.csv
    Devuelve un DataFrame concatenado o None si no hay datos válidos.
    """
    pattern = os.path.join(ATTENDANCE_BASE, "asistencia_*.csv")
    files = glob(pattern)

    if not files:
        return None

    dfs = []
    expected_cols = {"Enrollment", "Name", "Date", "Time", "Status"}

    for f in files:
        try:
            if os.path.getsize(f) == 0:
                continue
            df = pd.read_csv(f, dtype=str)
            if expected_cols.issubset(df.columns):
                dfs.append(df)
        except Exception:
            continue

    if not dfs:
        return None

    df_all = pd.concat(dfs, ignore_index=True)
    return df_all


def create_toplevel(title, width=800, height=500):
    """
    Crea una ventana Toplevel si ya existe una raíz Tk,
    o una raíz Tk si no existe ninguna. Devuelve (window, is_standalone).
    """
    root = tk._default_root
    if root is None:
        win = tk.Tk()
        is_standalone = True
    else:
        win = tk.Toplevel(root)
        is_standalone = False

    win.title(title)
    win.geometry(f"{width}x{height}")
    win.configure(background=PRIMARY_BG)
    fade_in_window(win)
    return win, is_standalone


def style_treeview(root):
    """Aplica estilo oscuro al Treeview."""
    style = ttk.Style(root)
    try:
        style.theme_use("default")
    except Exception:
        pass

    style.configure(
        "DarkTreeview",
        background=SECONDARY_BG,
        foreground=TEXT_PRIMARY,
        fieldbackground=SECONDARY_BG,
        rowheight=24,
        bordercolor=PRIMARY_BG,
        relief="flat",
    )
    style.map(
        "DarkTreeview",
        background=[("selected", ACCENT_SECONDARY)],
        foreground=[("selected", "#000000")],
    )
    style.configure(
        "DarkTreeview.Heading",
        background=PRIMARY_BG,
        foreground=TEXT_PRIMARY,
        relief="flat",
        font=("Segoe UI Semibold", 10),
    )


# ==============================
# TABLA GENÉRICA PARA MOSTRAR DF
# ==============================

def show_csv_window(df, title):
    """
    Muestra un DataFrame en una ventana con tabla (Treeview) y scroll.
    """
    if df is None or df.empty:
        return

    win, is_standalone = create_toplevel(title, width=950, height=550)

    # Header
    header = tk.Frame(win, bg=PRIMARY_BG)
    header.pack(fill="x", padx=20, pady=(20, 10))

    tk.Label(
        header,
        text=title,
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 18),
    ).pack(anchor="w")

    tk.Label(
        header,
        text=f"Registros: {len(df)}",
        bg=PRIMARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 9),
    ).pack(anchor="w", pady=(3, 0))

    # Frame de tarjeta para la tabla
    card = tk.Frame(win, bg=SECONDARY_BG, bd=0, relief="flat")
    card.pack(expand=True, fill="both", padx=20, pady=(10, 20))

    # Estilo Treeview
    style_treeview(win)

    # Frame interno con scrollbars
    table_frame = tk.Frame(card, bg=SECONDARY_BG)
    table_frame.pack(expand=True, fill="both", padx=10, pady=10)

    cols = list(df.columns)

    tree = ttk.Treeview(
        table_frame,
        columns=cols,
        show="headings",
        style="DarkTreeview",
    )

    # Scrollbars
    vsb = ttk.Scrollbar(
        table_frame, orient="vertical", command=tree.yview
    )
    hsb = ttk.Scrollbar(
        table_frame, orient="horizontal", command=tree.xview
    )
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    tree.pack(side="left", fill="both", expand=True)

    # Configurar columnas
    for col in cols:
        tree.heading(col, text=col)
        # Ancho base dependiendo del tipo de columna
        if col.lower() in ("date", "time", "status"):
            width = 90
        elif col.lower() in ("enrollment",):
            width = 100
        else:
            width = 150
        tree.column(col, width=width, anchor="center")

    # Insertar datos
    for _, row in df.iterrows():
        values = [str(row[c]) for c in cols]
        tree.insert("", "end", values=values)

    # Botón cerrar
    bottom = tk.Frame(win, bg=PRIMARY_BG)
    bottom.pack(fill="x", padx=20, pady=(0, 15))

    tk.Button(
        bottom,
        text="Cerrar",
        command=win.destroy,
        bg=PRIMARY_BG,
        fg=TEXT_SECONDARY,
        activebackground="#111827",
        activeforeground=TEXT_PRIMARY,
        font=("Segoe UI", 10),
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=16,
        pady=6,
    ).pack(side="right")

    if is_standalone:
        win.mainloop()


# ==============================
# 1. VER ASISTENCIA POR TRABAJADOR
# ==============================

def subjectchoose(text_to_speech):
    """
    Pide nombre de trabajador y muestra su asistencia detallada
    (Entrada/Salida por fecha) usando los archivos asistencia_YYYY-MM-DD.csv.
    """
    subject_win, is_standalone = create_toplevel(
        "Ver asistencia por trabajador",
        width=780,
        height=420,
    )
    subject_win.resizable(0, 0)

    # CONTENEDOR
    container = tk.Frame(subject_win, bg=PRIMARY_BG)
    container.pack(expand=True, fill="both", padx=30, pady=30)

    # HEADER
    header = tk.Frame(container, bg=PRIMARY_BG)
    header.pack(fill="x", pady=(0, 15))

    tk.Label(
        header,
        text="Ver asistencia de trabajador",
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 20),
    ).pack(anchor="w")

    tk.Label(
        header,
        text=(
            "Ingrese el nombre (o parte del nombre) del trabajador tal como figura "
            "en la base de datos de registros."
        ),
        bg=PRIMARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10),
        justify="left",
        wraplength=700,
    ).pack(anchor="w", pady=(4, 0))

    # TARJETA CENTRAL
    card = tk.Frame(container, bg=SECONDARY_BG, bd=0, relief="flat")
    card.pack(fill="both", expand=True, pady=(10, 0))

    form = tk.Frame(card, bg=SECONDARY_BG)
    form.pack(fill="x", padx=30, pady=(25, 10))

    tk.Label(
        form,
        text="Trabajador",
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
        text="Ejemplo: Juan Pérez / María / López (búsqueda no sensible a mayúsculas).",
        bg=SECONDARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 9),
    ).grid(row=3, column=0, sticky="w")

    # Mensajes
    msg_label = tk.Label(
        card,
        text="",
        bg=SECONDARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10, "bold"),
        justify="left",
        wraplength=700,
    )
    msg_label.pack(anchor="w", padx=30, pady=(10, 0))

    # LÓGICA
    def calculate_attendance():
        subject_name = tx.get().strip()
        if subject_name == "":
            t = "Por favor, ingrese el nombre del trabajador."
            msg_label.config(text=t, fg=WARNING_COLOR)
            text_to_speech(t)
            return

        df_all = load_all_attendance_frames()
        if df_all is None or df_all.empty:
            t = "No se encontraron registros de asistencia."
            msg_label.config(text=t, fg=ERROR_COLOR)
            text_to_speech(t)
            return

        # Convertir Date a datetime
        df_all["Date"] = pd.to_datetime(df_all["Date"], errors="coerce")

        # Filtrar por nombre
        mask = df_all["Name"].str.lower().str.contains(subject_name.lower(), na=False)
        df = df_all[mask].copy()

        if df.empty:
            t = f"No se encontraron registros de asistencia para '{subject_name}'."
            msg_label.config(text=t, fg=ERROR_COLOR)
            text_to_speech(t)
            return

        # Días laborables (días en los que hay registros de asistencia en general)
        total_days = df_all["Date"].nunique()

        # Resumen por trabajador (dentro del filtro)
        attendance_summary = (
            df.groupby(["Enrollment", "Name"])["Date"]
            .nunique()
            .reset_index()
            .rename(columns={"Date": "DiasPresentes"})
        )

        attendance_summary["TotalDias"] = total_days
        attendance_summary["Asistencia%"] = (
            attendance_summary["DiasPresentes"] / attendance_summary["TotalDias"] * 100
        ).round(2)

        # Unir el resumen a cada registro individual
        df = df.merge(attendance_summary, on=["Enrollment", "Name"], how="left")
        df["Asistencia%"] = df["Asistencia%"].fillna(0)
        df["Asistencia"] = df["Asistencia%"].astype(str) + "%"
        df.drop(columns=["Asistencia%"], inplace=True)

        # Ordenar por fecha y hora
        df.sort_values(by=["Date", "Time"], inplace=True)

        # Mostrar tabla
        t = (
            f"Se encontraron {len(df)} registros para '{subject_name}'. "
            "Se abrirá la vista detallada."
        )
        msg_label.config(text=t, fg=ACCENT)
        text_to_speech(t)

        show_csv_window(df, f"Asistencia detallada - {subject_name}")

    # BOTONES
    buttons_frame = tk.Frame(card, bg=SECONDARY_BG)
    buttons_frame.pack(fill="x", padx=30, pady=(20, 25))

    btn_ver = tk.Button(
        buttons_frame,
        text="📘 Ver asistencia",
        command=calculate_attendance,
        bg=ACCENT,
        fg="black",
        activebackground="#4ade80",
        activeforeground="black",
        font=("Segoe UI Semibold", 11),
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=20,
        pady=9,
    )
    btn_ver.pack(side="left")

    btn_close = tk.Button(
        buttons_frame,
        text="Cerrar",
        command=subject_win.destroy,
        bg=SECONDARY_BG,
        fg=TEXT_SECONDARY,
        activebackground="#111827",
        activeforeground=TEXT_PRIMARY,
        font=("Segoe UI", 10),
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=18,
        pady=7,
    )
    btn_close.pack(side="right")

    if is_standalone:
        subject_win.mainloop()


# ==============================
# 2. VER ASISTENCIA GENERAL
# ==============================

def ver_asistencia_general(text_to_speech):
    """
    Muestra un RESUMEN GENERAL de asistencia:
    - Días presentes
    - Total de días con registros
    - Porcentaje de asistencia
    para cada trabajador.
    """
    df_all = load_all_attendance_frames()
    if df_all is None or df_all.empty:
        text_to_speech("No se encontraron registros de asistencia.")
        return

    df_all["Date"] = pd.to_datetime(df_all["Date"], errors="coerce")
    df_all.sort_values(by=["Date", "Time"], inplace=True)

    total_days = df_all["Date"].nunique()

    summary = (
        df_all.groupby(["Enrollment", "Name"])["Date"]
        .nunique()
        .reset_index()
        .rename(columns={"Date": "DiasPresentes"})
    )
    summary["TotalDias"] = total_days
    summary["Asistencia%"] = (
        summary["DiasPresentes"] / summary["TotalDias"] * 100
    ).round(2)
    summary["Asistencia%"] = summary["Asistencia%"].astype(str) + "%"

    # Ordenar por porcentaje y nombre
    summary.sort_values(
        by=["Asistencia%", "Name"], ascending=[False, True], inplace=True
    )

    text_to_speech("Mostrando resumen general de asistencia.")
    show_csv_window(summary, "Resumen general de asistencia")


# ==============================
# 3. MENÚ DE OPCIONES
# ==============================

def menu_asistencia(text_to_speech):
    """
    Menú simple para elegir entre:
    - Ver asistencia por trabajador
    - Ver resumen general
    """
    menu_win, is_standalone = create_toplevel(
        "Opciones de asistencia",
        width=520,
        height=320,
    )
    menu_win.resizable(0, 0)

    container = tk.Frame(menu_win, bg=PRIMARY_BG)
    container.pack(expand=True, fill="both", padx=30, pady=30)

    tk.Label(
        container,
        text="Opciones de asistencia",
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 20),
    ).pack(anchor="w", pady=(0, 10))

    tk.Label(
        container,
        text="Seleccione el tipo de vista que desea consultar:",
        bg=PRIMARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10),
    ).pack(anchor="w")

    card = tk.Frame(container, bg=SECONDARY_BG)
    card.pack(fill="both", expand=True, pady=(20, 0))

    # Botones
    btn1 = tk.Button(
        card,
        text="📘 Ver asistencia por trabajador",
        command=lambda: [menu_win.destroy(), subjectchoose(text_to_speech)],
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        activebackground="#111827",
        activeforeground=TEXT_PRIMARY,
        font=("Segoe UI", 11),
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=20,
        pady=10,
    )
    btn1.pack(pady=(25, 10), padx=25, fill="x")

    btn2 = tk.Button(
        card,
        text="📋 Ver resumen general",
        command=lambda: [menu_win.destroy(), ver_asistencia_general(text_to_speech)],
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        activebackground="#111827",
        activeforeground=TEXT_PRIMARY,
        font=("Segoe UI", 11),
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=20,
        pady=10,
    )
    btn2.pack(pady=(0, 20), padx=25, fill="x")

    # Cerrar
    bottom = tk.Frame(container, bg=PRIMARY_BG)
    bottom.pack(fill="x", pady=(10, 0))

    tk.Button(
        bottom,
        text="Cerrar",
        command=menu_win.destroy,
        bg=PRIMARY_BG,
        fg=TEXT_SECONDARY,
        activebackground="#111827",
        activeforeground=TEXT_PRIMARY,
        font=("Segoe UI", 10),
        bd=0,
        relief="flat",
        cursor="hand2",
        padx=16,
        pady=6,
    ).pack(side="right")

    if is_standalone:
        menu_win.mainloop()


# ==============================
# PRUEBA DIRECTA (OPCIONAL)
# ==============================

if __name__ == "__main__":
    # Pequeña función de prueba de TTS
    def _tts(msg):
        print("[TTS]", msg)

    menu_asistencia(_tts)
