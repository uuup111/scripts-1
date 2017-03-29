# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 13:52:53 2016

@author: ad247405
"""


#Before running the script, delete the snapshots with just white background

import numpy as np
import os, os.path
import glob

WD = '/neurospin/brainomics/2016_classif_hallu_fmri/unsupervised_fmri/clustering_3rdcomp/cluster1/snapshosts'

WD = '/neurospin/brainomics/2016_classif_hallu_fmri/toward_on/Logistic_L1_L2_TV_with_HC/snapshosts'

WD = '/neurospin/brainomics/2016_classif_hallu_fmri/toward_on/svm_with_HC/snapshosts'


slices_montage(WD,nb_slices = 10)



def slices_montage(WD,nb_slices):
    os.chdir(WD)
    
    ax = glob.glob(os.path.join(WD,'*axial*'))
    co = glob.glob(os.path.join(WD,'*coronal*'))
    sa = glob.glob(os.path.join(WD,'*sagital*'))
    
    nb_axial = len(ax)
    nb_coronal = len(co)
    nb_sagital = len(sa)
    
    ax_slices = list()
    for i in np.linspace(0,nb_axial,nb_slices,dtype=int,endpoint=False):
        ax_slices.append(ax[i])
    print len(ax_slices)
    command = "montage %s -tile 1x -geometry +2+2 montage_ax.png" % (' '.join(ax_slices))
    os.system(command)
    
    co_slices = list()
    for i in np.linspace(0,nb_coronal,nb_slices,dtype=int,endpoint=False):
        co_slices.append(co[i])
    print len(co_slices)  
    command = "montage %s -tile 1x -geometry +2+2 montage_co.png" % (' '.join(co_slices))
    os.system(command)
    
    
    sa_slices = list()
    for i in np.linspace(0,nb_sagital,nb_slices,dtype=int,endpoint=False):
        sa_slices.append(sa[i])
    print len(sa_slices) 
    command = "montage %s -tile 1x -geometry +2+2 montage_sa.png" % (' '.join(sa_slices))
    os.system(command)
    
    
    
    command = "montage montage_ax.png montage_co.png montage_sa.png -tile 3x1 -geometry +2+2 montage.png" 
    os.system(command)
