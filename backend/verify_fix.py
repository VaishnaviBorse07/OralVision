import sys, os
sys.path.insert(0, r'E:\OralVision\backend')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import numpy as np

# Clear any cached model
from app.ai import local_predictor
local_predictor._load_model.cache_clear()

IMG_SIZE = (224, 224)

def test_image(img_path, label, age=50, tobacco="Gutka"):
    with open(img_path, 'rb') as f:
        image_bytes = f.read()
    result = local_predictor.predict_local(image_bytes, age=age, tobacco_type=tobacco)
    if result:
        print(f"  [{label}] raw={result['raw_score']:.3f} cancer={result['cancer_score']:.3f} "
              f"composite={result['composite_score']:.3f} => {result['risk_level']} "
              f"(conf={result['confidence_score']:.3f})")
    else:
        print(f"  [{label}] FAILED")

print("=== CANCER IMAGES (expect High/Medium) ===")
cancer_imgs = [
    (r'E:\OralVision\backend\dataset\Oral Cancer photos\S1.jpg', 'S1'),
    (r'E:\OralVision\backend\dataset\Oral Cancer photos\S2.jpg', 'S2'),
    (r'E:\OralVision\backend\dataset\Oral Cancer photos\oralcancer1.png', 'oralcancer1'),
]
for p, name in cancer_imgs:
    if os.path.exists(p):
        test_image(p, f'CANCER {name}', age=55, tobacco='Gutka')

print("\n=== NORMAL IMAGES (expect Low) ===")
normal_imgs = [
    (r'E:\OralVision\backend\dataset\normal\S BORMAL 3.png', 'S_NORMAL_3'),
    (r'E:\OralVision\backend\dataset\normal\1366.fig.1.png', '1366'),
]
for p, name in normal_imgs:
    if os.path.exists(p):
        test_image(p, f'NORMAL {name}', age=25, tobacco='None')

print("\n=== HEURISTIC ONLY (no image) ===")
from app.ai.predictor import _heuristic_score
cases = [(60,'Gutka'),(45,'Gutka'),(50,'Bidi'),(30,'None'),(25,'None')]
for age, tob in cases:
    r = _heuristic_score(age, tob)
    print(f"  Age={age} Tobacco={tob:12} -> {r['risk_level']:6} score={r['confidence_score']:.3f}")

print("\nDone.")
