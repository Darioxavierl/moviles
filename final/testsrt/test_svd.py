#!/usr/bin/env python3
"""
Debug para ver qué retorna tf.linalg.svd realmente
"""
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf
import numpy as np

# Test 1: SVD con matriz float
print("TEST 1: SVD with float matrix")
H_float = tf.constant([[1.0, 2.0], [3.0, 4.0]], dtype=tf.float32)
U, S, Vh = tf.linalg.svd(H_float)
print(f"  U.shape={U.shape}, S.shape={S.shape}, S.dtype={S.dtype}, Vh.shape={Vh.shape}")
print(f"  S = {S.numpy()}")

# Test 2: SVD con matriz complex
print("\nTEST 2: SVD with complex matrix")
H_complex = tf.constant([[1.0+0.1j, 2.0+0.2j], [3.0+0.3j, 4.0+0.4j]], dtype=tf.complex64)
U, S, Vh = tf.linalg.svd(H_complex)
print(f"  U.shape={U.shape}, S.shape={S.shape}, S.dtype={S.dtype}, Vh.shape={Vh.shape}")
print(f"  S = {S.numpy()}")

# Test 3: SVD con 1x1
print("\nTEST 3: SVD with 1x1 matrix")
H_1x1 = tf.constant([[1.5+0.5j]], dtype=tf.complex64)
U, S, Vh = tf.linalg.svd(H_1x1)
print(f"  U.shape={U.shape}, S.shape={S.shape}, S.dtype={S.dtype}, Vh.shape={Vh.shape}")
print(f"  S = {S.numpy()}")

# Test 4: SVD con 2x1
print("\nTEST 4: SVD with 2x1 matrix")
H_2x1 = tf.constant([[1.0+0.1j], [2.0+0.2j]], dtype=tf.complex64)
U, S, Vh = tf.linalg.svd(H_2x1)
print(f"  U.shape={U.shape}, S.shape={S.shape}, S.dtype={S.dtype}, Vh.shape={Vh.shape}")
print(f"  S = {S.numpy()}")
