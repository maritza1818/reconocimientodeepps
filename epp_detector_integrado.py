"""
Módulo de Detección de EPP Integrado (NUEVA VERSIÓN)
---------------------------------------------------
- Detecta:
    • Casco BLANCO (por color + forma aproximada circular en zona superior)
    • Chaleco NARANJA (por color + forma rectangular en zona media)
    • Códigos QR en la imagen (para validar EPP asignado)

Compatibilidad:
    - Mantiene:
        verify_epp(frame, min_score=0.3) -> list[ (clase, score, bbox) ]
        draw_results(frame, results) -> frame dibujado
    - Añade:
        verify_epp_con_qr(frame, min_score=0.3) -> (results, qr_data_list)
        generar_codigo_epp(enrollment, tipo_epp="chaleco") -> str

Notas:
    - Los elementos de results tienen la forma:
        (clase, score, (x1, y1, x2, y2))
      donde clase puede ser: "casco", "chaleco" o "qr:CODIGO".
    - Los QR se codifican como clase "qr:LO_QUE_CONTIENE_EL_QR".
"""

import cv2
import numpy as np
import uuid


# ============================================================
#   CLASE PRINCIPAL
# ============================================================


class EPPDetectorIntegrado:
    """Detector de EPP por color + forma + códigos QR"""

    def __init__(self):
        # ==========================
        # RANGOS HSV
        # ==========================
        # Casco BLANCO:
        #   - Bajo componente de saturación (S)
        #   - Alto valor (V)
        # Casco blanco: muy poca saturación y mucho valor
        self.casco_ranges = [
            {"lower": np.array([0, 0, 200]), "upper": np.array([180, 40, 255])},
        ]

        # Chaleco naranja: estrechar un poco el rango
        self.chaleco_ranges = [
            {"lower": np.array([8, 150, 150]), "upper": np.array([22, 255, 255])},
        ]

        # ==========================
        # UMBRALES Y PARÁMETROS
        # ==========================
        # Área mínima y umbral de pixeles para considerar detección
        self.threshold_casco = 4000      # antes 1500
        self.threshold_chaleco = 6000    # antes 2500

        # Casco (forma casi circular)
        self.min_circularidad_casco = 0.5  # 1.0 = círculo perfecto

        self.min_area_casco = 800        # antes 400
        self.min_area_chaleco = 3000     # antes 1500

        self.min_aspect_ratio_chaleco = 0.5  # w/h
        self.max_aspect_ratio_chaleco = 2.5  # rango amplio para diferentes cuerpos

        # Contador de detecciones para logs
        self.detecciones_count = 0

        # Detector de códigos QR de OpenCV
        self.qr_detector = cv2.QRCodeDetector()

    # ============================================================
    #   DETECCIÓN DE CASCO (BLANCO)
    # ============================================================

    def detectar_casco(self, frame):
        """
        Detecta casco blanco por color + circularidad en la zona superior.
        Devuelve:
            (tiene_casco: bool, confianza: float [0-100])
        """
        h, w = frame.shape[:2]
        zona_superior = frame[0 : h // 3, :]  # 1/3 superior

        # Convertir a HSV
        hsv = cv2.cvtColor(zona_superior, cv2.COLOR_BGR2HSV)

        # Máscara total (OR de todos los rangos)
        mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for color_range in self.casco_ranges:
            mask = cv2.inRange(hsv, color_range["lower"], color_range["upper"])
            mask_total = cv2.bitwise_or(mask_total, mask)

        # Suavizado morfológico
        kernel = np.ones((5, 5), np.uint8)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel)

        pixeles_color = cv2.countNonZero(mask_total)

        # Buscar contornos y medir circularidad
        tiene_forma_circular = False
        max_circularidad = 0.0

        contours, _ = cv2.findContours(
            mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area_casco:
                continue

            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue

            circularidad = 4 * np.pi * area / (perimeter * perimeter)
            max_circularidad = max(max_circularidad, circularidad)

            if circularidad >= self.min_circularidad_casco:
                tiene_forma_circular = True

        # Condición final
        tiene_casco = (pixeles_color >= self.threshold_casco) and tiene_forma_circular

        # Confianza basada en color + forma
        if pixeles_color <= 0:
            conf_color = 0.0
        else:
            conf_color = min(1.5, pixeles_color / float(self.threshold_casco)) * 70.0

        conf_shape = np.clip(max_circularidad, 0.0, 1.0) * 30.0

        confianza = conf_color + conf_shape if tiene_forma_circular else conf_color * 0.4
        confianza = float(np.clip(confianza, 0.0, 100.0))

        return tiene_casco, confianza

    # ============================================================
    #   DETECCIÓN DE CHALECO (NARANJA)
    # ============================================================

    def detectar_chaleco(self, frame):
        """
        Detecta chaleco naranja por color + forma rectangular en la zona media.
        Devuelve:
            (tiene_chaleco: bool, confianza: float [0-100])
        """
        h, w = frame.shape[:2]
        zona_media = frame[h // 3 : 2 * h // 3, :]  # 1/3 central (torso)

        hsv = cv2.cvtColor(zona_media, cv2.COLOR_BGR2HSV)

        mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for color_range in self.chaleco_ranges:
            mask = cv2.inRange(hsv, color_range["lower"], color_range["upper"])
            mask_total = cv2.bitwise_or(mask_total, mask)

        kernel = np.ones((7, 7), np.uint8)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel)

        pixeles_color = cv2.countNonZero(mask_total)

        tiene_forma_rectangular = False
        mejor_aspect_ratio = 0.0

        contours, _ = cv2.findContours(
            mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area_chaleco:
                continue

            x, y, w_rect, h_rect = cv2.boundingRect(contour)
            if h_rect == 0:
                continue

            aspect_ratio = w_rect / float(h_rect)
            mejor_aspect_ratio = aspect_ratio

            if (
                self.min_aspect_ratio_chaleco <= aspect_ratio <= self.max_aspect_ratio_chaleco
            ):
                tiene_forma_rectangular = True
                break

        tiene_chaleco = (pixeles_color >= self.threshold_chaleco) and tiene_forma_rectangular

        if pixeles_color <= 0:
            conf_color = 0.0
        else:
            conf_color = min(1.5, pixeles_color / float(self.threshold_chaleco)) * 70.0

        conf_shape = 30.0 if tiene_forma_rectangular else 0.0
        confianza = conf_color + conf_shape
        confianza = float(np.clip(confianza, 0.0, 100.0))

        return tiene_chaleco, confianza

    # ============================================================
    #   DETECCIÓN DE CÓDIGOS QR
    # ============================================================

    def detectar_qr(self, frame):
        """
        Detecta códigos QR en el frame usando OpenCV.
        Devuelve:
            (lista_data, lista_boxes)

        lista_data:  [str, ...]  contenido decodificado de cada QR
        lista_boxes: [(x1, y1, x2, y2), ...]  bounding boxes aproximados
        """
        data_list = []
        boxes = []

        try:
            if hasattr(self.qr_detector, "detectAndDecodeMulti"):
                # Soportar tanto la firma de 3 como de 4 valores
                res = self.qr_detector.detectAndDecodeMulti(frame)

                decoded_info = []
                points = None

                if isinstance(res, tuple):
                    if len(res) == 4:
                        # OpenCV nuevo: retval, decoded_info, points, straight_qrcode
                        _, decoded_info, points, _ = res
                    elif len(res) == 3:
                        # Alguna variante antigua: decoded_info, points, straight_qrcode
                        decoded_info, points, _ = res
                    else:
                        decoded_info, points = [], None
                else:
                    decoded_info, points = [], None

                if points is not None and len(decoded_info):
                    for d, pts in zip(decoded_info, points):
                        if not d:
                            continue
                        pts = pts.astype(int)
                        x1 = int(np.min(pts[:, 0]))
                        y1 = int(np.min(pts[:, 1]))
                        x2 = int(np.max(pts[:, 0]))
                        y2 = int(np.max(pts[:, 1]))
                        data_list.append(d)
                        boxes.append((x1, y1, x2, y2))
            else:
                # Versión simple detectAndDecode (un solo QR)
                d, pts, _ = self.qr_detector.detectAndDecode(frame)
                if d and pts is not None:
                    pts = pts.astype(int)
                    x1 = int(np.min(pts[:, 0]))
                    y1 = int(np.min(pts[:, 1]))
                    x2 = int(np.max(pts[:, 0]))
                    y2 = int(np.max(pts[:, 1]))
                    data_list.append(d)
                    boxes.append((x1, y1, x2, y2))

        except Exception as e:
            print(f"[QR] Error detectando QR: {e}")

        return data_list, boxes


    # ============================================================
    #   LÓGICA PRINCIPAL DE EPP + QR
    # ============================================================

    def verificar_epp(self, frame, min_score=0.3):
        """
        Verifica EPP completo y QR (no aplica restricción lógica, solo detecta).
        Devuelve:
            results: list[(clase, score, (x1, y1, x2, y2))]
        Nota:
            - clase puede ser "casco", "chaleco" o "qr:LO_QUE_CONTIENE".
        """
        self.detecciones_count += 1
        h, w = frame.shape[:2]

        # Detectar casco y chaleco
        tiene_casco, conf_casco = self.detectar_casco(frame)
        tiene_chaleco, conf_chaleco = self.detectar_chaleco(frame)

        resultados = []

        # Casco (usamos una caja aproximada en zona superior)
        if tiene_casco and conf_casco >= min_score * 100:
            x1 = w // 2 - 60
            x2 = w // 2 + 60
            y1 = 10
            y2 = h // 3
            resultados.append(("casco", conf_casco / 100.0, (x1, y1, x2, y2)))

        # Chaleco (caja aproximada en zona media)
        if tiene_chaleco and conf_chaleco >= min_score * 100:
            x1 = w // 2 - 100
            x2 = w // 2 + 100
            y1 = h // 3
            y2 = 2 * h // 3
            resultados.append(("chaleco", conf_chaleco / 100.0, (x1, y1, x2, y2)))

        # Detectar QR
        qr_data_list, qr_boxes = self.detectar_qr(frame)
        for d, (x1, y1, x2, y2) in zip(qr_data_list, qr_boxes):
            # Codificamos el contenido en el nombre de la clase: "qr:..."
            resultados.append((f"qr:{d}", 1.0, (x1, y1, x2, y2)))

        # Logs periódicos
        if self.detecciones_count % 30 == 0:
            print(
                f"[EPP] Casco: {tiene_casco} ({conf_casco:.1f}%) | "
                f"Chaleco: {tiene_chaleco} ({conf_chaleco:.1f}%) | "
                f"QRs detectados: {len(qr_data_list)}"
            )

        return resultados

    def verificar_epp_con_qr(self, frame, min_score=0.3):
        """
        Versión extendida:
        Devuelve:
            (results, qr_data_list)
        """
        results = self.verificar_epp(frame, min_score=min_score)
        qr_data_list = []

        for clase, score, bbox in results:
            if isinstance(clase, str) and clase.lower().startswith("qr:"):
                qr_data_list.append(clase.split("qr:", 1)[1])

        return results, qr_data_list

    # ============================================================
    #   DIBUJADO DE RESULTADOS
    # ============================================================

    def dibujar_resultados(self, frame, resultados):
        """
        Dibuja resultados en el frame:
            - Rectángulos para casco, chaleco y QRs
        """
        for clase, score, (x1, y1, x2, y2) in resultados:
            clase_str = str(clase).lower()

            if "casco" in clase_str:
                color = (0, 255, 0) if score >= 0.5 else (0, 165, 255)
                etiqueta = f"Casco: {score*100:.1f}%"
            elif "chaleco" in clase_str:
                color = (255, 140, 0) if score >= 0.5 else (0, 165, 255)
                etiqueta = f"Chaleco: {score*100:.1f}%"
            elif "qr:" in clase_str:
                color = (255, 0, 255)
                contenido = clase.split("qr:", 1)[1]
                etiqueta = f"QR: {contenido}"
            else:
                color = (255, 255, 255)
                etiqueta = str(clase)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame,
                etiqueta,
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )

        # Mensaje general
        tiene_casco = any("casco" in str(r[0]).lower() for r in resultados)
        tiene_chaleco = any("chaleco" in str(r[0]).lower() for r in resultados)
        tiene_qr = any(str(r[0]).lower().startswith("qr:") for r in resultados)

        tiene_todo = tiene_casco and tiene_chaleco

        # Nota: la lógica de "tiene_qr correcto" la harás en el módulo de asistencia
        # comparando el contenido del QR con el trabajador.

        estado = "EPP COMPLETO" if tiene_todo else "EPP INCOMPLETO"
        color_estado = (0, 255, 0) if tiene_todo else (0, 0, 255)
        cv2.putText(
            frame,
            estado,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color_estado,
            2,
        )

        if tiene_qr:
            cv2.putText(
                frame,
                "QR detectado",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 255),
                2,
            )

        return frame


