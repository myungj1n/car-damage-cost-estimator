"""
Model 1: Car Part Identification
Multi-label classification for 21 car part classes
Transfer learning with ResNet50
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TF warnings

import json
import numpy as np
from pathlib import Path
from PIL import Image
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration
CONFIG = {
    'dataset_root': Path.home() / ".cache/kagglehub/datasets/humansintheloop/car-parts-and-car-damages/versions/2",
    'img_dir': 'Car damages dataset/File1/img',
    'ann_dir': 'Car damages dataset/File1/ann',
    'img_size': (224, 224),
    'batch_size': 16,
    'epochs': 30,
    'learning_rate': 0.001,
    'test_size': 0.15,
    'val_size': 0.15,
    'seed': 42
}

# Model save path
MODEL_DIR = Path('models')
MODEL_DIR.mkdir(exist_ok=True)

print("="*70)
print("MODEL 1: CAR PART IDENTIFICATION")
print("="*70)

# ============================================================
# 1. DATA LOADING
# ============================================================

def load_dataset():
    """Load images and multi-label annotations"""
    print("\n[1/6] Loading dataset...")
    
    img_dir = CONFIG['dataset_root'] / CONFIG['img_dir']
    ann_dir = CONFIG['dataset_root'] / CONFIG['ann_dir']
    
    image_paths = []
    labels_list = []
    
    for ann_file in sorted(ann_dir.glob("*.json")):
        # Load annotation
        with open(ann_file, 'r') as f:
            data = json.load(f)
        
        # Get image path
        img_name = ann_file.stem  # Remove .json extension
        img_path = img_dir / img_name
        
        # Check if image exists (might be .png or .jpg)
        if not img_path.exists():
            # Try with .png extension
            img_path = img_dir / (img_name + '.png') if not img_name.endswith(('.png', '.jpg')) else img_path
            if not img_path.exists():
                # Try with .jpg
                img_path = img_dir / (img_name.replace('.png', '.jpg') if '.png' in img_name else img_name + '.jpg')
        
        if img_path.exists():
            # Extract all class labels from objects
            labels = list(set([obj['classTitle'] for obj in data['objects']]))
            
            image_paths.append(str(img_path))
            labels_list.append(labels)
    
    print(f"  ✓ Loaded {len(image_paths)} images")
    return image_paths, labels_list


# ============================================================
# 2. DATA PREPROCESSING
# ============================================================

def prepare_data(image_paths, labels_list):
    """Encode labels and split dataset"""
    print("\n[2/6] Preparing data...")
    
    # Convert labels to multi-hot encoding
    mlb = MultiLabelBinarizer()
    y = mlb.fit_transform(labels_list)
    
    classes = mlb.classes_
    print(f"  ✓ Found {len(classes)} classes")
    print(f"  ✓ Label encoding shape: {y.shape}")
    
    # Split dataset: 70% train, 15% val, 15% test
    X_train, X_temp, y_train, y_temp = train_test_split(
        image_paths, y, 
        test_size=(CONFIG['test_size'] + CONFIG['val_size']),
        random_state=CONFIG['seed'],
        stratify=None  # Multi-label stratification is complex, skip for now
    )
    
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp,
        test_size=0.5,  # Split the remaining 30% equally
        random_state=CONFIG['seed']
    )
    
    print(f"  ✓ Training:   {len(X_train)} images")
    print(f"  ✓ Validation: {len(X_val)} images")
    print(f"  ✓ Testing:    {len(X_test)} images")
    
    return (X_train, y_train), (X_val, y_val), (X_test, y_test), mlb, classes


# ============================================================
# 3. DATA GENERATORS
# ============================================================

def create_dataset(image_paths, labels, augment=False):
    """Create TF dataset with augmentation"""
    
    def load_and_preprocess_image(img_path, label):
        # Load image
        img = tf.io.read_file(img_path)
        img = tf.image.decode_image(img, channels=3, expand_animations=False)
        img = tf.image.resize(img, CONFIG['img_size'])
        
        # Data augmentation for training
        if augment:
            img = tf.image.random_flip_left_right(img)
            img = tf.image.random_brightness(img, 0.2)
            img = tf.image.random_contrast(img, 0.8, 1.2)
            img = tf.image.random_saturation(img, 0.8, 1.2)
        
        # Normalize to [0, 1]
        img = img / 255.0
        
        return img, label
    
    # Create dataset
    dataset = tf.data.Dataset.from_tensor_slices((image_paths, labels))
    dataset = dataset.map(load_and_preprocess_image, num_parallel_calls=tf.data.AUTOTUNE)
    dataset = dataset.batch(CONFIG['batch_size'])
    dataset = dataset.prefetch(tf.data.AUTOTUNE)
    
    return dataset


# ============================================================
# 4. MODEL ARCHITECTURE
# ============================================================

def build_model(num_classes):
    """Build ResNet50-based multi-label classifier"""
    print("\n[3/6] Building model...")
    
    # Base model: ResNet50 pretrained on ImageNet
    base_model = keras.applications.ResNet50(
        weights='imagenet',
        include_top=False,
        input_shape=(*CONFIG['img_size'], 3)
    )
    
    # Freeze base model initially
    base_model.trainable = False
    
    # Build complete model
    inputs = layers.Input(shape=(*CONFIG['img_size'], 3))
    
    # Preprocessing for ResNet50
    x = keras.applications.resnet50.preprocess_input(inputs)
    
    # Base model
    x = base_model(x, training=False)
    
    # Classification head
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.5)(x)
    x = layers.Dense(128, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    
    # Multi-label output (sigmoid for each class)
    outputs = layers.Dense(num_classes, activation='sigmoid')(x)
    
    model = keras.Model(inputs=inputs, outputs=outputs, name='part_identification_model')
    
    print(f"  ✓ Model built with {num_classes} output classes")
    print(f"  ✓ Trainable parameters: {model.count_params():,}")
    
    return model, base_model


# ============================================================
# 5. TRAINING
# ============================================================

def train_model(model, base_model, train_ds, val_ds, num_classes):
    """Two-stage training: frozen base → fine-tuning"""
    print("\n[4/6] Training model...")
    
    # Compile model (binary cross-entropy for multi-label)
    model.compile(
        optimizer=keras.optimizers.Adam(CONFIG['learning_rate']),
        loss='binary_crossentropy',
        metrics=[
            'binary_accuracy',
            keras.metrics.AUC(name='auc', multi_label=True),
            keras.metrics.Precision(name='precision'),
            keras.metrics.Recall(name='recall')
        ]
    )
    
    # Callbacks
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True,
            verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=3,
            verbose=1,
            min_lr=1e-7
        ),
        keras.callbacks.ModelCheckpoint(
            MODEL_DIR / 'part_model_best.keras',
            monitor='val_auc',
            mode='max',
            save_best_only=True,
            verbose=1
        )
    ]
    
    print("\n  Stage 1: Training with frozen base model...")
    history1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=10,
        callbacks=callbacks,
        verbose=1
    )
    
    # Stage 2: Fine-tuning
    print("\n  Stage 2: Fine-tuning last layers...")
    base_model.trainable = True
    
    # Freeze all layers except last 30
    for layer in base_model.layers[:-30]:
        layer.trainable = False
    
    # Recompile with lower learning rate
    model.compile(
        optimizer=keras.optimizers.Adam(CONFIG['learning_rate'] * 0.1),
        loss='binary_crossentropy',
        metrics=[
            'binary_accuracy',
            keras.metrics.AUC(name='auc', multi_label=True),
            keras.metrics.Precision(name='precision'),
            keras.metrics.Recall(name='recall')
        ]
    )
    
    history2 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=20,
        callbacks=callbacks,
        verbose=1
    )
    
    # Combine histories
    history = {
        key: history1.history[key] + history2.history[key]
        for key in history1.history.keys()
    }
    
    return history


# ============================================================
# 6. EVALUATION
# ============================================================

def evaluate_model(model, test_ds, mlb, classes):
    """Evaluate model on test set"""
    print("\n[5/6] Evaluating model...")
    
    # Evaluate
    results = model.evaluate(test_ds, verbose=1)
    
    print(f"\n  Test Results:")
    print(f"  ✓ Loss:           {results[0]:.4f}")
    print(f"  ✓ Binary Accuracy: {results[1]:.4f}")
    print(f"  ✓ AUC:            {results[2]:.4f}")
    print(f"  ✓ Precision:      {results[3]:.4f}")
    print(f"  ✓ Recall:         {results[4]:.4f}")
    
    # Calculate F1 score
    f1 = 2 * (results[3] * results[4]) / (results[3] + results[4] + 1e-7)
    print(f"  ✓ F1-Score:       {f1:.4f}")
    
    return results


# ============================================================
# 7. VISUALIZATION
# ============================================================

def plot_training_history(history):
    """Plot training curves"""
    print("\n[6/6] Plotting training history...")
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Model 1: Part Identification Training History', fontsize=14, fontweight='bold')
    
    # Loss
    axes[0, 0].plot(history['loss'], label='Training')
    axes[0, 0].plot(history['val_loss'], label='Validation')
    axes[0, 0].set_title('Loss')
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Binary Cross-Entropy')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Accuracy
    axes[0, 1].plot(history['binary_accuracy'], label='Training')
    axes[0, 1].plot(history['val_binary_accuracy'], label='Validation')
    axes[0, 1].set_title('Accuracy')
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('Binary Accuracy')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # AUC
    axes[1, 0].plot(history['auc'], label='Training')
    axes[1, 0].plot(history['val_auc'], label='Validation')
    axes[1, 0].set_title('AUC-ROC')
    axes[1, 0].set_xlabel('Epoch')
    axes[1, 0].set_ylabel('AUC')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Precision & Recall
    axes[1, 1].plot(history['precision'], label='Precision (Train)')
    axes[1, 1].plot(history['val_precision'], label='Precision (Val)')
    axes[1, 1].plot(history['recall'], label='Recall (Train)')
    axes[1, 1].plot(history['val_recall'], label='Recall (Val)')
    axes[1, 1].set_title('Precision & Recall')
    axes[1, 1].set_xlabel('Epoch')
    axes[1, 1].set_ylabel('Score')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(MODEL_DIR / 'part_model_training_history.png', dpi=150, bbox_inches='tight')
    print(f"  ✓ Saved training plot to {MODEL_DIR / 'part_model_training_history.png'}")


# ============================================================
# MAIN TRAINING PIPELINE
# ============================================================

if __name__ == "__main__":
    # Set random seeds
    np.random.seed(CONFIG['seed'])
    tf.random.set_seed(CONFIG['seed'])
    
    # Load data
    image_paths, labels_list = load_dataset()
    
    # Prepare data
    (X_train, y_train), (X_val, y_val), (X_test, y_test), mlb, classes = prepare_data(image_paths, labels_list)
    
    # Create datasets
    print("\n  Creating TF datasets...")
    train_ds = create_dataset(X_train, y_train, augment=True)
    val_ds = create_dataset(X_val, y_val, augment=False)
    test_ds = create_dataset(X_test, y_test, augment=False)
    
    # Build model
    model, base_model = build_model(len(classes))
    
    # Train model
    history = train_model(model, base_model, train_ds, val_ds, len(classes))
    
    # Evaluate
    evaluate_model(model, test_ds, mlb, classes)
    
    # Save final model
    model.save(MODEL_DIR / 'part_identification_model_final.keras')
    print(f"\n✓ Model saved to {MODEL_DIR / 'part_identification_model_final.keras'}")
    
    # Save label encoder
    import pickle
    with open(MODEL_DIR / 'part_mlb.pkl', 'wb') as f:
        pickle.dump(mlb, f)
    print(f"✓ Label encoder saved to {MODEL_DIR / 'part_mlb.pkl'}")
    
    # Plot history
    plot_training_history(history)
    
    print("\n" + "="*70)
    print("✓ MODEL 1 TRAINING COMPLETE!")
    print("="*70)
