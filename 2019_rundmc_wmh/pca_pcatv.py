import sys
import os
import time

import numpy as np
import nibabel
import pandas as pd
import matplotlib.pylab as plt
import nilearn
from nilearn import plotting
import argparse

from matplotlib.backends.backend_pdf import PdfPages


#sys.path.append('/home/ed203246/git/scripts/2013_mescog/proj_wmh_patterns')
#import pca_tv
from parsimony.decomposition import PCAL1L2TV
import  parsimony.decomposition.pca_tv as pca_tv

import parsimony.functions.nesterov.tv
from brainomics import array_utils


#from brainomics import plot_utilities
#import parsimony.utils.check_arrays as check_arrays

########################################################################################################################
STUDY_PATH = '/neurospin/brainomics/2019_rundmc_wmh'
DATA_PATH = os.path.join(STUDY_PATH, 'sourcedata', 'wmhmask')

ANALYSIS_PATH = os.path.join(STUDY_PATH, 'analyses', '201909_rundmc_wmh_pca')
ANALYSIS_DATA_PATH = os.path.join(ANALYSIS_PATH, "data")
ANALYSIS_MODELS_PATH = os.path.join(ANALYSIS_PATH, "models")

CONF = dict(clust_size_thres = 20, NI="WMH_2006", vs=1, shape=(181, 217, 181))
# nii_filenames = glob.glob(os.path.join(DATA_PATH, "*", "Stdt1wSubjTempl_RUNDMC_*_WMH_to_T1_*.nii.gz"))

# match_filename_re = re.compile("Stdt1wSubjTempl_RUNDMC_([0-9]+)_WMH_to_T1_(20[0-9]+).nii.gz")
# match_columns = ["participant_id", "year", "nii_path"]

OUTPUT_DIR = os.path.join(ANALYSIS_MODELS_PATH, '{key}')

########################################################################################################################
# parse command line options
parser = argparse.ArgumentParser()
parser.add_argument("--algo", help='enettv, pca, ica', type=str)
parser.add_argument("--penalties", help='l1, l2, tv penalties. ', nargs='+', type=float)

options = parser.parse_args()

if options.algo is None :
    parser.print_help()
    raise SystemExit("Error: algo is missing")

if options.penalties:
    ll1, ll2, ltv = options.penalties
    #ll1, ll2, ltv = -1, -1, -1
    print(ll1, ll2, ltv)
#raise SystemExit("Error: penalties are missing")

########################################################################################################################
# Read Data
mask_img = nibabel.load(os.path.join(ANALYSIS_DATA_PATH, "mask.nii.gz"))
mask_arr = mask_img.get_data() == 1
pop = pd.read_csv(os.path.join(ANALYSIS_DATA_PATH, "%s_participants.csv" % CONF["NI"]))
NI = nibabel.load(os.path.join(ANALYSIS_DATA_PATH, "%s.nii.gz" % CONF["NI"]))
NI_arr =  NI.get_data()
NI_arr_msk = NI.get_data()[mask_arr].T

# Check shape
assert NI_arr.shape == tuple(list(CONF["shape"]) + [pop.shape[0]])
assert NI_arr_msk.shape == (pop.shape[0], mask_arr.sum())
assert mask_arr.shape == CONF["shape"]
del NI_arr
del NI
X = NI_arr_msk - NI_arr_msk.mean(axis=0)
del NI_arr_msk

assert mask_arr.sum() == 371278

# assert X.shape == (503, 51637)
assert X.shape == (267, 371278)
assert mask_arr.sum() == X.shape[1]
assert np.allclose(X.mean(axis=0), 0)

# Fit model
N_COMP = 3

########################################################################################################################
if options.algo == 'ica':#(ll1, ll2, ltv) == (-1, -1, -1):
    key = "ica"
    os.makedirs(OUTPUT_DIR.format(key=key), exist_ok=True)

    from sklearn.decomposition import FastICA
    ica = FastICA(n_components=N_COMP)
    t0 = time.clock()
    ica.fit(X)
    t1 = time.clock()
    _time = t1 - t0
    print("Time TOT(s)", _time)
    print(ica.explained_variance_ratio_)
    # [9.84012749e-01 2.59148416e-03 7.08952491e-04 4.14767146e-04
    assert ica.components_.shape == (N_COMP, 371278)
    PC = ica.transform(X)
    #U = pca.transform(X)
    d = np.array([0] * N_COMP)
    V = ica.components_.T
    U = ica.transform(X)
    explained_variance = np.array([0] * N_COMP)


