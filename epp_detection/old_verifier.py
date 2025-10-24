import os
import cv2
import numpy as np
import tensorflow as tf
from .yolo_model import yolo_body
from .yolo_detection import detection
from .draw_utils import letterbox_image, draw_detection
from .utils import load_class_names, default_anchors
from .gpu_fix import fix_tf_gpu

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "epp_model", "weights", "yolo_epp_weights.h5")
CLASSES_FILE = os.path.join(BASE_DIR, "epp_classes.txt")

# Config
INPUT_SIZE = (416, 416)
CLASS_NAMES = load_class_names(CLASSES_FILE)
ANCHORS = default_anchors

_model = None

def init_model():
    global _model
    if _model is not None:
        return _model
    try:
        fix_tf_gpu()
    except Exception:
        pass
    inputs = tf.keras.layers.Input(shape=(*INPUT_SIZE, 3))
    num_classes = len(CLASS_NAMES)
    num_anchors = sum(len(a) for a in ANCHORS)
    num_out_filters = (num_anchors // 3) * (5 + num_classes)
    _model = yolo_body(inputs, num_out_filters)
    _model.load_weights(MODEL_PATH)
    return _model

def verify_epp(frame, min_score=0.3):
    model = init_model()
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_letter = letterbox_image(img_rgb, INPUT_SIZE)
    img_norm = img_letter.astype(np.float32) / 255.0
    preds = model.predict(np.expand_dims(img_norm, 0))
    boxes_batch = detection(preds, ANCHORS, len(CLASS_NAMES), INPUT_SIZE, INPUT_SIZE, score_threshold=min_score)
    boxes = boxes_batch[0]
    results = []
    for b in boxes:
        x1, y1, x2, y2, score, label = b
        name = CLASS_NAMES[int(label)]
        results.append((name, float(score), (int(x1), int(y1), int(x2), int(y2))))
    return results

def draw_results(frame, results):
    boxes = []
    for (cls, score, (x1, y1, x2, y2)) in results:
        idx = CLASS_NAMES.index(cls)
        boxes.append(np.array([x1, y1, x2, y2, score, idx]))
    if boxes:
        frame = draw_detection(frame, np.array(boxes), CLASS_NAMES)
    return frame
