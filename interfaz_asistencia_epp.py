"""
Interfaz Visual para Sistema de Asistencia con EPP
--------------------------------------------------
Se encarga de dibujar un HUD moderno sobre el frame de la cámara:

- Panel de información del trabajador (arriba izquierda)
- Panel de estado de EPP (arriba derecha)
- Barra inferior con mensaje y tiempo restante
- Opcionalmente, recuadros sobre rostro y EPP

Se usa desde automaticAttendance.py con:

    interfaz = InterfazAsistenciaEPP()
    frame = interfaz.dibujar_interfaz_completa(frame, info_trabajador, epp_results, tiempo_restante)

donde:
  - info_trabajador es un dict o None, por ejemplo:
        {
            "nombre": "Juan Pérez",
            "id": "123",
            "tiene_rostro": True,
            "bbox_rostro": (x, y, w, h),
        }

  - epp_results es la lista devuelta por verify_epp(frame):
        [("casco_blanco", score, (x, y, w, h)), ("chaleco_naranja", score, (x, y, w, h)), ...]

  - tiempo_restante es un entero (segundos) para mostrar una cuenta regresiva.
"""

import cv2
import numpy as np
from datetime import datetime


class InterfazAsistenciaEPP:
    def __init__(self):
        # Colores en BGR (porque OpenCV usa BGR)
        self.color_panel = (15, 23, 42)        # #0f172a
        self.color_panel_suave = (22, 30, 51)  # un poco más claro
        self.color_ok = (34, 197, 94)          # verde
        self.color_warn = (250, 204, 21)       # amarillo
        self.color_error = (52, 211, 153)      # (un verde claro para acentos)
        self.color_error_txt = (56, 56, 255)   # rojo-azulón para texto de error
        self.color_txt = (226, 232, 240)       # gris muy claro
        self.color_txt_sec = (148, 163, 184)   # gris secundario
        self.color_face_box = (129, 140, 248)  # lila

        self.font_main = cv2.FONT_HERSHEY_SIMPLEX

    # ------------------------------------------------------------------
    # Helpers para dibujar
    # ------------------------------------------------------------------
    def _draw_transparent_rect(self, img, pt1, pt2, color, alpha=0.4):
        """
        Dibuja un rectángulo semi-transparente en img.
        pt1 = (x1, y1), pt2 = (x2, y2), color en BGR, alpha 0–1
        """
        overlay = img.copy()
        cv2.rectangle(overlay, pt1, pt2, color, thickness=-1)
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

    def _draw_text(self, img, text, org, scale=0.5, color=None, thickness=1, align="left"):
        """
        Dibuja texto con fuente consistente.
        align puede ser "left" o "right".
        """
        if color is None:
            color = self.color_txt

        (tw, th), baseline = cv2.getTextSize(text, self.font_main, scale, thickness)
        x, y = org

        if align == "right":
            x = x - tw

        cv2.putText(
            img,
            text,
            (int(x), int(y)),
            self.font_main,
            scale,
            color,
            thickness,
            cv2.LINE_AA,
        )
        return tw, th

    def _resumen_epp(self, epp_results):
        """
        A partir de epp_results calcula:
            tiene_casco, tiene_chaleco, conf_casco, conf_chaleco
        """
        tiene_casco = False
        tiene_chaleco = False
        conf_casco = 0.0
        conf_chaleco = 0.0

        if not epp_results:
            return tiene_casco, tiene_chaleco, conf_casco, conf_chaleco

        for det in epp_results:
            if not det:
                continue

            label = str(det[0]).lower()
            score = 0.0
            if len(det) > 1:
                try:
                    score = float(det[1])
                except Exception:
                    score = 0.0
            score_pct = max(0.0, min(100.0, score * 100.0))

            if "casco" in label or "helmet" in label:
                tiene_casco = True
                conf_casco = max(conf_casco, score_pct)
            if "chaleco" in label or "vest" in label:
                tiene_chaleco = True
                conf_chaleco = max(conf_chaleco, score_pct)

        return tiene_casco, tiene_chaleco, conf_casco, conf_chaleco

    def _dibujar_bbox_epp(self, frame, epp_results):
        """
        Dibuja recuadros de EPP si vienen bounding boxes en epp_results.
        Espera cada elemento como: (label, score, (x, y, w, h))
        """
        if not epp_results:
            return

        for det in epp_results:
            if not det or len(det) < 3:
                continue

            label = str(det[0]).lower()
            bbox = det[2]

            if not isinstance(bbox, (tuple, list)) or len(bbox) != 4:
                continue

            x, y, w_box, h_box = bbox

            if "casco" in label or "helmet" in label:
                color = (34, 197, 94)    # verde
                txt = "Casco"
            elif "chaleco" in label or "vest" in label:
                color = (56, 189, 248)   # celeste
                txt = "Chaleco"
            else:
                color = (129, 140, 248)  # lila
                txt = "EPP"

            cv2.rectangle(frame, (x, y), (x + w_box, y + h_box), color, 2)
            (tw, th), _ = cv2.getTextSize(txt, self.font_main, 0.5, 1)
            cv2.rectangle(
                frame,
                (x, y - th - 6),
                (x + tw + 6, y),
                color,
                thickness=-1,
            )
            cv2.putText(
                frame,
                txt,
                (x + 3, y - 5),
                self.font_main,
                0.5,
                (0, 0, 0),
                1,
                cv2.LINE_AA,
            )

    # ------------------------------------------------------------------
    # Método principal
    # ------------------------------------------------------------------
    def dibujar_interfaz_completa(
        self,
        frame,
        info_trabajador=None,
        epp_results=None,
        tiempo_restante=None,
    ):
        """
        Dibuja HUD completo sobre el frame.

        Parámetros:
            frame           : frame BGR de OpenCV
            info_trabajador : dict o None, con campos opcionales:
                              "nombre", "id", "tiene_rostro", "bbox_rostro"
            epp_results     : lista de resultados de verify_epp
            tiempo_restante : segundos (int) o None

        Retorna:
            frame con overlay dibujado.
        """
        if frame is None or frame.size == 0:
            return frame

        if epp_results is None:
            epp_results = []

        if tiempo_restante is None:
            tiempo_restante = 0

        h, w = frame.shape[:2]
        output = frame.copy()

        # Información de EPP
        tiene_casco, tiene_chaleco, conf_casco, conf_chaleco = self._resumen_epp(
            epp_results
        )
        acceso_permitido = tiene_casco and tiene_chaleco

        # ------------------------------------------------------------------
        # 1. Dibujar bounding boxes de EPP (si existen)
        # ------------------------------------------------------------------
        self._dibujar_bbox_epp(output, epp_results)

        # 1b. Dibujar bbox del rostro si viene en info_trabajador
        if isinstance(info_trabajador, dict):
            bbox = info_trabajador.get("bbox_rostro")
            if bbox and len(bbox) == 4:
                x, y, w_box, h_box = bbox
                cv2.rectangle(output, (x, y), (x + w_box, y + h_box), self.color_face_box, 2)

        # ------------------------------------------------------------------
        # 2. Panel izquierdo (info trabajador)
        # ------------------------------------------------------------------
        panel_h = int(h * 0.16)
        panel_w = int(w * 0.40)
        x1, y1 = 10, 10
        x2, y2 = x1 + panel_w, y1 + panel_h

        self._draw_transparent_rect(
            output, (x1, y1), (x2, y2), self.color_panel, alpha=0.65
        )

        # Texto trabajador
        nombre_txt = "Sin trabajador detectado"
        id_txt = ""
        estado_rostro = "Sin rostro"

        if isinstance(info_trabajador, dict):
            nombre = info_trabajador.get("nombre") or info_trabajador.get("Name")
            enr = info_trabajador.get("id") or info_trabajador.get("Enrollment")
            tiene_rostro = info_trabajador.get("tiene_rostro", False)

            if nombre:
                nombre_txt = nombre
            if enr:
                id_txt = f"ID: {enr}"

            if tiene_rostro:
                estado_rostro = "Rostro detectado"
            else:
                estado_rostro = "Buscando rostro..."

        # Dibujar textos
        pad_x = x1 + 14
        pad_y = y1 + 24

        self._draw_text(
            output,
            "Trabajador",
            (pad_x, pad_y),
            scale=0.55,
            color=self.color_txt_sec,
        )

        self._draw_text(
            output,
            nombre_txt,
            (pad_x, pad_y + 20),
            scale=0.75,
            color=self.color_txt,
        )

        if id_txt:
            self._draw_text(
                output,
                id_txt,
                (pad_x, pad_y + 40),
                scale=0.55,
                color=self.color_txt_sec,
            )

        # Estado del rostro
        estado_color = self.color_txt_sec
        if "detectado" in estado_rostro.lower():
            estado_color = self.color_ok
        self._draw_text(
            output,
            estado_rostro,
            (pad_x, pad_y + 60),
            scale=0.5,
            color=estado_color,
        )

        # ------------------------------------------------------------------
        # 3. Panel derecho (estado de EPP)
        # ------------------------------------------------------------------
        panel_w2 = int(w * 0.42)
        x1r = w - panel_w2 - 10
        y1r = 10
        x2r = x1r + panel_w2
        y2r = y1r + panel_h

        self._draw_transparent_rect(
            output, (x1r, y1r), (x2r, y2r), self.color_panel_suave, alpha=0.70
        )

        # Título / estado global
        if acceso_permitido:
            titulo_epp = "EPP COMPLETO"
            color_titulo = self.color_ok
        else:
            if not tiene_casco and not tiene_chaleco:
                titulo_epp = "EPP NO DETECTADO"
            else:
                titulo_epp = "EPP INCOMPLETO"
            color_titulo = (0, 0, 255)  # rojo

        pad_xr = x1r + 14
        pad_yr = y1r + 24

        self._draw_text(
            output,
            titulo_epp,
            (pad_xr, pad_yr),
            scale=0.7,
            color=color_titulo,
        )

        # Detalles de casco / chaleco
        txt_casco = f"Casco: {'OK' if tiene_casco else 'FALTA'}"
        txt_chaleco = f"Chaleco: {'OK' if tiene_chaleco else 'FALTA'}"
        if conf_casco > 0:
            txt_casco += f"  ({conf_casco:.0f}%)"
        if conf_chaleco > 0:
            txt_chaleco += f"  ({conf_chaleco:.0f}%)"

        color_casco = self.color_ok if tiene_casco else (0, 0, 255)
        color_chaleco = self.color_ok if tiene_chaleco else (0, 0, 255)

        self._draw_text(
            output,
            txt_casco,
            (pad_xr, pad_yr + 20),
            scale=0.55,
            color=color_casco,
        )
        self._draw_text(
            output,
            txt_chaleco,
            (pad_xr, pad_yr + 40),
            scale=0.55,
            color=color_chaleco,
        )

        # Fecha/hora pequeña
        now_str = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
        self._draw_text(
            output,
            now_str,
            (x2r - 10, y2r - 10),
            scale=0.45,
            color=self.color_txt_sec,
            align="right",
        )

        # ------------------------------------------------------------------
        # 4. Barra inferior: mensaje + tiempo
        # ------------------------------------------------------------------
        bar_h = int(h * 0.11)
        y_bar1 = h - bar_h - 8
        y_bar2 = h - 8

        self._draw_transparent_rect(
            output,
            (8, y_bar1),
            (w - 8, y_bar2),
            (15, 23, 42),
            alpha=0.85,
        )

        # Tiempo restante
        msg_tiempo = f"Tiempo restante: {max(0, int(tiempo_restante))} s"
        self._draw_text(
            output,
            msg_tiempo,
            (18, y_bar1 + 26),
            scale=0.6,
            color=self.color_txt_sec,
        )

        # Mensaje principal según estado
        if acceso_permitido:
            msg_estado = "EPP completo. Acceso permitido."
            msg_color = self.color_ok
        else:
            if not isinstance(info_trabajador, dict) or not info_trabajador.get(
                "tiene_rostro", False
            ):
                msg_estado = "Buscando rostro del trabajador..."
                msg_color = self.color_txt_sec
            else:
                faltantes = []
                if not tiene_casco:
                    faltantes.append("casco")
                if not tiene_chaleco:
                    faltantes.append("chaleco")
                if faltantes:
                    msg_estado = "EPP incompleto: falta " + ", ".join(faltantes)
                    msg_color = (0, 0, 255)
                else:
                    msg_estado = "EPP no detectado aún."
                    msg_color = self.color_txt_sec

        self._draw_text(
            output,
            msg_estado,
            (18, y_bar1 + 50),
            scale=0.7,
            color=msg_color,
        )

        # Mensaje pequeño a la derecha
        helper_txt = "Presione ESC para salir"
        self._draw_text(
            output,
            helper_txt,
            (w - 18, y_bar1 + 50),
            scale=0.5,
            color=self.color_txt_sec,
            align="right",
        )

        return output


# ----------------------------------------------------------------------
# DEMO RÁPIDA (opcional)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    """
    Prueba rápida de la interfaz.
    Requiere tener epp_detector_integrado.verify_epp disponible.
    """
    try:
        from epp_detector_integrado import verify_epp
    except Exception:
        verify_epp = None

    interfaz = InterfazAsistenciaEPP()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("No se pudo abrir la cámara para la demo.")
        exit(0)

    print("Demo InterfazAsistenciaEPP - Presione ESC para salir")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        info_trabajador = {
            "nombre": "Trabajador Demo",
            "id": "000",
            "tiene_rostro": True,
            "bbox_rostro": (50, 80, 120, 140),  # aproximado, solo para ver el recuadro
        }

        if verify_epp is not None:
            epp_results = verify_epp(frame)
        else:
            # Si no hay verify_epp, simulamos sin EPP
            epp_results = []

        frame_out = interfaz.dibujar_interfaz_completa(
            frame,
            info_trabajador=info_trabajador,
            epp_results=epp_results,
            tiempo_restante=5,
        )

        cv2.imshow("Test Interfaz Asistencia", frame_out)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Demo finalizada.")
