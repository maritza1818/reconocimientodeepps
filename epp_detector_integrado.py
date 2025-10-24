"""
Módulo de Detección de EPP - VERSION DE PRUEBA
Detecta: CABELLO NEGRO + CAMISA BEIGE
"""

import cv2
import numpy as np


class EPPDetectorIntegrado:
    """Detector de EPP por color y forma - VERSION PRUEBA"""
    
    def __init__(self):
        """Inicializa el detector"""
        # CABELLO NEGRO (en lugar de casco blanco)
        # Negro en HSV tiene V (luminosidad) muy baja
        self.casco_ranges = [
            {'lower': np.array([0, 0, 0]), 'upper': np.array([180, 255, 50])}
        ]
        
        # CAMISA BEIGE/CREMA (en lugar de chaleco azul)
        # Beige está en el rango amarillo-naranja con saturación baja
        self.chaleco_ranges = [
            {'lower': np.array([10, 20, 100]), 'upper': np.array([30, 150, 255])},
            {'lower': np.array([15, 10, 120]), 'upper': np.array([25, 100, 240])}
        ]
        
        # Umbrales más sensibles para pruebas
        self.threshold_casco = 1500      # Más bajo para cabello
        self.threshold_chaleco = 3000    # Más bajo para camisa
        
        self.min_circularidad_casco = 0.3   # Menos exigente
        self.min_aspect_ratio_chaleco = 0.5
        self.max_aspect_ratio_chaleco = 3.0
        self.detecciones_count = 0
    
    def detectar_casco(self, frame):
        """Detecta CABELLO NEGRO con forma CIRCULAR"""
        h, w = frame.shape[:2]
        zona_superior = frame[0:h//3, :]
        hsv = cv2.cvtColor(zona_superior, cv2.COLOR_BGR2HSV)
        mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
        
        for color_range in self.casco_ranges:
            mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
            mask_total = cv2.bitwise_or(mask_total, mask)
        
        kernel = np.ones((5, 5), np.uint8)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel)
        pixeles_color = cv2.countNonZero(mask_total)
        
        tiene_forma_circular = False
        max_circularidad = 0
        contours, _ = cv2.findContours(mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 500:
                continue
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            circularidad = 4 * np.pi * area / (perimeter * perimeter)
            if circularidad > max_circularidad:
                max_circularidad = circularidad
            if circularidad >= self.min_circularidad_casco:
                tiene_forma_circular = True
                break
        
        tiene_casco = (pixeles_color >= self.threshold_casco) and tiene_forma_circular
        confianza_color = min(100, (pixeles_color / self.threshold_casco) * 50)
        confianza_forma = max_circularidad * 50
        confianza = (confianza_color + confianza_forma) if tiene_forma_circular else 0
        return tiene_casco, min(100, confianza)
    
    def detectar_chaleco(self, frame):
        """Detecta CAMISA BEIGE con forma RECTANGULAR"""
        h, w = frame.shape[:2]
        zona_media = frame[h//3:2*h//3, :]
        hsv = cv2.cvtColor(zona_media, cv2.COLOR_BGR2HSV)
        mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
        
        for color_range in self.chaleco_ranges:
            mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
            mask_total = cv2.bitwise_or(mask_total, mask)
        
        kernel = np.ones((7, 7), np.uint8)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel)
        pixeles_color = cv2.countNonZero(mask_total)
        
        tiene_forma_rectangular = False
        contours, _ = cv2.findContours(mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 1000:
                continue
            x, y, w_rect, h_rect = cv2.boundingRect(contour)
            if h_rect == 0:
                continue
            aspect_ratio = w_rect / h_rect
            if self.min_aspect_ratio_chaleco <= aspect_ratio <= self.max_aspect_ratio_chaleco:
                tiene_forma_rectangular = True
                break
        
        tiene_chaleco = (pixeles_color >= self.threshold_chaleco) and tiene_forma_rectangular
        confianza_color = min(100, (pixeles_color / self.threshold_chaleco) * 50)
        confianza_forma = 50 if tiene_forma_rectangular else 0
        confianza = confianza_color + confianza_forma
        return tiene_chaleco, min(100, confianza)
    
    def verificar_epp(self, frame):
        """Verifica EPP completo"""
        self.detecciones_count += 1
        tiene_casco, conf_casco = self.detectar_casco(frame)
        tiene_chaleco, conf_chaleco = self.detectar_chaleco(frame)
        resultados = []
        
        if tiene_casco:
            h, w = frame.shape[:2]
            resultados.append(('casco', conf_casco/100, (w//2-50, 50, w//2+50, 150)))
        if tiene_chaleco:
            h, w = frame.shape[:2]
            resultados.append(('chaleco', conf_chaleco/100, (w//2-80, h//3, w//2+80, 2*h//3)))
        
        if self.detecciones_count % 30 == 0:
            print(f"[EPP] Cabello: {tiene_casco} ({conf_casco:.1f}%) | Camisa: {tiene_chaleco} ({conf_chaleco:.1f}%)")
        return resultados
    
    def dibujar_resultados(self, frame, resultados):
        """Dibuja resultados en el frame"""
        for clase, score, (x1, y1, x2, y2) in resultados:
            color = (0, 255, 0) if score > 0.5 else (0, 165, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            texto = f"{clase}: {score*100:.1f}%"
            cv2.putText(frame, texto, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        tiene_todos = len(resultados) >= 2
        estado = "EPP COMPLETO (PRUEBA)" if tiene_todos else "EPP INCOMPLETO"
        color_estado = (0, 255, 0) if tiene_todos else (0, 0, 255)
        cv2.putText(frame, estado, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_estado, 2)
        return frame


_detector_global = None

def get_detector():
    """Obtiene instancia singleton"""
    global _detector_global
    if _detector_global is None:
        _detector_global = EPPDetectorIntegrado()
    return _detector_global

def verify_epp(frame, min_score=0.3):
    """Función compatible con sistema de asistencia"""
    detector = get_detector()
    return detector.verificar_epp(frame)

def draw_results(frame, results):
    """Dibuja resultados"""
    detector = get_detector()
    return detector.dibujar_resultados(frame, results)


if __name__ == "__main__":
    print("="*60)
    print("TEST - DETECTOR EPP (MODO PRUEBA)")
    print("="*60)
    print("Detectando:")
    print("  - Cabello NEGRO (como casco)")
    print("  - Camisa BEIGE (como chaleco)")
    print("\nControles:")
    print("  Q - Salir")
    print("="*60)
    
    detector = EPPDetectorIntegrado()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: camara")
        exit()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        resultados = detector.verificar_epp(frame)
        frame = detector.dibujar_resultados(frame, resultados)
        cv2.imshow('Test EPP - Modo Prueba', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("\nTest finalizado")