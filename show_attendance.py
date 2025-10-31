# show_attendance.py
# muestra asistencia (izquierda) + intentos (derecha) PERO
# los intentos se AGRUPAN para no ver 50 filas casi iguales

import os
import glob
import csv
import pandas as pd
import tkinter as tk
from tkinter import ttk


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
            if os.path.getsize(f) == 0:
                continue
            try:
                df = pd.read_csv(f, dtype=str)
            except:
                continue
            # asegurar columnas nuevas
            for col in ["Reason", "Zone", "EPP_Detected", "CaptureSeconds"]:
                if col not in df.columns:
                    df[col] = ""
            dfs.append(df)
        if not dfs:
            return pd.DataFrame(columns=[
                "Enrollment", "Name", "Date", "Time", "Status",
                "Reason", "Zone", "EPP_Detected", "CaptureSeconds"
            ])
        df = pd.concat(dfs, ignore_index=True)
        return df

    def leer_intentos_raw():
        pattern = os.path.join(attendance_base, "intentos_*.csv")
        files = glob.glob(pattern)
        dfs = []
        for f in files:
            if os.path.getsize(f) == 0:
                continue
            try:
                df = pd.read_csv(f, dtype=str)
            except:
                continue
            for col in ["Reason", "Zone", "EPP_Detected", "CaptureSeconds"]:
                if col not in df.columns:
                    df[col] = ""
            dfs.append(df)
        if not dfs:
            return pd.DataFrame(columns=[
                "Enrollment", "Name", "Date", "Time", "Status",
                "Reason", "Zone", "EPP_Detected", "CaptureSeconds"
            ])
        df = pd.concat(dfs, ignore_index=True)
        return df

    # 👇 este es el truco: agrupar para NO mostrar repetidos
    def agrupar_intentos(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        # 1) convertir fecha
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        # 2) crear un “bucket” de minuto para juntar capturas muy seguidas
        #    si no hay Time, dejamos vacío
        if "Time" in df.columns:
            df["MinuteBucket"] = df["Time"].fillna("").str[:5]  # HH:MM
        else:
            df["MinuteBucket"] = ""

        # 3) nos quedamos con 1 por:
        #    persona + día + zona + razón + minuto
        #    (esto ya quita la mayoría de repetidos)
        grouped = (
            df.sort_values(["Date", "Time"])
              .groupby(
                  [
                      "Enrollment",
                      "Name",
                      "Date",
                      "Zone",
                      "Reason",
                      "MinuteBucket",
                  ],
                  as_index=False
              )
              .first()
        )

        # 4) ordenamos bonito
        grouped = grouped.sort_values(["Date", "Time"])
        return grouped

    # -------------------------------------------------
    # ventana
    # -------------------------------------------------
    win = tk.Tk()
    win.title("Asistencia e Intentos")
    win.geometry("1150x520")
    win.configure(bg="black")

    tk.Label(
        win,
        text="Asistencia vs Intentos",
        bg="black",
        fg="green",
        font=("arial", 22, "bold"),
    ).pack(pady=5)

    # filtros
    filtro_frame = tk.Frame(win, bg="black")
    filtro_frame.pack(fill="x", pady=5)

    tk.Label(
        filtro_frame,
        text="Nombre contiene:",
        bg="black",
        fg="yellow"
    ).grid(row=0, column=0, padx=5)

    entry_nombre = tk.Entry(
        filtro_frame,
        width=20,
        bg="black",
        fg="yellow",
        font=("times", 12, "bold"),
    )
    entry_nombre.grid(row=0, column=1, padx=5)

    tk.Label(
        filtro_frame,
        text="Zona:",
        bg="black",
        fg="yellow"
    ).grid(row=0, column=2, padx=5)

    # leer zonas de archivos de asistencia e intentos
    zonas_existentes = set()
    for pat in ["asistencia_*.csv", "intentos_*.csv"]:
        files = glob.glob(os.path.join(attendance_base, pat))
        for f in files:
            try:
                dfz = pd.read_csv(f, dtype=str)
                if "Zone" in dfz.columns:
                    zonas_existentes.update(dfz["Zone"].dropna().tolist())
            except:
                pass

    zonas_lista = ["Todas"] + sorted([z for z in zonas_existentes if z != ""])
    combo_zona = ttk.Combobox(
        filtro_frame,
        values=zonas_lista,
        state="readonly",
        width=15
    )
    combo_zona.grid(row=0, column=3, padx=5)
    combo_zona.set("Todas")

    # botones de acción
    def exportar_asistencia():
        if not hasattr(win, "df_asistencia_filtrada"):
            text_to_speech("No hay asistencia filtrada para exportar.")
            return
        out = os.path.join(attendance_base, "reporte_asistencia_filtrada.csv")
        win.df_asistencia_filtrada.to_csv(out, index=False, encoding="utf-8-sig")
        text_to_speech("Reporte de asistencia guardado.")

    def exportar_intentos():
        if not hasattr(win, "df_intentos_filtrados"):
            text_to_speech("No hay intentos filtrados para exportar.")
            return
        out = os.path.join(attendance_base, "reporte_intentos_filtrados.csv")
        win.df_intentos_filtrados.to_csv(out, index=False, encoding="utf-8-sig")
        text_to_speech("Reporte de intentos guardado.")

    btn_filtrar = tk.Button(
        filtro_frame,
        text="Filtrar",
        bg="black",
        fg="yellow",
        font=("times", 12, "bold"),
        command=lambda: aplicar_filtros(),
    )
    btn_filtrar.grid(row=0, column=4, padx=8)

    btn_exp_as = tk.Button(
        filtro_frame,
        text="⭳ Exportar Asistencia",
        bg="darkgreen",
        fg="white",
        command=exportar_asistencia,
    )
    btn_exp_as.grid(row=0, column=5, padx=8)

    btn_exp_in = tk.Button(
        filtro_frame,
        text="⭳ Exportar Intentos",
        bg="darkred",
        fg="white",
        command=exportar_intentos,
    )
    btn_exp_in.grid(row=0, column=6, padx=8)

    # -------------------------------------------------
    # tablas lado a lado
    # -------------------------------------------------
    tables_frame = tk.Frame(win, bg="black")
    tables_frame.pack(fill="both", expand=True, pady=5)

    # ---- tabla asistencia (izq) ----
    frame_as = tk.LabelFrame(
        tables_frame,
        text="ASISTENCIA",
        bg="black",
        fg="white",
        font=("arial", 11, "bold"),
    )
    frame_as.pack(side="left", fill="both", expand=True, padx=5)

    cols_as = ("Enrollment", "Name", "Date", "Time", "Status", "Zone", "Reason")
    tree_as = ttk.Treeview(frame_as, columns=cols_as, show="headings", height=12)
    for c in cols_as:
        tree_as.heading(c, text=c)
        tree_as.column(c, width=100, anchor="w")
    tree_as.pack(side="left", fill="both", expand=True)

    scroll_as = ttk.Scrollbar(frame_as, orient="vertical", command=tree_as.yview)
    tree_as.configure(yscroll=scroll_as.set)
    scroll_as.pack(side="right", fill="y")

    # ---- tabla intentos (der) ----
    frame_in = tk.LabelFrame(
        tables_frame,
        text="INTENTOS / FALLIDOS / FORZADOS (agrupados)",
        bg="black",
        fg="white",
        font=("arial", 11, "bold"),
    )
    frame_in.pack(side="left", fill="both", expand=True, padx=5)

    cols_in = ("Enrollment", "Name", "Date", "Time", "Status", "Zone", "Reason")
    tree_in = ttk.Treeview(frame_in, columns=cols_in, show="headings", height=12)
    for c in cols_in:
        tree_in.heading(c, text=c)
        tree_in.column(c, width=100, anchor="w")
    tree_in.pack(side="left", fill="both", expand=True)

    scroll_in = ttk.Scrollbar(frame_in, orient="vertical", command=tree_in.yview)
    tree_in.configure(yscroll=scroll_in.set)
    scroll_in.pack(side="right", fill="y")

    # -------------------------------------------------
    # lógica de filtrado
    # -------------------------------------------------
    def aplicar_filtros():
        nombre = entry_nombre.get().strip().lower()
        zona = combo_zona.get().strip()

        df_as = leer_asistencias()
        df_in_raw = leer_intentos_raw()

        # asistencia: SOLO las que te interesan
        df_as = df_as[df_as["Status"].isin(["Entrada", "Salida", "EntradaF"])]

        # INTENTOS: los agrupamos para que no salgan tantos
        df_in = agrupar_intentos(df_in_raw)

        if nombre != "":
            df_as = df_as[df_as["Name"].str.lower().str.contains(nombre)]
            df_in = df_in[df_in["Name"].str.lower().str.contains(nombre)]

        if zona != "" and zona != "Todas":
            df_as = df_as[df_as["Zone"] == zona]
            df_in = df_in[df_in["Zone"] == zona]

        # ordenar por fecha/hora si hay
        if "Date" in df_as.columns and "Time" in df_as.columns:
            df_as["Date"] = pd.to_datetime(df_as["Date"], errors="coerce")
            df_as = df_as.sort_values(by=["Date", "Time"])

        if "Date" in df_in.columns and "Time" in df_in.columns:
            df_in["Date"] = pd.to_datetime(df_in["Date"], errors="coerce")
            df_in = df_in.sort_values(by=["Date", "Time"])

        # guardar en la ventana para exportar
        win.df_asistencia_filtrada = df_as
        win.df_intentos_filtrados = df_in

        # limpiar tablas
        for i in tree_as.get_children():
            tree_as.delete(i)
        for i in tree_in.get_children():
            tree_in.delete(i)

        # llenar asistencia
        for _, row in df_as.iterrows():
            tree_as.insert(
                "",
                "end",
                values=(
                    row.get("Enrollment", ""),
                    row.get("Name", ""),
                    str(row.get("Date", ""))[:10],
                    row.get("Time", ""),
                    row.get("Status", ""),
                    row.get("Zone", ""),
                    row.get("Reason", ""),
                ),
            )

        # llenar intentos AGRUPADOS
        for _, row in df_in.iterrows():
            tree_in.insert(
                "",
                "end",
                values=(
                    row.get("Enrollment", ""),
                    row.get("Name", ""),
                    str(row.get("Date", ""))[:10],
                    row.get("Time", ""),
                    row.get("Status", ""),
                    row.get("Zone", ""),
                    row.get("Reason", ""),
                ),
            )

        if df_as.empty and df_in.empty:
            text_to_speech("No hay registros que coincidan con el filtro.")

    # primera carga
    aplicar_filtros()

    win.mainloop()


def menu_asistencia(text_to_speech):
    subjectchoose(text_to_speech)
