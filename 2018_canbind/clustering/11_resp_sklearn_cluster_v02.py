#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 27 09:07:06 2018

@author: ed203246
"""

"""
Created on Thu Jul  5 18:41:41 2018

@author: ed203246

cp /neurospin/psy/canbind/models/vbm_resp_1.5mm/XTreatTivSite.npy /neurospin/psy/canbind/models/clustering_v02/
cp /neurospin/psy/canbind/models/vbm_resp_1.5mm/XTreatTivSitePca.npy /neurospin/psy/canbind/models/clustering_v02/
cp /neurospin/psy/canbind/models/vbm_resp_1.5mm/population.csv /neurospin/psy/canbind/models/clustering_v02/
cp /neurospin/psy/canbind/models/vbm_resp_1.5mm/mask.nii.gz /neurospin/psy/canbind/models/clustering_v02/
cp /neurospin/psy/canbind/models/vbm_resp_1.5mm/y.npy /neurospin/psy/canbind/models/clustering_v02/

"""

#############################################################################
# Models of respond_wk16_num + psyhis_mdd_age + age + sex_num + site
import os
import numpy as np
import nibabel
import pandas as pd
# from sklearn import datasets
import sklearn.svm as svm
from sklearn import preprocessing
from sklearn.model_selection import cross_val_score, cross_validate
from sklearn.model_selection import StratifiedKFold
#from sklearn.feature_selection import SelectKBest
#from sklearn.feature_selection import f_classif
#from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
import sklearn.metrics as metrics
import sklearn.linear_model as lm
from matplotlib import pyplot as plt
import mulm
import seaborn as sns

WD = '/neurospin/psy/canbind'
#BASE_PATH = '/neurospin/brainomics/2018_euaims_leap_predict_vbm/results/VBM/1.5mm'

# Voxel size
# vs = "1mm"
#vs = "1.5mm-s8mm"
vs = "1.5mm"

"""
Xa = np.load("/neurospin/psy/canbind/models/vbm_resp_1.5mm/XTreatTivSite.npy")
Xb = np.load("/neurospin/psy/canbind/models/vbm_resp_1.5mm-/XTreatTivSite.npy")
np.all(Xa == Xb)
ya = np.load("/neurospin/psy/canbind/models/vbm_resp_1.5mm/y.npy")
yb = np.load("/neurospin/psy/canbind/models/vbm_resp_1.5mm-/y.npy")
np.all(ya == yb)
"""

INPUT = os.path.join(WD, "models", "clustering_v02")

OUTPUT = INPUT

# load data
#DATASET = "XTreatTivSitePca"
#DATASET = "XTreatTivSite-ClinIm"
IMADATASET = "XTreatTivSite"
# IMADATASET = "XTreatTivSitePca"

#X = np.load(os.path.join(INPUT, "Xres.npy"))
#Xim = np.load(os.path.join(INPUT, "Xrawsc.npy"))
Xim = np.load(os.path.join(INPUT, IMADATASET+".npy"))


yorig = np.load(os.path.join(INPUT, "y.npy"))

pop = pd.read_csv(os.path.join(INPUT, "population.csv"))
assert np.all(pop['respond_wk16_num'] == yorig)

democlin = pop[['age', 'sex_num', 'educ', 'age_onset', 'respond_wk16', 'mde_num', 'madrs_Baseline', 'madrs_Screening']]
democlin.describe()

"""
              age     sex_num        educ   age_onset    mde_num  madrs_Baseline  madrs_Screening
count  124.000000  124.000000  123.000000  118.000000  88.000000      120.000000       117.000000
mean    35.693548    0.620968   16.813008   20.983051   3.840909       29.975000        30.427350
std     12.560214    0.487114    2.255593    9.964881   2.495450        5.630742         5.234692
min     18.000000    0.000000    9.000000    5.000000   1.000000       21.000000        22.000000
25%     25.000000    0.000000   16.000000   14.250000   2.000000       25.750000        27.000000
50%     33.000000    1.000000   17.000000   18.000000   3.000000       29.000000        29.000000
75%     46.000000    1.000000   19.000000   25.750000   5.000000       34.000000        33.000000
max     61.000000    1.000000   21.000000   55.000000  10.000000       47.000000        46.000000
"""
democlin.isnull().sum()
"""
age                 0
sex_num             0
educ                1
age_onset           6
respond_wk16        0
mde_num            36
madrs_Baseline      4
madrs_Screening     7
"""

# Imput missing value with the median

democlin.loc[democlin["educ"].isnull(), "educ"] = democlin["educ"].median()
democlin.loc[democlin["age_onset"].isnull(), "age_onset"] = democlin["age_onset"].median()
democlin.loc[democlin["mde_num"].isnull(), "mde_num"] = democlin["mde_num"].median()


democlin.loc[democlin["madrs_Baseline"].isnull(), "madrs_Baseline"] = democlin.loc[democlin["madrs_Baseline"].isnull(), "madrs_Screening"]
assert democlin["madrs_Baseline"].isnull().sum() == 0

democlin.pop("madrs_Screening")
assert(np.all(democlin.isnull().sum() == 0))

# add duration
democlin["duration"] = democlin["age"] - democlin["age_onset"]

# Rm response
resp_ = democlin.pop("respond_wk16")
assert np.all((resp_ == "Responder") == yorig)

democlin.columns
"""
['age', 'sex_num', 'educ', 'age_onset', 'mde_num', 'madrs_Baseline', 'duration']
"""
Xclin = np.asarray(democlin)

###############################################################################
# ML
from sklearn.model_selection import cross_val_score, cross_validate
from sklearn.model_selection import StratifiedKFold
import copy

#clustering = pd.read_csv(os.path.join(INPUT, DATASET+"-clust.csv"))
#cluster_labels = clustering.cluster
C = 0.1
NFOLDS = 5
cv = StratifiedKFold(n_splits=NFOLDS)
model = lm.LogisticRegression(class_weight='balanced', fit_intercept=False, C=C)
scaler = preprocessing.StandardScaler()
def balanced_acc(estimator, X, y):
    return metrics.recall_score(y, estimator.predict(X), average=None).mean()
scorers = {'auc': 'roc_auc', 'bacc':balanced_acc, 'acc':'accuracy'}


###############################################################################
## Clust Clinic / Classify clinic

X = scaler.fit(Xclin).transform(Xclin)

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score


range_n_clusters = [2, 3, 4, 5, 6, 7, 8, 9]
for n_clusters in range_n_clusters:
    clusterer = KMeans(n_clusters=n_clusters, random_state=10)
    cluster_labels = clusterer.fit_predict(X)

    # The silhouette_score gives the average value for all the samples.
    # This gives a perspective into the density and separation of the formed
    # clusters
    silhouette_avg = silhouette_score(X, cluster_labels)
    print("For n_clusters =", n_clusters,
          "The average silhouette_score is :", silhouette_avg)

'''
For n_clusters = 2 The average silhouette_score is : 0.236327338035
For n_clusters = 3 The average silhouette_score is : 0.248227481469
For n_clusters = 4 The average silhouette_score is : 0.257889640987
For n_clusters = 5 The average silhouette_score is : 0.249662837914
For n_clusters = 6 The average silhouette_score is : 0.216915960545
For n_clusters = 7 The average silhouette_score is : 0.213423981512
For n_clusters = 8 The average silhouette_score is : 0.218288231815
For n_clusters = 9 The average silhouette_score is : 0.219306207968

array([[16, 16],
       [32, 60]])
'''

X = scaler.fit(Xclin).transform(Xclin)
clustering = dict()
clustering['participant_id'] = pop['participant_id']

range_n_clusters = [2, 3]
res = list()
for n_clusters in range_n_clusters:
    print("######################################")
    print("# nclust", n_clusters)
    clusterer = KMeans(n_clusters=n_clusters, random_state=10)
    cluster_labels = clusterer.fit_predict(X)
    clustering["nclust=%i" % n_clusters] = cluster_labels
    for clust in np.unique(cluster_labels):
        print("===================================")
        subset = cluster_labels == clust
        print(clust, subset.sum())
        Xg = Xclin[subset, :]
        yg = yorig[subset]
        Xg = scaler.fit(Xg).transform(Xg)

        cv = StratifiedKFold(n_splits=NFOLDS)
        model = lm.LogisticRegression(class_weight='balanced', fit_intercept=False, C=C)

        cv_results = cross_validate(estimator=copy.copy(model), X=Xg, y=yg, cv=cv, scoring=scorers, n_jobs=-1)
        res.append(['Clinic', 'test_auc', n_clusters, clust, subset.sum()] + cv_results["test_auc"].tolist() + [cv_results["test_auc"].mean()])
        res.append(['Clinic', 'test_bacc', n_clusters, clust, subset.sum()] + cv_results["test_bacc"].tolist() + [cv_results["test_bacc"].mean()])
        res.append(['Clinic', 'test_acc', n_clusters, clust, subset.sum()] + cv_results["test_acc"].tolist() + [cv_results["test_acc"].mean()])

clustering = pd.DataFrame(clustering)
clustering.to_csv(os.path.join(INPUT, "Xclin-clust.csv"), index=False)

clustering["nclust=2"]

res = pd.DataFrame(res, columns=['data', 'score', 'n_clusters', 'clust', 'size'] + ["fold%i" % i for i in range(NFOLDS)] + ['avg'])

print(res)
'''
      data      score  n_clusters  clust  size     fold0     fold1     fold2     fold3     fold4       avg
0   Clinic   test_auc           2      0    42  0.555556  0.388889  0.444444  0.666667  0.300000  0.471111
1   Clinic  test_bacc           2      0    42  0.583333  0.416667  0.333333  0.633333  0.350000  0.463333
2   Clinic   test_acc           2      0    42  0.555556  0.444444  0.333333  0.625000  0.285714  0.448810
3   Clinic   test_auc           2      1    82  0.326923  0.634615  0.576923  0.282051  0.222222  0.408547
4   Clinic  test_bacc           2      1    82  0.355769  0.605769  0.682692  0.346154  0.250000  0.448077
5   Clinic   test_acc           2      1    82  0.411765  0.529412  0.647059  0.562500  0.400000  0.510147
6   Clinic   test_auc           3      0    19  1.000000  0.500000  1.000000  1.000000  0.000000  0.700000
7   Clinic  test_bacc           3      0    19  0.833333  0.583333  0.750000  0.500000  0.250000  0.583333
8   Clinic   test_acc           3      0    19  0.800000  0.600000  0.666667  0.666667  0.333333  0.613333
9   Clinic   test_auc           3      1    67  0.666667  0.545455  0.545455  0.500000  0.400000  0.531515
10  Clinic  test_bacc           3      1    67  0.606061  0.439394  0.469697  0.566667  0.500000  0.516364
11  Clinic   test_acc           3      1    67  0.571429  0.500000  0.357143  0.692308  0.500000  0.524176
12  Clinic   test_auc           3      2    38  0.500000  0.250000  0.100000  0.400000  0.200000  0.290000
13  Clinic  test_bacc           3      2    38  0.500000  0.250000  0.250000  0.700000  0.100000  0.360000
14  Clinic   test_acc           3      2    38  0.444444  0.375000  0.142857  0.571429  0.142857  0.335317

Nothing
'''

###############################################################################
# Clustering Im

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score

scaler = preprocessing.StandardScaler()
X = scaler.fit(Xim).transform(Xim)
clustering = dict()
clustering['participant_id'] = pop['participant_id']

range_n_clusters = [2, 3, 4]
#range_n_clusters = [2]

for n_clusters in range_n_clusters:
    clusterer = KMeans(n_clusters=n_clusters, random_state=10)
    cluster_labels = clusterer.fit_predict(X)
    clustering["nclust=%i" % n_clusters] = cluster_labels
    # The silhouette_score gives the average value for all the samples.
    # This gives a perspective into the density and separation of the formed
    # clusters
    silhouette_avg = silhouette_score(X, cluster_labels)
    print("For n_clusters =", n_clusters,
          "The average silhouette_score is :", silhouette_avg)

"""
XTreatTivSite
For n_clusters = 2 The average silhouette_score is : 0.0477990828217
For n_clusters = 3 The average silhouette_score is : 0.0192031806854
For n_clusters = 4 The average silhouette_score is : 0.017407720471

