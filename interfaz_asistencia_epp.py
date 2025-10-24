"""
Interfaz Visual para Sistema de Asistencia con EPP
Adaptado de SafeWork AI
"""

import cv2
import numpy as np
from datetime import datetime


class InterfazAsistenciaEPP:
    """
    Interfaz visual moderna para mostrar detección de EPP
    en el sistema de asistencia
    """
    
    def __init__(self):
        self.colores = {
            'verde': (0, 255, 0),
            'rojo': (0, 0, 255),
            'azul': (255, 140, 0),
            'blanco': (255, 255, 255),
            'negro': (0, 0, 0),
            'amarillo': (0, 255, 255),
            'gris': (128, 128, 128),
            'naranja': (0, 165, 255)
        }
        
        # Transparencia de los paneles
        self.alpha_panel = 0.85
    
    def dibujar_interfaz_completa(self, frame, info_trabajador, epp_results, tiempo_restante=0):
        """
        Dibuja toda la interfaz sobre el frame
        
        Args:
            frame: Frame de video BGR
            info_trabajador: dict con 'nombre', 'id', 'tiene_rostro', 'bbox_rostro'
            epp_results: lista de detecciones EPP [(clase, score, bbox), ...]
            tiempo_restante: segundos restantes de captura
            
        Returns:
            Frame con interfaz dibujada
        """
        h, w = frame.shape[:2]
        overlay = frame.copy()
        
        # Analizar EPP
        tiene_casco = any('casco' in str(r[0]).lower() for r in epp_results)
        tiene_chaleco = any('chaleco' in str(r[0]).lower() for r in epp_results)
        acceso_permitido = tiene_casco and tiene_chaleco
        
        # Preparar resultado para paneles
        resultado = {
            'trabajador': info_trabajador,
            'tiene_casco': tiene_casco,
            'tiene_chaleco': tiene_chaleco,
            'acceso_permitido': acceso_permitido,
            'confianza_casco': next((r[1]*100 for r in epp_results if 'casco' in str(r[0]).lower()), 0),
            'confianza_chaleco': next((r[1]*100 for r in epp_results if 'chaleco' in str(r[0]).lower()), 0),
            'faltantes': []
        }
        
        if not tiene_casco:
            resultado['faltantes'].append('Casco')
        if not tiene_chaleco:
            resultado['faltantes'].append('Chaleco')
        
        # Dibujar rostro si está detectado
        if info_trabajador and info_trabajador.get('tiene_rostro'):
            bbox = info_trabajador.get('bbox_rostro')
            if bbox:
                x, y, bw, bh = bbox
                # Rectángulo verde para rostro reconocido
                cv2.rectangle(overlay, (x, y), (x + bw, y + bh), (0, 255, 0), 3)
                
                # Label superior
                label_y = max(y - 10, 30)
                cv2.rectangle(overlay, (x, label_y - 25), (x + 250, label_y), (0, 255, 0), -1)
                cv2.putText(overlay, info_trabajador['nombre'], (x + 5, label_y - 8),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        # Dibujar componentes
        self._dibujar_header(overlay, w, resultado)
        self._dibujar_panel_epp(overlay, resultado)
        self._dibujar_mensaje_central(overlay, resultado, w, h)
        self._dibujar_footer(overlay, resultado, w, h, tiempo_restante)
        
        # Aplicar transparencia
        frame_final = cv2.addWeighted(overlay, self.alpha_panel, frame, 1 - self.alpha_panel, 0)
        
        return frame_final
    
    def _dibujar_header(self, img, w, resultado):
        """Dibuja el header superior"""
        # Fondo del header
        cv2.rectangle(img, (0, 0), (w, 60), (40, 40, 40), -1)
        
        # Título
        cv2.putText(img, "SISTEMA DE ASISTENCIA - DETECTOR EPP", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, self.colores['amarillo'], 3)
        
        # Panel de trabajador
        trabajador = resultado.get('trabajador')
        if trabajador and trabajador.get('nombre'):
            nombre = trabajador['nombre']
            id_trabajador = trabajador.get('id', '---')
            
            panel_x = w - 280
            panel_y = 15
            panel_w = 260
            panel_h = 35
            
            # Fondo del panel
            cv2.rectangle(img, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), 
                         (60, 60, 60), -1)
            cv2.rectangle(img, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), 
                         (0, 255, 0), 2)
            
            # Texto
            cv2.putText(img, f"ID:{id_trabajador} - {nombre}", (panel_x + 10, panel_y + 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colores['blanco'], 2)
    
    def _dibujar_panel_epp(self, img, resultado):
        """Dibuja el panel de verificación de EPP"""
        x, y = 20, 80
        panel_w, panel_h = 340, 200
        
        # Fondo del panel
        cv2.rectangle(img, (x, y), (x + panel_w, y + panel_h),
                     (30, 30, 30), -1)
        cv2.rectangle(img, (x, y), (x + panel_w, y + panel_h),
                     self.colores['blanco'], 2)
        
        # Título del panel
        cv2.putText(img, "VERIFICACION EPP", (x + 15, y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.colores['amarillo'], 2)
        
        # Línea separadora
        cv2.line(img, (x + 15, y + 40), (x + panel_w - 15, y + 40),
                self.colores['gris'], 1)
        
        # Items de EPP
        items = [
            {
                'nombre': 'Casco Blanco',
                'tiene': resultado['tiene_casco'],
                'confianza': resultado.get('confianza_casco', 0)
            },
            {
                'nombre': 'Chaleco Azul',
                'tiene': resultado['tiene_chaleco'],
                'confianza': resultado.get('confianza_chaleco', 0)
            }
        ]
        
        y_offset = y + 75
        for item in items:
            # Color según estado
            if item['tiene']:
                color_icono = self.colores['verde']
                simbolo = "✓"
                estado_texto = "OK"
            else:
                color_icono = self.colores['rojo']
                simbolo = "✗"
                estado_texto = "NO"
            
            # Círculo de estado
            cv2.circle(img, (x + 35, y_offset), 20, color_icono, -1)
            cv2.circle(img, (x + 35, y_offset), 20, self.colores['blanco'], 2)
            
            # Símbolo en el círculo
            cv2.putText(img, simbolo, (x + 25, y_offset + 8),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.colores['blanco'], 2)
            
            # Nombre del EPP
            cv2.putText(img, item['nombre'], (x + 70, y_offset + 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.colores['blanco'], 2)
            
            # Estado
            cv2.putText(img, f"[{estado_texto}]", (x + 240, y_offset + 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_icono, 2)
            
            # Barra de confianza
            barra_w = 200
            barra_h = 8
            barra_x = x + 70
            barra_y = y_offset + 18
            
            # Fondo de la barra
            cv2.rectangle(img, (barra_x, barra_y), 
                         (barra_x + barra_w, barra_y + barra_h),
                         self.colores['gris'], -1)
            
            # Progreso
            progreso_w = int((item['confianza'] / 100) * barra_w)
            cv2.rectangle(img, (barra_x, barra_y),
                         (barra_x + progreso_w, barra_y + barra_h),
                         color_icono, -1)
            
            # Porcentaje
            cv2.putText(img, f"{item['confianza']:.0f}%",
                       (barra_x + barra_w + 10, barra_y + 7),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.colores['blanco'], 1)
            
            y_offset += 70
    
    def _dibujar_mensaje_central(self, img, resultado, w, h):
        """Dibuja el mensaje grande central"""
        acceso = resultado['acceso_permitido']
        
        # Dimensiones del panel
        panel_w, panel_h = 500, 140
        x = (w - panel_w) // 2
        y = h - panel_h - 100
        
        # Color según estado
        if acceso:
            color_fondo = (0, 150, 0)  # Verde oscuro
            color_texto = self.colores['blanco']
            texto_principal = "ACCESO PERMITIDO"
            icono = "✓"
        else:
            color_fondo = (0, 0, 180)  # Rojo oscuro
            color_texto = self.colores['blanco']
            texto_principal = "ACCESO DENEGADO"
            icono = "✗"
        
        # Fondo del panel
        cv2.rectangle(img, (x, y), (x + panel_w, y + panel_h),
                     color_fondo, -1)
        cv2.rectangle(img, (x, y), (x + panel_w, y + panel_h),
                     self.colores['blanco'], 5)
        
        # Ícono grande
        cv2.putText(img, icono, (x + 30, y + 85),
                   cv2.FONT_HERSHEY_SIMPLEX, 2.5, color_texto, 5)
        
        # Texto principal
        cv2.putText(img, texto_principal, (x + 130, y + 75),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.1, color_texto, 3)
        
        # Texto secundario
        if acceso:
            texto_sec = "Registro de asistencia OK"
        else:
            faltantes = resultado.get('faltantes', [])
            if faltantes:
                texto_sec = f"Falta: {', '.join(faltantes)}"
            else:
                texto_sec = "EPP Incompleto"
        
        cv2.putText(img, texto_sec, (x + 130, y + 115),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_texto, 2)
    
    def _dibujar_footer(self, img, resultado, w, h, tiempo_restante):
        """Dibuja información adicional en la parte inferior"""
        footer_y = h - 60
        
        # Fondo del footer
        cv2.rectangle(img, (0, footer_y), (w, h), (40, 40, 40), -1)
        
        # Tiempo restante (izquierda)
        if tiempo_restante > 0:
            texto_tiempo = f"Tiempo restante: {tiempo_restante}s"
            cv2.putText(img, texto_tiempo, (20, footer_y + 38),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.colores['amarillo'], 2)
        
        # Hora actual (derecha)
        hora_actual = datetime.now().strftime("%H:%M:%S")
        text_size = cv2.getTextSize(hora_actual, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        hora_x = w - text_size[0] - 20
        
        cv2.putText(img, hora_actual, (hora_x, footer_y + 38),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.colores['blanco'], 2)
        
        # Estado del sistema (centro)
        estado = "✓ Sistema Activo" if resultado['acceso_permitido'] else "⚠ Verificar EPP"
        color_estado = self.colores['verde'] if resultado['acceso_permitido'] else self.colores['naranja']
        
        text_size_estado = cv2.getTextSize(estado, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        estado_x = (w - text_size_estado[0]) // 2
        
        cv2.putText(img, estado, (estado_x, footer_y + 38),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_estado, 2)


# ===== TEST DEL MÓDULO =====

if __name__ == "__main__":
    print("="*60)
    print("TEST - INTERFAZ VISUAL DE ASISTENCIA")
    print("="*60)
    print("\nControles:")
    print("  Q - Salir")
    print("  ESPACIO - Simular detección")
    print("\nIniciando...\n")
    
    interfaz = InterfazAsistenciaEPP()
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Error: No se pudo abrir la cámara")
        exit()
    
    # Simular datos
    simular_con_epp = True
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Simular trabajador
        info_trabajador = {
            'nombre': 'Juan Pérez',
            'id': '777',
            'tiene_rostro': True,
            'bbox_rostro': (100, 100, 200, 250)
        }
        
        # Simular EPP
        if simular_con_epp:
            epp_results = [
                ('casco', 0.85, (100, 50, 300, 150)),
                ('chaleco', 0.92, (80, 200, 320, 400))
            ]
        else:
            epp_results = []
        
        # Dibujar interfaz
        frame_con_interfaz = interfaz.dibujar_interfaz_completa(
            frame, 
            info_trabajador, 
            epp_results,
            tiempo_restante=5
        )
        
        cv2.imshow('Test Interfaz Asistencia', frame_con_interfaz)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord(' '):
            simular_con_epp = not simular_con_epp
            print(f"Modo: {'CON EPP' if simular_con_epp else 'SIN EPP'}")
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ Test finalizado")