# dashboard.py
import tkinter as tk
from tkinter import ttk
import os
import glob
import pandas as pd
import datetime

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except Exception:
    PIL_OK = False

# =========================
# RUTAS Y CONSTANTES
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ATTENDANCE_DIR = os.path.join(BASE_DIR, "Attendance")
TRAINING_DIR = os.path.join(BASE_DIR, "TrainingImage")

# Paleta coherente con attendance.py
PRIMARY_BG = "#020617"
CARD_BG = "#0f172a"
TEXT_PRIMARY = "#e5e7eb"
TEXT_SECONDARY = "#9ca3af"
ACCENT = "#22c55e"
ACCENT_SECONDARY = "#38bdf8"
ERROR_COLOR = "#f97373"
WARNING_COLOR = "#facc15"


# =========================
# HELPERS DE DATOS
# =========================

ASIST_COLS = [
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


def _leer_csv_dia(path: str):
    """Lee un CSV de asistencia/intentoss del día, asegurando columnas."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame(columns=ASIST_COLS)
    df = pd.read_csv(path, dtype=str)
    for c in ASIST_COLS:
        if c not in df.columns:
            df[c] = ""
    return df[ASIST_COLS]


def leer_asistencias_hoy():
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(ATTENDANCE_DIR, f"asistencia_{hoy}.csv")
    return _leer_csv_dia(path)


def leer_intentos_hoy():
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(ATTENDANCE_DIR, f"intentos_{hoy}.csv")
    return _leer_csv_dia(path)


def buscar_foto_por_enrollment(enrollment: str):
    """
    Intenta encontrar una foto en TrainingImage que contenga el enrollment.
    Ejemplos comunes:
      - Nombre.Enrollment.1.jpg
      - Enrollment.1.jpg
    Si no la encuentra, devuelve None.
    """
    if not PIL_OK or not enrollment:
        return None

    patrones = [
        os.path.join(TRAINING_DIR, f"*.{enrollment}.*"),
        os.path.join(TRAINING_DIR, f"{enrollment}.*"),
    ]
    for pat in patrones:
        files = glob.glob(pat)
        if files:
            return files[0]
    return None


# =========================
# DASHBOARD
# =========================

def build_dashboard():
    """Crea la ventana de dashboard como Toplevel."""
    # Reusar root existente si lo hay
    root = tk._default_root
    if root is None:
        win = tk.Tk()
    else:
        win = tk.Toplevel(root)

    win.title("Dashboard de Asistencia + EPP")
    win.geometry("1180x640")
    win.configure(bg=PRIMARY_BG)
    win.resizable(0, 0)

    # ---------- HEADER ----------
    top = tk.Frame(win, bg=PRIMARY_BG)
    top.pack(fill="x", pady=6, padx=12)

    titulo = tk.Label(
        top,
        text="Dashboard de Asistencia + EPP",
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 18),
        anchor="w",
    )
    titulo.pack(side="left")

    lbl_fecha = tk.Label(
        top,
        text="",
        bg=PRIMARY_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10),
        anchor="e",
    )
    lbl_fecha.pack(side="right")

    def actualizar_fecha():
        if not win.winfo_exists():
            return
        ahora = datetime.datetime.now()
        lbl_fecha.config(text=ahora.strftime("%d/%m/%Y   %H:%M:%S"))
        try:
            win.after(1000, actualizar_fecha)
        except tk.TclError:
            pass

    actualizar_fecha()

    # ---------- TARJETAS SUPERIORES ----------
    cards = tk.Frame(win, bg=PRIMARY_BG)
    cards.pack(fill="x", pady=4, padx=12)

    def make_card(parent, title, bg_color="#0b1120"):
        frame = tk.Frame(parent, bg=bg_color, bd=0, relief="flat")
        frame.pack(side="left", padx=8, pady=4, fill="x", expand=True)
        lbl_title = tk.Label(
            frame,
            text=title,
            bg=bg_color,
            fg=TEXT_PRIMARY,
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        lbl_title.pack(fill="x", padx=10, pady=(8, 0))
        return frame

    card1 = make_card(cards, "Asistencias HOY")
    card2 = make_card(cards, "Intentos fallidos HOY")
    card3 = make_card(cards, "Cumplimiento EPP")
    card4 = make_card(cards, "Top intentos por persona")

    val_asistencias_hoy = tk.Label(
        card1,
        text="0",
        bg=card1["bg"],
        fg=ACCENT,
        font=("Segoe UI", 24, "bold"),
    )
    val_asistencias_hoy.pack(pady=(2, 10))

    val_intentos_hoy = tk.Label(
        card2,
        text="0",
        bg=card2["bg"],
        fg=ERROR_COLOR,
        font=("Segoe UI", 24, "bold"),
    )
    val_intentos_hoy.pack(pady=(2, 10))

    pb = ttk.Progressbar(
        card3,
        orient="horizontal",
        length=160,
        mode="determinate",
    )
    pb.pack(pady=(4, 2), padx=10, anchor="w")
    val_cumplimiento = tk.Label(
        card3,
        text="0%",
        bg=card3["bg"],
        fg=ACCENT,
        font=("Segoe UI", 14, "bold"),
        anchor="w",
    )
    val_cumplimiento.pack(pady=(0, 8), padx=10, anchor="w")

    # resumen top persona (solo texto)
    val_top_persona = tk.Label(
        card4,
        text="Sin datos",
        bg=card4["bg"],
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10),
        justify="left",
        anchor="w",
        wraplength=220,
    )
    val_top_persona.pack(pady=(4, 8), padx=10, anchor="w")

    # ---------- CONTENEDOR CENTRAL ----------
    middle = tk.Frame(win, bg=PRIMARY_BG)
    middle.pack(fill="both", expand=True, padx=12, pady=4)

    # LEFT: tabla por zona + gráfico
    left = tk.Frame(middle, bg=PRIMARY_BG)
    left.pack(side="left", fill="both", expand=True, padx=(0, 6))

    tk.Label(
        left,
        text="Por zona (hoy)",
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 12),
        anchor="w",
    ).pack(anchor="w")

    cols_zona = ("Zona", "OK", "Forzados", "Fallidos")
    tree_zona = ttk.Treeview(left, columns=cols_zona, show="headings", height=6)
    for c in cols_zona:
        tree_zona.heading(c, text=c)
        tree_zona.column(c, width=90, anchor="w")
    tree_zona.pack(fill="x", pady=4)

    # gráfico barras
    chart_frame = tk.Frame(left, bg=PRIMARY_BG)
    chart_frame.pack(fill="both", expand=True, pady=(4, 0))
    chart_canvas = tk.Canvas(
        chart_frame,
        bg="#020617",
        height=180,
        highlightthickness=0,
        bd=0,
    )
    chart_canvas.pack(fill="both", expand=True)

    # RIGHT: tabla de intentos
    right = tk.Frame(middle, bg=PRIMARY_BG)
    right.pack(side="left", fill="both", expand=True, padx=(6, 0))

    tk.Label(
        right,
        text="Últimos intentos (hoy)",
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 12),
        anchor="w",
    ).pack(anchor="w")

    cols_int = ("Fecha", "Hora", "Trabajador", "Zona", "Motivo")
    tree_int = ttk.Treeview(right, columns=cols_int, show="headings", height=10)
    for c in cols_int:
        tree_int.heading(c, text=c)
        if c == "Motivo":
            tree_int.column(c, width=260, anchor="w")
        elif c == "Trabajador":
            tree_int.column(c, width=150, anchor="w")
        else:
            tree_int.column(c, width=80, anchor="w")
    tree_int.pack(fill="both", expand=True, pady=4)

    # ---------- PANEL INFERIOR: TOP PERSONAS CON MÁS INTENTOS ----------
    bottom = tk.Frame(win, bg=PRIMARY_BG)
    bottom.pack(fill="x", padx=12, pady=(0, 10))

    tk.Label(
        bottom,
        text="Personas con más intentos (hoy)",
        bg=PRIMARY_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 12),
        anchor="w",
    ).pack(anchor="w", pady=(0, 4))

    panel_top = tk.Frame(bottom, bg=PRIMARY_BG)
    panel_top.pack(fill="x")
    panel_top.images_refs = []  # para mantener referencias a PhotoImage

    # ---------- FUNCIONES DE DIBUJO Y REFRESCO ----------

    def dibujar_grafico_barras(datos_por_zona):
        """Dibuja un gráfico de barras horizontal sencillo."""
        chart_canvas.delete("all")
        if not datos_por_zona:
            chart_canvas.create_text(
                200,
                80,
                text="Sin datos para graficar",
                fill=TEXT_SECONDARY,
                font=("Segoe UI", 10),
            )
            return

        zonas = [z for z, _ in datos_por_zona]
        valores = [v for _, v in datos_por_zona]
        max_val = max(valores) if valores else 1

        width = chart_canvas.winfo_width()
        height = chart_canvas.winfo_height()
        if width <= 1:
            width = 400
        if height <= 1:
            height = 180

        margin_x = 40
        margin_y = 20
        usable_width = width - 2 * margin_x
        usable_height = height - 2 * margin_y

        bar_height = usable_height / max(len(zonas), 1) * 0.6
        spacing = usable_height / max(len(zonas), 1)

        for i, (zona, val) in enumerate(datos_por_zona):
            top_y = margin_y + i * spacing
            bottom_y = top_y + bar_height
            bar_len = 0 if max_val == 0 else (val / max_val) * usable_width

            chart_canvas.create_rectangle(
                margin_x,
                top_y,
                margin_x + bar_len,
                bottom_y,
                fill=ACCENT_SECONDARY,
                outline="",
            )
            chart_canvas.create_text(
                margin_x - 5,
                (top_y + bottom_y) / 2,
                text=zona or "(sin zona)",
                anchor="e",
                fill=TEXT_PRIMARY,
                font=("Segoe UI", 9),
            )
            chart_canvas.create_text(
                margin_x + bar_len + 4,
                (top_y + bottom_y) / 2,
                text=str(val),
                anchor="w",
                fill=TEXT_SECONDARY,
                font=("Segoe UI", 9),
            )

    def actualizar_panel_top(df_int):
        # limpiamos
        for w in panel_top.winfo_children():
            w.destroy()
        panel_top.images_refs.clear()

        if df_int.empty:
            lbl = tk.Label(
                panel_top,
                text="Sin intentos registrados.",
                bg=PRIMARY_BG,
                fg=TEXT_SECONDARY,
                font=("Segoe UI", 9),
                anchor="w",
            )
            lbl.pack(anchor="w")
            return

        conteo = (
            df_int.groupby(["Enrollment", "Name"])
            .size()
            .reset_index(name="Intentos")
            .sort_values(by="Intentos", ascending=False)
        )

        # Mostrar resumen corto en la tarjeta 4
        top1 = conteo.head(1)
        if not top1.empty:
            r = top1.iloc[0]
            val_top_persona.config(
                text=f"{r['Name']} (ID {r['Enrollment']})\nIntentos hoy: {r['Intentos']}"
            )
        else:
            val_top_persona.config(text="Sin datos")

        top3 = conteo.head(3).to_dict(orient="records")
        for person in top3:
            frm = tk.Frame(panel_top, bg=CARD_BG)
            frm.pack(side="left", padx=6, pady=3, fill="y")

            enr = str(person.get("Enrollment", ""))
            name = str(person.get("Name", ""))
            intentos = int(person.get("Intentos", 0))

            # Imagen (si existe)
            img_label = tk.Label(frm, bg=CARD_BG)
            img_label.pack(padx=8, pady=(6, 2))

            if PIL_OK and enr:
                foto_path = buscar_foto_por_enrollment(enr)
            else:
                foto_path = None

            if foto_path and os.path.exists(foto_path):
                try:
                    img = Image.open(foto_path)
                    img = img.resize((72, 72))
                    img_tk = ImageTk.PhotoImage(img)
                    img_label.config(image=img_tk)
                    panel_top.images_refs.append(img_tk)
                except Exception:
                    img_label.config(text="Sin\nfoto", fg=TEXT_SECONDARY)
            else:
                img_label.config(text="Sin\nfoto", fg=TEXT_SECONDARY)

            tk.Label(
                frm,
                text=name,
                bg=CARD_BG,
                fg=TEXT_PRIMARY,
                font=("Segoe UI", 9, "bold"),
                wraplength=120,
                justify="center",
            ).pack(padx=6)
            tk.Label(
                frm,
                text=f"Intentos: {intentos}",
                bg=CARD_BG,
                fg=TEXT_SECONDARY,
                font=("Segoe UI", 9),
            ).pack(pady=(0, 6))

    def pintar_dashboard(df_as, df_in):
        # totales básicos
        asistencias_hoy = len(df_as)
        intentos_hoy = len(df_in)

        val_asistencias_hoy.config(text=str(asistencias_hoy))
        val_intentos_hoy.config(text=str(intentos_hoy))

        # cumplimiento EPP
        if df_as.empty and df_in.empty:
            cumplimiento = 0
        else:
            # Consideramos "OK" los registros de asistencia con Reason vacío
            ok_rows = df_as[df_as["Reason"].fillna("") == ""]
            total_revisados = len(ok_rows) + len(df_in)
            cumplimiento = 0 if total_revisados == 0 else (len(ok_rows) / total_revisados) * 100

        cumplimiento = max(0, min(100, cumplimiento))
        pb["value"] = cumplimiento
        val_cumplimiento.config(text=f"{cumplimiento:.1f}%")

        # tabla por zona
        for i in tree_zona.get_children():
            tree_zona.delete(i)

        zonas = sorted(
            {z for z in df_as["Zone"].dropna().tolist() + df_in["Zone"].dropna().tolist() if z}
        )

        datos_grafico = []
        for z in zonas:
            df_as_z = df_as[df_as["Zone"] == z]
            df_in_z = df_in[df_in["Zone"] == z]

            ok_z = df_as_z[df_as_z["Reason"].fillna("") == ""]
            forzados_z = df_as_z[df_as_z["Reason"].fillna("").str.startswith("FORZADO")]
            fallidos_z = df_in_z[df_in_z["Status"].isin(["RECHAZADO", "NO_REGISTRADO"])]

            tree_zona.insert(
                "",
                "end",
                values=(z, len(ok_z), len(forzados_z), len(fallidos_z)),
            )

            total_mov = len(ok_z) + len(forzados_z) + len(fallidos_z)
            datos_grafico.append((z, total_mov))

        dibujar_grafico_barras(datos_grafico)

        # tabla intentos
        for i in tree_int.get_children():
            tree_int.delete(i)

        df_in_sorted = df_in.copy()
        if not df_in_sorted.empty:
            if "Date" in df_in_sorted.columns:
                df_in_sorted["Date"] = pd.to_datetime(df_in_sorted["Date"], errors="coerce")
                df_in_sorted = df_in_sorted.sort_values(
                    by=["Date", "Time"], ascending=False
                )

        for _, row in df_in_sorted.head(50).iterrows():
            tree_int.insert(
                "",
                "end",
                values=(
                    str(row.get("Date", ""))[:10],
                    row.get("Time", ""),
                    row.get("Name", ""),
                    row.get("Zone", ""),
                    row.get("Reason", ""),
                ),
            )

        # panel inferior top personas
        actualizar_panel_top(df_in)

    # ---------- BOTÓN REFRESCAR ----------
    btn_refrescar = tk.Button(
        win,
        text="Refrescar",
        bg=ACCENT_SECONDARY,
        fg="black",
        font=("Segoe UI Semibold", 10),
        bd=0,
        padx=14,
        pady=6,
        cursor="hand2",
    )
    btn_refrescar.pack(pady=(0, 4))

    def refrescar():
        df_as = leer_asistencias_hoy()
        df_in = leer_intentos_hoy()
        pintar_dashboard(df_as, df_in)

    btn_refrescar.config(command=refrescar)

    # Primera carga
    refrescar()

    if isinstance(win, tk.Tk):
        win.mainloop()


if __name__ == "__main__":
    build_dashboard()