XTreatTivSitePca
For n_clusters = 2 The average silhouette_score is : 0.00444455719081
For n_clusters = 3 The average silhouette_score is : 0.00226944083272
For n_clusters = 4 The average silhouette_score is : -0.00550654879244
"""
clustering = pd.DataFrame(clustering)
clustering.to_csv(os.path.join(INPUT, IMADATASET+"-clust.csv"), index=False)

# refit with 2 cluster
clusterer = KMeans(n_clusters=2, random_state=10)
cluster_labels_ = clusterer.fit_predict(X)
assert np.all(cluster_labels_ == clustering["nclust=2"])

np.savez_compressed(os.path.join(INPUT, IMADATASET+"-clust_centers.npz"),
                    cluster_labels=cluster_labels_,
                    cluster_centers=clusterer.cluster_centers_)

# Caracterize cluster
clusters = np.load(os.path.join(INPUT, IMADATASET+"-clust_centers.npz"))
clusters["cluster_labels"]
cluster_centers = clusters["cluster_centers"]
## WIP HERE
from nilearn import datasets, plotting, image

import  nibabel
mask_img = nibabel.load(os.path.join(INPUT, "mask.nii.gz"))

coef_arr = np.zeros(mask_img.get_data().shape)
coef = cluster_centers[0, :]
coef = cluster_centers[1, :]
coef = cluster_centers[1, :] - cluster_centers[0, :]
pd.Series(np.abs(coef)).describe()

coef_arr[mask_img.get_data() != 0] = coef
coef_img = nibabel.Nifti1Image(coef_arr, affine=mask_img.affine)
plotting.plot_glass_brain(coef_img, threshold=0.2)#, figure=fig, axes=ax)
## WIP HERE

clustering = pd.DataFrame(clustering)
clustering.to_csv(os.path.join(INPUT, IMADATASET+"-clust.csv"), index=False)

###############################################################################
# Clustering Im classifiy Clin

clustering = pd.read_csv(os.path.join(INPUT, IMADATASET+"-clust.csv"))
#pop = pd.read_csv(os.path.join(INPUT,"population.csv"))
assert np.all(pop.participant_id == clustering.participant_id)

metrics.confusion_matrix(yorig, clustering["nclust=2"])

"""
array([[17, 15],
       [45, 47]])

XTreatTivSitePca
array([[ 6, 26],
       [31, 61]])
"""
metrics.confusion_matrix(yorig, clustering["nclust=3"])[:2, :]
"""
array([[ 6, 18,  8],
       [33, 32, 27]])
"""

range_n_clusters = [2]#, 3]
res = list()
for n_clusters in range_n_clusters:
    print("######################################")
    print("# nclust", n_clusters)
    cluster_labels = clustering["nclust=%i" % n_clusters]
    for clust in np.unique(cluster_labels):
        print("===================================")
        subset = cluster_labels == clust
        print(clust, subset.sum())
        Xg = Xclin[subset, :]
        yg = yorig[subset]
        Xg = scaler.fit(Xg).transform(Xg)

        cv = StratifiedKFold(n_splits=NFOLDS)
        model = lm.LogisticRegression(class_weight='balanced', fit_intercept=False, C=C)

        cv_results = cross_validate(estimator=copy.copy(model), X=Xg, y=yg, cv=cv, scoring=scorers, n_jobs=-1)
        res.append(['Clinic', 'test_auc', n_clusters, clust, subset.sum()] + cv_results["test_auc"].tolist() + [cv_results["test_auc"].mean()])
        res.append(['Clinic', 'test_bacc', n_clusters, clust, subset.sum()] + cv_results["test_bacc"].tolist() + [cv_results["test_bacc"].mean()])
        res.append(['Clinic', 'test_acc', n_clusters, clust, subset.sum()] + cv_results["test_acc"].tolist() + [cv_results["test_acc"].mean()])


res = pd.DataFrame(res, columns=['data', 'score', 'n_clusters', 'clust', 'size'] + ["fold%i" % i for i in range(NFOLDS)] + ['avg'])
print(res)

"""
XTreatTivSite
      data      score  n_clusters  clust  size     fold0     fold1     fold2     fold3     fold4       avg
0   Clinic   test_auc           2      0    62  0.694444  0.472222  0.592593  0.740741  0.222222  0.544444
1   Clinic  test_bacc           2      0    62  0.458333  0.486111  0.555556  0.611111  0.166667  0.455556
2   Clinic   test_acc           2      0    62  0.538462  0.384615  0.500000  0.750000  0.250000  0.484615
3   Clinic   test_auc           2      1    62  0.700000  0.566667  0.888889  0.925926  0.740741  0.764444
4   Clinic  test_bacc           2      1    62  0.533333  0.466667  0.833333  0.833333  0.555556  0.644444
5   Clinic   test_acc           2      1    62  0.461538  0.538462  0.750000  0.750000  0.666667  0.633333
6   Clinic   test_auc           3      0    39  0.142857  0.857143  1.000000  1.000000  1.000000  0.800000
7   Clinic  test_bacc           3      0    39  0.142857  0.857143  0.785714  0.750000  0.833333  0.673810
8   Clinic   test_acc           3      0    39  0.222222  0.750000  0.625000  0.571429  0.714286  0.576587
9   Clinic   test_auc           3      1    50  0.285714  0.392857  0.333333  0.611111  0.611111  0.446825
10  Clinic  test_bacc           3      1    50  0.464286  0.339286  0.416667  0.666667  0.500000  0.477381
11  Clinic   test_acc           3      1    50  0.454545  0.363636  0.400000  0.555556  0.555556  0.465859
12  Clinic   test_auc           3      2    35  0.416667  0.500000  1.000000  0.000000  0.200000  0.423333
13  Clinic  test_bacc           3      2    35  0.416667  0.500000  0.900000  0.400000  0.100000  0.463333
14  Clinic   test_acc           3      2    35  0.375000  0.500000  0.857143  0.666667  0.166667  0.513095

YEAH
2 clusters:
3   Clinic   test_auc           2      1    62  0.700000  0.566667  0.888889  0.925926  0.740741  0.764444
4   Clinic  test_bacc           2      1    62  0.533333  0.466667  0.833333  0.833333  0.555556  0.644444
5   Clinic   test_acc           2      1    62  0.461538  0.538462  0.750000  0.750000  0.666667  0.633333

XTreatTivSitePca
     data      score  n_clusters  clust  size     fold0     fold1     fold2     fold3     fold4       avg
0  Clinic   test_auc           2      0    37  0.357143  0.666667  0.333333  0.500000  0.333333  0.438095
1  Clinic  test_bacc           2      0    37  0.535714  0.750000  0.250000  0.250000  0.583333  0.473810
2  Clinic   test_acc           2      0    37  0.555556  0.571429  0.428571  0.428571  0.285714  0.453968
3  Clinic   test_auc           2      1    87  0.538462  0.366667  0.866667  0.550000  0.283333  0.521026
4  Clinic  test_bacc           2      1    87  0.512821  0.308333  0.733333  0.591667  0.350000  0.499231
5  Clinic   test_acc           2      1    87  0.578947  0.352941  0.705882  0.588235  0.411765  0.527554
"""


###############################################################################
# Clustering Im classifiy Im

clustering = pd.read_csv(os.path.join(INPUT, IMADATASET+"-clust.csv"))
#pop = pd.read_csv(os.path.join(INPUT,"population.csv"))
assert np.all(pop.participant_id == clustering.participant_id)

metrics.confusion_matrix(yorig, clustering["nclust=2"])

"""
array([[17, 15],
       [45, 47]])

    XTreatTivSitePca
array([[ 6, 26],
       [31, 61]])
"""
metrics.confusion_matrix(yorig, clustering["nclust=3"])[:2, :]
"""
array([[ 6, 18,  8],
       [33, 32, 27]])
"""

range_n_clusters = [2]
res = list()
for n_clusters in range_n_clusters:
    print("######################################")
    print("# nclust", n_clusters)
    cluster_labels = clustering["nclust=%i" % n_clusters]
    for clust in np.unique(cluster_labels):
        print("===================================")
        subset = cluster_labels == clust
        print(clust, subset.sum())
        Xg = Xim[subset, :]
        yg = yorig[subset]
        Xg = scaler.fit(Xg).transform(Xg)

        cv = StratifiedKFold(n_splits=NFOLDS)
        model = lm.LogisticRegression(class_weight='balanced', fit_intercept=False, C=C)

        cv_results = cross_validate(estimator=copy.copy(model), X=Xg, y=yg, cv=cv, scoring=scorers, n_jobs=-1)
        res.append(['Ima', 'test_auc', n_clusters, clust, subset.sum()] + cv_results["test_auc"].tolist() + [cv_results["test_auc"].mean()])
        res.append(['Ima', 'test_bacc', n_clusters, clust, subset.sum()] + cv_results["test_bacc"].tolist() + [cv_results["test_bacc"].mean()])
        res.append(['Ima', 'test_acc', n_clusters, clust, subset.sum()] + cv_results["test_acc"].tolist() + [cv_results["test_acc"].mean()])

res = pd.DataFrame(res, columns=['data', 'score', 'n_clusters', 'clust', 'size'] + ["fold%i" % i for i in range(NFOLDS)] + ['avg'])
print(res)

"""
XTreatTivSite
  data      score  n_clusters  clust  size     fold0     fold1     fold2     fold3     fold4       avg
