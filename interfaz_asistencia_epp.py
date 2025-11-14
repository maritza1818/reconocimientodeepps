import cv2
import numpy as np


class InterfazAsistenciaEPP:
    """
    Interfaz gráfica sobre el frame de la cámara.

    Muestra:
      - Rostro del trabajador (recuadro verde + nombre)
      - Cajas para:
            * Casco
            * Chaleco
            * Códigos QR detectados
      - Panel lateral de estado de EPP
      - Mensaje central de acceso permitido / denegado
      - Footer con contador de tiempo restante
    """

    def __init__(self):
        # Transparencia de los paneles
        self.alpha_panel = 0.35

        # Paleta de colores (BGR)
        self.colores = {
            "verde": (0, 255, 0),
            "rojo": (0, 0, 255),
            "amarillo": (0, 255, 255),
            "blanco": (255, 255, 255),
            "gris_oscuro": (40, 40, 40),
            "gris_medio": (70, 70, 70),
            "naranja": (0, 140, 255),
            "magenta": (255, 0, 255),
            "cyan": (255, 255, 0),
        }

    # -------------------------------------------------------
    #  MÉTODO PRINCIPAL
    # -------------------------------------------------------
    def dibujar_interfaz_completa(
        self,
        frame,
        info_trabajador=None,
        epp_results=None,
        tiempo_restante=None,
    ):
        """
        Dibuja toda la interfaz sobre el frame.

        :param frame: frame original de la cámara (BGR)
        :param info_trabajador: dict con info del trabajador reconocid@
            {
                'id': str/int,
                'nombre': str,
                'hora': str,
                'tiene_rostro': bool,
                'bbox_rostro': (x, y, w, h),
                ...
            }
        :param epp_results: lista de (clase, score, (x1,y1,x2,y2))
            clase puede ser: 'casco', 'chaleco', 'qr:LO_QUE_CONTIENE'
        :param tiempo_restante: segundos para terminar la toma de asistencia
        """
        if epp_results is None:
            epp_results = []

        h, w = frame.shape[:2]
        overlay = frame.copy()

        # ---------- Análisis EPP a partir de epp_results ----------
        tiene_casco = any("casco" in str(r[0]).lower() for r in epp_results)
        tiene_chaleco = any("chaleco" in str(r[0]).lower() for r in epp_results)
        tiene_qr = any(str(r[0]).lower().startswith("qr:") for r in epp_results)

        # Por ahora, consideramos acceso permitido si hay casco + chaleco.
        # Más adelante añadiremos la validación del QR contra el CSV.
        acceso_permitido = tiene_casco and tiene_chaleco and tiene_qr

        resultado = {
            "trabajador": info_trabajador,
            "tiene_casco": tiene_casco,
            "tiene_chaleco": tiene_chaleco,
            "tiene_qr": tiene_qr,
            "acceso_permitido": acceso_permitido,
            "confianza_casco": next(
                (r[1] * 100 for r in epp_results if "casco" in str(r[0]).lower()),
                0,
            ),
            "confianza_chaleco": next(
                (r[1] * 100 for r in epp_results if "chaleco" in str(r[0]).lower()),
                0,
            ),
            "faltantes": [],
        }

        if not tiene_casco:
            resultado["faltantes"].append("Casco")
        if not tiene_chaleco:
            resultado["faltantes"].append("Chaleco")
        # Solo a nivel visual, marcamos si no hay ningún QR detectado
        if not tiene_qr:
            resultado["faltantes"].append("QR")

        # ---------- Dibujo de rostro ----------
        self._dibujar_rostro(overlay, info_trabajador)

        # ---------- Dibujo de EPP + QR (cajas) ----------
        self._dibujar_bboxes_epp_y_qr(overlay, epp_results, resultado)

        # ---------- Paneles y textos ----------
        self._dibujar_header(overlay, w, resultado)
        self._dibujar_panel_epp(overlay, resultado)
        self._dibujar_mensaje_central(overlay, resultado, w, h)
        self._dibujar_footer(overlay, resultado, w, h, tiempo_restante)

        # ---------- Mezcla con transparencia ----------
        frame_final = cv2.addWeighted(
            overlay, self.alpha_panel, frame, 1 - self.alpha_panel, 0
        )

        return frame_final

    # -------------------------------------------------------
    #  ROSTRO
    # -------------------------------------------------------
    def _dibujar_rostro(self, img, info_trabajador):
        """Dibuja el recuadro verde y el nombre del trabajador."""
        if not info_trabajador:
            return

        if not info_trabajador.get("tiene_rostro"):
            return

        bbox = info_trabajador.get("bbox_rostro")
        if not bbox:
            return

        x, y, bw, bh = bbox

        # Caja verde alrededor del rostro
        cv2.rectangle(img, (x, y), (x + bw, y + bh), self.colores["verde"], 3)

        # Fondo para el nombre
        label_y = max(y - 10, 30)
        cv2.rectangle(
            img,
            (x, label_y - 25),
            (x + 260, label_y),
            self.colores["verde"],
            -1,
        )

        texto = info_trabajador.get("nombre", "Trabajador")
        cv2.putText(
            img,
            texto,
            (x + 5, label_y - 7),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            2,
        )

    # -------------------------------------------------------
    #  EPP + QR (CAJAS)
    # -------------------------------------------------------
    def _dibujar_bboxes_epp_y_qr(self, img, epp_results, resultado):
        """
        Dibuja las cajas de:
          - casco
          - chaleco
          - qr:...
        con colores y etiquetas claras.
        """
        for clase, score, (x1, y1, x2, y2) in epp_results:
            clase_str = str(clase).lower()
            score_pct = int(score * 100)

            if "casco" in clase_str:
                color = self.colores["verde"]
                etiqueta = f"Casco ({score_pct}%)"
            elif "chaleco" in clase_str:
                color = self.colores["naranja"]
                etiqueta = f"Chaleco ({score_pct}%)"
            elif clase_str.startswith("qr:"):
                color = self.colores["magenta"]
                # extraer contenido del QR
                contenido = clase_str.split("qr:", 1)[1]
                if len(contenido) > 25:
                    contenido = contenido[:22] + "..."
                etiqueta = f"QR: {contenido}"
            else:
                continue

            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                img,
                etiqueta,
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )

    # -------------------------------------------------------
    #  HEADER
    # -------------------------------------------------------
    def _dibujar_header(self, img, w, resultado):
        """Dibuja el header superior con título + info del trabajador."""
        # Fondo
        cv2.rectangle(img, (0, 0), (w, 60), self.colores["gris_oscuro"], -1)

        # Título general
        cv2.putText(
            img,
            "SISTEMA DE ASISTENCIA - DETECTOR EPP",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            self.colores["amarillo"],
            2,
        )

        # Panel pequeño a la derecha con info del trabajador
        trabajador = resultado.get("trabajador")
        if trabajador and trabajador.get("nombre"):
            nombre = trabajador["nombre"]
            id_trabajador = trabajador.get("id", "---")
            hora = trabajador.get("hora", "")

            panel_w, panel_h = 340, 40
            panel_x = w - panel_w - 20
            panel_y = 10

            # Fondo panel
            cv2.rectangle(
                img,
                (panel_x, panel_y),
                (panel_x + panel_w, panel_y + panel_h),
                self.colores["gris_medio"],
                -1,
            )
            cv2.rectangle(
                img,
                (panel_x, panel_y),
                (panel_x + panel_w, panel_y + panel_h),
                self.colores["verde"],
                2,
            )

            texto = f"ID: {id_trabajador} - {nombre}"
            cv2.putText(
                img,
                texto,
                (panel_x + 10, panel_y + 18),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                self.colores["blanco"],
                1,
            )

            if hora:
                cv2.putText(
                    img,
                    f"{hora}",
                    (panel_x + 10, panel_y + 34),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    self.colores["amarillo"],
                    1,
                )

    # -------------------------------------------------------
    #  PANEL LATERAL: ESTADO EPP
    # -------------------------------------------------------
    def _dibujar_panel_epp(self, img, resultado):
        """Panel en la parte izquierda con estado de casco, chaleco y QR."""
        x, y = 20, 80
        panel_w, panel_h = 360, 210

        # Fondo panel
        cv2.rectangle(
            img, (x, y), (x + panel_w, y + panel_h), self.colores["gris_medio"], -1
        )
        cv2.rectangle(
            img, (x, y), (x + panel_w, y + panel_h), self.colores["amarillo"], 2
        )

        cv2.putText(
            img,
            "VERIFICACION EPP",
            (x + 20, y + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            self.colores["blanco"],
            2,
        )

        # Ítems
        items = [
            {
                "nombre": "Casco",
                "tiene": resultado.get("tiene_casco", False),
                "confianza": resultado.get("confianza_casco", 0),
            },
            {
                "nombre": "Chaleco",
                "tiene": resultado.get("tiene_chaleco", False),
                "confianza": resultado.get("confianza_chaleco", 0),
            },
            {
                "nombre": "Codigo QR EPP",
                "tiene": resultado.get("tiene_qr", False),
                "confianza": 0,  # por ahora no usamos % de confianza de QR
            },
        ]

        start_y = y + 60
        step_y = 50
        radius = 16

        for i, item in enumerate(items):
            cy = start_y + i * step_y
            cx = x + 30

            tiene = item["tiene"]
            if tiene:
                color_icono = self.colores["verde"]
                simbolo = "✓"
            else:
                color_icono = self.colores["rojo"]
                simbolo = "✗"

            # Círculo
            cv2.circle(img, (cx, cy), radius, color_icono, -1)
            cv2.putText(
                img,
                simbolo,
                (cx - 7, cy + 7),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 0),
                2,
            )

            # Texto del ítem
            texto = item["nombre"]
            if item["nombre"] != "Codigo QR EPP":
                texto += f" ({int(item['confianza'])}%)"

            cv2.putText(
                img,
                texto,
                (cx + 40, cy + 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                self.colores["blanco"],
                2,
            )

    # -------------------------------------------------------
    #  MENSAJE CENTRAL
    # -------------------------------------------------------
    def _dibujar_mensaje_central(self, img, resultado, w, h):
        """Mensaje grande de ACCESO PERMITIDO / DENEGADO."""
        acceso = resultado.get("acceso_permitido", False)
        faltantes = resultado.get("faltantes", [])

        texto_principal = "ACCESO PERMITIDO" if acceso else "ACCESO DENEGADO"
        color = self.colores["verde"] if acceso else self.colores["rojo"]

        # Fondo suave
        cx1, cy1 = w // 2 - 250, h // 2 - 50
        cx2, cy2 = w // 2 + 250, h // 2 + 50
        cv2.rectangle(img, (cx1, cy1), (cx2, cy2), (30, 30, 30), -1)
        cv2.rectangle(img, (cx1, cy1), (cx2, cy2), color, 2)

        # Texto principal
        cv2.putText(
            img,
            texto_principal,
            (cx1 + 40, cy1 + 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            color,
            3,
        )

        # Texto secundario
        if faltantes and not acceso:
            detalle = "Falta: " + ", ".join(faltantes)
        else:
            detalle = "EPP completo y detectable"

        cv2.putText(
            img,
            detalle,
            (cx1 + 40, cy1 + 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.colores["blanco"],
            2,
        )

    # -------------------------------------------------------
    #  FOOTER
    # -------------------------------------------------------
    def _dibujar_footer(self, img, resultado, w, h, tiempo_restante):
        """Footer inferior con estado del sistema y tiempo restante."""
        footer_h = 45
        y1 = h - footer_h
        y2 = h

        cv2.rectangle(img, (0, y1), (w, y2), self.colores["gris_oscuro"], -1)

        # Estado general
        acceso = resultado.get("acceso_permitido", False)
        if acceso:
            texto_estado = "✓ Sistema activo - EPP OK"
            color = self.colores["verde"]
        else:
            texto_estado = "⚠ Verificar EPP / QR"
            color = self.colores["amarillo"]

        cv2.putText(
            img,
            texto_estado,
            (20, y1 + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )

        # Tiempo restante
        if tiempo_restante is not None:
            texto_tiempo = f"Tiempo restante: {int(tiempo_restante)} s"
            cv2.putText(
                img,
                texto_tiempo,
                (w - 260, y1 + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                self.colores["blanco"],
                2,
            )
