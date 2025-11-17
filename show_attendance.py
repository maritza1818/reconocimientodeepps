# show_attendance.py
# Muestra asistencia (izquierda) + intentos (derecha)
# Interfaz modernizada para IHC: tema oscuro, filtros y resumen.

import os
import glob
import pandas as pd
import tkinter as tk
from tkinter import ttk

# Paleta coherente con el resto del sistema
PRIMARY_BG = "#020617"      # fondo general
PANEL_BG = "#0f172a"        # paneles / tarjetas
SURFACE_BG = "#020617"
TEXT_PRIMARY = "#e5e7eb"
TEXT_SECONDARY = "#9ca3af"
ACCENT = "#22c55e"
ACCENT_SECONDARY = "#38bdf8"
DANGER = "#f97373"
WARNING = "#facc15"


def subjectchoose(text_to_speech):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    attendance_base = os.path.join(BASE_DIR, "Attendance")

    # -------------------------------------------------
    # helpers de lectura
    # -------------------------------------------------
    def leer_asistencias():
        pattern = os.path.join(attendance_base, "asistencia_*.csv")
        files = glob.glob(pattern)
        dfs = []
        for f in files:
            if not os.path.exists(f) or os.path.getsize(f) == 0:
                continue
            try:
                df = pd.read_csv(f, dtype=str)
            except pd.errors.EmptyDataError:
                continue
            for col in ["Reason", "Zone", "EPP_Detected", "CaptureSeconds"]:
                if col not in df.columns:
                    df[col] = ""
            dfs.append(df)
        if not dfs:
            return pd.DataFrame(
                columns=[
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
            )
        df = pd.concat(dfs, ignore_index=True)
        return df

    def leer_intentos():
        pattern = os.path.join(attendance_base, "intentos_*.csv")
        files = glob.glob(pattern)
        dfs = []
        for f in files:
            if not os.path.exists(f) or os.path.getsize(f) == 0:
                continue
            try:
                df = pd.read_csv(f, dtype=str)
            except pd.errors.EmptyDataError:
                continue
            for col in ["Reason", "Zone", "EPP_Detected", "CaptureSeconds"]:
                if col not in df.columns:
                    df[col] = ""
            dfs.append(df)
        if not dfs:
            return pd.DataFrame(
                columns=[
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
            )
        df = pd.concat(dfs, ignore_index=True)
        return df

    # -------------------------------------------------
    # ventana principal
    # -------------------------------------------------
    win = tk.Toplevel()
    win.title("Histórico de Asistencia y EPP")
    win.geometry("1180x640")
    win.configure(bg=PRIMARY_BG)
    win.resizable(0, 0)

    # --------- estilos ttk (Treeview oscuro) ----------
    style = ttk.Style(win)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(
        "Dark.Treeview",
        background=PANEL_BG,
        foreground=TEXT_PRIMARY,
        fieldbackground=PANEL_BG,
        bordercolor=PANEL_BG,
        borderwidth=0,
        rowheight=22,
    )
    style.map(
        "Dark.Treeview",
        background=[("selected", "#1d4ed8")],
        foreground=[("selected", "#ffffff")],
    )
    style.configure(
        "Dark.Treeview.Heading",
        background=PRIMARY_BG,
        foreground=TEXT_PRIMARY,
        relief="flat",
        font=("Segoe UI Semibold", 9),
    )

    # -------------------------------------------------
    # HEADER
    # -------------------------------------------------
    top = tk.Frame(win, bg=PRIMARY_BG)
    top.pack(fill="x", padx=16, pady=(10, 4))

    title_lbl = tk.Label(
        top,
        text="Histórico de Asistencia e Intentos (EPP + Códigos)",
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 16),
        anchor="w",
    )
    title_lbl.pack(side="left")

    summary_lbl = tk.Label(
        top,
        text="",
        bg=PRIMARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10),
        anchor="e",
    )
    summary_lbl.pack(side="right")

    # -------------------------------------------------
    # FILTROS
    # -------------------------------------------------
    filtro_frame = tk.Frame(win, bg=PANEL_BG)
    filtro_frame.pack(fill="x", padx=16, pady=(0, 8))

    # Nombre
    tk.Label(
        filtro_frame,
        text="Nombre contiene:",
        bg=PANEL_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10),
    ).grid(row=0, column=0, padx=(12, 4), pady=8, sticky="w")

    entry_nombre = tk.Entry(
        filtro_frame,
        width=24,
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        insertbackground=TEXT_PRIMARY,
        relief="flat",
        font=("Segoe UI", 10),
    )
    entry_nombre.grid(row=0, column=1, padx=4, pady=8, sticky="w")

    # Desde
    tk.Label(
        filtro_frame,
        text="Desde (YYYY-MM-DD):",
        bg=PANEL_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10),
    ).grid(row=0, column=2, padx=(20, 4), pady=8, sticky="w")

    entry_desde = tk.Entry(
        filtro_frame,
        width=14,
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        insertbackground=TEXT_PRIMARY,
        relief="flat",
        font=("Segoe UI", 10),
    )
    entry_desde.grid(row=0, column=3, padx=4, pady=8, sticky="w")

    # Hasta
    tk.Label(
        filtro_frame,
        text="Hasta (YYYY-MM-DD):",
        bg=PANEL_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10),
    ).grid(row=0, column=4, padx=(20, 4), pady=8, sticky="w")

    entry_hasta = tk.Entry(
        filtro_frame,
        width=14,
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        insertbackground=TEXT_PRIMARY,
        relief="flat",
        font=("Segoe UI", 10),
    )
    entry_hasta.grid(row=0, column=5, padx=4, pady=8, sticky="w")

    # Botones de acción
    btn_frame = tk.Frame(filtro_frame, bg=PANEL_BG)
    btn_frame.grid(row=0, column=6, padx=(20, 10), pady=4, sticky="e")

    def limpiar_filtros():
        entry_nombre.delete(0, "end")
        entry_desde.delete(0, "end")
        entry_hasta.delete(0, "end")
        aplicar_filtros(voz=True)

    btn_aplicar = tk.Button(
        btn_frame,
        text="Aplicar filtros",
        command=lambda: aplicar_filtros(voz=True),
        bg=ACCENT_SECONDARY,
        fg="#020617",
        font=("Segoe UI Semibold", 9),
        bd=0,
        padx=10,
        pady=4,
        cursor="hand2",
    )
    btn_aplicar.pack(side="left", padx=4)

    btn_limpiar = tk.Button(
        btn_frame,
        text="Limpiar",
        command=limpiar_filtros,
        bg="#1f2937",
        fg=TEXT_PRIMARY,
        font=("Segoe UI", 9),
        bd=0,
        padx=10,
        pady=4,
        cursor="hand2",
    )
    btn_limpiar.pack(side="left", padx=4)

    btn_cerrar = tk.Button(
        btn_frame,
        text="Cerrar",
        command=win.destroy,
        bg="#b91c1c",
        fg="white",
        font=("Segoe UI", 9),
        bd=0,
        padx=10,
        pady=4,
        cursor="hand2",
    )
    btn_cerrar.pack(side="left", padx=4)

    # -------------------------------------------------
    # SPLIT: IZQUIERDA (asistencia) / DERECHA (intentos)
    # -------------------------------------------------
    split = tk.Frame(win, bg=PRIMARY_BG)
    split.pack(fill="both", expand=True, padx=16, pady=(4, 12))

    # ---------- ASISTENCIA ----------
    left = tk.Frame(split, bg=PRIMARY_BG)
    left.pack(side="left", fill="both", expand=True, padx=(0, 8))

    tk.Label(
        left,
        text="Asistencia registrada",
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 12),
    ).pack(anchor="w", pady=(0, 4))

    as_frame = tk.Frame(left, bg=PANEL_BG)
    as_frame.pack(fill="both", expand=True)

    cols_asistencia = (
        "Enrollment",
        "Name",
        "Date",
        "Time",
        "Status",
        "Zone",
        "EPP_Detected",
        "Reason",
    )

    tree_as = ttk.Treeview(
        as_frame,
        columns=cols_asistencia,
        show="headings",
        height=16,
        style="Dark.Treeview",
    )

    for c in cols_asistencia:
        tree_as.heading(c, text=c, anchor="w", style="Dark.Treeview.Heading")
        if c in ("Enrollment", "Date", "Time", "Status"):
            width = 80
        elif c == "Zone":
            width = 100
        elif c == "EPP_Detected":
            width = 150
        else:
            width = 150
        tree_as.column(c, width=width, anchor="w")

    scroll_y_as = ttk.Scrollbar(as_frame, orient="vertical", command=tree_as.yview)
    tree_as.configure(yscrollcommand=scroll_y_as.set)

    tree_as.pack(side="left", fill="both", expand=True)
    scroll_y_as.pack(side="right", fill="y")

    # tags para colorear filas
    tree_as.tag_configure("ok", foreground=ACCENT)
    tree_as.tag_configure("forzado", foreground=WARNING)
    tree_as.tag_configure("fallo", foreground=DANGER)

    # ---------- INTENTOS ----------
    right = tk.Frame(split, bg=PRIMARY_BG)
    right.pack(side="right", fill="both", expand=True, padx=(8, 0))

    tk.Label(
        right,
        text="Intentos / rechazos",
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 12),
    ).pack(anchor="w", pady=(0, 4))

    in_frame = tk.Frame(right, bg=PANEL_BG)
    in_frame.pack(fill="both", expand=True)

    cols_intentos = (
        "Enrollment",
        "Name",
        "Date",
        "Time",
        "Status",
        "Zone",
        "EPP_Detected",
        "Reason",
    )

    tree_in = ttk.Treeview(
        in_frame,
        columns=cols_intentos,
        show="headings",
        height=16,
        style="Dark.Treeview",
    )

    for c in cols_intentos:
        tree_in.heading(c, text=c, anchor="w", style="Dark.Treeview.Heading")
        if c in ("Enrollment", "Date", "Time", "Status"):
            width = 80
        elif c == "Zone":
            width = 100
        elif c == "EPP_Detected":
            width = 150
        else:
            width = 150
        tree_in.column(c, width=width, anchor="w")

    scroll_y_in = ttk.Scrollbar(in_frame, orient="vertical", command=tree_in.yview)
    tree_in.configure(yscrollcommand=scroll_y_in.set)

    tree_in.pack(side="left", fill="both", expand=True)
    scroll_y_in.pack(side="right", fill="y")

    tree_in.tag_configure("ok", foreground=ACCENT)
    tree_in.tag_configure("forzado", foreground=WARNING)
    tree_in.tag_configure("fallo", foreground=DANGER)

    # -------------------------------------------------
    # Lógica de filtros
    # -------------------------------------------------
    df_as_global = leer_asistencias()
    df_in_global = leer_intentos()

    def insertar_row_tree(tree, row, cols, es_intento=False):
        """
        Inserta una fila en el Treeview con un tag según el estado / razón.
        """
        status = (row.get("Status", "") or "").upper()
        reason = (row.get("Reason", "") or "")

        tag = ""
        if status in ("ENTRADA", "SALIDA") and reason.strip() in ("", "OK"):
            tag = "ok"
        elif "FORZADO" in reason.upper() or status.startswith("REG_FORZADO"):
            tag = "forzado"
        elif status.startswith("NO_") or "FALTA" in reason.upper():
            tag = "fallo"

        values = [
            row.get("Enrollment", ""),
            row.get("Name", ""),
            str(row.get("Date", ""))[:10],
            row.get("Time", ""),
            row.get("Status", ""),
            row.get("Zone", ""),
            row.get("EPP_Detected", ""),
            row.get("Reason", ""),
        ]
        tree.insert("", "end", values=values, tags=(tag,))

    def aplicar_filtros(voz=False):
        nombre_f = entry_nombre.get().strip().lower()
        desde_f = entry_desde.get().strip()
        hasta_f = entry_hasta.get().strip()

        df_as = df_as_global.copy()
        df_in = df_in_global.copy()

        # Filtro por nombre (contiene)
        if nombre_f:
            df_as = df_as[df_as["Name"].fillna("").str.lower().str.contains(nombre_f)]
            df_in = df_in[df_in["Name"].fillna("").str.lower().str.contains(nombre_f)]

        # Filtro por rango de fechas (las fechas vienen en formato 'YYYY-MM-DD')
        if desde_f:
            df_as = df_as[df_as["Date"] >= desde_f]
            df_in = df_in[df_in["Date"] >= desde_f]
        if hasta_f:
            df_as = df_as[df_as["Date"] <= hasta_f]
            df_in = df_in[df_in["Date"] <= hasta_f]

        # Limpiar tablas
        for item in tree_as.get_children():
            tree_as.delete(item)
        for item in tree_in.get_children():
            tree_in.delete(item)

        # Ordenar por fecha + hora descendente
        if not df_as.empty:
            df_as["Date"] = pd.to_datetime(df_as["Date"], errors="coerce")
            df_as = df_as.sort_values(by=["Date", "Time"], ascending=False)

        if not df_in.empty:
            df_in["Date"] = pd.to_datetime(df_in["Date"], errors="coerce")
            df_in = df_in.sort_values(by=["Date", "Time"], ascending=False)

        # Rellenar asistencia
        for _, row in df_as.iterrows():
            insertar_row_tree(tree_as, row, cols_asistencia)

        # Rellenar intentos
        for _, row in df_in.iterrows():
            insertar_row_tree(tree_in, row, cols_intentos, es_intento=True)

        # actualizar resumen
        summary_lbl.config(
            text=f"Asistencias: {len(df_as)}   |   Intentos: {len(df_in)}"
        )

        # Mensaje por voz
        if voz and text_to_speech:
            if df_as.empty and df_in.empty:
                text_to_speech("No hay registros que coincidan con el filtro.")
            else:
                msg = f"Se encontraron {len(df_as)} asistencias y {len(df_in)} intentos."
                text_to_speech(msg)

    # primera carga (sin filtros, pero sin hablar)
    aplicar_filtros(voz=False)

    win.mainloop()


def menu_asistencia(text_to_speech):
    subjectchoose(text_to_speech)