0  Ima   test_auc           2      0    62  0.472222  0.694444  0.444444  0.111111  0.740741  0.492593
1  Ima  test_bacc           2      0    62  0.500000  0.500000  0.500000  0.500000  0.500000  0.500000
2  Ima   test_acc           2      0    62  0.307692  0.307692  0.250000  0.250000  0.250000  0.273077
3  Ima   test_auc           2      1    62  0.433333  0.866667  0.888889  0.814815  0.444444  0.689630
4  Ima  test_bacc           2      1    62  0.500000  0.500000  0.500000  0.500000  0.500000  0.500000
5  Ima   test_acc           2      1    62  0.230769  0.230769  0.250000  0.250000  0.250000  0.242308

YEAH:
3  Ima   test_auc           2      1    62  0.433333  0.866667  0.888889  0.814815  0.444444  0.689630

XTreatTivSitePca
  data      score  n_clusters  clust  size     fold0     fold1     fold2     fold3     fold4       avg
0  Ima   test_auc           2      0    37  0.500000  0.333333  0.333333  0.000000  0.000000  0.233333
1  Ima  test_bacc           2      0    37  0.500000  0.500000  0.500000  0.500000  0.500000  0.500000
2  Ima   test_acc           2      0    37  0.222222  0.142857  0.142857  0.142857  0.142857  0.158730
3  Ima   test_auc           2      1    87  0.500000  0.300000  0.600000  0.350000  0.916667  0.533333
4  Ima  test_bacc           2      1    87  0.500000  0.500000  0.500000  0.500000  0.500000  0.500000
5  Ima   test_acc           2      1    87  0.315789  0.294118  0.294118  0.294118  0.294118  0.298452
"""


###############################################################################
# Clustering Clin classifiy Im

clustering = pd.read_csv(os.path.join(INPUT, "Xclin-clust.csv"))
#pop = pd.read_csv(os.path.join(INPUT,"population.csv"))
assert np.all(pop.participant_id == clustering.participant_id)

metrics.confusion_matrix(yorig, clustering["nclust=2"])

"""
array([[16, 16],
       [32, 60]])
"""
metrics.confusion_matrix(yorig, clustering["nclust=3"])[:2, :]
"""
array([[ 9, 13, 10],
       [11, 55, 26]])
"""

range_n_clusters = [2, 3]
res = list()
for n_clusters in range_n_clusters:
    print("######################################")
    print("# nclust", n_clusters)
    cluster_labels = clustering["nclust=%i" % n_clusters]
    for clust in np.unique(cluster_labels):
        print("===================================")
        subset = cluster_labels == clust
        print(clust, subset.sum())
        Xg = Xim[subset, :]
        yg = yorig[subset]
        Xg = scaler.fit(Xg).transform(Xg)

        cv = StratifiedKFold(n_splits=NFOLDS)
        model = lm.LogisticRegression(class_weight='balanced', fit_intercept=False, C=C)

        cv_results = cross_validate(estimator=copy.copy(model), X=Xg, y=yg, cv=cv, scoring=scorers, n_jobs=-1)
        res.append(['Ima', 'test_auc', n_clusters, clust, subset.sum()] + cv_results["test_auc"].tolist() + [cv_results["test_auc"].mean()])
        res.append(['Ima', 'test_bacc', n_clusters, clust, subset.sum()] + cv_results["test_bacc"].tolist() + [cv_results["test_bacc"].mean()])
        res.append(['Ima', 'test_acc', n_clusters, clust, subset.sum()] + cv_results["test_acc"].tolist() + [cv_results["test_acc"].mean()])


res = pd.DataFrame(res, columns=['data', 'score', 'n_clusters', 'clust', 'size'] + ["fold%i" % i for i in range(NFOLDS)] + ['avg'])
print(res)

"""
XTreatTivSite
   data      score  n_clusters  clust  size     fold0     fold1     fold2     fold3     fold4       avg
0   Ima   test_auc           2      0    42  0.777778  0.666667  0.222222  0.733333  0.000000  0.480000
1   Ima  test_bacc           2      0    42  0.500000  0.500000  0.500000  0.500000  0.500000  0.500000
2   Ima   test_acc           2      0    42  0.333333  0.333333  0.333333  0.375000  0.285714  0.332143
3   Ima   test_auc           2      1    82  0.576923  0.442308  0.730769  0.487179  0.555556  0.558547
4   Ima  test_bacc           2      1    82  0.500000  0.500000  0.500000  0.500000  0.500000  0.500000
5   Ima   test_acc           2      1    82  0.235294  0.235294  0.235294  0.187500  0.200000  0.218676
6   Ima   test_auc           3      0    19  0.333333  0.000000  0.500000  0.000000  0.000000  0.166667
7   Ima  test_bacc           3      0    19  0.500000  0.500000  0.500000  0.500000  0.500000  0.500000
8   Ima   test_acc           3      0    19  0.400000  0.400000  0.333333  0.333333  0.333333  0.360000
9   Ima   test_auc           3      1    67  0.424242  0.333333  0.181818  0.233333  0.300000  0.294545
10  Ima  test_bacc           3      1    67  0.500000  0.333333  0.500000  0.500000  0.500000  0.466667
11  Ima   test_acc           3      1    67  0.214286  0.142857  0.214286  0.230769  0.166667  0.193773
12  Ima   test_auc           3      2    38  0.666667  0.416667  0.000000  0.900000  0.000000  0.396667
13  Ima  test_bacc           3      2    38  0.500000  0.500000  0.500000  0.500000  0.500000  0.500000
14  Ima   test_acc           3      2    38  0.333333  0.250000  0.285714  0.285714  0.285714  0.288095

NOTHING

XTreatTivSitePca
   data      score  n_clusters  clust  size     fold0     fold1     fold2     fold3     fold4       avg
0   Ima   test_auc           2      0    42  0.722222  0.555556  0.444444  0.733333  0.300000  0.551111
1   Ima  test_bacc           2      0    42  0.500000  0.500000  0.500000  0.500000  0.500000  0.500000
2   Ima   test_acc           2      0    42  0.333333  0.333333  0.333333  0.375000  0.285714  0.332143
3   Ima   test_auc           2      1    82  0.576923  0.346154  0.615385  0.461538  0.472222  0.494444
4   Ima  test_bacc           2      1    82  0.500000  0.500000  0.500000  0.500000  0.500000  0.500000
5   Ima   test_acc           2      1    82  0.235294  0.235294  0.235294  0.187500  0.200000  0.218676
6   Ima   test_auc           3      0    19  0.333333  0.000000  1.000000  0.500000  0.000000  0.366667
7   Ima  test_bacc           3      0    19  0.500000  0.500000  0.500000  0.500000  0.500000  0.500000
8   Ima   test_acc           3      0    19  0.400000  0.400000  0.333333  0.333333  0.333333  0.360000
9   Ima   test_auc           3      1    67  0.424242  0.181818  0.151515  0.266667  0.200000  0.244848
10  Ima  test_bacc           3      1    67  0.500000  0.333333  0.500000  0.500000  0.500000  0.466667
11  Ima   test_acc           3      1    67  0.214286  0.142857  0.214286  0.230769  0.166667  0.193773
12  Ima   test_auc           3      2    38  0.722222  0.500000  0.300000  0.800000  0.300000  0.524444
13  Ima  test_bacc           3      2    38  0.500000  0.500000  0.500000  0.500000  0.500000  0.500000
14  Ima   test_acc           3      2    38  0.333333  0.250000  0.285714  0.285714  0.285714  0.288095

"""



###############################################################################
# Clustering Im classifiy ClinIm

clustering = pd.read_csv(os.path.join(INPUT, IMADATASET+"-clust.csv"))
#pop = pd.read_csv(os.path.join(INPUT,"population.csv"))
assert np.all(pop.participant_id == clustering.participant_id)

metrics.confusion_matrix(yorig, clustering["nclust=2"])

"""
array([[17, 15],
       [45, 47]])
"""

"""
Use mlxtend
http://rasbt.github.io/mlxtend/
conda install -c conda-forge mlxtend

https://rasbt.github.io/mlxtend/user_guide/classifier/StackingClassifier/
"""
from mlxtend.classifier import StackingClassifier
from mlxtend.feature_selection import ColumnSelector
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression

XClinIm = np.concatenate([Xclin, Xim], axis=1)

range_n_clusters = [2]
res = list()
for n_clusters in range_n_clusters:
    print("######################################")
    print("# nclust", n_clusters)
    cluster_labels = clustering["nclust=%i" % n_clusters]
    for clust in np.unique(cluster_labels):
        print("===================================")
        subset = cluster_labels == clust
        print(clust, subset.sum())
        Xg = XClinIm[subset, :]
        yg = yorig[subset]
        Xg = scaler.fit(Xg).transform(Xg)

        cv = StratifiedKFold(n_splits=NFOLDS)
        lr = lm.LogisticRegression(class_weight='balanced', fit_intercept=False, C=C)
        pipe1 = make_pipeline(ColumnSelector(cols=np.arange(0, Xclin.shape[1])),
                      copy.copy(lr))
        pipe2 = make_pipeline(ColumnSelector(cols=np.arange(Xclin.shape[1], XClinIm.shape[1])),
                              copy.copy(lr))
        model = StackingClassifier(classifiers=[pipe1, pipe2],
                                  meta_classifier=LogisticRegression())

        cv_results = cross_validate(estimator=copy.copy(model), X=Xg, y=yg, cv=cv, scoring=scorers, n_jobs=-1)
        res.append(['ClinIma', 'test_auc', n_clusters, clust, subset.sum()] + cv_results["test_auc"].tolist() + [cv_results["test_auc"].mean()])
        res.append(['ClinIma', 'test_bacc', n_clusters, clust, subset.sum()] + cv_results["test_bacc"].tolist() + [cv_results["test_bacc"].mean()])
        res.append(['ClinIma', 'test_acc', n_clusters, clust, subset.sum()] + cv_results["test_acc"].tolist() + [cv_results["test_acc"].mean()])


res = pd.DataFrame(res, columns=['data', 'score', 'n_clusters', 'clust', 'size'] + ["fold%i" % i for i in range(NFOLDS)] + ['avg'])
print(res)

"""
      data      score  n_clusters  clust  size     fold0     fold1     fold2     fold3     fold4       avg