########################################################################################################################
# Fit Regular PCA
if options.algo == 'pca':#(ll1, ll2, ltv) == (-1, -1, -1):
    key = "pca"
    os.makedirs(OUTPUT_DIR.format(key=key), exist_ok=True)

    from sklearn.decomposition import PCA
    pca = PCA(n_components=N_COMP)
    t0 = time.clock()
    pca.fit(X)
    t1 = time.clock()
    _time = t1 - t0
    print("Time TOT(s)", _time)
    print(pca.explained_variance_ratio_)
    # [0.19778403 0.04279359 0.03579749]
    assert pca.components_.shape == (N_COMP, 371278)
    PC = pca.transform(X)
    #U = pca.transform(X)
    d = pca.singular_values_
    V = pca.components_.T
    U = pca.transform(X)
    explained_variance = pca.explained_variance_ratio_.cumsum()

if options.algo == 'enettv':
    ########################################################################################################################
    # PCA TV
    from parsimony.utils.linalgs import LinearOperatorNesterov

    #mask_img = nibabel.Nifti1Image(mask_arr.astype(float), affine=ref_img.affine)
    Atv = LinearOperatorNesterov(filename=os.path.join(ANALYSIS_DATA_PATH, "Atv.npz"))
    #assert Atv.get_singular_values(0) == Atv_.get_singular_values(0)
    assert np.allclose(Atv.get_singular_values(0), 11.974760295502465)

    inner_max_iter = int(1e3)
    l1max = pca_tv.PCAL1L2TV.l1_max(X) * .9 # 0.03899665773990707
    assert np.allclose(l1max, 0.03509699196591636)

    if False:  # Not to bad, TV too low
        # ll1 < 0.01 * l1max,  tv = 0.01 * 1/3
        ll1, ll2, ltv = 0.01 * l1max, 1, 0.01
        key_pca_enettv = "pca_enettv_%.4f_%.3f_%.3f" % (ll1, ll2, ltv)
        # Corr with old PC[-0.99966211718252285, -0.99004655401439967, -0.74332811780676245]


    if False:# Too much l1, not enough tv
        ll1, ll2, ltv = 0.05 * l1max, 1, 0.001
        key_pca_enettv = "pca_enettv_%.4f_%.3f_%.3f" % (ll1, ll2, ltv)
        CHOICE = key_pca_enettv
        # pending: for 10 PCs
        #Corr with old PC[0.99999222883809447, 0.9994293857297728, -0.99247826586372279]
        #Explained variance:[ 0.19876024  0.22844359  0.24310107  0.25474415  0.26392774]


    if False:  # Parameters settings 7: Almost but too much TV
        # ll1 < 0.01 * l1max,  tv = 0.01 * 1/3
        ll1, ll2, ltv = 0.01 * l1max, 1, 0.1
        key_pca_enettv = "pca_enettv_%.4f_%.3f_%.3f" % (ll1, ll2, ltv)
        # Corr with old PC[-0.99966211718252285, -0.99004655401439967, -0.74332811780676245]

    ## key_pca_enettv = CHOICE
    key = "pca_enettv_%.6f_%.3f_%.3f" % (ll1, ll2, ltv)
    print(OUTPUT_DIR.format(key=key))

    os.makedirs(OUTPUT_DIR.format(key=key), exist_ok=True)

    model = PCAL1L2TV(n_components=N_COMP,
                                l1=ll1, l2=ll2, ltv=ltv,
                                Atv=Atv,
                                criterion="frobenius",
                                eps=1e-6,
                                max_iter=100,
                                inner_max_iter=inner_max_iter,
                                verbose=True)

    t0 = time.clock()
    model.fit(X)
    model.l1_max(X)
    t1 = time.clock()
    _time = t1 - t0
    print("Time TOT(s)", _time)

    explained_variance = model.explained_variance(X, n_components=N_COMP)

    # Save results
    PC, d = model.transform(X)
    U = model.U.copy()
    d = model.d.copy()
    V = model.V.copy()

