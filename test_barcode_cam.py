import cv2
from pyzbar.pyzbar import decode

def main():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara")
        return

    print("✅ Cámara abierta. Apunta un código de barras o QR hacia la cámara.")
    print("Pulsa ESC para salir.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ No se pudo leer la cámara")
            break

        # Decodificar códigos
        codes = decode(frame)

        for code in codes:
            data = code.data.decode("utf-8").strip()
            tipo = code.type  # QR_CODE, CODE128, etc.

            # Dibujar un rectángulo donde está el código
            x, y, w, h = code.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            texto = f"{tipo}: {data}"
            cv2.putText(frame, texto, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 0), 2)

            print(f"➡ Detectado: {texto}")

        cv2.imshow("Test lector cámara", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