0  ClinIma   test_auc           2      0    62  0.458333  0.486111  0.555556  0.611111  0.166667  0.455556
1  ClinIma  test_bacc           2      0    62  0.500000  0.500000  0.500000  0.500000  0.500000  0.500000
2  ClinIma   test_acc           2      0    62  0.307692  0.307692  0.250000  0.250000  0.250000  0.273077
3  ClinIma   test_auc           2      1    62  0.533333  0.466667  0.833333  0.833333  0.555556  0.644444
4  ClinIma  test_bacc           2      1    62  0.500000  0.500000  0.500000  0.500000  0.500000  0.500000
5  ClinIma   test_acc           2      1    62  0.230769  0.230769  0.250000  0.250000  0.250000  0.242308

NOTHING
"""
###############################################################################
# No Clustering / classifiy ImEnettv

import nibabel
import parsimony.algorithms as algorithms
import parsimony.estimators as estimators
import parsimony.functions.nesterov.tv as nesterov_tv
from parsimony.utils.linalgs import LinearOperatorNesterov

# Data
Xim = np.load(os.path.join(OUTPUT, IMADATASET + ".npy"))
yorig = np.load(os.path.join(OUTPUT, "y.npy"))
mask = nibabel.load(os.path.join(OUTPUT, "mask.nii.gz"))
# Atv = nesterov_tv.linear_operator_from_mask(mask.get_data(), calc_lambda_max=True)
# Atv.save(os.path.join(OUTPUT, "Atv.npz"))
Atv = LinearOperatorNesterov(filename=os.path.join(OUTPUT, "Atv.npz"))
#assert Atv.get_singular_values(0) == Atv_.get_singular_values(0)
assert np.allclose(Atv.get_singular_values(0), 11.956104408414376)

X = Xim.copy()
y = yorig.copy()

# parameters
key = 'enettv_0.1_0.1_0.8'.split("_")
algo, alpha, l1l2ratio, tvratio = key[0], float(key[1]), float(key[2]), float(key[3])
tv = alpha * tvratio
l1 = alpha * float(1 - tv) * l1l2ratio
l2 = alpha * float(1 - tv) * (1- l1l2ratio)

print(key, algo, alpha, l1, l2, tv)

scaler = preprocessing.StandardScaler()
X = scaler.fit(X).transform(X)

y_test_pred = np.zeros(len(y))
y_test_prob_pred = np.zeros(len(y))
y_test_decfunc_pred = np.zeros(len(y))
y_train_pred = np.zeros(len(y))
coefs_cv = np.zeros((NFOLDS, X.shape[1]))

auc_test = list()
recalls_test = list()

acc_test = list()

for cv_i, (train, test) in enumerate(cv.split(X, y)):
    #for train, test in cv.split(X, y, None):
    print(cv_i)
    X_train, X_test, y_train, y_test = X[train, :], X[test, :], y[train], y[test]
    #estimator = clone(model)
    conesta = algorithms.proximal.CONESTA(max_iter=10000)
    estimator = estimators.LogisticRegressionL1L2TV(l1, l2, tv, Atv, algorithm=conesta,
                                                    class_weight="auto", penalty_start=0)
    estimator.fit(X_train, y_train.ravel())
    # Store prediction for micro avg
    y_test_pred[test] = estimator.predict(X_test).ravel()
    y_test_prob_pred[test] = estimator.predict_probability(X_test).ravel()#[:, 1]
    #y_test_decfunc_pred[test] = estimator.decision_function(X_test)
    y_train_pred[train] = estimator.predict(X_train).ravel()
    # Compute score for macro avg
    auc_test.append(metrics.roc_auc_score(y_test, estimator.predict_probability(X_test).ravel()))
    recalls_test.append(metrics.recall_score(y_test, estimator.predict(X_test).ravel(), average=None))
    acc_test.append(metrics.accuracy_score(y_test, estimator.predict(X_test).ravel()))

    coefs_cv[cv_i, :] = estimator.beta.ravel()


np.savez_compressed(os.path.join(OUTPUT, IMADATASET+"_enettv_0.1_0.1_0.8_5cv.npz"),
                    coefs_cv=coefs_cv, y_pred=y_test_pred, y_true=y,
                    proba_pred=y_test_prob_pred, beta=coefs_cv)

# Micro Avg
recall_test_microavg = metrics.recall_score(y, y_test_pred, average=None)
recall_train_microavg = metrics.recall_score(y, y_train_pred, average=None)
bacc_test_microavg = recall_test_microavg.mean()
auc_test_microavg = metrics.roc_auc_score(y, y_test_prob_pred)
acc_test_microavg = metrics.accuracy_score(y, y_test_pred)

print("#", IMADATASET, X.shape)
print("#", auc_test_microavg, bacc_test_microavg, acc_test_microavg)

#print(auc_test_microavg, bacc_test_microavg, acc_test_microavg)
"""
XTreatTivSite
# 0.438519021739 0.451766304348 0.443548387097

XTreatTivSitePca

ICI NoPca RESULTS

"""

###############################################################################
# Clustering Im classifiy ImEnettv

import nibabel
import parsimony.algorithms as algorithms
import parsimony.estimators as estimators
import parsimony.functions.nesterov.tv as nesterov_tv
from parsimony.utils.linalgs import LinearOperatorNesterov

# Data
Xim = np.load(os.path.join(OUTPUT, IMADATASET + ".npy"))
yorig = np.load(os.path.join(OUTPUT, "y.npy"))
mask = nibabel.load(os.path.join(OUTPUT, "mask.nii.gz"))
# Atv = nesterov_tv.linear_operator_from_mask(mask.get_data(), calc_lambda_max=True)
# Atv.save(os.path.join(OUTPUT, "Atv.npz"))
Atv = LinearOperatorNesterov(filename=os.path.join(OUTPUT, "Atv.npz"))
#assert Atv.get_singular_values(0) == Atv_.get_singular_values(0)
assert np.allclose(Atv.get_singular_values(0), 11.956104408414376)

# Cluster
clustering = pd.read_csv(os.path.join(INPUT, IMADATASET+"-clust.csv"))
#pop = pd.read_csv(os.path.join(INPUT,"population.csv"))
assert np.all(pop.participant_id == clustering.participant_id)
metrics.confusion_matrix(yorig, clustering["nclust=2"])
"""
array([[ 6, 26],
       [31, 61]])
