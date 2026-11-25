import os
from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Paths - adjust if needed
train_dir = 'datasets/train'
test_dir = 'datasets/test'

# Check if folders exist
print("Train folder exists:", os.path.exists(train_dir))
print("Test folder exists:", os.path.exists(test_dir))

# Create model
vgg = VGG16(input_shape=(224, 224, 3), weights='imagenet', include_top=False)

for layer in vgg.layers:
    layer.trainable = False

x = Flatten()(vgg.output)
prediction = Dense(2, activation='softmax')(x)
model = Model(inputs=vgg.input, outputs=prediction)

model.compile(
    loss='categorical_crossentropy',
    optimizer='adam',
    metrics=['accuracy']
)

# Data generators
train_datagen = ImageDataGenerator(
    rescale=1./255,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True
)

test_datagen = ImageDataGenerator(rescale=1./255)

training_set = train_datagen.flow_from_directory(
    train_dir,
    target_size=(224, 224),
    batch_size=16,
    class_mode='categorical'
)

test_set = test_datagen.flow_from_directory(
    test_dir,
    target_size=(224, 224),
    batch_size=16,
    class_mode='categorical'
)

print("Starting training... This may take 20-60 minutes depending on your computer.")

# Train for a few epochs (increase if you have time)
model.fit(
    training_set,
    validation_data=test_set,
    epochs=3,                    # You can change to 5 if you have more time
    steps_per_epoch=len(training_set),
    validation_steps=len(test_set)
)

# Save the model
model.save('chest_xray.h5')
print("\n✅ Model saved successfully as chest_xray.h5")