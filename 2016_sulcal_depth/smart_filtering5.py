"""
@author yl247234 
"""

import pandas as pd
import numpy as np
import optparse
import re, glob, os, json
import matplotlib.pyplot as plt
import matplotlib as mpl
import math
label_size = 22
mpl.rcParams['xtick.labelsize'] = label_size
mpl.rcParams['ytick.labelsize'] = label_size 
text_size = 26
## INPUTS ##
DIRECTORY_STAP = '/neurospin/brainomics/2016_sulcal_depth/STAP_output/'
left_STAP = 'morpho_S.T.s._left.dat'
right_STAP = 'morpho_S.T.s._right.dat'
## OUTPUT ##
left_pheno = 'left_STAP.phe'
right_pheno = 'right_STAP.phe'
asym_pheno = 'asym_STAP.phe'
DIRECTORY_PHENO = DIRECTORY_STAP+'new_pheno/6th_filter/'

from scipy.stats.stats import pearsonr
def plot_scatter(x,y):
    fig = plt.figure()
    ax = plt.gca()
    ax.plot(x, y,'o', markersize=7, color='blue', alpha=0.5, label='Subjects')
    ax.plot(np.mean(x), np.mean(y), 'o', markersize=7, color='green', alpha=1, label='Gravity center')
    p = np.polyfit(x, y, 1)
    print p
    ax.plot(x, np.poly1d(np.polyfit(x, y, 1))(x), color='red', label='Pearson corr: '+ str(pearsonr(x,y)[0]))
    ax.legend()
    plt.axis('equal')

columns = ['geodesicDepthMax', 'geodesicDepthMean', 'plisDePassage', 'hullJunctionsLength']
columns_f = ['FID', 'IID']+columns

df_right = pd.read_csv(DIRECTORY_STAP+'brut_output/'+right_STAP, delim_whitespace=True)
p = [2 if p >0 else 1 for p in df_right['plisDePassage']]
df_right['plisDePassage'] = p 
df_right['FID'] = ['%012d' % int(i) for i in df_right['subject']]
df_right['IID'] = ['%012d' % int(i) for i in df_right['subject']]
df_right.index = df_right['IID']
df_right = df_right[columns_f]

df_left = pd.read_csv(DIRECTORY_STAP+'brut_output/'+left_STAP, delim_whitespace=True)
p = [2 if p >0 else 1 for p in df_left['plisDePassage']]
df_left['plisDePassage'] = p 
df_left['FID'] = ['%012d' % int(i) for i in df_left['subject']]
df_left['IID'] = ['%012d' % int(i) for i in df_left['subject']]
df_left.index = df_left['IID']
df_left = df_left[columns_f]


df = pd.DataFrame()
df['asym_mean'] =(df_left['geodesicDepthMean']-df_right['geodesicDepthMean'])/(df_left['geodesicDepthMean']+df_right['geodesicDepthMean'])
df['asym_max'] =(df_left['geodesicDepthMax']-df_right['geodesicDepthMax'])/(df_left['geodesicDepthMax']+df_right['geodesicDepthMax'])

df_right = df_right.loc[df_right['hullJunctionsLength']>35]
df_right = df_right.loc[df_right['hullJunctionsLength']<80]
df_left = df_left.loc[df_left['hullJunctionsLength']>35]
df_left = df_left.loc[df_left['hullJunctionsLength']<80]


df_right = df_right.loc[df_left.index]
df_right = df_right.dropna()
df_left = df_left.loc[df_right.index]
df_left = df_left.dropna()




"""x = df_right['geodesicDepthMean']
y = df_right['geodesicDepthMax']
plot_scatter(x,y)
plt.xlabel('Right depth mean', fontsize=text_size, fontweight = 'bold', labelpad=0)
plt.ylabel('Right depth max', fontsize=text_size, fontweight = 'bold', labelpad=0)
mu_x = np.mean(x)
mu_y = np.mean(y)
radius=2*abs(np.std(x)+np.std(y))
x_norm = x-mu_x
y_norm = y-mu_y
p = np.polyfit(x, y, 1)
index = np.abs(p[0]*x-y+p[1])/np.sqrt(1+p[0]*p[0])
index = index < np.mean(index)+np.std(index) # 1762/2080 85% left

df_right = df_right.loc[index]
df_left = df_left.loc[index]"""

df  = pd.DataFrame()
df['asym_mean'] =(df_left['geodesicDepthMean']-df_right['geodesicDepthMean'])/(df_left['geodesicDepthMean']+df_right['geodesicDepthMean'])
df['asym_max'] =(df_left['geodesicDepthMax']-df_right['geodesicDepthMax'])/(df_left['geodesicDepthMax']+df_right['geodesicDepthMax'])
df['IID'] = df.index
df['FID'] = df.index
df = df[['FID', 'IID', 'asym_mean', 'asym_max']]