"""
CLUST = 1
subset = clustering["nclust=2"] == CLUST

X = Xim[subset, :]
y = yorig[subset]

# parameters
key = 'enettv_0.1_0.1_0.8'.split("_")
algo, alpha, l1l2ratio, tvratio = key[0], float(key[1]), float(key[2]), float(key[3])
tv = alpha * tvratio
l1 = alpha * float(1 - tv) * l1l2ratio
l2 = alpha * float(1 - tv) * (1- l1l2ratio)

print(key, algo, alpha, l1, l2, tv)

scaler = preprocessing.StandardScaler()
X = scaler.fit(X).transform(X)

y_test_pred = np.zeros(len(y))
y_test_prob_pred = np.zeros(len(y))
y_test_decfunc_pred = np.zeros(len(y))
y_train_pred = np.zeros(len(y))
coefs_cv = np.zeros((NFOLDS, X.shape[1]))

auc_test = list()
recalls_test = list()

acc_test = list()

for cv_i, (train, test) in enumerate(cv.split(X, y)):
    #for train, test in cv.split(X, y, None):
    print(cv_i)
    X_train, X_test, y_train, y_test = X[train, :], X[test, :], y[train], y[test]
    #estimator = clone(model)
    conesta = algorithms.proximal.CONESTA(max_iter=10000)
    estimator = estimators.LogisticRegressionL1L2TV(l1, l2, tv, Atv, algorithm=conesta,
                                                    class_weight="auto", penalty_start=0)
    estimator.fit(X_train, y_train.ravel())
    # Store prediction for micro avg
    y_test_pred[test] = estimator.predict(X_test).ravel()
    y_test_prob_pred[test] = estimator.predict_probability(X_test).ravel()#[:, 1]
    #y_test_decfunc_pred[test] = estimator.decision_function(X_test)
    y_train_pred[train] = estimator.predict(X_train).ravel()
    # Compute score for macro avg
    auc_test.append(metrics.roc_auc_score(y_test, estimator.predict_probability(X_test).ravel()))
    recalls_test.append(metrics.recall_score(y_test, estimator.predict(X_test).ravel(), average=None))
    acc_test.append(metrics.accuracy_score(y_test, estimator.predict(X_test).ravel()))

    coefs_cv[cv_i, :] = estimator.beta.ravel()

np.savez_compressed(os.path.join(OUTPUT,  IMADATASET+"-clust%i"%CLUST +"_enettv_0.1_0.1_0.8_5cv.npz"),
                    coefs_cv=coefs_cv, y_pred=y_test_pred, y_true=y,
                    proba_pred=y_test_prob_pred, beta=coefs_cv)

# Micro Avg
recall_test_microavg = metrics.recall_score(y, y_test_pred, average=None)
recall_train_microavg = metrics.recall_score(y, y_train_pred, average=None)
bacc_test_microavg = recall_test_microavg.mean()
auc_test_microavg = metrics.roc_auc_score(y, y_test_prob_pred)
acc_test_microavg = metrics.accuracy_score(y, y_test_pred)

print("#", IMADATASET+"-clust%i"%CLUST, X.shape)
print("#", auc_test_microavg, bacc_test_microavg, acc_test_microavg)

#
# YEAH !!

# XTreatTivSite-clust1
# 0.697872340426 0.678014184397 0.58064516129

# XTreatTivSitePca-clust1 (87, 397559)
# 0.465321563682 0.474148802018 0.448275862069

###############################################################################
# Clustering Im classifiy ClinImEnettv

import nibabel
import parsimony.algorithms as algorithms
import parsimony.estimators as estimators
import parsimony.functions.nesterov.tv as nesterov_tv
from parsimony.utils.linalgs import LinearOperatorNesterov


# Cluster
clustering = pd.read_csv(os.path.join(INPUT, IMADATASET+"-clust.csv"))
#pop = pd.read_csv(os.path.join(INPUT,"population.csv"))
assert np.all(pop.participant_id == clustering.participant_id)
metrics.confusion_matrix(yorig, clustering["nclust=2"])
CLUST = 1
subset = clustering["nclust=2"] == CLUST

# Data
Xim = np.load(os.path.join(OUTPUT, IMADATASET + ".npy"))
yorig = np.load(os.path.join(OUTPUT, "y.npy"))
mask = nibabel.load(os.path.join(OUTPUT, "mask.nii.gz"))
# Atv = nesterov_tv.linear_operator_from_mask(mask.get_data(), calc_lambda_max=True)
# Atv.save(os.path.join(OUTPUT, "Atv.npz"))
Atv = LinearOperatorNesterov(filename=os.path.join(OUTPUT, "Atv.npz"))
#assert Atv.get_singular_values(0) == Atv_.get_singular_values(0)
assert np.allclose(Atv.get_singular_values(0), 11.956104408414376)

scaler = preprocessing.StandardScaler()
Ximg = Xim[subset, :]
Xcling = Xclin[subset, :]
y = yorig[subset]
Ximg = scaler.fit(Ximg).transform(Ximg)
Xcling = scaler.fit(Xcling).transform(Xcling)

# Load models
modelscv = np.load(os.path.join(OUTPUT,  IMADATASET+"-clust%i"%CLUST +"_enettv_0.1_0.1_0.8_5cv.npz"))


# parameters
key = 'enettv_0.1_0.1_0.8'.split("_")
algo, alpha, l1l2ratio, tvratio = key[0], float(key[1]), float(key[2]), float(key[3])
tv = alpha * tvratio
l1 = alpha * float(1 - tv) * l1l2ratio
l2 = alpha * float(1 - tv) * (1- l1l2ratio)

print(key, algo, alpha, l1, l2, tv)

# CV loop

y_test_pred_img = np.zeros(len(y))
y_test_prob_pred_img = np.zeros(len(y))
y_test_decfunc_pred_img = np.zeros(len(y))
y_train_pred_img = np.zeros(len(y))
coefs_cv_img = np.zeros((NFOLDS, Ximg.shape[1]))
auc_test_img = list()
recalls_test_img = list()
acc_test_img = list()

y_test_pred_clin = np.zeros(len(y))
y_test_prob_pred_clin = np.zeros(len(y))
y_test_decfunc_pred_clin = np.zeros(len(y))
y_train_pred_clin = np.zeros(len(y))
coefs_cv_clin = np.zeros((NFOLDS, Xcling.shape[1]))
auc_test_clin = list()
recalls_test_clin = list()
acc_test_clin = list()

y_test_pred_stck = np.zeros(len(y))
y_test_prob_pred_stck = np.zeros(len(y))
y_test_decfunc_pred_stck = np.zeros(len(y))
y_train_pred_stck = np.zeros(len(y))
coefs_cv_stck = np.zeros((NFOLDS, 2))
auc_test_stck = list()
recalls_test_stck = list()
acc_test_stck = list()

for cv_i, (train, test) in enumerate(cv.split(Ximg, y)):
    #for train, test in cv.split(X, y, None):
    print(cv_i)
    X_train_img, X_test_img, y_train, y_test = Ximg[train, :], Ximg[test, :], y[train], y[test]
    X_train_clin, X_test_clin = Xcling[train, :], Xcling[test, :]

    # Im
    conesta = algorithms.proximal.CONESTA(max_iter=10000)
    estimator_img = estimators.LogisticRegressionL1L2TV(l1, l2, tv, Atv, algorithm=conesta,
                                                    class_weight="auto", penalty_start=0)
    estimator_img.beta = modelscv["coefs_cv"][cv_i][:, None]
    # Store prediction for micro avg
    y_test_pred_img[test] = estimator_img.predict(X_test_img).ravel()
    y_test_prob_pred_img[test] = estimator_img.predict_probability(X_test_img).ravel()#[:, 1]
    y_test_decfunc_pred_img[test] = np.dot(X_test_img, estimator_img.beta).ravel()
    y_train_pred_img[train] = estimator_img.predict(X_train_img).ravel()
    # Compute score for macro avg
    auc_test_img.append(metrics.roc_auc_score(y_test, estimator_img.predict_probability(X_test_img).ravel()))
    recalls_test_img.append(metrics.recall_score(y_test, estimator_img.predict(X_test_img).ravel(), average=None))
    acc_test_img.append(metrics.accuracy_score(y_test, estimator_img.predict(X_test_img).ravel()))
    coefs_cv_img[cv_i, :] = estimator_img.beta.ravel()

    # Clin
    estimator_clin = lm.LogisticRegression(class_weight='balanced', fit_intercept=False, C=C)
    estimator_clin.fit(X_train_clin, y_train)
    y_test_pred_clin[test] = estimator_clin.predict(X_test_clin).ravel()
    y_test_prob_pred_clin[test] =  estimator_clin.predict_proba(X_test_clin)[:, 1]
    y_test_decfunc_pred_clin[test] = estimator_clin.decision_function(X_test_clin)
    y_train_pred_clin[train] = estimator_clin.predict(X_train_clin).ravel()
    # Compute score for macro avg
    auc_test_clin.append(metrics.roc_auc_score(y_test, estimator_clin.predict_proba(X_test_clin)[:, 1]))
    recalls_test_clin.append(metrics.recall_score(y_test, estimator_clin.predict(X_test_clin).ravel(), average=None))
    acc_test_clin.append(metrics.accuracy_score(y_test, estimator_clin.predict(X_test_clin).ravel()))
    coefs_cv_clin[cv_i, :] = estimator_clin.coef_.ravel()

    # Stacking
    X_train_stck = np.c_[
            np.dot(X_train_img, estimator_img.beta).ravel(),
            estimator_clin.decision_function(X_train_clin).ravel()]
    X_test_stck = np.c_[
            np.dot(X_test_img, estimator_img.beta).ravel(),
            estimator_clin.decision_function(X_test_clin).ravel()]
    X_train_stck = scaler.fit(X_train_stck).transform(X_train_stck)
    X_test_stck = scaler.transform(X_test_stck)

    #
    estimator_stck = lm.LogisticRegression(class_weight='balanced', fit_intercept=False, C=100)
    estimator_stck.fit(X_train_stck, y_train)
    y_test_pred_stck[test] = estimator_stck.predict(X_test_stck).ravel()
    y_test_prob_pred_stck[test] =  estimator_stck.predict_proba(X_test_stck)[:, 1]
    y_test_decfunc_pred_stck[test] = estimator_stck.decision_function(X_test_stck)
    y_train_pred_stck[train] = estimator_stck.predict(X_train_stck).ravel()
    # Compute score for macro avg
    auc_test_stck.append(metrics.roc_auc_score(y_test, estimator_stck.predict_proba(X_test_stck)[:, 1]))
    recalls_test_stck.append(metrics.recall_score(y_test, estimator_stck.predict(X_test_stck).ravel(), average=None))
    acc_test_stck.append(metrics.accuracy_score(y_test, estimator_stck.predict(X_test_stck).ravel()))
    coefs_cv_stck[cv_i, :] = estimator_stck.coef_.ravel()


print("#", IMADATASET+"-clust%i"%CLUST, Ximg.shape)

# Micro Avg Img
recall_test_img_microavg = metrics.recall_score(y, y_test_pred_img, average=None)
recall_train_img_microavg = metrics.recall_score(y, y_train_pred_img, average=None)
bacc_test_img_microavg = recall_test_img_microavg.mean()
auc_test_img_microavg = metrics.roc_auc_score(y, y_test_prob_pred_img)
acc_test_img_microavg = metrics.accuracy_score(y, y_test_pred_img)

print("#", auc_test_img_microavg, bacc_test_img_microavg, acc_test_img_microavg)
# 0.697872340426 0.678014184397 0.58064516129

# Micro Avg Clin
recall_test_clin_microavg = metrics.recall_score(y, y_test_pred_clin, average=None)
recall_train_clin_microavg = metrics.recall_score(y, y_train_pred_clin, average=None)
bacc_test_clin_microavg = recall_test_clin_microavg.mean()
auc_test_clin_microavg = metrics.roc_auc_score(y, y_test_prob_pred_clin)
acc_test_clin_microavg = metrics.accuracy_score(y, y_test_pred_clin)

print("#", auc_test_clin_microavg, bacc_test_clin_microavg, acc_test_clin_microavg)
# 0.723404255319 0.641843971631 0.629032258065

# Micro Avg Stacking
recall_test_stck_microavg = metrics.recall_score(y, y_test_pred_stck, average=None)
recall_train_stck_microavg = metrics.recall_score(y, y_train_pred_stck, average=None)
bacc_test_stck_microavg = recall_test_stck_microavg.mean()
auc_test_stck_microavg = metrics.roc_auc_score(y, y_test_prob_pred_stck)
acc_test_stck_microavg = metrics.accuracy_score(y, y_test_pred_stck)

print("#", auc_test_stck_microavg, bacc_test_stck_microavg, acc_test_stck_microavg)


# Save
df = democlin.copy()
df["participant_id"] = pop.participant_id
df["respond_wk16"] = pop.respond_wk16

# Cluster
clustering = pd.read_csv(os.path.join(INPUT, IMADATASET+"-clust.csv"))
assert(np.all(clustering.participant_id == df["participant_id"]))
df["cluster"] = clustering["nclust=2"]

df.loc[df["cluster"] == 1, "y_test_pred_img"] = y_test_pred_img
df.loc[df["cluster"] == 1, "y_test_prob_pred_img"] = y_test_prob_pred_img
df.loc[df["cluster"] == 1, "y_test_decfunc_pred_img"] = y_test_decfunc_pred_img

df.loc[df["cluster"] == 1, "y_test_pred_clin"] = y_test_pred_clin
df.loc[df["cluster"] == 1, "y_test_prob_pred_clin"] = y_test_prob_pred_clin
df.loc[df["cluster"] == 1, "y_test_decfunc_pred_clin"] = y_test_decfunc_pred_clin

df.loc[df["cluster"] == 1, "y_test_pred_stck"] = y_test_pred_stck
df.loc[df["cluster"] == 1, "y_test_prob_pred_stck"] = y_test_prob_pred_stck
df.loc[df["cluster"] == 1, "y_test_decfunc_pred_stck"] = y_test_decfunc_pred_stck

df.to_csv(os.path.join(OUTPUT,  IMADATASET+"-clust%i"%CLUST +"_demo-clin-imputed-decisionfunction.csv"), index=False)

# 0.739007092199 0.68865248227 0.596774193548

# YEAH !!!
# XTreatTivSite-clust1 (62, 397559)
# 0.697872340426 0.678014184397 0.58064516129
# 0.723404255319 0.641843971631 0.629032258065
# 0.739007092199 0.68865248227 0.596774193548

# Some test on C
# C=0.1
# 0.748936170213 0.656737588652 0.548387096774

# C=1
# 0.73475177305 0.656737588652 0.548387096774

# C=10
# 0.736170212766 0.678014184397 0.58064516129

# C=100
# 0.739007092199 0.68865248227 0.596774193548

# C=1000
# 0.737588652482 0.68865248227 0.596774193548


###############################################################################
# Caracterize Cluster 1/2: scatterplot Clinic vs image
# Run first Clustering Im classifiy ClinImEnettv
df = pd.read_csv(os.path.join(OUTPUT,  IMADATASET+"-clust%i"%CLUST +"_demo-clin-imputed-decisionfunction.csv"))


sns.lmplot(x="y_test_prob_pred_clin", y="y_test_prob_pred_img", hue="respond_wk16" , data=df, fit_reg=False)
sns.lmplot(x="y_test_decfunc_pred_clin", y="y_test_decfunc_pred_img", hue="respond_wk16" , data=df, fit_reg=False)
#sns.jointplot(x=df["decfunc_pred_clin_clust1"], y=df["decfunc_pred_img_clust1"], color="respond_wk16", kind='scatter')

sns.distplot(df["y_test_prob_pred_clin"][(df.cluster == 1) & (df["respond_wk16"] == "Responder")], rug=True, color="red")
sns.distplot(df["y_test_prob_pred_clin"][(df.cluster == 1) & (df["respond_wk16"] == "NonResponder")], rug=True, color="blue")
# Or
sns.kdeplot(df["y_test_prob_pred_clin"][(df.cluster == 1) & (df["respond_wk16"] == "Responder")],  color="red")
sns.kdeplot(df["y_test_prob_pred_clin"][(df.cluster == 1) & (df["respond_wk16"] == "NonResponder")],  color="blue")

sns.distplot(df["y_test_prob_pred_img"][(df.cluster == 1) & (df["respond_wk16"] == "Responder")], rug=True, color="red")
sns.distplot(df["y_test_prob_pred_img"][(df.cluster == 1) & (df["respond_wk16"] == "NonResponder")], rug=True, color="blue")
# Or
sns.kdeplot(df["y_test_prob_pred_img"][(df.cluster == 1) & (df["respond_wk16"] == "Responder")], color="red")
sns.kdeplot(df["y_test_prob_pred_img"][(df.cluster == 1) & (df["respond_wk16"] == "NonResponder")], color="blue")

sns.distplot(df["y_test_decfunc_pred_stck"][(df.cluster == 1) & (df["respond_wk16"] == "Responder")], rug=True, color="red")
sns.distplot(df["y_test_decfunc_pred_stck"][(df.cluster == 1) & (df["respond_wk16"] == "NonResponder")], rug=True, color="blue")
# or
sns.kdeplot(df["y_test_decfunc_pred_stck"][(df.cluster == 1) & (df["respond_wk16"] == "Responder")], color="red")
sns.kdeplot(df["y_test_decfunc_pred_stck"][(df.cluster == 1) & (df["respond_wk16"] == "NonResponder")], color="blue")

assert np.all(yorig == df.respond_wk16.map({'NonResponder':0, 'Responder':1}))

dfclust1 = df.loc[(df.cluster == 1), ['y_test_prob_pred_clin', 'y_test_prob_pred_img', "respond_wk16"]]
X = np.array(dfclust1[['y_test_prob_pred_clin', 'y_test_prob_pred_img']])
y = np.array(dfclust1.respond_wk16.map({'NonResponder':0, 'Responder':1}))
#scaler = preprocessing.StandardScaler()
#X = scaler.fit(X).transform(X)
estimator_stck = lm.LogisticRegression(class_weight='balanced', fit_intercept=True, C=100)
estimator_stck.fit(X, y)

recall_post_stck_microavg = metrics.recall_score(y, estimator_stck.predict(X), average=None)
bacc_post_stck_microavg = recall_post_stck_microavg.mean()
auc_post_stck_microavg = metrics.roc_auc_score(y, estimator_stck.predict_proba(X)[:, 1])
acc_post_stck_microavg = metrics.accuracy_score(y,  estimator_stck.predict(X))

print("#", auc_post_stck_microavg, bacc_post_stck_microavg, acc_post_stck_microavg, recall_post_stck_microavg)
# 0.782978723404 0.717730496454 0.709677419355 [ 0.73333333  0.70212766]

estimator_stck.coef_
# array([[ 5.5799257 ,  2.60588734]])
estimator_stck.intercept_
# Out[227]: array([-3.70611507])

df.loc[df.cluster == 1, "y_post_decfunc_pred_stck"] = estimator_stck.decision_function(X)
df.loc[df.cluster == 1, "y_post_prob_pred_stck"] = estimator_stck.predict_proba(X)[:, 1]


# contour
# https://matplotlib.org/1.3.0/examples/pylab_examples/contour_demo.html

nx = ny = 100
x = np.linspace(0.1, 0.7, num=nx)
y = np.linspace(0.0, 0.9, num=ny)
xx, yy = np.meshgrid(x, y)
z_proba = estimator_stck.predict_proba(np.c_[xx.ravel(), yy.ravel()])[:, 1]
z_proba = z_proba.reshape(xx.shape)

palette = {"NonResponder":sns.xkcd_rgb["denim blue"], "Responder":sns.xkcd_rgb["pale red"]}
palette = {"NonResponder":"blue", "Responder":"red"}

g = sns.JointGrid(x="y_test_prob_pred_clin", y="y_test_prob_pred_img", data=df)
g.ax_joint.scatter(df["y_test_prob_pred_clin"], df["y_test_prob_pred_img"], c=[palette[res] for res in df.respond_wk16])
#sns.lmplot(x="y_test_prob_pred_clin", y="y_test_prob_pred_img", hue="respond_wk16" , data=df, fit_reg=False, palette=palette, axis=g.ax_joint)
CS = g.ax_joint.contour(xx, yy, z_proba, 6, levels=[0.5], colors='k', axis=g.ax_joint)
plt.clabel(CS, fontsize=9, inline=1)

"""
#sns.distplot(df.loc["y_test_prob_pred_clin"], kde=True, hist=False, color="r", ax=g.ax_marg_x)
sns.kdeplot(df["y_test_prob_pred_clin"][(df.cluster == 1) & (df["respond_wk16"] == "NonResponder")], bw=.05,
             color=palette["NonResponder"], ax=g.ax_marg_x, label="NonResponder")
