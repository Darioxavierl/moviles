#!/usr/bin/env python3
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf

print("TensorFlow version:", tf.__version__)

# Test con full_matrices=False
H_complex = tf.constant([[1.0+0.1j, 2.0+0.2j], [3.0+0.3j, 4.0+0.4j]], dtype=tf.complex64)

print("\nWith full_matrices=False:")
U, S, Vh = tf.linalg.svd(H_complex, full_matrices=False)
print(f"  U.shape={U.shape}, S.shape={S.shape}, S.dtype={S.dtype}, Vh.shape={Vh.shape}")
print(f"  S = {S.numpy()}")

print("\nWith full_matrices=True:")
U, S, Vh = tf.linalg.svd(H_complex, full_matrices=True)
print(f"  U.shape={U.shape}, S.shape={S.shape}, S.dtype={S.dtype}, Vh.shape={Vh.shape}")
print(f"  S = {S.numpy()}")
