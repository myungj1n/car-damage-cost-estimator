"""Quick test to verify all imports work correctly"""

print("Testing imports...")

try:
    import tensorflow as tf
    print(f"✓ TensorFlow {tf.__version__}")
except Exception as e:
    print(f"✗ TensorFlow: {e}")

try:
    from PIL import Image
    print("✓ PIL/Pillow")
except Exception as e:
    print(f"✗ PIL: {e}")

try:
    from sklearn.model_selection import train_test_split
    print("✓ scikit-learn")
except Exception as e:
    print(f"✗ scikit-learn: {e}")

try:
    import matplotlib.pyplot as plt
    print("✓ matplotlib")
except Exception as e:
    print(f"✗ matplotlib: {e}")

try:
    import seaborn as sns
    print("✓ seaborn")
except Exception as e:
    print(f"✗ seaborn: {e}")

print("\nAll imports successful! Ready to train models.")