sns.kdeplot(df["y_test_prob_pred_clin"][(df.cluster == 1) & (df["respond_wk16"] == "Responder")], bw=.05,
             color=palette["Responder"], ax=g.ax_marg_x, label="Responder")
sns.kdeplot(df["y_test_prob_pred_img"][(df.cluster == 1) & (df["respond_wk16"] == "NonResponder")],  bw=.1,
             color=palette["NonResponder"], ax=g.ax_marg_y, vertical=True, label="NonResponder")
sns.kdeplot(df["y_test_prob_pred_img"][(df.cluster == 1) & (df["respond_wk16"] == "Responder")],  bw=.05,
             color=palette["Responder"], ax=g.ax_marg_y, vertical=True, label="Responder")
"""
g.ax_joint.set_xlim(0.0, .8)
g.ax_joint.set_ylim(0.0, 1)

from matplotlib.transforms import Affine2D
import mpl_toolkits.axisartist.floating_axes as floating_axes

fig = plt.figure()

plot_extents = 0, 10, 0, 10
transform = Affine2D().rotate_deg(45)
helper = floating_axes.GridHelperCurveLinear(transform, plot_extents)
ax = floating_axes.FloatingSubplot(fig, 111, grid_helper=helper)

sns.kdeplot(df["y_post_prob_pred_stck"][(df.cluster == 1) & (df["respond_wk16"] == "Responder")],
            color=palette["Responder"], shade=True, label="Responder", ax=ax)
sns.kdeplot(df["y_post_prob_pred_stck"][(df.cluster == 1) & (df["respond_wk16"] == "NonResponder")],
            color=palette["NonResponder"], shade=True, label="NonResponder", ax=ax)

fig.add_subplot(ax)
plt.show()



"""
sns.distplot(df["y_test_prob_pred_clin"][(df.cluster == 1) & (df["respond_wk16"] == "NonResponder")], kde=True, hist=False,
             color=palette["NonResponder"], ax=g.ax_marg_x)
sns.distplot(df["y_test_prob_pred_clin"][(df.cluster == 1) & (df["respond_wk16"] == "Responder")], kde=True, hist=False,
             color=palette["Responder"], ax=g.ax_marg_x)
sns.distplot(df["y_test_prob_pred_img"][(df.cluster == 1) & (df["respond_wk16"] == "NonResponder")], kde=True, hist=False,
             color=palette["NonResponder"], ax=g.ax_marg_y, vertical=True)
sns.distplot(df["y_test_prob_pred_img"][(df.cluster == 1) & (df["respond_wk16"] == "Responder")], kde=True, hist=False,
             color=palette["Responder"], ax=g.ax_marg_y, vertical=True)
