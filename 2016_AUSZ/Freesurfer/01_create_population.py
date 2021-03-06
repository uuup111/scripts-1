# -*- coding: utf-8 -*-
"""
Created on Wed Nov 16 16:05:57 2016

@author: ad247405
"""

import os
import pandas as pd
import glob

GROUP_MAP = {1: 1, '2a': 2, '2b': 3, 3 : 0}
GENDER_MAP = {'F': 0, 'M': 1}



BASE_PATH = '/neurospin/brainomics/2016_AUSZ'
INPUT_CLINIC_FILENAME = '/neurospin/brainomics/2016_AUSZ/documents/Tableau_IRM_AUSZ_GM_16_12.xlsx'
INPUT_FS = '/neurospin/brainomics/2016_AUSZ/preproc_FS/freesurfer_assembled_data_fsaverage'

OUTPUT_CSV = os.path.join(BASE_PATH,"results","Freesurfer","population.csv")


#AUSZpopulation file
##############################################################################
# Read clinic data
clinic = pd.read_excel(INPUT_CLINIC_FILENAME,header = (1))
assert  clinic.shape == (136, 11)
#Take into account error of codes as notified by Gilles Martinez

#First error : GM120123 --> GO120133
row_index = clinic['IRM.1'] == 'GM120133'
clinic.loc[row_index,"IRM.1"] =  'GO120133'

#2nd error : SA120160 --> SA120159
row_index = clinic['IRM.1'] == 'SA120159'
clinic.loc[row_index,"IRM.1"] =  'SA120160'

#3rd error :  SB1201I8  --> SB120158 
row_index = clinic['IRM.1'] == 'SB1201I8'
clinic.loc[row_index,"IRM.1"] =  'SB120158'

#4th error :  ME150271   --> ME150371 
row_index = clinic['IRM.1'] == 'ME150271'
clinic.loc[row_index,"IRM.1"] =  'ME150371'

#5th error :  KD150466  --> KH150466
row_index = clinic['IRM.1'] == 'KD150466'
clinic.loc[row_index,"IRM.1"] =  'KH150466'

#6th error :  RE160510  --> RE1606510 
row_index = clinic['IRM.1'] == 'RE160510'
clinic.loc[row_index,"IRM.1"] =  'RE1606510'

#7th error :  
row_index = clinic['Ausz'] == 'AZ-RH-01-105'
clinic.loc[row_index,"IRM.1"] =  'RH150462'

#8th error : not spotted by Gilles 
row_index = clinic['IRM.1'] == 'LE160192'
clinic.loc[row_index,"IRM.1"] =  'LE160692'

#9th error : not spotted by Gilles 
row_index = clinic['IRM.1'] == 'RC160671'
clinic.loc[row_index,"IRM.1"] =  'RC160676'

assert  clinic.shape == (136, 11)


# Read free surfer assembled_data
input_subjects_fs = dict()
paths = glob.glob(INPUT_FS+"/*_lh.mgh")
for path in paths:
    subject = os.path.basename(path)[:-10]
    input_subjects_fs[subject] = [path]

paths = glob.glob(INPUT_FS+"/*_rh.mgh")
for path in paths:
    subject =os.path.basename(path)[:-10]
    input_subjects_fs[subject].append(path)
    
# drop images that do not correspond to AUSZ dataset    

# Remove if some hemisphere is missing
input_subjects_fs = [[k]+input_subjects_fs[k] for k in input_subjects_fs if len(input_subjects_fs[k]) == 2]

input_subjects_fs = pd.DataFrame(input_subjects_fs,  columns=["IRM.1", "mri_path_lh",  "mri_path_rh"])
assert input_subjects_fs.shape == (130, 3)

#Remove the 4 images that are not AUSZ (according to Gilles mail)
input_subjects_fs = input_subjects_fs[input_subjects_fs["IRM.1"] != "SA130280"]
input_subjects_fs = input_subjects_fs[input_subjects_fs["IRM.1"] != "CF140297"]
input_subjects_fs = input_subjects_fs[input_subjects_fs["IRM.1"] != "BM130180"]
input_subjects_fs = input_subjects_fs[input_subjects_fs["IRM.1"] != "CT130238"]

assert input_subjects_fs.shape == (126, 3)


# intersect with subject with image
clinic = clinic.merge(input_subjects_fs, on="IRM.1")
pop = clinic[["IRM.1","Groupe", "Sexe", "Âge", "mri_path_lh",  "mri_path_rh"]]
assert pop.shape == (126, 6)

pop = pop[pop["Groupe"]!="exclu"]
assert pop.shape == (123, 6) 

# Map group
pop['group.num'] = pop["Groupe"].map(GROUP_MAP)
pop['sex.num'] = pop["Sexe"].map(GENDER_MAP)

# Save population information
pop.to_csv(OUTPUT_CSV, encoding='utf-8' ) 
##############################################################################





 #Check subjects that do not correpsond between images and clinic   
#for i, ID in enumerate(input_subjects_fs["IRM.1"] ):
#    if ID not in list(clinic["IRM.1"]):
#        print (ID)
#        print ("is not in list")
