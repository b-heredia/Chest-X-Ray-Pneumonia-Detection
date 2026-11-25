# Chest X-Ray Pneumonia Detection

A desktop app that looks at a chest X-ray and predicts **NORMAL** or **PNEUMONIA**,
using a VGG16 transfer-learning model converted to TensorFlow Lite.

Upload or drag an X-ray into the window and get the result, a confidence score,
and a spoken answer in about a second.

> Student project for a tech expo. Not a medical diagnosis tool.

## Files

| File | What it does |
| --- | --- |
| `chest.py` | Main app: pop-up window, upload or drag and drop an X-ray |
| `fast_demo.py` | Terminal version using the fast TFLite model |
| `demo.py` | Terminal version using the original `.h5` Keras model |
| `train_model.py` | Trains the VGG16 model and saves `chest_xray.h5` |
| `convert_model.py` | Converts `chest_xray.h5` to `chest_xray.tflite` |

## Setup (Windows)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Get the model

The trained model is too big for the repo (about 59 MB). Download `chest_xray.tflite`
from this repo's **Releases** page and put it in the same folder as `chest.py`.

Or train your own: download the
[Chest X-Ray Images (Pneumonia) dataset](https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia),
put it in `datasets/` (with `train/` and `test/` folders), then run:

```
python train_model.py
python convert_model.py
```

## Run

```
python chest.py
```

## Results

On 20 test X-rays (10 normal, 10 pneumonia) the model got 19 right (95%).

## Built with

Python, TensorFlow / Keras, TensorFlow Lite, NumPy, Pillow, PyQt5
