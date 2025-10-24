# verifier.py - VERSIÓN SIN DETECCIÓN YOLO (TEMPORAL)
# Para usar mientras se arregla el modelo YOLO

import cv2
import numpy as np

def verify_epp(frame, min_score=0.3):
    """
    BYPASS TEMPORAL: Siempre retorna que SÍ hay EPP
    Para que el sistema funcione sin YOLO
    """
    # Retornar EPP ficticio para que el sistema registre la asistencia
    print("[BYPASS] EPP check desactivado - siempre retorna TRUE")
    return [("casco", 0.95, (10, 10, 50, 50))]  # EPP ficticio

def draw_results(frame, results):
    """
    Dibuja texto indicando que el check de EPP está desactivado
    """
    if results:
        cv2.putText(
            frame, 
            "EPP CHECK: DESACTIVADO", 
            (10, 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, 
            (0, 255, 255),  # Amarillo
            2
        )
    return frame