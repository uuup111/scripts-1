"""
@author: yl247234
Copyrignt : CEA NeuroSpin - 2016
"""
import pandas as pd
import numpy as np
import os, glob, re

import nibabel.gifti.giftiio as gio

df = pd.DataFrame()
df['index'] = range(256)
df.index = df['index']

## INPUTS ###
#right 'R' or left 'L'
side = 'L'
sides = {'R': 'Right',
         'L': 'Left'}


## OUTPUT ##
OUTPUT = "/neurospin/brainomics/2016_sulcal_pits/extracting_pits_V0/"

path = '/neurospin/imagen/workspace/cati/BVdatabase/'

centres = ['Berlin','Dresden', 'Dublin', 'Hamburg', 'London', 'Mannheim', 'Nottingham', 'Paris']
s_ids = []
for centre in centres:
    path_c = path+centre+'/'
    for s_id in os.listdir(path_c):
        subject_folder =  path_c+s_id+'/'
        if os.path.isdir(subject_folder):
            #path_nifti = path_s + 't1mri/BL/'+subject+'.nii.gz'

            #### DEFINING THE PATH TO GET THE REPRESENTATION OF THE MAILLAGE #####

            file_white_mesh = os.path.join(subject_folder, "t1mri", "BL",
                               "default_analysis", "segmentation", "mesh",
                               ""+ s_id+ "_"+side+"white.gii")

            file_pits = os.path.join(subject_folder, "t1mri", "BL",
                                     "default_analysis", "segmentation", "mesh",
                                     "surface_analysis", ""+ s_id+ "_"+side+"white_pits.gii")

            file_parcels_marsAtlas = os.path.join(subject_folder, "t1mri", "BL",
                                                  "default_analysis", "segmentation", "mesh",
                                                  "surface_analysis", ""+ s_id+ "_"+side+"white_parcels_marsAtlas.gii")

            file_DPF = os.path.join(subject_folder, "t1mri", "BL",
                                     "default_analysis", "segmentation", "mesh",
                                     "surface_analysis", ""+ s_id+ "_"+side+"white_DPF.gii")
            file_lat = os.path.join(subject_folder, "t1mri", "BL",
                                     "default_analysis", "segmentation", "mesh",
                                     "surface_analysis", ""+ s_id+ "_"+side+"white_lat.gii")
            file_lon = os.path.join(subject_folder, "t1mri", "BL",
                                     "default_analysis", "segmentation", "mesh",
                                     "surface_analysis", ""+ s_id+ "_"+side+"white_lon.gii")

            if os.path.isfile(file_pits) and os.path.isfile(file_parcels_marsAtlas):


                pits_data = gio.read(file_pits).darrays[0].data
                parcels_data=  gio.read(file_parcels_marsAtlas).darrays[0].data
                DPF_data = gio.read(file_DPF).darrays[0].data
                lon_data = gio.read(file_lon).darrays[0].data
                lat_data = gio.read(file_lat).darrays[0].data


                pits_index = np.nonzero(pits_data)[0]
                parcels_numbers = parcels_data[pits_index]
                DPF_pits = DPF_data[pits_index]
                lat_pits = lat_data[pits_index]
                lon_pits = lon_data[pits_index]
                np.savetxt(OUTPUT+sides[side]+'/all/pits/'+side+s_id+'_pits.txt', pits_index)
                np.savetxt(OUTPUT+sides[side]+'/all/parcels/'+side+s_id+'_parcels_numbers.txt', parcels_numbers)
                np.savetxt(OUTPUT+sides[side]+'/all/DPF/'+side+s_id+'_DPF_pits.txt', DPF_pits)
                np.savetxt(OUTPUT+sides[side]+'/all/lat/'+side+s_id+'_lat_pits.txt', lat_pits)
                np.savetxt(OUTPUT+sides[side]+'/all/lon/'+side+s_id+'_lon_pits.txt', lon_pits)
                pits_per_parcels = [len(parcels_numbers)-np.count_nonzero(parcels_numbers-p) for p in range(256)]
                s_ids.append(s_id)
                df[s_id] = pits_per_parcels

df = df[s_ids]

