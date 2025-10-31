# dashboard.py
import tkinter as tk
from tkinter import ttk
import os, glob
import pandas as pd
import datetime

# para mostrar fotitos (ya usas PIL en attendance.py, así que lo uso también)
try:
    from PIL import Image, ImageTk
    PIL_OK = True
except Exception:
    PIL_OK = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ATTENDANCE_DIR = os.path.join(BASE_DIR, "Attendance")
TRAINING_DIR = os.path.join(BASE_DIR, "TrainingImage")  # para las fotos de rostro


def leer_asistencias_hoy():
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(ATTENDANCE_DIR, f"asistencia_{hoy}.csv")
    if not os.path.exists(path):
        return pd.DataFrame(columns=[
            "Enrollment","Name","Date","Time","Status","Reason","Zone","EPP_Detected","CaptureSeconds"
        ])
    df = pd.read_csv(path, dtype=str)
    for c in ["Reason","Zone","EPP_Detected","CaptureSeconds"]:
        if c not in df.columns:
            df[c] = ""
    return df


def leer_intentos_hoy():
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(ATTENDANCE_DIR, f"intentos_{hoy}.csv")
    if not os.path.exists(path):
        return pd.DataFrame(columns=[
            "Enrollment","Name","Date","Time","Status","Reason","Zone","EPP_Detected","CaptureSeconds"
        ])
    df = pd.read_csv(path, dtype=str)
    for c in ["Reason","Zone","EPP_Detected","CaptureSeconds"]:
        if c not in df.columns:
            df[c] = ""
    return df


def buscar_foto_por_enrollment(enrollment: str):
    """
    Intenta encontrar una foto en TrainingImage que contenga el enrollment.
    Ejemplos comunes:
      - Nombre.Enrollment.1.jpg
      - Enrollment.1.jpg
    Si no la encuentra, devuelve None.
    """
    if not PIL_OK:
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


