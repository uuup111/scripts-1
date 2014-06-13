# -*- coding: utf-8 -*-
"""
Created on Thu Jun 12 08:50:45 2014

@author: hl237680

Comparison of Pylearn Parsimony and Scikit Learn
Elastic Net algorithms on simple sets of values
"""

import os, sys
import json
import numpy as np
import pandas as pd
import tables
import matplotlib.pyplot as plt
import parsimony.estimators as estimators
from sklearn.linear_model import ElasticNet
from sklearn.cross_validation import KFold
from sklearn.metrics import r2_score


sys.path.append(os.path.join(os.getenv('HOME'), 'gits', 'scripts', '2013_imagen_bmi', 'scripts'))
import bmi_utils
    
sys.path.append(os.path.join(os.environ["HOME"], "gits", "scripts", "2013_imagen_subdepression", "lib"))
import utils



def load_globals(config):
    import mapreduce as GLOBAL  # access to global variables
    GLOBAL.DATA = GLOBAL.load_data(config["data"])


def resample(config, resample_nb):
    import mapreduce as GLOBAL  # access to global variables
    #GLOBAL.DATA = GLOBAL.load_data(config["data"])
    resample = config["resample"][resample_nb]
    print "reslicing %d" %resample_nb
    GLOBAL.DATA_RESAMPLED = {k: [GLOBAL.DATA[k][idx, ...] for idx in resample]
                            for k in GLOBAL.DATA}                            
    print "done reslicing %d" %resample_nb


def mapper(key, output_collector):
    import mapreduce as GLOBAL # access to global variables:
    # key: list of parameters
    alpha, l1_ratio = key[0], key[1]
    Xtr = GLOBAL.DATA_RESAMPLED["X"][0]
    Xte = GLOBAL.DATA_RESAMPLED["X"][1]
    ztr = GLOBAL.DATA_RESAMPLED["z"][0]
    zte = GLOBAL.DATA_RESAMPLED["z"][1]
    print key, "Data shape:", Xtr.shape, Xte.shape, ztr.shape, zte.shape
    
    mod_SL = ElasticNet(alpha, l1_ratio, fit_intercept = True)
    z_pred_SL = mod_SL.fit(Xtr, ztr).predict(Xte)

    mod_PP = estimators.ElasticNet(alpha*l1_ratio, penalty_start = 11, mean = True)     #since we residualized BMI with 2 categorical covariables (Gender and ImagingCentreCity - 8 columns) and 2 ordinal variables (tiv_gaser and mean_pds - 2 columns)
    z_pred_PP = mod_PP.fit(Xtr,ztr).predict(Xte)

    t = np.arange(0., 5., 0.1)    
    plt.plot(t, mod_SL.beta, 'ro', t, mod_PP.beta, 'b^')
    plt.show()
    
    ret = dict(z_pred_SL=z_pred_SL, z_pred_PP=z_pred_PP, z_true=zte, beta_SL=mod_SL.beta, beta_PP=mod_PP.beta)
    output_collector.collect(key, ret)
    

def reducer(key, values):
    # key : string of intermediary key
    # load return dict corresponding to mapper ouput. they need to be loaded.
    values = [item.load() for item in values]
    z_true = np.concatenate([item["z_true"].ravel() for item in values])
    z_pred_SL = np.concatenate([item["z_pred_SL"].ravel() for item in values])
    z_pred_PP = np.concatenate([item["z_pred_PP"].ravel() for item in values])
    scores =  dict(param=key, r2_SL=r2_score(z_true, z_pred_SL, r2_PP=r2_score(z_true, z_pred_PP)))
    return scores
    


#############
# Read data #
#############
# SNPs and BMI
def load_residualized_bmi_data(cache):
    if not(cache):
        #SNPs = pd.io.parsers.read_csv(os.path.join(DATA_PATH, "SNPs.csv"), dtype='float64', index_col=0).as_matrix()
        BMI = pd.io.parsers.read_csv(os.path.join(DATA_PATH, "BMI.csv"), index_col=0).as_matrix()

        # Dataframe      
        COFOUND = ["Subject", "Gender de Feuil2", "ImagingCentreCity", "tiv_gaser", "mean_pds"]
        df = pd.io.parsers.read_csv(os.path.join(CLINIC_DATA_PATH, "1534bmi-vincent2.csv"), index_col=0)
        df = df[COFOUND]

        # Conversion dummy coding
        design_mat = utils.make_design_matrix(df, regressors=COFOUND).as_matrix()

        # Keep only subjects for which we have all data and remove the 1. column containing subject_id from the numpy array design_mat
        subjects_id = np.genfromtxt(os.path.join(DATA_PATH, "subjects_id.csv"), dtype=None, delimiter=',', skip_header=1)
        design_mat = np.delete(np.delete(design_mat, np.where(np.in1d(design_mat[:,0], np.delete(design_mat, np.where(np.in1d(design_mat[:,0], subjects_id)), 0))), 0),0,1)
               
        # Images
        h5file = tables.openFile(IMAGES_FILE)
        masked_images = bmi_utils.read_array(h5file, "/standard_mask/residualized_images_gender_center_TIV_pds")    #images already masked
        print "Data loaded"
        
        # Concatenate images with covariates gender, imaging city centrr, tiv_gaser and mean pds status in order to do as though BMI had been residualized
        X = np.concatenate((design_mat, masked_images), axis=1)
        #Y = SNPs
        z = BMI
        
        np.save(os.path.join(SHARED_DIR, "X.npy"), X)
        #np.save(os.path.join(SHARED_DIR, "Y.npy"), Y)
        np.save(os.path.join(SHARED_DIR, "z.npy"), z)
        h5file.close()
        
        print "Data saved"
    else:
        X = np.load(os.path.join(SHARED_DIR, "X.npy"))        
        #Y = np.load(os.path.join(SHARED_DIR, "Y.npy"))
        z = np.load(os.path.join(SHARED_DIR, "z.npy"))        
        print "Data read from cache"
    
    return X, z #X, Y, z

