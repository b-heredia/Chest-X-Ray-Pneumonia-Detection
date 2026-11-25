import tensorflow as tf

print("Converting model to faster format...")

# Load the original model
model = tf.keras.models.load_model('chest_xray.h5')

# Convert to TensorFlow Lite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

# Save the new fast model
with open('chest_xray.tflite', 'wb') as f:
    f.write(tflite_model)

print("✅ Done! Fast model saved as chest_xray.tflite")