def build_dashboard():
    win = tk.Toplevel()
    win.title("Dashboard de Asistencia + EPP")
    win.geometry("1180x640")
    win.configure(bg="black")
    win.resizable(0, 0)

    # ---------- HEADER ----------
    top = tk.Frame(win, bg="black")
    top.pack(fill="x", pady=5)

    titulo = tk.Label(
        top,
        text="DASHBOARD - Asistencia y Cumplimiento EPP",
        bg="black",
        fg="#21f700",
        font=("Verdana", 22, "bold"),
    )
    titulo.pack(side="left", padx=15)

    lbl_fecha = tk.Label(
        top,
        text="...",
        bg="black",
        fg="white",
        font=("Verdana", 11),
    )
    lbl_fecha.pack(side="right", padx=15)

    # ---------- TARJETAS ----------
    cards = tk.Frame(win, bg="black")
    cards.pack(fill="x", pady=5)

    card1 = tk.Frame(cards, bg="#111111", bd=2, relief="ridge")
    card1.place(x=10, y=0, width=250, height=90)

    card2 = tk.Frame(cards, bg="#111111", bd=2, relief="ridge")
    card2.place(x=275, y=0, width=250, height=90)

    card3 = tk.Frame(cards, bg="#111111", bd=2, relief="ridge")
    card3.place(x=540, y=0, width=250, height=90)

    card4 = tk.Frame(cards, bg="#111111", bd=2, relief="ridge")
    card4.place(x=805, y=0, width=250, height=90)

    tk.Label(card1, text="Asistencias HOY", bg="#111111", fg="white", font=("Verdana", 11)).pack(anchor="w", padx=10, pady=2)
    val_asistencias_hoy = tk.Label(card1, text="0", bg="#111111", fg="#00ff7f", font=("Verdana", 23, "bold"))
    val_asistencias_hoy.pack(anchor="center")

    tk.Label(card2, text="Intentos fallidos HOY", bg="#111111", fg="white", font=("Verdana", 11)).pack(anchor="w", padx=10, pady=2)
    val_intentos_hoy = tk.Label(card2, text="0", bg="#111111", fg="#ff4d4d", font=("Verdana", 23, "bold"))
    val_intentos_hoy.pack(anchor="center")

    tk.Label(card3, text="Cumplimiento EPP", bg="#111111", fg="white", font=("Verdana", 11)).pack(anchor="w", padx=10, pady=2)
    pb = ttk.Progressbar(card3, orient="horizontal", length=180, mode="determinate")
    pb.pack(pady=3)
    val_cumplimiento = tk.Label(card3, text="0%", bg="#111111", fg="#00ff7f", font=("Verdana", 13, "bold"))
    val_cumplimiento.pack()

    tk.Label(card4, text="Zonas con movimiento", bg="#111111", fg="white", font=("Verdana", 11)).pack(anchor="w", padx=10, pady=2)
    val_zonas = tk.Label(card4, text="0", bg="#111111", fg="#ffd700", font=("Verdana", 23, "bold"))
    val_zonas.pack(anchor="center")

    # ---------- BOTÓN REFRESCAR ----------
    def refrescar():
        df_as = leer_asistencias_hoy()
        df_in = leer_intentos_hoy()
        pintar_dashboard(df_as, df_in)

    btn_refrescar = tk.Button(
        win,
        text="Refrescar",
        bg="#222",
        fg="yellow",
        font=("Verdana", 11, "bold"),
        command=refrescar,
    )
    btn_refrescar.pack(pady=5)

    # ---------- CONTENEDOR CENTRAL ----------
    middle = tk.Frame(win, bg="black")
    middle.pack(fill="both", expand=True)

    # LEFT: tabla por zona + gráfico
    left = tk.Frame(middle, bg="black")
    left.pack(side="left", fill="both", expand=True, padx=8, pady=5)

    tk.Label(left, text="Por zona (hoy)", bg="black", fg="white", font=("Verdana", 12, "bold")).pack(anchor="w")

    cols_zona = ("Zona", "OK", "Forzados", "Fallidos")
    tree_zona = ttk.Treeview(left, columns=cols_zona, show="headings", height=6)
    for c in cols_zona:
        tree_zona.heading(c, text=c)
        tree_zona.column(c, width=90, anchor="w")
    tree_zona.pack(fill="x", pady=5)

    # gráfico de barras sencillo
    chart_frame = tk.Frame(left, bg="black")
    chart_frame.pack(fill="both", expand=True, pady=5)
    chart_canvas = tk.Canvas(chart_frame, bg="#040404", height=160, highlightthickness=0)
    chart_canvas.pack(fill="both", expand=True)

    # RIGHT: tabla de intentos
    right = tk.Frame(middle, bg="black")
    right.pack(side="left", fill="both", expand=True, padx=8, pady=5)
    tk.Label(right, text="Últimos intentos / fallidos", bg="black", fg="white", font=("Verdana", 12, "bold")).pack(anchor="w")

    cols_int = ("Date", "Time", "Name", "Zone", "Reason")
    tree_int = ttk.Treeview(right, columns=cols_int, show="headings", height=12)
    for c in cols_int:
        tree_int.heading(c, text=c)
        tree_int.column(c, width=90, anchor="w")
    tree_int.pack(fill="both", expand=True, pady=5)

    # ---------- PANEL DE TOP INCIDENTES (ABAJO) ----------
    bottom = tk.Frame(win, bg="black")
    bottom.pack(fill="x", pady=5)

    tk.Label(bottom, text="Top con más incidentes hoy", bg="black", fg="white",
             font=("Verdana", 12, "bold")).pack(anchor="w", padx=10)

    panel_top = tk.Frame(bottom, bg="black")
    panel_top.pack(fill="x", padx=10)

    # para no se borren las imágenes
    panel_top.images_refs = []

    # ---------- FUNCIONES INTERNAS ----------

    def dibujar_grafico_barras(datos_por_zona):
        """
        datos_por_zona: lista de tuplas (zona, total)
        Dibuja en chart_canvas
        """
        chart_canvas.delete("all")
        if not datos_por_zona:
            chart_canvas.create_text(
                200, 80, text="Sin datos para graficar",
                fill="white", font=("Verdana", 10, "bold")
            )
            return

        # márgenes
        x0 = 40
        y0 = 140
        max_bar_width = 300
        max_val = max([t[1] for t in datos_por_zona]) or 1

        # título
        chart_canvas.create_text(5, 10, anchor="w",
                                 text="Movimientos por zona (asistencia + intentos)",
                                 fill="white", font=("Verdana", 9, "bold"))

        y = 35
        for zona, total in datos_por_zona:
            bar_len = int((total / max_val) * max_bar_width)
            chart_canvas.create_rectangle(x0, y, x0 + bar_len, y + 18,
                                          fill="#00bfff", outline="")
            chart_canvas.create_text(5, y + 9, anchor="w",
                                     text=zona, fill="white", font=("Verdana", 8))
            chart_canvas.create_text(x0 + bar_len + 10, y + 9, anchor="w",
                                     text=str(total), fill="white", font=("Verdana", 8, "bold"))
            y += 25

    def mostrar_top_incidentes(df_int):
        # limpiar
        for w in panel_top.winfo_children():
            w.destroy()
        panel_top.images_refs.clear()

        if df_int.empty:
            tk.Label(panel_top, text="Sin incidentes hoy",
                     bg="black", fg="white").pack()
            return

        # contamos por persona
        conteo = (
            df_int.groupby(["Enrollment", "Name"])
                  .size()
                  .reset_index(name="Intentos")
                  .sort_values(by="Intentos", ascending=False)
        )

        top3 = conteo.head(3).to_dict(orient="records")

        for person in top3:
            frm = tk.Frame(panel_top, bg="#111111", bd=1, relief="ridge")
            frm.pack(side="left", padx=6, pady=3)

            enr = str(person.get("Enrollment", ""))
            name = str(person.get("Name", ""))
            intentos = person.get("Intentos", 0)

            # intento foto
            if PIL_OK and enr:
                foto_path = buscar_foto_por_enrollment(enr)
            else:
                foto_path = None

            if foto_path and os.path.exists(foto_path):
                try:
                    img = Image.open(foto_path)
                    img = img.resize((80, 80))
                    img_tk = ImageTk.PhotoImage(img)
                    lbl_img = tk.Label(frm, image=img_tk, bg="#111111")
                    lbl_img.pack()
                    panel_top.images_refs.append(img_tk)
                except Exception:
                    tk.Label(frm, text="[Sin foto]", bg="#111111", fg="white").pack()
            else:
                tk.Label(frm, text="[Sin foto]", bg="#111111", fg="white").pack()

            tk.Label(frm, text=name, bg="#111111", fg="white",
                     font=("Verdana", 9, "bold"), wraplength=90).pack()
            tk.Label(frm, text=f"Intentos: {intentos}",
                     bg="#111111", fg="#ff4d4d", font=("Verdana", 9)).pack()
            if enr:
                tk.Label(frm, text=f"ID: {enr}",
                         bg="#111111", fg="gray", font=("Verdana", 8)).pack()

    # ---------- pinta dashboard ----------

    def pintar_dashboard(df_as, df_in):
        asistencias_hoy = len(df_as)
        intentos_hoy = len(df_in)

        ok_rows = df_as[df_as["Reason"].fillna("") == "OK"]
        total_revisados = len(ok_rows) + intentos_hoy
        if total_revisados == 0:
            cumplimiento = 0
        else:
            cumplimiento = (len(ok_rows) / total_revisados) * 100

        zonas_as = set(df_as["Zone"].dropna().tolist())
        zonas_in = set(df_in["Zone"].dropna().tolist())
        zonas_total = {z for z in zonas_as.union(zonas_in) if z != ""}

        val_asistencias_hoy.config(text=str(asistencias_hoy))
        val_intentos_hoy.config(text=str(intentos_hoy))
        val_cumplimiento.config(text=f"{cumplimiento:.1f}%")
        pb["value"] = cumplimiento
        val_zonas.config(text=str(len(zonas_total)))

        # tabla zonas
        for i in tree_zona.get_children():
            tree_zona.delete(i)
        datos_grafico = []
        if not zonas_total:
            tree_zona.insert("", "end", values=("Sin datos", 0, 0, 0))
        else:
            for z in sorted(zonas_total):
                ok_z = df_as[(df_as["Zone"] == z) & (df_as["Reason"] == "OK")]
                forzados_z = df_as[(df_as["Zone"] == z) & (df_as["Reason"].str.contains("FORZADO", na=False))]
                fallidos_z = df_in[(df_in["Zone"] == z)]
                tree_zona.insert("", "end", values=(z, len(ok_z), len(forzados_z), len(fallidos_z)))

                total_mov = len(ok_z) + len(forzados_z) + len(fallidos_z)
                datos_grafico.append((z, total_mov))

        # dibujar gráfico
        dibujar_grafico_barras(datos_grafico)

        # tabla intentos
        for i in tree_int.get_children():
            tree_int.delete(i)
        df_in_sorted = df_in.copy()
        if not df_in_sorted.empty:
            if "Date" in df_in_sorted.columns and "Time" in df_in_sorted.columns:
                df_in_sorted["Date"] = pd.to_datetime(df_in_sorted["Date"], errors="coerce")
                df_in_sorted = df_in_sorted.sort_values(by=["Date", "Time"], ascending=False)
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

        # panel top incidentes
        mostrar_top_incidentes(df_in)

    # ---------- reloj arriba ----------
    def actualizar_reloj():
        ahora = datetime.datetime.now()
        # sin emojis para Windows
        lbl_fecha.config(text=f"Fecha: {ahora.strftime('%d/%m/%Y')}  Hora: {ahora.strftime('%H:%M:%S')}")
        win.after(1000, actualizar_reloj)

    # primera carga
    refrescar()
    actualizar_reloj()

    win.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    build_dashboard()