#"""
#run /home/hl237680/gits/scripts/2013_imagen_bmi/scripts/15_cv_multivariate_residualized_BMI.py
#"""
if __name__ == "__main__":

    ## Set pathes
    WD = "/neurospin/tmp/brainomics/algo_tests_PP_vs_SL-2"
    if not os.path.exists(WD): os.makedirs(WD)

    print "#################"
    print "# Build dataset #"
    print "#################"
    if True:
        # Pathnames
        BASE_PATH = '/neurospin/brainomics/2013_imagen_bmi/'
        DATA_PATH = os.path.join(BASE_PATH, 'data')
        CLINIC_DATA_PATH = os.path.join(DATA_PATH, 'clinic')
        IMAGES_FILE = os.path.join(DATA_PATH, 'smoothed_images.hdf5')
        #SNPS_FILE = os.path.join(DATA_PATH, 'SNPs.csv')
        BMI_FILE = os.path.join(DATA_PATH, 'BMI.csv')
        
        # Shared data
        BASE_SHARED_DIR = "/neurospin/tmp/brainomics/"
        SHARED_DIR = os.path.join(BASE_SHARED_DIR, 'residualized_bmi_cache')
        if not os.path.exists(SHARED_DIR):
            os.makedirs(SHARED_DIR)
        
        X, z = load_residualized_bmi_data(cache=False)
        #assert X.shape == (1265, 336188)
        n, p = X.shape
        np.save(os.path.join(WD, 'X.npy'), np.hstack((np.ones((z.shape[0],1)),X)))
        np.save(os.path.join(WD, "z.npy"), z)

    print "#####################"
    print "# Build config file #"
    print "#####################"
    ## Parameterize the mapreduce 
    ##   1) pathes
    NFOLDS = 5
    alpha = 1.
    ## 2) cv index and parameters to test
    cv = [[tr.tolist(), te.tolist()] for tr,te in KFold(n, n_folds=NFOLDS, shuffle=True, random_state=2505)]    
    params = [[alpha, l1_ratio] for l1_ratio in np.arange(0.1, 1., .1)]
    # User map/reduce function file:
    #user_func_filename = os.path.join("/home/hl237680",
    user_func_filename = os.path.join("/home/vf140245",
        "gits", "scripts", "2013_imagen_bmi", "scripts", 
        "test_PP_vs_SL.py")
    #print __file__, os.path.abspath(__file__)
    print "user_func", user_func_filename
    # Use relative path from config.json
    config = dict(data=dict(X='X.npy', z='z.npy'),
                  params=params, resample=cv,
                  structure="",
                  map_output="results",
                  user_func=user_func_filename,
                  reduce_input="results/*/*", 
                  reduce_group_by="results/.*/(.*)",
                  reduce_output="results_test_PP_vs_SL-2.csv")
    json.dump(config, open(os.path.join(WD, "config_test_PP_vs_SL-2.json"), "w"))

    #############################################################################
    # Build utils files: sync (push/pull) and PBS
    sys.path.append(os.path.join(os.getenv('HOME'),
                                'gits','scripts'))
    import brainomics.cluster_gabriel as clust_utils
    sync_push_filename, sync_pull_filename, WD_CLUSTER = \
        clust_utils.gabriel_make_sync_data_files(WD, user="vf140245")
    cmd = "mapreduce.py -m %s/config_test_PP_vs_SL-2.json  --ncore 12" % WD_CLUSTER
    clust_utils.gabriel_make_qsub_job_files(WD, cmd)
    #############################################################################
    # Sync to cluster
    print "Sync data to gabriel.intra.cea.fr: "
    os.system(sync_push_filename)

    #############################################################################
    print "# Start by running Locally with 12 cores, to check that everything is OK)"
    print "Interrupt after a while CTL-C"
    print "mapreduce.py -m %s/config_test_PP_vs_SL-2.json --ncore 12" % WD
    #os.system("mapreduce.py --mode map --config %s/config.json" % WD)
    print "# 1) Log on gabriel:"
    print 'ssh -t gabriel.intra.cea.fr'
    print "# 2) Run one Job to test"
    print "qsub -I"
    print "cd %s" % WD_CLUSTER
    print "./job_Global_long.pbs"
    print "# 3) Run on cluster"
    print "qsub job_Global_long.pbs"
    print "# 4) Log out and pull Pull"
    print "exit"
    print sync_pull_filename
    #############################################################################
    print "# Reduce"
    print "mapreduce.py -r %s/config_test_PP_vs_SL-2.json" % WD
    #ATTENTION ! Si envoi sur le cluster, modifier le path de config-2.json : /neurospin/tmp/hl237680/residual_bmi_images_cluster-2/config-2.json