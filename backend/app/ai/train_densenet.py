# backend/app/ai/train_densenet.py
"""
DenseNet121 Transfer Learning — Oral Cancer Binary Classifier
Stage 1: Train top layers only  (frozen base)
Stage 2: Fine-tune entire network with very low LR

Dataset layout expected:
  dataset/
    normal/               ← class 0
    Oral Cancer photos/   ← class 1
"""
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import DenseNet121
from tensorflow.keras.layers import (
    Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
)
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import (
    EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR   = os.path.join(BASE_DIR, "dataset")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "oral_cancer_model.h5")

# ── Hyper-parameters ──────────────────────────────────────────────────────────
BATCH_SIZE     = 16
IMG_SIZE       = (224, 224)
EPOCHS_STAGE1  = 25   # train top head only
EPOCHS_STAGE2  = 15   # fine-tune full network


# ── Data augmentation layer (applied only during training) ────────────────────
def _augmentation_layer():
    return tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal_and_vertical"),
        tf.keras.layers.RandomRotation(0.15),
        tf.keras.layers.RandomZoom(0.15),
        tf.keras.layers.RandomContrast(0.15),
        tf.keras.layers.RandomBrightness(0.10),
    ], name="augmentation")


def build_datasets():
    """Build train/val datasets with preprocessing."""
    common = dict(
        directory   = DATA_DIR,
        seed        = 42,
        image_size  = IMG_SIZE,
        batch_size  = BATCH_SIZE,
    )
    train_ds = tf.keras.utils.image_dataset_from_directory(
        validation_split=0.20, subset="training",  **common)
    val_ds   = tf.keras.utils.image_dataset_from_directory(
        validation_split=0.20, subset="validation", **common)

    class_names = train_ds.class_names
    print(f"Classes detected: {class_names}")

    # Figure out which class index is "Oral Cancer photos"
    cancer_idx = next(
        (i for i, n in enumerate(class_names)
         if "cancer" in n.lower() or "oral" in n.lower()), 1
    )
    normal_idx = 1 - cancer_idx
    print(f"  Cancer class index: {cancer_idx}, Normal class index: {normal_idx}")

    # Re-map labels so cancer=1, normal=0
    if cancer_idx != 1:
        def remap(x, y):
            return x, tf.cast(1 - y, tf.float32)
    else:
        def remap(x, y):
            return x, tf.cast(y, tf.float32)

    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = (train_ds
                .map(remap, num_parallel_calls=AUTOTUNE)
                .cache()
                .shuffle(buffer_size=500)
                .prefetch(AUTOTUNE))
    val_ds   = (val_ds
                .map(remap, num_parallel_calls=AUTOTUNE)
                .cache()
                .prefetch(AUTOTUNE))

    return train_ds, val_ds, cancer_idx


def build_model():
    """DenseNet121 + custom head with BatchNorm and Dropout."""
    base = DenseNet121(
        weights     = "imagenet",
        include_top = False,
        input_shape = IMG_SIZE + (3,),
    )
    base.trainable = False

    augment = _augmentation_layer()

    inputs = tf.keras.Input(shape=IMG_SIZE + (3,))
    x = augment(inputs)                                      # augment in graph
    x = tf.keras.applications.densenet.preprocess_input(x)  # DenseNet norm
    x = base(x, training=False)
    x = GlobalAveragePooling2D()(x)
    x = BatchNormalization()(x)
    x = Dropout(0.4)(x)
    x = Dense(256, activation="relu")(x)
    x = Dropout(0.3)(x)
    outputs = Dense(1, activation="sigmoid")(x)

    model = Model(inputs, outputs, name="oral_cancer_densenet")
    return model, base


def _compute_class_weights(train_ds):
    """Compute class weights for imbalanced dataset."""
    labels = []
    for _, y in train_ds.unbatch().take(10000):
        labels.append(int(y.numpy()))
    labels = np.array(labels)
    n_normal = np.sum(labels == 0)
    n_cancer = np.sum(labels == 1)
    n_total  = len(labels)
    w_normal = n_total / (2.0 * n_normal) if n_normal else 1.0
    w_cancer = n_total / (2.0 * n_cancer) if n_cancer else 1.0
    print(f"Class weights — Normal: {w_normal:.3f}, Cancer: {w_cancer:.3f}")
    return {0: w_normal, 1: w_cancer}


def train():
    print("=" * 60)
    print("OralVision — DenseNet121 Training Pipeline")
    print("=" * 60)

    train_ds, val_ds, _ = build_datasets()
    model, base          = build_model()
    class_weights        = _compute_class_weights(train_ds)

    # ── Stage 1: Train head only ─────────────────────────────────────────────
    print("\n[Stage 1] Training classification head (base frozen)...")
    model.compile(
        optimizer = tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss      = "binary_crossentropy",
        metrics   = ["accuracy", tf.keras.metrics.AUC(name="auc")],
    )
    callbacks_s1 = [
        EarlyStopping(monitor="val_auc", patience=6, restore_best_weights=True,
                      mode="max", verbose=1),
        ReduceLROnPlateau(monitor="val_loss", factor=0.4, patience=3,
                          min_lr=1e-6, verbose=1),
        ModelCheckpoint(MODEL_PATH, monitor="val_auc", save_best_only=True,
                        mode="max", verbose=1),
    ]
    model.fit(
        train_ds, validation_data=val_ds,
        epochs=EPOCHS_STAGE1,
        class_weight=class_weights,
        callbacks=callbacks_s1,
    )

    # ── Stage 2: Fine-tune whole network ─────────────────────────────────────
    print("\n[Stage 2] Fine-tuning full DenseNet121 (very low LR)...")
    base.trainable = True
    # Freeze first 100 layers (early feature extractors — don't overfit)
    for layer in base.layers[:100]:
        layer.trainable = False

    model.compile(
        optimizer = tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss      = "binary_crossentropy",
        metrics   = ["accuracy", tf.keras.metrics.AUC(name="auc")],
    )
    callbacks_s2 = [
        EarlyStopping(monitor="val_auc", patience=5, restore_best_weights=True,
                      mode="max", verbose=1),
        ReduceLROnPlateau(monitor="val_loss", factor=0.3, patience=3,
                          min_lr=1e-7, verbose=1),
        ModelCheckpoint(MODEL_PATH, monitor="val_auc", save_best_only=True,
                        mode="max", verbose=1),
    ]
    model.fit(
        train_ds, validation_data=val_ds,
        epochs=EPOCHS_STAGE2,
        class_weight=class_weights,
        callbacks=callbacks_s2,
    )

    # ── Final evaluation ──────────────────────────────────────────────────────
    print("\n[Evaluation] Final metrics on validation set:")
    loss, acc, auc = model.evaluate(val_ds, verbose=1)
    print(f"  Val Loss: {loss:.4f}  |  Val Accuracy: {acc:.4f}  |  Val AUC: {auc:.4f}")
    print(f"\nModel saved → {MODEL_PATH}")
    print("✅ Training complete!")


if __name__ == "__main__":
    train()