# This part is now in filter_pits.py
"""count = 0
parcels_kept = []
for i in range(256):
    if np.mean(df.loc[i]) > 0.2 and np.std(df.loc[i]) < 2:
        count += 1
        print "\n"
        print "Parcel number: " + str(i)
        parcels_kept.append(i)
        print "Mean: " + str(np.mean(df.loc[i]))
        print "Std: " + str(np.std(df.loc[i]))

s_ids_max = []
nb_pits_max = []
for p in parcels_kept:
    # I know several subjects can reach the maximum number of pits in a parcel for the moment we just take the one given by argmax (maybe to be changed later)
    s_ids_max.append(np.argmax(df.loc[p]))
    nb_pits_max.append(np.amax(df.loc[p]))

path_saved = '/neurospin/brainomics/2016_sulcal_pits/extracting_pits_V0/'
filename_sav = sides[side]+'_s_ids_max.txt'
thefile = open(path_saved+ filename_sav, 'w')
for item in s_ids_max:
    print item
    thefile.write("%s\n" % item)
thefile.close()

path_saved = '/neurospin/brainomics/2016_sulcal_pits/extracting_pits_V0/'
filename_sav = sides[side]+'_parcels_kept.txt'
filename_sav2 = sides[side]+'_max_pits.txt'
np.savetxt(path_saved+filename_sav, parcels_kept)
np.savetxt(path_saved+filename_sav2, nb_pits_max)

import itertools
for centre in centres:
    path_c = path+centre+'/'
    for s_id in os.listdir(path_c):
        subject_folder =  path_c+s_id+'/'
        if os.path.isdir(subject_folder):
            file_pits = os.path.join(subject_folder, "t1mri", "BL",
                                     "default_analysis", "segmentation", "mesh",
                                     "surface_analysis", ""+ s_id+ "_"+side+"white_pits.gii")

            file_parcels_marsAtlas = os.path.join(subject_folder, "t1mri", "BL",
                                                  "default_analysis", "segmentation", "mesh",
                                                  "surface_analysis", ""+ s_id+ "_"+side+"white_parcels_marsAtlas.gii")

            file_DPF = os.path.join(subject_folder, "t1mri", "BL",
                                     "default_analysis", "segmentation", "mesh",
                                     "surface_analysis", ""+ s_id+ "_"+side+"white_DPF.gii")
            if os.path.isfile(file_pits) and os.path.isfile(file_parcels_marsAtlas):
                pits_index = np.loadtxt(OUTPUT+sides[side]+'/all/pits/'+side+s_id+'_pits.txt')
                parcels_numbers = np.loadtxt(OUTPUT+sides[side]+'/all/parcels/'+side+s_id+'_parcels_numbers.txt')
                DPF_pits = np.loadtxt(OUTPUT+sides[side]+'/all/DPF/'+side+s_id+'_DPF_pits.txt')
                lat_pits = np.loadtxt(OUTPUT+sides[side]+'/all/lat/'+side+s_id+'_lat_pits.txt')
                lon_pits = np.loadtxt(OUTPUT+sides[side]+'/all/lon/'+side+s_id+'_lon_pits.txt')
                index_parcels = [np.where(parcels_numbers==p)[0].tolist() for p in parcels_kept]
                index_parcels = list(itertools.chain.from_iterable(index_parcels))
                pits_index_kept = pits_index[index_parcels]
                parcels_numbers_kept = parcels_numbers[index_parcels]
                DPF_pits_kept = DPF_pits[index_parcels]
                lat_pits_kept = lat_pits[index_parcels]
                lon_pits_kept = lon_pits[index_parcels]

                np.savetxt(OUTPUT+sides[side]+'/kept/pits/'+side+s_id+'_pits_kept.txt', pits_index_kept)
                np.savetxt(OUTPUT+sides[side]+'/kept/parcels/'+side+s_id+'_parcels_numbers_kept.txt', parcels_numbers_kept)
                np.savetxt(OUTPUT+sides[side]+'/kept/DPF/'+side+s_id+'_DPF_pits_kept.txt', DPF_pits_kept)
                np.savetxt(OUTPUT+sides[side]+'/kept/lat/'+side+s_id+'_lat_pits_kept.txt', lat_pits_kept)
                np.savetxt(OUTPUT+sides[side]+'/kept/lon/'+side+s_id+'_lon_pits_kept.txt', lon_pits_kept)
"""
