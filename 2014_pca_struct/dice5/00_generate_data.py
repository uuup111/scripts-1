# -*- coding: utf-8 -*-
"""
Created on Tue Mar 18 10:57:39 2014

@author:  edouard.duchesnay@cea.fr
@license: BSD-3-Clause

Generate all the data to be used.

After generation, we enter data and compute the l1_max value. As we use
centered data, the value is always the same (approximatively
sqrt(N_SAMPLES)/N_SAMPLES).

"""

import os
import numpy as np

from sklearn.preprocessing import StandardScaler

from parsimony.datasets.regression import dice5

import pca_tv

import dice5_data

################
# Input/Output #
################

OUTPUT_BASE_DIR = "/neurospin/brainomics/2014_pca_struct/dice5/data"

OUTPUT_DIR_FORMAT = os.path.join(OUTPUT_BASE_DIR, "data_{s[0]}_{s[1]}_{snr}")
OUTPUT_DATASET_FILE = "data.npy"
OUTPUT_STD_DATASET_FILE = "data.std.npy"
OUTPUT_BETA_FILE = "beta3d.std.npy"
OUTPUT_OBJECT_MASK_FILE_FORMAT = "mask_{i}.npy"
OUTPUT_MASK_FILE = "mask.npy"
OUTPUT_L1MASK_FILE = "l1_max.txt"

##############
# Parameters #
##############

# All SNR values
SNRS = dice5_data.ALL_SNRS

#############
# Functions #
#############

########
# Code #
########

# Generate data for all the SNR values
for snr in SNRS:
    model = dice5_data.create_model(snr)
    X3d, y, beta3d = dice5.load(n_samples=dice5_data.N_SAMPLES,
                                shape=dice5_data.SHAPE,
                                model=model,
                                random_seed=dice5_data.SEED)
    objects = dice5.dice_five_with_union_of_pairs(dice5_data.SHAPE)
    # Save data and scaled data
    output_dir = OUTPUT_DIR_FORMAT.format(s=dice5_data.SHAPE,
                                          snr=snr)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    X = X3d.reshape(dice5_data.N_SAMPLES, np.prod(dice5_data.SHAPE))
    full_filename = os.path.join(output_dir, OUTPUT_DATASET_FILE)
    np.save(full_filename, X)
    scaler = StandardScaler(with_mean=True, with_std=False)
    X_std = scaler.fit_transform(X)
    full_filename = os.path.join(output_dir, OUTPUT_STD_DATASET_FILE)
    np.save(full_filename, X_std)
    # Save beta
    full_filename = os.path.join(output_dir, OUTPUT_BETA_FILE)
    np.save(full_filename, beta3d)

    # Generate mask with the last objects since they have the same geometry
    # We only use union12, d3, union45
    _, _, d3, _, _, union12, union45, _ = objects
    sub_objects = [union12, union45, d3]
    full_mask = np.zeros(dice5_data.SHAPE, dtype=bool)
    for i, o in enumerate(sub_objects):
        mask = o.get_mask()
        full_mask += mask
        filename = OUTPUT_OBJECT_MASK_FILE_FORMAT.format(i=i)
        full_filename = os.path.join(output_dir, filename)
        np.save(full_filename, mask)
    full_filename = os.path.join(output_dir, OUTPUT_MASK_FILE)
    np.save(full_filename, full_mask)

    # Compute l1_max for this dataset
    l1_max = pca_tv.PCA_L1_L2_TV.l1_max(X_std)
    full_filename = os.path.join(output_dir, OUTPUT_L1MASK_FILE)
    with open(full_filename, "w") as f:
        print >> f, l1_max
