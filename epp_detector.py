# epp_detector.py
import cv2
import numpy as np
import tensorflow as tf
from epp_model.model_yolov3 import yolo_body
from epp_model.detection import detection
from epp_model.utils import letterbox_image, draw_detection

# Clases detectadas (ajústalas según tu modelo)
CLASS_NAMES = ["helmet", "vest", "no_helmet", "no_vest"]

# Anclas y tamaño de entrada
ANCHORS = np.array([
    [[10,13], [16,30], [33,23]],
    [[30,61], [62,45], [59,119]],
    [[116,90], [156,198], [373,326]]
])
INPUT_SHAPE = (416, 416)

# Cargar modelo YOLOv3 entrenado
def load_epp_model(weights_path="epp_model/weights/epp_weights.h5"):
    image_input = tf.keras.layers.Input(shape=(*INPUT_SHAPE, 3))
    model = yolo_body(image_input, num_out_filters=(3 * (5 + len(CLASS_NAMES))))
    model.load_weights(weights_path)
    return model

# Detectar EPP en una imagen
def detect_epp(model, frame):
    image_data = letterbox_image(frame, INPUT_SHAPE)
    image_data = np.expand_dims(image_data / 255., 0)

    preds = model.predict(image_data)
    boxes = detection(preds, ANCHORS, len(CLASS_NAMES), frame.shape[:2], INPUT_SHAPE)
    boxes = boxes[0].numpy() if hasattr(boxes[0], "numpy") else boxes[0]

    output_frame = draw_detection(frame.copy(), boxes, CLASS_NAMES)

    # Verificar si la persona tiene EPP correcto
    epp_ok = any(CLASS_NAMES[int(b[-1])] in ["helmet", "vest"] for b in boxes)
    return epp_ok, output_frame
