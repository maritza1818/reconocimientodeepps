"""
Módulo de Detección de EPP integrado

Responsabilidades:
- Detectar CASCO BLANCO (parte superior de la imagen)
- Detectar CHALECO NARANJA (zona media del cuerpo)
- Detectar códigos QR en la imagen (para depuración visual)
- Proveer funciones utilitarias para el resto del sistema:
    - verify_epp(frame) -> lista de detecciones
    - draw_results(frame, results) -> frame con dibujos
    - generar_codigo_epp(enrollment, tipo_epp) -> código de EPP estable
"""

import cv2
import numpy as np


class EPPDetectorIntegrado:
    def __init__(self):
        # =============== CASCO BLANCO =================
        self.casco_ranges = [
            {"lower": np.array([0, 0, 190]), "upper": np.array([180, 50, 255])},
            {"lower": np.array([0, 0, 160]), "upper": np.array([180, 70, 255])},
        ]

        # =============== CHALECO NARANJA =================
        self.chaleco_ranges = [
            {"lower": np.array([5, 120, 120]), "upper": np.array([20, 255, 255])},
            {"lower": np.array([10, 80, 90]), "upper": np.array([25, 255, 255])},
        ]

        self.threshold_casco = 1800
        self.threshold_chaleco = 3500

        self.min_circularidad_casco = 0.35
        self.min_aspect_ratio_chaleco = 0.4
        self.max_aspect_ratio_chaleco = 3.0

        self.detecciones_count = 0
        self.qr_detector = cv2.QRCodeDetector()

    # ------------------------------------------------------------------
    #  DETECCIÓN DE CASCO
    # ------------------------------------------------------------------
    def detectar_casco(self, frame):
        h, w = frame.shape[:2]
        zona_superior = frame[0 : h // 3, :]
        hsv = cv2.cvtColor(zona_superior, cv2.COLOR_BGR2HSV)

        mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for r in self.casco_ranges:
            mask = cv2.inRange(hsv, r["lower"], r["upper"])
            mask_total = cv2.bitwise_or(mask_total, mask)

        kernel = np.ones((5, 5), np.uint8)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel)

        pixeles_color = cv2.countNonZero(mask_total)

        tiene_forma_circular = False
        max_circularidad = 0.0
        contours, _ = cv2.findContours(
            mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        for c in contours:
            area = cv2.contourArea(c)
            if area < 500:
                continue
            per = cv2.arcLength(c, True)
            if per == 0:
                continue
            circularidad = 4 * np.pi * area / (per * per)
            max_circularidad = max(max_circularidad, circularidad)
            if circularidad >= self.min_circularidad_casco:
                tiene_forma_circular = True
                break

        tiene_casco = (pixeles_color >= self.threshold_casco) and tiene_forma_circular
        conf_color = min(1.0, pixeles_color / float(self.threshold_casco))
        conf_forma = max_circularidad
        confianza = conf_color * 0.6 + conf_forma * 0.4

        return tiene_casco, float(f"{confianza:.2f}")

    # ------------------------------------------------------------------
    #  DETECCIÓN DE CHALECO
    # ------------------------------------------------------------------
    def detectar_chaleco(self, frame):
        h, w = frame.shape[:2]
        zona_media = frame[h // 3 : 2 * h // 3, w // 5 : 4 * w // 5]
        hsv = cv2.cvtColor(zona_media, cv2.COLOR_BGR2HSV)

        mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for r in self.chaleco_ranges:
            mask = cv2.inRange(hsv, r["lower"], r["upper"])
            mask_total = cv2.bitwise_or(mask_total, mask)

        kernel = np.ones((7, 7), np.uint8)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel)

        pixeles_color = cv2.countNonZero(mask_total)

        tiene_forma_rect = False
        contours, _ = cv2.findContours(
            mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        for c in contours:
            area = cv2.contourArea(c)
            if area < 1000:
                continue
            x, y, w_rect, h_rect = cv2.boundingRect(c)
            if h_rect == 0:
                continue
            ar = w_rect / float(h_rect)
            if self.min_aspect_ratio_chaleco <= ar <= self.max_aspect_ratio_chaleco:
                tiene_forma_rect = True
                break

        tiene_chaleco = (pixeles_color >= self.threshold_chaleco) and tiene_forma_rect
        conf_color = min(1.0, pixeles_color / float(self.threshold_chaleco))
        conf_forma = 1.0 if tiene_forma_rect else 0.0
        confianza = conf_color * 0.7 + conf_forma * 0.3

        return tiene_chaleco, float(f"{confianza:.2f}")

    # ------------------------------------------------------------------
    #  DETECCIÓN DE QR
    # ------------------------------------------------------------------
    def detectar_qr(self, frame):
        data_list = []
        boxes = []
        try:
            if hasattr(self.qr_detector, "detectAndDecodeMulti"):
                res = self.qr_detector.detectAndDecodeMulti(frame)
                decoded_info = []
                points = None
                if isinstance(res, tuple):
                    if len(res) == 4:
                        _, decoded_info, points, _ = res
                    elif len(res) == 3:
                        decoded_info, points, _ = res

                if points is not None and len(decoded_info):
                    for d, pts in zip(decoded_info, points):
                        if not d:
                            continue
                        pts = np.array(pts, dtype=int)
                        x1 = int(np.min(pts[:, 0]))
                        y1 = int(np.min(pts[:, 1]))
                        x2 = int(np.max(pts[:, 0]))
                        y2 = int(np.max(pts[:, 1]))
                        data_list.append(d)
                        boxes.append((x1, y1, x2, y2))
            else:
                d, pts, _ = self.qr_detector.detectAndDecode(frame)
                if d and pts is not None:
                    pts = np.array(pts, dtype=int)
                    x1 = int(np.min(pts[:, 0]))
                    y1 = int(np.min(pts[:, 1]))
                    x2 = int(np.max(pts[:, 0]))
                    y2 = int(np.max(pts[:, 1]))
                    data_list.append(d)
                    boxes.append((x1, y1, x2, y2))
        except Exception as e:
            print(f"[QR] Error detectando QR: {e}")

        return data_list, boxes

    # ------------------------------------------------------------------
    #  VERIFICACIÓN GLOBAL
    # ------------------------------------------------------------------
    def verificar_epp(self, frame):
        self.detecciones_count += 1

        tiene_casco, conf_casco = self.detectar_casco(frame)
        tiene_chaleco, conf_chaleco = self.detectar_chaleco(frame)

        resultados = []
        h, w = frame.shape[:2]

        if tiene_casco:
            resultados.append(
                ("casco", conf_casco, (w // 2 - 50, 40, w // 2 + 50, 140))
            )
        if tiene_chaleco:
            resultados.append(
                ("chaleco", conf_chaleco, (w // 2 - 80, h // 3, w // 2 + 80, 2 * h // 3))
            )

        qr_data, qr_boxes = self.detectar_qr(frame)
        for data, (x1, y1, x2, y2) in zip(qr_data, qr_boxes):
            label = f"qr:{data}"
            resultados.append((label, 1.0, (x1, y1, x2, y2)))

        if self.detecciones_count % 30 == 0:
            print(
                f"[EPP] Casco blanco: {tiene_casco} ({conf_casco*100:.0f}%) | "
                f"Chaleco naranja: {tiene_chaleco} ({conf_chaleco*100:.0f}%) | "
                f"QR detectados: {len(qr_data)}"
            )

        return resultados

    # ------------------------------------------------------------------
    #  DIBUJAR RESULTADOS
    # ------------------------------------------------------------------
    def dibujar_resultados(self, frame, resultados):
        tiene_chaleco = False
        tiene_casco = False
        tiene_qr = False

        for clase, score, (x1, y1, x2, y2) in resultados:
            if clase.startswith("qr"):
                color = (255, 0, 255)
                tiene_qr = True
                texto = clase
            else:
                color = (0, 255, 0) if score >= 0.65 else (0, 165, 255)
                if "chaleco" in clase.lower():
                    tiene_chaleco = True
                if "casco" in clase.lower():
                    tiene_casco = True
                texto = f"{clase}: {score*100:.1f}%"

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame,
                texto,
                (x1, max(20, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )

        if tiene_chaleco:
            estado = "EPP OK (chaleco)"
            color_estado = (0, 255, 0)
        else:
            estado = "EPP INCOMPLETO"
            color_estado = (0, 0, 255)

        cv2.putText(
            frame,
            estado,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color_estado,
            2,
        )
        return frame


# ----------------------------------------------------------------------
# SINGLETON Y FUNCIONES GLOBALES
# ----------------------------------------------------------------------
_detector_global = None


def get_detector():
    global _detector_global
    if _detector_global is None:
        _detector_global = EPPDetectorIntegrado()
    return _detector_global


def verify_epp(frame, min_score=0.3):
    detector = get_detector()
    return detector.verificar_epp(frame)


def draw_results(frame, results):
    detector = get_detector()
    return detector.dibujar_resultados(frame, results)


# ----------------------------------------------------------------------
# GENERADOR DE CÓDIGOS DE EPP
# ----------------------------------------------------------------------
def generar_codigo_epp(enrollment, tipo_epp="chaleco"):
    """
    Genera un código de EPP estable para un trabajador.

    Patrón:
        - CASCO:   C-XXXX
        - CHALECO: V-XXXX

    donde XXXX es el enrollment padded a 4 dígitos.
    """
    tipo = (tipo_epp or "").lower()
    prefijo = "C" if "casco" in tipo else "V"
    try:
        enr_int = int(str(enrollment))
        enr_str = f"{enr_int:04d}"
    except Exception:
        enr_str = str(enrollment).strip().upper().replace(" ", "_") or "0000"

    return f"{prefijo}-{enr_str}"
