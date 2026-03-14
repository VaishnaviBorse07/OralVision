import sys, os
sys.path.insert(0, r'E:\OralVision\backend')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
import numpy as np
from PIL import Image

MODEL_PATH = r'E:\OralVision\backend\app\ai\oral_cancer_model.h5'
IMG_SIZE = (224, 224)

model = tf.keras.models.load_model(MODEL_PATH)
print('Model input shape:', model.input_shape)
print('Model output shape:', model.output_shape)
print('First 8 layers:', [l.name for l in model.layers[:8]])
print()

# Check if augmentation/preprocess is in the model
layer_names = [l.name for l in model.layers]
has_augment = any('augment' in n.lower() or 'random' in n.lower() for n in layer_names)
has_preprocess = any('preprocess' in n.lower() for n in layer_names)
has_densenet_preprocess = any('densenet' in n.lower() for n in layer_names)
print('Has augmentation layer:', has_augment)
print('Has preprocess in model:', has_preprocess or has_densenet_preprocess)
print()

def run_inference(img_path, description, preprocess_outside=False):
    try:
        img = Image.open(img_path).convert('RGB').resize(IMG_SIZE)
        arr = np.array(img, dtype=np.float32)
        if preprocess_outside:
            arr = tf.keras.applications.densenet.preprocess_input(arr)
        arr = np.expand_dims(arr, axis=0)
        scores = [float(model.predict(arr, verbose=0)[0][0]) for _ in range(5)]
        print(f'{description}:')
        print(f'  Scores: {[round(s,4) for s in scores]}')
        print(f'  Mean: {round(np.mean(scores),4)}  Std: {round(np.std(scores),4)}')
        return np.mean(scores)
    except Exception as e:
        print(f'ERROR for {description}: {e}')
        return None

print('=== CANCER IMAGES (expected high scores) ===')
cancer_imgs = [
    r'E:\OralVision\backend\dataset\Oral Cancer photos\S1.jpg',
    r'E:\OralVision\backend\dataset\Oral Cancer photos\S2.jpg',
    r'E:\OralVision\backend\dataset\Oral Cancer photos\oralcancer1.png',
]
for p in cancer_imgs:
    if os.path.exists(p):
        run_inference(p, f'CANCER[raw] {os.path.basename(p)}', preprocess_outside=False)
        run_inference(p, f'CANCER[dbl] {os.path.basename(p)}', preprocess_outside=True)
        print()

print('=== NORMAL IMAGES (expected low scores) ===')
normal_imgs = [
    r'E:\OralVision\backend\dataset\normal\1366.fig.1.png',
    r'E:\OralVision\backend\dataset\normal\S BORMAL 3.png',
]
for p in normal_imgs:
    if os.path.exists(p):
        run_inference(p, f'NORMAL[raw] {os.path.basename(p)}', preprocess_outside=False)
        print()

print('\nDone.')
