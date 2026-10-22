from typing import Tuple
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array

class ModelHandler:
    def __init__(self, model_path: str, input_shape: Tuple[int, int]):
        self.model = load_model(model_path)
        self.input_shape = input_shape
        self.classes = ['tall-intern', 'meter', 'no-meter']
        self.class_to_id = {
            'tall-intern': 1,  # alto-interno
            'meter': 2,        # legible
            'no-meter': 3      # sin-medidor
        }

    def preprocess_image(self, image_path: str) -> np.ndarray:
        img = load_img(image_path, target_size=self.input_shape)
        img_array = img_to_array(img)
        img_array = img_array / 255.0
        return np.expand_dims(img_array, axis=0)

    def classify_image(self, image_path: str) -> Tuple[int, float]:
        preprocessed_img = self.preprocess_image(image_path)
        predictions = self.model.predict(preprocessed_img, verbose=0)
        class_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][class_idx])
        class_name = self.classes[class_idx]
        return self.class_to_id[class_name], confidence * 100