"""

#plt.clabel(CS, fontsize=9, inline=1)

#plt.clabel(CS)
#plt.clabel(CS, fontsize=9, inline=1)
# plt.plot([0, 4], [1.5, 0], linewidth=2)

# density left an top
# https://stackoverflow.com/questions/49671053/seaborn-changing-line-styling-in-kdeplot

###############################################################################
import os
import seaborn as sns
import pandas as pd

from matplotlib.backends.backend_pdf import PdfPages

df = pd.read_csv(os.path.join(INPUT, DATASET+"-clust.csv"))
pop = pd.read_csv(os.path.join(INPUT, "population.csv"))
df = pd.merge(df, pop)
assert df.shape[0] == 124

df["cluster"] = df['nclust=2']
pdf = PdfPages(os.path.join(OUTPUT, DATASET+'-clust.pdf'))

fig = plt.figure()
#fig.suptitle('Cluster x GMratio')
sns.set(style="whitegrid")
sns.violinplot(x="cluster", y="GMratio", hue="respond_wk16", data=df, split=True, label=None, legend_out = True)
sns.swarmplot(x="cluster", y="GMratio", hue="respond_wk16", data=df,  dodge=True, linewidth=1, edgecolor='black')
plt.legend(loc='lower right')

pdf.savefig(); plt.close()

fig = plt.figure()
#fig.suptitle('Cluster x GMratio')
sns.lmplot(x="age", y="GMratio", hue="cluster", data=df)
pdf.savefig(); plt.close()

fig = plt.figure()
sns.lmplot(x="psyhis_mdd_age", y="GMratio", hue="cluster" , data=df, fit_reg=False)
pdf.savefig(); plt.close()

fig = plt.figure()
df_nona = df.copy()
df_nona.loc[df_nona["psyhis_mdd_age"].isnull(), "psyhis_mdd_age"] = df_nona["psyhis_mdd_age"].mean()
g = sns.PairGrid(df_nona[["GMratio", "age", "psyhis_mdd_age", "cluster", "respond_wk16"]], hue="cluster")
g.map_diag(plt.hist)
g.map_offdiag(plt.scatter)
pdf.savefig(); plt.close()


fig = plt.figure()
sns.lmplot(x="age", y="GMratio", hue="respond_wk16", col="cluster", data=df, fit_reg=False)
pdf.savefig(); plt.close()

"""
#sns.lmplot(x="test_decfunc", y="GMratio", hue="respond_wk16", col="cluster", data=df, fit_reg=False)
fig = plt.figure()
tmp = df[["test_decfunc-clust-1", "respond_wk16", "cluster", "GMratio", "psyhis_mdd_age", "age"]].dropna()
sns.distplot(tmp["test_decfunc-clust-1"][tmp["respond_wk16"] == "Responder"], rug=True, color="red")
sns.distplot(tmp["test_decfunc-clust-1"][tmp["respond_wk16"] == "NonResponder"], rug=True, color="blue")
pdf.savefig(); plt.close()

fig = plt.figure()
sns.lmplot(x="test_decfunc-clust-1", y="GMratio", hue="respond_wk16" , data=tmp, fit_reg=False)
pdf.savefig(); plt.close()

fig = plt.figure()
sns.lmplot(x="test_decfunc-clust-1", y="psyhis_mdd_age", hue="respond_wk16" , data=tmp, fit_reg=False)
pdf.savefig(); plt.close()

fig = plt.figure()
sns.lmplot(x="test_decfunc-clust-1", y="age", hue="respond_wk16" , data=tmp, fit_reg=False)
pdf.savefig(); plt.close()

fig = plt.figure()
tmp = df[["test_decfunc", "respond_wk16", "GMratio", "psyhis_mdd_age", "age"]]
sns.distplot(tmp["test_decfunc"][tmp["respond_wk16"] == "Responder"], rug=True, color="red")
sns.distplot(tmp["test_decfunc"][tmp["respond_wk16"] == "NonResponder"], rug=True, color="blue")
pdf.savefig(); plt.close()

fig = plt.figure()
sns.lmplot(x="test_decfunc", y="GMratio", hue="respond_wk16" , data=tmp, fit_reg=False)
pdf.savefig(); plt.close()

fig = plt.figure()
sns.lmplot(x="test_decfunc", y="psyhis_mdd_age", hue="respond_wk16" , data=tmp, fit_reg=False)
pdf.savefig(); plt.close()

fig = plt.figure()
sns.lmplot(x="test_decfunc", y="age", hue="respond_wk16" , data=tmp, fit_reg=False)
pdf.savefig(); plt.close()
"""
pdf.close()


###############################################################################
#Clustering Im-clust1 learn ClinImEnettv Im-clust1 predict Im-clust0
TODO
import nibabel
import parsimony.algorithms as algorithms
import parsimony.estimators as estimators
import parsimony.functions.nesterov.tv as nesterov_tv
from parsimony.utils.linalgs import LinearOperatorNesterov


# Cluster
clustering = pd.read_csv(os.path.join(INPUT, IMADATASET+"-clust.csv"))
#pop = pd.read_csv(os.path.join(INPUT,"population.csv"))
assert np.all(pop.participant_id == clustering.participant_id)
metrics.confusion_matrix(yorig, clustering["nclust=2"])
"""
array([[17, 15],
       [45, 47]])