# ============================================================
#   SINGLETON / FUNCIONES DE MÓDULO (COMPATIBILIDAD)
# ============================================================

_detector_global = None


def get_detector():
    """Obtiene una instancia singleton del detector."""
    global _detector_global
    if _detector_global is None:
        _detector_global = EPPDetectorIntegrado()
    return _detector_global


def verify_epp(frame, min_score=0.3):
    """
    Función compatible con el sistema actual:
        epp_results = verify_epp(frame)
    """
    detector = get_detector()
    return detector.verificar_epp(frame, min_score=min_score)


def verify_epp_with_qr(frame, min_score=0.3):
    """
    NUEVA función:
        results, qr_data_list = verify_epp_with_qr(frame)
    """
    detector = get_detector()
    return detector.verificar_epp_con_qr(frame, min_score=min_score)


def draw_results(frame, results):
    """Dibuja resultados sobre el frame."""
    detector = get_detector()
    return detector.dibujar_resultados(frame, results)


# ============================================================
#   UTILIDAD: GENERADOR DE CÓDIGO DE EPP
# ============================================================


def generar_codigo_epp(enrollment, tipo_epp="chaleco"):
    """
    Genera un código único de EPP a partir del ID de trabajador.
    Ejemplo de salida:
        'CHALECO-12345-AB12CD'
    Este código es el que deberías poner dentro del QR.
    """
    enrollment = str(enrollment).strip()
    base = f"{tipo_epp.upper()}-{enrollment}"
    sufijo = uuid.uuid4().hex[:6].upper()
    return f"{base}-{sufijo}"


# ============================================================
#   TEST RÁPIDO
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST - DETECTOR EPP + QR")
    print("=" * 60)
    print("\nControles:")
    print("  Q - Salir")
    print("\nIniciando cámara...\n")

    det = get_detector()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error: No se pudo abrir la cámara")
        raise SystemExit

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = det.verificar_epp(frame)
        frame_out = det.dibujar_resultados(frame, results)
        cv2.imshow("Test EPP + QR", frame_out)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ Test finalizado")
