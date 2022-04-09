##
# for use with Jupyter

import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
# %matplotlib inline

base_dir = os.path.abspath('../../..')
base_dir = os.path.join('/mnt/4e43a4f6-7402-4881-bcf5-d280e54cc385/',
                        'Analysis/NEU_Phantom/DCM2NII_NEU')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
manualwork_dir = os.path.join(base_dir, 'derivatives', 'manualwork')

print(datasink_dir)

##
