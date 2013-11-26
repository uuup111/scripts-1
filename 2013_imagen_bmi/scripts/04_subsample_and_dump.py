# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 17:47:44 2013

@author: md238665

This script subsamples the Gaser-segmented images and the mask and dump them in a HDF5 file for faster access.

The segmentation procedure is borrowed from Vincent Frouin subsampling scripts.
It uses a recent version of nilearn.
The git repository can be cloned at https://github.com/nilearn/nilearn.git

Warning: there are 1534 images but only 1265 subjects for BMI.
We reduce all the images but cache only the one relevant for BMI.

Warning: the cache file will be modified.

"""

import os, fnmatch
import numpy, pandas
import tables
import nibabel
from nilearn.image.resampling import resample_img

import bmi_utils

# Input
BASE_DIR='/neurospin/brainomics/2013_imagen_bmi/'
DATA_DIR=os.path.join(BASE_DIR, 'data')
CLINIC_DIR=os.path.join(DATA_DIR, 'clinic');
IMAGES_DIR=os.path.join(DATA_DIR, 'VBM', 'gaser_vbm8')
INIMG_FILENAME_TEMPLATE='smwp1{subject_id:012}*.nii'
CACHE_FILE=os.path.join(DATA_DIR, 'dataset.hdf5')
FULL_CLINIC_FILE=os.path.join(CLINIC_DIR, '1534bmi-vincent2.csv')

# Original mask and mask without cerebellum
MASK_FILE=os.path.join(DATA_DIR, 'mask.nii')
MASK_WITHOUT_CEREBELUM_FILE=os.path.join(DATA_DIR, 'mask_without_cerebellum', 'mask_without_cerebellum_7.nii')

# Images will be shaped as this image
TARGET_FILE='/neurospin/brainomics/neuroimaging_ressources/atlases/HarvardOxford/HarvardOxford-LR-cort-333mm.nii.gz'

# Output files
OUT_DIR=os.path.join(DATA_DIR, 'subsampled_images/tmp')
OUTIMG_FILENAME_TEMPLATE='rsmwp1{subject_id:012}*.nii'
RMASK_FILE=os.path.join(OUT_DIR, 'rmask.nii')
RMASK_WITHOUT_CEREBELUM_FILE=os.path.join(OUT_DIR, 'rmask_without_cerebellum_7.nii')
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# Resampling function
def resample(input_image, target_affine, target_shape, interpolation='continuous'):
    outim = resample_img(input_image,
                         target_affine=target_affine, target_shape=target_shape,
                         interpolation=interpolation)
    return outim

# Open the clinic file to get all the subject's ID
df = pandas.io.parsers.read_csv(FULL_CLINIC_FILE)
all_subject_indices = df.Subjects
n_images = df.shape[0]

# Read the BMI subject ID from cache file
h5file = tables.openFile(CACHE_FILE, mode="r+")
bmi_subject_indices = numpy.array(h5file.root.subject_id)

# Open target image
target = nibabel.load(TARGET_FILE)
target_shape = target.shape
target_affine = target.get_affine()

# Resize masks & save them
babel_mask  = nibabel.load(MASK_FILE)
babel_rmask = resample(babel_mask, target_affine, target_shape, interpolation='continuous')
nibabel.save(babel_rmask, RMASK_FILE)
rmask        = babel_rmask.get_data()
binary_rmask = rmask!=0
useful_voxels = numpy.ravel_multi_index(numpy.where(binary_rmask), rmask.shape)
n_useful_voxels = len(useful_voxels)
print "Mask reduced: {n} true voxels".format(n=n_useful_voxels)

babel_mask_without_cerebellum  = nibabel.load(MASK_WITHOUT_CEREBELUM_FILE)
babel_rmask_without_cerebellum = resample(babel_mask_without_cerebellum, target_affine, target_shape, interpolation='continuous')
nibabel.save(babel_rmask_without_cerebellum, RMASK_WITHOUT_CEREBELUM_FILE)
rmask_without_cerebellum        = babel_rmask_without_cerebellum.get_data()
binary_rmask_without_cerebellum = rmask_without_cerebellum!=0
useful_voxels_without_cerebellum = numpy.ravel_multi_index(numpy.where(binary_rmask_without_cerebellum), rmask_without_cerebellum.shape)
n_useful_voxels_without_cerebellum = len(useful_voxels_without_cerebellum)
print "Mask without cerebellum reduced: {n} true voxels".format(n=n_useful_voxels_without_cerebellum)

# Reduce all images
all_images_filename = bmi_utils.find_images(all_subject_indices, INIMG_FILENAME_TEMPLATE, IMAGES_DIR)

## Read images in the same order than subjects, resample & dump
#images = numpy.zeros((n_images, n_useful_voxels))
#images_without_cerebellum = numpy.zeros((n_images, n_useful_voxels_without_cerebellum))
#images_dir_files = os.listdir(IMAGES_DIR)
#for (index, subject_index) in enumerate(subject_indices):
#    # Find filename
#    pattern = INIMG_FILENAME_TEMPLATE.format(subject_id=subject_index)
#    filename = fnmatch.filter(images_dir_files, pattern)
#    if len(filename) != 1:
#        raise Exception
#    else:
#        full_infilename = os.path.join(IMAGES_DIR, filename[0])
#    # Generate output name
#    full_outfilename = os.path.join(OUT_DIR, 'r'+filename[0])
#    print "Reducing {in_} to {out}".format(in_=full_infilename, out=full_outfilename)
#    # Resample and save
#    input_image = nibabel.load(full_infilename)
#    out_image = resample(input_image, target_affine, target_shape)
#    nibabel.save(out_image, full_outfilename)
#    # Apply mask & store in array
#    masked_image = out_image.get_data()[binary_rmask]
#    images[index, :] = masked_image
#    # Apply mask without cerebellum & store in array
#    masked_image_without_cerebellum = out_image.get_data()[binary_rmask_without_cerebellum]
#    images_without_cerebellum[index, :] = masked_image_without_cerebellum
## Open the HDF5 file
#h5file = tables.openFile(OUT_HDF5_FILE, mode = "w", title = 'reduced_images')
#atom = tables.Atom.from_dtype(images.dtype)
#filters = tables.Filters(complib='zlib', complevel=5)
#ds = h5file.createCArray(h5file.root, 'images', atom, images.shape, filters=filters)
#ds[:] = images
#ds = h5file.createCArray(h5file.root, 'images_without_cerebellum', atom, images_without_cerebellum.shape, filters=filters)
#ds[:] = images_without_cerebellum
#h5file.close()
#print "Images reduced and dumped"