########################################################################################################################
# Save results

from brainomics.array_utils import arr_get_threshold_from_norm2_ratio
thresholds = np.array([arr_get_threshold_from_norm2_ratio(V[: ,k], ratio=.99) for k in range(V.shape[1])])

sign = np.sign([V[:, k][np.abs(V[:, k]) > thresholds[k]].mean() for k in range(V.shape[1])]).reshape(1, -1)
sign[np.isnan(sign)] = 1
V = V * sign
U = U * sign
PC = PC * sign

explained_variance_ratio = np.concatenate([[explained_variance[0]], np.ediff1d(explained_variance)])

np.savez_compressed(os.path.join(OUTPUT_DIR.format(key=key), "model.npz"),
                    U=U, d=d, V=V, PC=PC, explained_variance=explained_variance)

info = pd.DataFrame(dict(
    key = key,
    comp = ["PC%i" % k for k in range(1, V.shape[1]+1)],
    rsquared = explained_variance,
    rsquared_ratio = explained_variance_ratio,
    v_max=V.max(axis=0),
    v_min=V.min(axis=0),
    v_abs_mean=np.abs(V).mean(axis=0),
    v_prop_nonnull=np.sum(np.abs(V) > thresholds, axis=0) / V.shape[0],
    time=_time))

info.to_csv(os.path.join(OUTPUT_DIR.format(key=key), "info.csv"), index=False)

########################################################################################################################
# Reload

m = np.load(os.path.join(OUTPUT_DIR.format(key=key), "model.npz"))
U, d, V, PC, explained_variance = m["U"], m["d"], m["V"], m["PC"], m["explained_variance"]

from brainomics.array_utils import arr_get_threshold_from_norm2_ratio
thresholds = np.array([arr_get_threshold_from_norm2_ratio(V[: ,k], ratio=.99) for k in range(V.shape[1])])
V[V < thresholds] = 0

# Save loadings as 4D image
map_arr = np.zeros(list(mask_arr.shape) + [V.shape[1]])
map_arr[mask_arr] = V
map_img = nibabel.Nifti1Image(map_arr, mask_img.affine)
map_img.to_filename(os.path.join(OUTPUT_DIR.format(key=key), "components-brain-maps.nii.gz"))
map_img_l = nibabel.four_to_three(map_img)


##############################################################################################################
# Plot
"""
mask_img = nibabel.load(os.path.join(ANALYSIS_DATA_PATH, "mask.nii.gz"))
mask_img.affine[0, 3] *= -1  # Tr X
# mask_img.affine[0, 1] *= -1  # flip X

mask_img.affine[1, 1] *= -1  # flip Y
#mask_img.affine[2, 3] *= -1

#V = pca.components_.T
brain_mni_1mm = nibabel.load("/usr/share/data/fsl-mni152-templates/MNI152_T1_1mm_brain.nii.gz")
brain_mni_1mm.affine
"""

pdf = PdfPages(os.path.join(OUTPUT_DIR.format(key=key), "PCs.pdf"))

fig = plt.figure(figsize=(13.33, 10 * U.shape[1]))
axis = fig.subplots(nrows=U.shape[1] * 2, ncols=1)

for k in range(U.shape[1]):
    #k = 0
    idx = 2 * k
    map_img = map_img_l[k]

    #ax = fig.add_subplot(111)
    #ax.set_title("T-stats T>%.2f" %  tstats_thres)


    vmax = np.abs(map_arr).max()

    axis[idx].set_title("PC%i (EV:%.3f%%)" %  (k+1, explained_variance_ratio[k] * 100))
    plotting.plot_glass_brain(map_img, colorbar=True, vmax=vmax, figure=fig, axes=axis[idx])

    #pdf.savefig()
    display = plotting.plot_stat_map(map_img, colorbar=True, draw_cross=True, figure=fig, axes=axis[idx+1])#, symmetric_cbar=False)#, cmap=plt.cm.hot_r)#,  cut_coords=[16, -4, 0], symmetric_cbar=False, cmap=cold_blue)#, threshold=3,)#, figure=fig, axes=ax)


pdf.savefig()
plt.savefig(os.path.join(OUTPUT_DIR.format(key=key), "PCs.png"))
plt.close(fig)
pdf.close()
