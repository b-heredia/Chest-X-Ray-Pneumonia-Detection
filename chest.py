"""
Chest X-Ray Pneumonia Detection - Expo App
Pop-up window: upload (or drag & drop) an X-ray -> shows NORMAL / PNEUMONIA.

Why this doesn't freeze (the old chest_xray.py did):
  * The model is loaded ONCE at startup, not on every button click.
  * It uses the fast .tflite model (same one fast_demo.py uses).
  * Model loading, prediction and the voice all run in background threads,
    so the window stays responsive the whole time.
"""
import os
import sys
import threading
import warnings

warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import numpy as np
from PIL import Image

# IMPORTANT (Windows): TensorFlow must be imported BEFORE PyQt5,
# otherwise you get "DLL load failed ... _pywrap_tensorflow_internal".
import tensorflow as tf

from PyQt5 import QtCore, QtGui, QtWidgets

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "chest_xray.tflite")
SPEAK_RESULTS = True  # set False to turn the voice off


# ---------------------------------------------------------------- helpers
def preprocess(path):
    """Must match training (train_model.py used rescale=1./255).
    Do NOT use vgg16.preprocess_input here - the model wasn't trained with it,
    and it makes almost every image come out as PNEUMONIA."""
    img = Image.open(path).convert("RGB").resize((224, 224), Image.NEAREST)
    x = np.asarray(img, dtype=np.float32) / 255.0
    return np.expand_dims(x, axis=0)


def speak(text):
    def _run():
        try:
            import pythoncom
            from win32com.client import Dispatch
            pythoncom.CoInitialize()
            Dispatch("SAPI.SpVoice").Speak(text)
        except Exception:
            pass
    if SPEAK_RESULTS:
        threading.Thread(target=_run, daemon=True).start()


# ---------------------------------------------------------------- workers
class ModelLoader(QtCore.QThread):
    done = QtCore.pyqtSignal(object, str)

    def run(self):
        try:
            interp = tf.lite.Interpreter(model_path=MODEL_PATH)
            interp.allocate_tensors()
            self.done.emit(interp, "")
        except Exception as e:
            self.done.emit(None, str(e))


class Predictor(QtCore.QThread):
    done = QtCore.pyqtSignal(float, str)

    def __init__(self, interp, lock, path):
        super().__init__()
        self.interp, self.lock, self.path = interp, lock, path

    def run(self):
        try:
            x = preprocess(self.path)
            with self.lock:
                inp = self.interp.get_input_details()[0]["index"]
                out = self.interp.get_output_details()[0]["index"]
                self.interp.set_tensor(inp, x)
                self.interp.invoke()
                score = float(self.interp.get_tensor(out)[0][0])
            self.done.emit(score, "")
        except Exception as e:
            self.done.emit(-1.0, str(e))


# ---------------------------------------------------------------- window
BTN_STYLE = """
QPushButton { border-radius: 12px; background-color: #DF582C; color: white;
              padding: 10px 24px; font-size: 15px; font-weight: bold; }
QPushButton:hover { background-color: #7D93E0; }
QPushButton:disabled { background-color: #557a88; color: #ccd; }
"""


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.interp = None
        self.lock = threading.Lock()
        self.worker = None

        self.setWindowTitle("Chest X-Ray Pneumonia Detection")
        self.resize(720, 760)
        self.setAcceptDrops(True)

        root = QtWidgets.QWidget()
        root.setStyleSheet("background-color: #035874; color: white;")
        self.setCentralWidget(root)
        lay = QtWidgets.QVBoxLayout(root)
        lay.setContentsMargins(30, 20, 30, 25)
        lay.setSpacing(14)

        title = QtWidgets.QLabel("Chest X-Ray Pneumonia Detection")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: bold;")
        lay.addWidget(title)

        self.preview = QtWidgets.QLabel()
        self.preview.setAlignment(QtCore.Qt.AlignCenter)
        self.preview.setMinimumSize(420, 420)
        self.preview.setStyleSheet(
            "border: 3px dashed #7fb3c4; border-radius: 14px; font-size: 16px;")
        gif_path = os.path.join(HERE, "picture.gif")
        if os.path.exists(gif_path):
            self.gif = QtGui.QMovie(gif_path)
            self.gif.setScaledSize(QtCore.QSize(400, 400))
            self.preview.setMovie(self.gif)
            self.gif.start()
        else:
            self.preview.setText("Drop an X-ray image here")
        lay.addWidget(self.preview, stretch=1)

        self.result = QtWidgets.QLabel("Loading model, one moment...")
        self.result.setAlignment(QtCore.Qt.AlignCenter)
        self.result.setWordWrap(True)
        self.result.setMinimumHeight(90)
        self.result.setStyleSheet("font-size: 18px; border-radius: 12px; padding: 10px;")
        lay.addWidget(self.result)

        self.button = QtWidgets.QPushButton("Upload X-Ray Image")
        self.button.setStyleSheet(BTN_STYLE)
        self.button.setCursor(QtCore.Qt.PointingHandCursor)
        self.button.setEnabled(False)
        self.button.clicked.connect(self.choose_file)
        lay.addWidget(self.button, alignment=QtCore.Qt.AlignCenter)

        note = QtWidgets.QLabel("Student demo project - not a medical diagnosis.")
        note.setAlignment(QtCore.Qt.AlignCenter)
        note.setStyleSheet("font-size: 11px; color: #b9d6df;")
        lay.addWidget(note)

        self.loader = ModelLoader()
        self.loader.done.connect(self.on_model_loaded)
        self.loader.start()

    # --- model ready
    def on_model_loaded(self, interp, err):
        if interp is None:
            self.set_result(f"Could not load model:\n{err}", "#8b1e1e")
            return
        self.interp = interp
        self.button.setEnabled(True)
        self.set_result("Ready! Click Upload or drag an X-ray onto this window.", None)

    # --- picking an image
    def choose_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choose a chest X-ray", HERE,
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All files (*)")
        if path:
            self.analyze(path)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        if urls:
            self.analyze(urls[0].toLocalFile())

    # --- prediction
    def analyze(self, path):
        if self.interp is None or (self.worker and self.worker.isRunning()):
            return
        pix = QtGui.QPixmap(path)
        if pix.isNull():
            self.set_result("That file isn't an image I can open. Try a .jpg or .png.", "#8b1e1e")
            return
        self.preview.setMovie(None)
        self.preview.setPixmap(pix.scaled(
            self.preview.width() - 20, self.preview.height() - 20,
            QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        self.button.setEnabled(False)
        self.set_result("Analyzing...", None)

        self.worker = Predictor(self.interp, self.lock, path)
        self.worker.done.connect(self.on_prediction)
        self.worker.start()

    def on_prediction(self, score, err):
        self.button.setEnabled(True)
        if err:
            self.set_result(f"Error: {err}", "#8b1e1e")
            return
        if score > 0.5:
            label, conf, color, voice = "NORMAL", score, "#1f8a4c", "Result is Normal"
        else:
            label, conf, color, voice = "PNEUMONIA", 1 - score, "#c0392b", "Affected by Pneumonia"
        self.set_result(
            f"<div style='font-size:36px; font-weight:bold;'>{label}</div>"
            f"<div style='font-size:16px;'>Confidence: {conf * 100:.1f}%</div>", color)
        speak(voice)

    def set_result(self, text, bg):
        self.result.setText(text)
        self.result.setStyleSheet(
            "font-size: 18px; border-radius: 12px; padding: 10px;"
            + (f"background-color: {bg};" if bg else ""))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
