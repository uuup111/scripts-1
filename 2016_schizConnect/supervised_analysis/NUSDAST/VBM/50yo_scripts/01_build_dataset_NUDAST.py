#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 21 17:20:32 2017


5@author: ad24740

Compute mask, concatenate masked non-smoothed images for all the subjects.
Build X, y, and mask

INPUT:
- subject_list.txt:
- population.csv

OUTPUT_ICAARZ:
- mask.nii
- y.npy
- X.npy = intercept + Age + Gender + Voxel
"""

import os
import numpy as np
import glob
import pandas as pd
import nibabel
import brainomics.image_atlas
import shutil
import mulm
import sklearn


BASE_PATH = '/neurospin/brainomics/2016_schizConnect/analysis/NUSDAST/VBM'
INPUT_CSV= os.path.join(BASE_PATH,"population_50yo.csv")
OUTPUT = os.path.join(BASE_PATH,"data/data_50yo")
penalty_start = 2


# Read pop csv
pop = pd.read_csv(INPUT_CSV)
[[lab, np.sum(pop["dx_num"] == lab)] for lab in pop["dx_num"].unique()]
# [[1, 97], [0, 139]]
pop.shape
# (236, 9)
#############################################################################
# Read images
n = len(pop)
assert n == 236
Z = np.zeros((n, penalty_start)) # Age + Gender
Z[:, 0] = 1 # Intercept
y = np.zeros((n, 1)) # DX
images = list()
for i, index in enumerate(pop.index):
    cur = pop[pop.index== index]
    print(cur)
    imagefile_name = cur.path_VBM
    babel_image = nibabel.load(imagefile_name.as_matrix()[0])
    images.append(babel_image.get_data().ravel())
    Z[i, :] = np.asarray(cur[["age", "sex_num"]]).ravel()
    y[i, 0] = cur["dx_num"]

shape = babel_image.get_data().shape



#############################################################################
# Compute mask
# Implicit Masking involves assuming that a lower than a givent threshold
# at some voxel, in any of the images, indicates an unknown and is
# excluded from the analysis.
Xtot = np.vstack(images)
mask = (np.min(Xtot, axis=0) > 0.01) & (np.std(Xtot, axis=0) > 1e-6)
mask = mask.reshape(shape)
assert mask.sum() == 282263

#############################################################################
# Compute atlas mask
babel_mask_atlas = brainomics.image_atlas.resample_atlas_harvard_oxford(
    ref=imagefile_name.as_matrix()[0],
    output=os.path.join(OUTPUT, "mask.nii.gz"))

mask_atlas = babel_mask_atlas.get_data()
assert np.sum(mask_atlas != 0) == 617728
mask_atlas[np.logical_not(mask)] = 0  # apply implicit mask
# smooth
mask_atlas = brainomics.image_atlas.smooth_labels(mask_atlas, size=(3, 3, 3))
assert np.sum(mask_atlas != 0) ==  239780
out_im = nibabel.Nifti1Image(mask_atlas,
                             affine=babel_image.get_affine())
out_im.to_filename(os.path.join(OUTPUT, "mask.nii.gz"))
im = nibabel.load(os.path.join(OUTPUT, "mask.nii.gz"))
assert np.all(mask_atlas == im.get_data())

#############################################################################
# Compute mask with atlas but binarized (not group tv)
mask_bool = mask_atlas != 0
mask_bool.sum() == 239780
out_im = nibabel.Nifti1Image(mask_bool.astype("int16"),
                             affine=babel_image.get_affine())
out_im.to_filename(os.path.join(OUTPUT, "mask.nii.gz"))
babel_mask = nibabel.load(os.path.join(OUTPUT, "mask.nii.gz"))
assert np.all(mask_bool == (babel_mask.get_data() != 0))


#############################################################################

# Save data X and y
X = Xtot[:, mask_bool.ravel()]
#Use mean imputation, we could have used median for age
#imput = sklearn.preprocessing.Imputer(strategy = 'median',axis=0)
#Z = imput.fit_transform(Z)
X = np.hstack([Z, X])
assert X.shape == (236, 239782)

#Remove nan lines
X= X[np.logical_not(np.isnan(y)).ravel(),:]
y=y[np.logical_not(np.isnan(y))]
assert X.shape == (236, 239782)


X -= X.mean(axis=0)
X /= X.std(axis=0)
n, p = X.shape
np.save(os.path.join(OUTPUT, "X.npy"), X)
np.save(os.path.join(OUTPUT, "y.npy"), y)

###############################################################################
# precompute linearoperator

X = np.load(os.path.join(OUTPUT, "X.npy"))
y = np.load(os.path.join(OUTPUT, "y.npy"))

import parsimony.functions.nesterov.tv as nesterov_tv
from parsimony.utils.linalgs import LinearOperatorNesterov

mask = nibabel.load(os.path.join(OUTPUT, "mask.nii.gz"))

Atv = nesterov_tv.linear_operator_from_mask(mask.get_data(), calc_lambda_max=True)
Atv.save(os.path.join(OUTPUT, "Atv.npz"))
Atv_ = LinearOperatorNesterov(filename=os.path.join(OUTPUT, "Atv.npz"))
assert Atv.get_singular_values(0) == Atv_.get_singular_values(0)
assert np.allclose(Atv_.get_singular_values(0), 11.904427527000694)

###############################################################################
# precompute beta start
import parsimony.estimators as estimators
from sklearn import preprocessing
import time

X = np.load(os.path.join(OUTPUT, "X.npy"))
y = np.load(os.path.join(OUTPUT, "y.npy"))

#scaler = preprocessing.StandardScaler().fit(X)
#Xs = scaler.transform(X)
# Xs[:, 0] = 1 # Let Intercept be null to be compliant with previous study

betas = dict()


alphas = [0.0001, 0.001, 0.01, 0.1, 1.0]
# alphas = [0.0001, 0.001]

for alpha in alphas:
    mod = estimators.RidgeLogisticRegression(l=alpha, class_weight="auto",
                                             penalty_start=penalty_start,
                                             algorithm_params=dict(max_iter=10000))
    t_ = time.clock()
    mod.fit(X, y.ravel())
    print(time.clock() - t_, mod.algorithm.num_iter) # 11564
    betas["lambda_%.4f" % alpha] = mod.beta

#np.savez(os.path.join(OUTPUT, "beta_start_1000ite.npz"), **betas)
np.savez(os.path.join(OUTPUT, "beta_start.npz"), **betas)

betas.keys()

beta_start = np.load(os.path.join(OUTPUT, "beta_start.npz"))
assert np.all([np.all(beta_start[a] == betas[a]) for a in beta_start.keys()])

