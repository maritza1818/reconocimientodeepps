"""
Módulo de Detección de EPP Integrado
Combina el detector de SafeWork AI con el sistema de asistencia

Detecta:
- Casco BLANCO con forma CIRCULAR
- Chaleco AZUL con forma RECTANGULAR
"""

import cv2
import numpy as np


class EPPDetectorIntegrado:
    """
    Detector de EPP simplificado para integración con sistema de asistencia
    Basado en detección por COLOR + FORMA
    """
    
    def __init__(self):
        """Inicializa el detector con rangos de color optimizados"""
        
        # ===== RANGOS DE COLOR HSV =====
        
        # CASCO BLANCO
        self.casco_ranges = [
    {'lower': np.array([0, 0, 0]), 'upper': np.array([180, 255, 30])}
]
        
        # CHALECO AZUL/CELESTE
       self.chaleco_ranges = [
    {'lower': np.array([20, 50, 150]), 'upper': np.array([35, 150, 255])}
]
        
        # ===== UMBRALES =====
        self.threshold_casco = 3000      # Píxeles mínimos para casco
        self.threshold_chaleco = 5000    # Píxeles mínimos para chaleco
        
        # ===== PARÁMETROS DE FORMA =====
        self.min_circularidad_casco = 0.5      # Circularidad mínima (0-1)
        self.min_aspect_ratio_chaleco = 0.8    # Aspecto mínimo chaleco
        self.max_aspect_ratio_chaleco = 2.5    # Aspecto máximo chaleco
        
        # Contador para debug
        self.detecciones_count = 0
    
    def detectar_casco(self, frame):
        """
        Detecta casco BLANCO con forma CIRCULAR en zona superior
        
        Args:
            frame: Imagen BGR de OpenCV
            
        Returns:
            tuple: (tiene_casco, confianza)
        """
        h, w = frame.shape[:2]
        
        # Zona superior (1/3 superior)
        zona_superior = frame[0:h//3, :]
        
        # Convertir a HSV
        hsv = cv2.cvtColor(zona_superior, cv2.COLOR_BGR2HSV)
        
        # Crear máscara para color blanco
        mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
        
        for color_range in self.casco_ranges:
            mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
            mask_total = cv2.bitwise_or(mask_total, mask)
        
        # Limpiar ruido
        kernel = np.ones((5, 5), np.uint8)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel)
        
        # Contar píxeles blancos
        pixeles_color = cv2.countNonZero(mask_total)
        
        # Buscar forma circular
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
            
            # Circularidad: 4π*área / perímetro²
            circularidad = 4 * np.pi * area / (perimeter * perimeter)
            
            if circularidad > max_circularidad:
                max_circularidad = circularidad
            
            if circularidad >= self.min_circularidad_casco:
                tiene_forma_circular = True
                break
        
        # Decisión: debe cumplir COLOR + FORMA
        tiene_casco = (pixeles_color >= self.threshold_casco) and tiene_forma_circular
        
        # Confianza combinada
        confianza_color = min(100, (pixeles_color / self.threshold_casco) * 50)
        confianza_forma = max_circularidad * 50
        confianza = (confianza_color + confianza_forma) if tiene_forma_circular else 0
        
        return tiene_casco, min(100, confianza)
    
    def detectar_chaleco(self, frame):
        """
        Detecta chaleco AZUL con forma RECTANGULAR en zona media
        
        Args:
            frame: Imagen BGR de OpenCV
            
        Returns:
            tuple: (tiene_chaleco, confianza)
        """
        h, w = frame.shape[:2]
        
        # Zona media (centro)
        zona_media = frame[h//3:2*h//3, :]
        
        # Convertir a HSV
        hsv = cv2.cvtColor(zona_media, cv2.COLOR_BGR2HSV)
        
        # Crear máscara para color azul
        mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
        
        for color_range in self.chaleco_ranges:
            mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
            mask_total = cv2.bitwise_or(mask_total, mask)
        
        # Limpiar ruido
        kernel = np.ones((7, 7), np.uint8)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel)
        
        # Contar píxeles azules
        pixeles_color = cv2.countNonZero(mask_total)
        
        # Buscar forma rectangular
        tiene_forma_rectangular = False
        
        contours, _ = cv2.findContours(mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 1000:
                continue
            
            x, y, w_rect, h_rect = cv2.boundingRect(contour)
            
            if h_rect == 0:
                continue
            
            # Relación de aspecto (ancho/alto)
            aspect_ratio = w_rect / h_rect
            
            # Verificar si es forma de chaleco (más ancho que alto)
            if self.min_aspect_ratio_chaleco <= aspect_ratio <= self.max_aspect_ratio_chaleco:
                tiene_forma_rectangular = True
                break
        
        # Decisión: debe cumplir COLOR + FORMA
        tiene_chaleco = (pixeles_color >= self.threshold_chaleco) and tiene_forma_rectangular
        
        # Confianza combinada
        confianza_color = min(100, (pixeles_color / self.threshold_chaleco) * 50)
        confianza_forma = 50 if tiene_forma_rectangular else 0
        confianza = confianza_color + confianza_forma
        
        return tiene_chaleco, min(100, confianza)
    
    def verificar_epp(self, frame):
        """
        Función principal compatible con automaticAttendance.py
        Verifica EPP completo (casco + chaleco)
        
        Args:
            frame: Imagen BGR de OpenCV
            
        Returns:
            list: Lista de detecciones en formato [(clase, score, bbox), ...]
                  Si tiene EPP completo retorna detecciones, sino lista vacía
        """
        self.detecciones_count += 1
        
        # Detectar componentes
        tiene_casco, conf_casco = self.detectar_casco(frame)
        tiene_chaleco, conf_chaleco = self.detectar_chaleco(frame)
        
        # Lista de resultados
        resultados = []
        
        # Solo retorna detecciones si tiene AMBOS EPPs
        if tiene_casco:
            # Bbox ficticio para compatibilidad (zona superior)
            h, w = frame.shape[:2]
            resultados.append(('casco', conf_casco/100, (w//2-50, 50, w//2+50, 150)))
        
        if tiene_chaleco:
            # Bbox ficticio para compatibilidad (zona media)
            h, w = frame.shape[:2]
            resultados.append(('chaleco', conf_chaleco/100, (w//2-80, h//3, w//2+80, 2*h//3)))
        
        # Debug info
        if self.detecciones_count % 30 == 0:  # Cada 30 frames
            print(f"[EPP] Casco: {tiene_casco} ({conf_casco:.1f}%) | Chaleco: {tiene_chaleco} ({conf_chaleco:.1f}%)")
        
        return resultados
    
    def dibujar_resultados(self, frame, resultados):
        """
        Dibuja los resultados de detección en el frame
        Compatible con draw_results() del sistema original
        
        Args:
            frame: Imagen BGR
            resultados: Lista de detecciones
            
        Returns:
            Frame con visualizaciones
        """
        for clase, score, (x1, y1, x2, y2) in resultados:
            # Color según EPP
            color = (0, 255, 0) if score > 0.5 else (0, 165, 255)
            
            # Dibujar bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Texto
            texto = f"{clase}: {score*100:.1f}%"
            cv2.putText(frame, texto, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Indicador general
        tiene_todos = len(resultados) >= 2
        estado = "EPP COMPLETO" if tiene_todos else "EPP INCOMPLETO"
        color_estado = (0, 255, 0) if tiene_todos else (0, 0, 255)
        
        cv2.putText(frame, estado, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_estado, 2)
        
        return frame


# ===== FUNCIONES DE COMPATIBILIDAD =====

# Instancia global para usar en automaticAttendance.py
_detector_global = None

def get_detector():
    """Obtiene instancia singleton del detector"""
    global _detector_global
    if _detector_global is None:
        _detector_global = EPPDetectorIntegrado()
    return _detector_global

def verify_epp(frame, min_score=0.3):
    """
    Función compatible con el sistema de asistencia original
    
    Args:
        frame: Imagen BGR
        min_score: Umbral mínimo (no usado, mantenido por compatibilidad)
        
    Returns:
        list: Detecciones en formato [(clase, score, bbox), ...]
    """
    detector = get_detector()
    return detector.verificar_epp(frame)

def draw_results(frame, results):
    """
    Función compatible para dibujar resultados
    
    Args:
        frame: Imagen BGR
        results: Lista de detecciones
        
    Returns:
        Frame con visualizaciones
    """
    detector = get_detector()
    return detector.dibujar_resultados(frame, results)


# ===== TEST DEL MÓDULO =====

if __name__ == "__main__":
    print("="*60)
    print("TEST - DETECTOR DE EPP INTEGRADO")
    print("="*60)
    print("\nControles:")
    print("  Q o ESC - Salir")
    print("  ESPACIO - Captura momento actual")
    print("\nIniciando cámara...\n")
    
    detector = EPPDetectorIntegrado()
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Error: No se pudo abrir la cámara")
        exit()
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Detectar EPP
        resultados = detector.verificar_epp(frame)
        
        # Dibujar resultados
        frame = detector.dibujar_resultados(frame, resultados)
        
        # Info en consola cada segundo
        if frame_count % 30 == 0:
            tiene_completo = len(resultados) >= 2
            print(f"Frame {frame_count}: EPP {'✅ COMPLETO' if tiene_completo else '❌ INCOMPLETO'}")
        
        # Mostrar
        cv2.imshow('Test Detector EPP', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord(' '):
            print(f"\n📸 Captura - Resultados: {resultados}\n")
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ Test finalizado")