df.to_csv(DIRECTORY_PHENO+asym_pheno, sep= '\t',  header=True, index=False)
df_right.to_csv(DIRECTORY_PHENO+right_pheno, sep= '\t',  header=True, index=False)
df_left.to_csv(DIRECTORY_PHENO+left_pheno, sep= '\t',  header=True, index=False)



x = df_right['hullJunctionsLength']
y = df_right['geodesicDepthMax']
plot_scatter(x,y)
plt.xlabel('Right hullJunctionsLength', fontsize=text_size, fontweight = 'bold', labelpad=0)
plt.ylabel('Right depth max', fontsize=text_size, fontweight = 'bold', labelpad=0)

x = df_left['hullJunctionsLength']
y = df_left['geodesicDepthMax']
plot_scatter(x,y)
plt.xlabel('Left hullJunctionsLength', fontsize=text_size, fontweight = 'bold', labelpad=0)
plt.ylabel('Left depth max', fontsize=text_size, fontweight = 'bold', labelpad=0)

x = df_left['hullJunctionsLength']
y = df_right['geodesicDepthMax']
plot_scatter(x,y)
plt.plot(np.mean(x), np.mean(y), 'o', markersize=7, color='green', alpha=1, label='Gravity center')
plt.xlabel('Left hullJunctionsLength', fontsize=text_size, fontweight = 'bold', labelpad=0)
plt.ylabel('Right depth max', fontsize=text_size, fontweight = 'bold', labelpad=0)

x = df_right['hullJunctionsLength']
y = df_left['geodesicDepthMax']
plot_scatter(x,y)
plt.plot(np.mean(x), np.mean(y), 'o', markersize=7, color='green', alpha=1, label='Gravity center')
plt.xlabel('Right hullJunctionsLength', fontsize=text_size, fontweight = 'bold', labelpad=0)
plt.ylabel('Left depth max', fontsize=text_size, fontweight = 'bold', labelpad=0)


x = df_right['hullJunctionsLength']
y = df_right['geodesicDepthMean']
plot_scatter(x,y)
plt.xlabel('Right hullJunctionsLength', fontsize=text_size, fontweight = 'bold', labelpad=0)
plt.ylabel('Right depth mean', fontsize=text_size, fontweight = 'bold', labelpad=0)

x = df_left['hullJunctionsLength']
y = df_left['geodesicDepthMean']
plot_scatter(x,y)
plt.xlabel('Left hullJunctionsLength', fontsize=text_size, fontweight = 'bold', labelpad=0)
plt.ylabel('Left depth mean', fontsize=text_size, fontweight = 'bold', labelpad=0)

x = df_left['hullJunctionsLength']
y = df_right['geodesicDepthMean']
plot_scatter(x,y)
plt.xlabel('Left hullJunctionsLength', fontsize=text_size, fontweight = 'bold', labelpad=0)
plt.ylabel('Right depth mean', fontsize=text_size, fontweight = 'bold', labelpad=0)


x = df_right['hullJunctionsLength']
y = df_left['geodesicDepthMean']
plot_scatter(x,y)
plt.xlabel('Right hullJunctionsLength', fontsize=text_size, fontweight = 'bold', labelpad=0)
plt.ylabel('Left depth mean', fontsize=text_size, fontweight = 'bold', labelpad=0)

x = df_left['hullJunctionsLength']
y = df['asym_max']
plot_scatter(x,y)
plt.xlabel('Left hullJunctionsLength', fontsize=text_size, fontweight = 'bold', labelpad=0)
plt.ylabel('Asym depth max', fontsize=text_size, fontweight = 'bold', labelpad=0)

x = df_right['hullJunctionsLength']
y = df['asym_max']
plot_scatter(x,y)
plt.xlabel('Right hullJunctionsLength', fontsize=text_size, fontweight = 'bold', labelpad=0)
plt.ylabel('Asym depth max', fontsize=text_size, fontweight = 'bold', labelpad=0)

x = df_left['hullJunctionsLength']
y = df['asym_mean']
plot_scatter(x,y)
plt.xlabel('Left hullJunctionsLength', fontsize=text_size, fontweight = 'bold', labelpad=0)
plt.ylabel('Asym depth mean', fontsize=text_size, fontweight = 'bold', labelpad=0)

x = df_right['hullJunctionsLength']
y = df['asym_mean']
plot_scatter(x,y)
plt.xlabel('Right hullJunctionsLength', fontsize=text_size, fontweight = 'bold', labelpad=0)
plt.ylabel('Asym depth mean', fontsize=text_size, fontweight = 'bold', labelpad=0)




plt.show()


