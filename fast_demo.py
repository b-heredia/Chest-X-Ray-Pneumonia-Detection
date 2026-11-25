import warnings
warnings.filterwarnings("ignore")

import numpy as np
import tensorflow as tf
from keras.preprocessing import image
from win32com.client import Dispatch
import os

print("Loading fast model...")
interpreter = tf.lite.Interpreter(model_path="chest_xray.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
print("Model loaded successfully!\n")

def speak(text):
    try:
        speaker = Dispatch("SAPI.SpVoice")
        speaker.Speak(text)
    except:
        pass

while True:
    print("="*50)
    print("Chest X-Ray Pneumonia Detection (Fast Demo)")
    print("="*50)
    
    path = input("\nDrag & drop an image here and press Enter:\n→ ").strip().strip('"')
    
    if not path:
        continue
        
    if not os.path.exists(path):
        print("❌ File not found. Try again.\n")
        continue

    try:
        print("\nProcessing image...")
        
        img = image.load_img(path, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = (x / 255.0).astype(np.float32)  # must match training (rescale=1./255)

        interpreter.set_tensor(input_details[0]['index'], x)
        interpreter.invoke()
        
        pred = interpreter.get_tensor(output_details[0]['index'])
        score = pred[0][0]

        print(f"Prediction score: {score:.4f}")

        if score > 0.5:
            result = "Result is Normal"
        else:
            result = "Affected By PNEUMONIA"

        print("\n" + "*"*40)
        print(f"  → {result}")
        print("*"*40 + "\n")

        speak(result)

    except Exception as e:
        print("Error:", e)

    again = input("Test another image? (y/n): ").lower()
    if again != 'y':
        break

print("\nDemo finished!")