#!/usr/bin/env python3
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf
import numpy as np

H_complex = np.array([[1.0+0.1j, 2.0+0.2j], [3.0+0.3j, 4.0+0.4j]], dtype=np.complex64)

print("Using NumPy SVD:")
U_np, S_np, Vh_np = np.linalg.svd(H_complex, full_matrices=False)
print(f"  U.shape={U_np.shape}, S.shape={S_np.shape}, S.dtype={S_np.dtype}, Vh.shape={Vh_np.shape}")
print(f"  S = {S_np}")

print("\nUsing TensorFlow SVD on TF tensor:")
H_tf = tf.constant(H_complex, dtype=tf.complex64)
U_tf, S_tf, Vh_tf = tf.linalg.svd(H_tf, full_matrices=False)
print(f"  U.shape={U_tf.shape}, S.shape={S_tf.shape}, S.dtype={S_tf.dtype}, Vh.shape={Vh_tf.shape}")
print(f"  S = {S_tf.numpy()}")

print("\nUsing tf.raw_ops.Svd:")
import tensorflow as tf
try:
    U_raw, S_raw, Vh_raw = tf.raw_ops.Svd(input=H_tf, full_matrices=False, compute_uv=True)
    print(f"  U.shape={U_raw.shape}, S.shape={S_raw.shape}, Vh.shape={Vh_raw.shape}")
except Exception as e:
    print(f"  Error: {e}")
