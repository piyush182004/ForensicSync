import tensorflow as tf
import numpy as np
from PIL import Image

class_names = ["A+", "A-", "AB+", "AB-", "B+", "B-", "O+", "O-"]

try:
    model = tf.keras.models.load_model('fingerprint_bloodgroup_classifier_attention.h5')
except Exception as e:
    model = None
    print(f"Warning: Could not load fingerprint model: {str(e)}")

def analyze_fingerprint(fingerprint_file):
    """Analyze fingerprint image to determine blood group."""
    if model is None:
        return "Fingerprint analysis unavailable: Model not loaded"
    
    try:
        img = Image.open(fingerprint_file).convert('RGB').resize((128, 128))
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)  # Shape: (1, 128, 128, 3)
        
        prediction = model.predict(img_array)
        class_idx = np.argmax(prediction)
        return class_names[class_idx]
    except Exception as e:
        return f"Error processing fingerprint: {str(e)}"