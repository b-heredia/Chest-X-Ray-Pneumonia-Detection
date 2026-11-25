import warnings
warnings.filterwarnings("ignore")

import numpy as np
from keras.models import load_model
from keras.preprocessing import image
from win32com.client import Dispatch
import os

print("Loading model... please wait 10-20 seconds")
model = load_model('chest_xray.h5')
print("Model loaded!\n")

def speak(text):
    try:
        speaker = Dispatch("SAPI.SpVoice")
        speaker.Speak(text)
    except:
        pass

while True:
    print("\n" + "="*50)
    print("Chest X-Ray Pneumonia Detection Demo")
    print("="*50)
    
    path = input("\nDrag & drop an image here (or type the full path) and press Enter:\n→ ").strip().strip('"')
    
    if not path:
        continue
        
    if not os.path.exists(path):
        print("❌ File not found. Try again.")
        continue

    try:
        print("\nProcessing image... please wait...")
        img = image.load_img(path, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = x / 255.0  # must match training (rescale=1./255)

        pred = model.predict(x, verbose=0)
        score = pred[0][0]

        print(f"\nPrediction score: {score:.4f}")

        if score > 0.5:
            result = "Result is Normal"
        else:
            result = "Affected By PNEUMONIA"

        print("\n" + "*"*40)
        print(f"  {result}")
        print("*"*40)

        speak(result)

    except Exception as e:
        print("Error:", e)

    again = input("\nTest another image? (y/n): ").lower()
    if again != 'y':
        break

print("\nDemo finished. Thank you!")