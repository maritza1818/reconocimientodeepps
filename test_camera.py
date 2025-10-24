import cv2
import sys

# Intenta abrir la cámara web. '0' es usualmente la cámara integrada.
# Si tienes una cámara USB, a veces puede ser '1' o '2'.
cap = cv2.VideoCapture(0) 

if not cap.isOpened():
    print("\n[ERROR] No se pudo abrir la cámara.")
    print("Verifica si otra app la está usando o si los permisos son correctos.\n")
    sys.exit()

print("\n[INFO] Cámara detectada. Presiona 'q' para salir.")

while True:
    # Lee un frame de la cámara
    ret, frame = cap.read()

    if not ret:
        print("[ERROR] No se pudo leer el frame.")
        break

    # Muestra el frame en una ventana
    cv2.imshow('Prueba de Cámara - Presiona "q" para salir', frame)

    # Espera 1ms y revisa si se presionó la tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libera la cámara y cierra ventanas
cap.release()
cv2.destroyAllWindows()
print("[INFO] Cámara cerrada. Fin de la prueba.")
