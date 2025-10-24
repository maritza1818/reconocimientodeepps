import pandas as pd
import os
import tkinter as tk
from tkinter import *
import csv
from glob import glob

#FUNCIÓN 1: Ver asistencia de una materia específica ===
def subjectchoose(text_to_speech):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    attendance_base = os.path.join(BASE_DIR, "Attendance")

    def calculate_attendance():
        Subject = tx.get().strip()
        if Subject == "":
            t = "Por favor, ingrese el nombre del trabajador."
            text_to_speech(t)
            return

        subject_folder = os.path.join(attendance_base, Subject)
        filenames = glob(os.path.join(subject_folder, f"{Subject}_*.csv"))

        if not filenames:
            t = f"No se encontraron registros de asistencia para '{Subject}'."
            text_to_speech(t)
            return

        dfs = [pd.read_csv(f) for f in filenames if os.path.getsize(f) > 0]
        df = pd.concat(dfs, ignore_index=True)

        expected_cols = {"Enrollment", "Name", "Date", "Time", "Status"}
        if not expected_cols.issubset(df.columns):
            t = "Los archivos de asistencia no tienen las columnas esperadas."
            text_to_speech(t)
            return

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        total_days = df["Date"].nunique()

        attendance_summary = (
            df.groupby(["Enrollment", "Name"])["Date"]
            .nunique()
            .reset_index()
            .rename(columns={"Date": "DiasPresentes"})
        )

        attendance_summary["TotalDias"] = total_days
        attendance_summary["Asistencia%"] = (
            (attendance_summary["DiasPresentes"] / attendance_summary["TotalDias"]) * 100
        ).round(2)

        df = df.merge(attendance_summary, on=["Enrollment", "Name"], how="left")
        df["Asistencia"] = df["Asistencia%"].astype(str) + "%"
        df.drop(columns=["Asistencia%"], inplace=True)
        df.sort_values(by=["Date", "Time"], inplace=True)

        output_file = os.path.join(subject_folder, "asistencia_detallada.csv")
        df.to_csv(output_file, index=False)

        show_csv_window(output_file, f"Asistencia Detallada - {Subject}")

    subject = Tk()
    subject.title("Ver Asistencia por Trabajador")
    subject.geometry("600x350")
    subject.resizable(0, 0)
    subject.configure(background="black")

    titl = tk.Label(subject, text="Ver Asistencia de Trabajador", bg="black", fg="green", font=("arial", 25))
    titl.pack(pady=20)

    sub_label = tk.Label(subject, text="Trabajador:", width=12, height=2, bg="black", fg="yellow", font=("times new roman", 15))
    sub_label.place(x=40, y=100)

    tx = tk.Entry(subject, width=15, bd=5, bg="black", fg="yellow", font=("times", 30, "bold"))
    tx.place(x=200, y=100)

    fill_a = tk.Button(subject, text="Ver Asistencia", command=calculate_attendance, bd=7,
                       font=("times new roman", 15), bg="black", fg="yellow", height=2, width=12)
    fill_a.place(x=200, y=200)

    subject.mainloop()


# === FUNCIÓN 2: Ver asistencia general (todas las materias combinadas) ===
def ver_asistencia_general(text_to_speech):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    attendance_base = os.path.join(BASE_DIR, "Attendance")

    all_files = glob(os.path.join(attendance_base, "*", "*.csv"))

    if not all_files:
        text_to_speech("No se encontraron registros de asistencia del trabajador.")
        return

    dfs = []
    for f in all_files:
        try:
            df = pd.read_csv(f)
            if {"Enrollment", "Name", "Date", "Time", "Status"}.issubset(df.columns):
                df["Materia"] = os.path.basename(os.path.dirname(f))
                dfs.append(df)
        except Exception:
            continue

    if not dfs:
        text_to_speech("No hay datos válidos para mostrar.")
        return

    df = pd.concat(dfs, ignore_index=True)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df.sort_values(by=["Date", "Time"], inplace=True)

    total_days = df["Date"].nunique()
    summary = (
        df.groupby(["Enrollment", "Name"])["Date"]
        .nunique()
        .reset_index()
        .rename(columns={"Date": "DiasPresentes"})
    )
    summary["TotalDias"] = total_days
    summary["Asistencia%"] = (summary["DiasPresentes"] / summary["TotalDias"] * 100).round(2)
    summary["Asistencia%"] = summary["Asistencia%"].astype(str) + "%"

    output_file = os.path.join(attendance_base, "asistencia_general.csv")
    summary.to_csv(output_file, index=False)

    show_csv_window(output_file, "Resumen General de Asistencia")


def show_csv_window(csv_path, title):
    root = tk.Tk()
    root.title(title)
    root.configure(background="black")

    with open(csv_path, newline="", encoding="utf-8-sig") as file:
        reader = csv.reader(file)
        r = 0
        for col in reader:
            c = 0
            for row in col:
                label = tk.Label(
                    root,
                    width=15,
                    height=1,
                    fg="yellow",
                    font=("times", 12, "bold"),
                    bg="black",
                    text=row,
                    relief=tk.RIDGE,
                )
                label.grid(row=r, column=c)
                c += 1
            r += 1

    root.mainloop()


def menu_asistencia(text_to_speech):
    ventana = Tk()
    ventana.title("Opciones de Asistencia")
    ventana.geometry("500x300")
    ventana.configure(bg="black")

    Label(ventana, text="Seleccione tipo de vista:", fg="green", bg="black", font=("Arial", 18)).pack(pady=30)

    Button(
        ventana,
        text="📘 Ver Asistencia por Trabajador",
        command=lambda: [ventana.destroy(), subjectchoose(text_to_speech)],
        bg="darkblue",
        fg="white",
        font=("Arial", 14),
        height=2,
        width=25
    ).pack(pady=10)

    Button(
        ventana,
        text="📋 Ver Asistencia General",
        command=lambda: [ventana.destroy(), ver_asistencia_general(text_to_speech)],
        bg="darkgreen",
        fg="white",
        font=("Arial", 14),
        height=2,
        width=25
    ).pack(pady=10)

    ventana.mainloop()