"""
CLUST = 1
subset1 = clustering["nclust=2"] == CLUST
subset0 = clustering["nclust=2"] == 0

# Data
Xim = np.load(os.path.join(OUTPUT, IMADATASET + ".npy"))
yorig = np.load(os.path.join(OUTPUT, "y.npy"))
mask = nibabel.load(os.path.join(OUTPUT, "mask.nii.gz"))
# Atv = nesterov_tv.linear_operator_from_mask(mask.get_data(), calc_lambda_max=True)
# Atv.save(os.path.join(OUTPUT, "Atv.npz"))
Atv = LinearOperatorNesterov(filename=os.path.join(OUTPUT, "Atv.npz"))
#assert Atv.get_singular_values(0) == Atv_.get_singular_values(0)
assert np.allclose(Atv.get_singular_values(0), 11.956104408414376)

scaler_img = preprocessing.StandardScaler()
scaler_clin = preprocessing.StandardScaler()

# clust1
Ximg1 = Xim[subset1, :]
Xcling1 = Xclin[subset1, :]
y1 = yorig[subset1]
Ximg1 = scaler_img.fit(Ximg1).transform(Ximg1)
Xcling1 = scaler_clin.fit(Xcling1).transform(Xcling1)
[np.sum(y1 == lev) for lev in np.unique(y1)]

# clust0
Ximg0 = Xim[subset0, :]
Xcling0 = Xclin[subset0, :]
y0 = yorig[subset0]
Ximg0 = scaler_img.fit(Ximg0).transform(Ximg0)
Xcling0 = scaler_clin.fit(Xcling0).transform(Xcling0)
[np.sum(y0 == lev) for lev in np.unique(y0)]

# Load models
modelscv = np.load(os.path.join(OUTPUT,  IMADATASET+"-clust%i"%CLUST +"_enettv_0.1_0.1_0.8_5cv.npz"))

# parameters
key = 'enettv_0.1_0.1_0.8'.split("_")
algo, alpha, l1l2ratio, tvratio = key[0], float(key[1]), float(key[2]), float(key[3])
tv = alpha * tvratio
l1 = alpha * float(1 - tv) * l1l2ratio
l2 = alpha * float(1 - tv) * (1- l1l2ratio)
print(key, algo, alpha, l1, l2, tv)


conesta = algorithms.proximal.CONESTA(max_iter=10000)
estimator_img = estimators.LogisticRegressionL1L2TV(l1, l2, tv, Atv, algorithm=conesta,
                                                class_weight="auto", penalty_start=0)
estimator_img.fit(Ximg0, y0)
coef_all_clust0 = estimator_img.beta

estimator_img.fit(Ximg1, y1)
coef_all_clust1 = estimator_img.beta

modelscv.keys()
['coefs_cv', 'y_pred', 'y_true', 'proba_pred', 'beta']

np.savez_compressed(os.path.join(OUTPUT,  IMADATASET+"-clust%i"%CLUST +"_enettv_0.1_0.1_0.8_5cv.npz"),
                    coefs_cv=modelscv["coefs_cv"], y_pred=modelscv["y_pred"], y_true=modelscv["y_true"],
                    proba_pred=modelscv["proba_pred"],
                    coef_refitall_clust0=coef_all_clust0.ravel(), coef_refitall_clust1=coef_all_clust1.ravel())

"""
modelscv = np.load(os.path.join(OUTPUT,  IMADATASET+"-clust%i"%CLUST +"_enettv_0.1_0.1_0.8_5cv.npz"))
modelscv_["coefs_cv"] == modelscv["coefs_cv"]
modelscv[
#estimator_img.beta = modelscv["coefs_cv"].mean(axis=0)[:, None]
modelscv.keys()
"""

# Store prediction for micro avg
y_clust0_pred_img = estimator_img.predict(Ximg0).ravel()
y_clust0_prob_pred_img = estimator_img.predict_probability(Ximg0).ravel()#[:, 1]
y_clust0_decfunc_pred_img = np.dot(Ximg0, estimator_img.beta).ravel()
y_clust1_pred_img = estimator_img.predict(Ximg1).ravel()

# Compute score for macro avg
print("#",
    metrics.roc_auc_score(y0, y_clust0_prob_pred_img),
    metrics.recall_score(y0, y_clust0_pred_img, average=None),
    metrics.accuracy_score(y0, y_clust0_pred_img))

# 0.481045751634 [ 0.52941176  0.55555556] 0.548387096774
# Boff

    # Stack
###############################################################################
# OLDIES

CLUSTER = 1
subset = clustering.cluster == CLUSTER
if DATASET == "XTreatTivSite-ClinIm":
    X = np.concatenate([Xclin, Xim], axis=1)
if DATASET == "XTreatTivSite-Im":
    X = np.copy(Xim)
#X = np.concatenate([Xclin, Xim], axis=1)
X = X[subset, :]
y = yorig[subset]

X = scaler.fit(X).transform(X)

model.fit(X, y)
model.coef_

# clustering
NFOLDS = 5
C = 0.1 if X.shape[0] == 62 else 1

# All
def balanced_acc(estimator, X, y):
    return metrics.recall_score(y, estimator.predict(X), average=None).mean()
scorers = {'auc': 'roc_auc', 'bacc':balanced_acc, 'acc':'accuracy'}

cv = StratifiedKFold(n_splits=NFOLDS)
model = lm.LogisticRegression(class_weight='balanced', fit_intercept=False, C=C)
estimator = model
%time cv_results = cross_validate(estimator=model, X=X, y=y, cv=cv, scoring=scorers, n_jobs=-1)
print(
      cv_results["test_auc"], cv_results["test_auc"].mean(), "\n",
      cv_results["test_bacc"], cv_results["test_bacc"].mean(), "\n",
      cv_results["test_acc"], cv_results["test_acc"].mean())



XTreatTivSite-ClinIm
[ 0.48120301  0.57894737  0.66666667  0.43518519  0.77777778] 0.587956001114
[ 0.42857143  0.5         0.5         0.5         0.5       ] 0.485714285714
[ 0.23076923  0.26923077  0.25        0.25        0.25      ] 0.25

XTreatTivSite-ClinIm-clust-1
[ 0.43333333  0.86666667  0.88888889  0.81481481  0.44444444] 0.68962962963
[ 0.5  0.5  0.5  0.5  0.5] 0.5
[ 0.23076923  0.23076923  0.25        0.25        0.25      ] 0.242307692308

XTreatTivSite-Im-clust-1

[ 0.43333333  0.86666667  0.88888889  0.81481481  0.44444444] 0.68962962963
[ 0.5  0.5  0.5  0.5  0.5] 0.5
[ 0.23076923  0.23076923  0.25        0.25        0.25      ] 0.242307692308
"""

"""
    %time scores_auc = cross_val_score(estimator=model, X=X, y=y, cv=cv, scoring='roc_auc', n_jobs=-1)
    print(model, "\n", scores_auc, scores_auc.mean())
    %time scores_bacc = cross_val_score(estimator=model, X=X, y=y, cv=cv, scoring=balanced_acc, n_jobs=-1)
    np.mean(scores_bacc)

    X_, y_, groups_ = indexable(X, y, None)
    cv_ = check_cv(cv, y, classifier=is_classifier(estimator))
    scorers, _ = _check_multimetric_scoring(estimator, scoring='roc_auc')
    scorer = check_scoring(estimator, scoring='roc_auc')
    scorer(estimator, X_test, y_test)
    metrics.roc_auc_score(y_test, estimator.predict(X_test))

y_test_pred = np.zeros(len(y))
y_test_prob_pred = np.zeros(len(y))
y_test_decfunc_pred = np.zeros(len(y))
y_train_pred = np.zeros(len(y))
coefs_cv = np.zeros((NFOLDS, X.shape[1]))

auc_test = list()
recalls_test = list()
acc_test = list()

for cv_i, (train, test) in enumerate(cv.split(X, y)):
    #for train, test in cv.split(X, y, None):
    print(cv_i)
    X_train, X_test, y_train, y_test = X[train, :], X[test, :], y[train], y[test]
    #estimator = clone(model)
    estimator = lm.LogisticRegression(class_weight='balanced', fit_intercept=False, C=C)
    estimator.fit(X_train, y_train)
    # Store prediction for micro avg
    y_test_pred[test] = estimator.predict(X_test)
    y_test_prob_pred[test] = estimator.predict_proba(X_test)[:, 1]
    y_test_decfunc_pred[test] = estimator.decision_function(X_test)
    y_train_pred[train] = estimator.predict(X_train)
    # Compute score for macro avg
    auc_test.append(metrics.roc_auc_score(y_test, estimator.predict_proba(X_test)[:, 1]))
    recalls_test.append(metrics.recall_score(y_test, estimator.predict(X_test), average=None))
    acc_test.append(metrics.accuracy_score(y_test, estimator.predict(X_test)))

    coefs_cv[cv_i, :] = estimator.coef_

# Macro Avg
auc_test = np.array(auc_test)
recalls_test = np.array(recalls_test)
acc_test = np.array(acc_test)

# Micro Avg
recall_test_microavg = metrics.recall_score(y, y_test_pred, average=None)
recall_train_microavg = metrics.recall_score(y, y_train_pred, average=None)
bacc_test_microavg = recall_test_microavg.mean()
auc_test_microavg = metrics.roc_auc_score(y, y_test_prob_pred)
acc_test_microavg = metrics.accuracy_score(y, y_test_pred)

print("AUC (Macro-cross_validate/Macro-manual-loop/Micro-manual-loop)")
print(cv_results["test_auc"], cv_results["test_auc"].mean())
print(auc_test, auc_test.mean())
print(auc_test_microavg)
import scipy.stats as stats
print(stats.mannwhitneyu(y_test_decfunc_pred[y == 0], y_test_decfunc_pred[y == 1]))

print("bAcc (Macro-cross_validate/Macro-manual-loop/Micro-manual-loop)")
print(cv_results["test_bacc"], cv_results["test_bacc"].mean())
print(recalls_test.mean(axis=1), recalls_test.mean(axis=1).mean())
print(bacc_test_microavg)

print("Acc (Macro-cross_validate/Macro-manual-loop/Micro-manual-loop)")
print(cv_results["test_acc"], cv_results["test_acc"].mean())
print(acc_test, acc_test.mean())
print(acc_test_microavg)



df = pd.read_csv(os.path.join(INPUT, DATASET+"-clust.csv"))

if X.shape[0] == 62:
    df["test_decfunc-clust-1"] = np.NaN
    df.loc[df.cluster == CLUSTER, "test_decfunc-clust-1"] = y_test_decfunc_pred

if X.shape[0] == 124:
    df["test_decfunc"] = y_test_decfunc_pred

df.to_csv(os.path.join(INPUT, DATASET+"-clust.csv"), index=False)

"""
XTreatTivSite-ClinIm
AUC (Macro-cross_validate/Macro-manual-loop/Micro-manual-loop)
[ 0.48120301  0.57894737  0.66666667  0.43518519  0.77777778] 0.587956001114
[ 0.48120301  0.57894737  0.66666667  0.43518519  0.77777778] 0.587956001114
0.547214673913
MannwhitneyuResult(statistic=1333.0, pvalue=0.21450387817058197)
bAcc (Macro-cross_validate/Macro-manual-loop/Micro-manual-loop)
[ 0.42857143  0.5         0.5         0.5         0.5       ] 0.485714285714
[ 0.42857143  0.5         0.5         0.5         0.5       ] 0.485714285714
0.484375
Acc (Macro-cross_validate/Macro-manual-loop/Micro-manual-loop)
[ 0.23076923  0.26923077  0.25        0.25        0.25      ] 0.25
[ 0.23076923  0.26923077  0.25        0.25        0.25      ] 0.25
0.25

XTreatTivSite-ClinIm-clust-1
AUC (Macro-cross_validate/Macro-manual-loop/Micro-manual-loop)
[ 0.43333333  0.86666667  0.88888889  0.81481481  0.44444444] 0.68962962963
[ 0.43333333  0.86666667  0.88888889  0.81481481  0.44444444] 0.68962962963
0.651063829787
MannwhitneyuResult(statistic=246.0, pvalue=0.040724923246777296)
bAcc (Macro-cross_validate/Macro-manual-loop/Micro-manual-loop)
[ 0.5  0.5  0.5  0.5  0.5] 0.5
[ 0.5  0.5  0.5  0.5  0.5] 0.5
0.5
Acc (Macro-cross_validate/Macro-manual-loop/Micro-manual-loop)
[ 0.23076923  0.23076923  0.25        0.25        0.25      ] 0.242307692308
[ 0.23076923  0.23076923  0.25        0.25        0.25      ] 0.242307692308
0.241935483871

XTreatTivSite-Im-clust-1
AUC (Macro-cross_validate/Macro-manual-loop/Micro-manual-loop)
[ 0.43333333  0.86666667  0.88888889  0.81481481  0.44444444] 0.68962962963
[ 0.43333333  0.86666667  0.88888889  0.81481481  0.44444444] 0.68962962963
0.651063829787
MannwhitneyuResult(statistic=246.0, pvalue=0.040724923246777296)
bAcc (Macro-cross_validate/Macro-manual-loop/Micro-manual-loop)
[ 0.5  0.5  0.5  0.5  0.5] 0.5
[ 0.5  0.5  0.5  0.5  0.5] 0.5
0.5
Acc (Macro-cross_validate/Macro-manual-loop/Micro-manual-loop)
[ 0.23076923  0.23076923  0.25        0.25        0.25      ] 0.242307692308
[ 0.23076923  0.23076923  0.25        0.25        0.25      ] 0.242307692308
0.241935483871
"""
###############################################################################
# Stack demo with Ima

X = np.concatenate([Xclin[subset, :], y_test_decfunc_pred[:, None]], axis=1)
X = Xclin[subset, :]
#X = Xclin.copy()
#y = yorig.copy()
X = scaler.fit(X).transform(X)

cv = StratifiedKFold(n_splits=NFOLDS)
model = lm.LogisticRegression(class_weight='balanced', fit_intercept=False, C=C)

estimator = model
%time cv_results = cross_validate(estimator=model, X=X, y=y, cv=cv, scoring=scorers, n_jobs=-1)
print(
      cv_results["test_auc"], cv_results["test_auc"].mean(), "\n",
      cv_results["test_bacc"], cv_results["test_bacc"].mean(), "\n",
      cv_results["test_acc"], cv_results["test_acc"].mean())

'''
XTreatTivSite-Im-clust-1

[ 0.7         0.46666667  0.7037037   0.92592593  0.66666667] 0.692592592593
[ 0.58333333  0.51666667  0.72222222  0.77777778  0.61111111] 0.642222222222
[ 0.53846154  0.61538462  0.75        0.66666667  0.75      ] 0.664102564103

Xclin
[ 0.39849624  0.51879699  0.66203704  0.65740741  0.49074074] 0.545495683654
[ 0.45112782  0.47744361  0.66666667  0.69444444  0.41666667] 0.54126984127
[ 0.46153846  0.5         0.66666667  0.625       0.54166667] 0.558974358974
'''



###############################################################################
# Clinic only

X = Xclin.copy()
y = yorig.copy()
X = scaler.fit(X).transform(X)

cv = StratifiedKFold(n_splits=NFOLDS)
model = lm.LogisticRegression(class_weight='balanced', fit_intercept=False, C=C)

estimator = model
%time cv_results = cross_validate(estimator=model, X=X, y=y, cv=cv, scoring=scorers, n_jobs=-1)
print(
      cv_results["test_auc"], cv_results["test_auc"].mean(), "\n",
      cv_results["test_bacc"], cv_results["test_bacc"].mean(), "\n",
      cv_results["test_acc"], cv_results["test_acc"].mean())

'''
[ 0.39849624  0.51879699  0.66203704  0.65740741  0.49074074] 0.545495683654
 [ 0.45112782  0.47744361  0.66666667  0.69444444  0.41666667] 0.54126984127
 [ 0.46153846  0.5         0.66666667  0.625       0.54166667] 0.558974358974
'''


np.r_['-1',
  np.r_["test_auc", cv_results["test_auc"], cv_results["test_auc"].mean()],
  np.r_[cv_results["test_bacc"], cv_results["test_bacc"].mean()],
  np.r_[cv_results["test_acc"], cv_results["test_acc"].mean()]]
