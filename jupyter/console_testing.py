##
# Imports, etc.

import os
import glob
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
base_dir = os.path.abspath('../../..')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
manualwork_dir = os.path.join(base_dir, 'derivatives', 'manualwork')

# experiment_list = ['02']
# for exp_num in experiment_list:
exp_num = '02'
csv_file = os.path.join(datasink_dir, 'csv_work', 'exp-{}'.format(exp_num),
                        'exp-{}_proc_summary.csv'.format(exp_num))
summary_df = pd.read_csv(csv_file)
summary_df

##
# Initial plot
sns_plot = sns.relplot(x='region_num',
                       y='SNR',
                       hue=summary_df.fname.tolist(),
                       kind='line',
                       data=summary_df)

##
# Loading scan parameters

for f in summary_df['fname'].unique():
    print(f)
    scan_dir = os.path.join(base_dir, 'Experiment_' + exp_num)
    f = f.replace('.tsv', '')
    jsons = glob.glob(os.path.join(scan_dir, '*' + f + '*.json'))
    jsonfilename = jsons[0]

    with open(jsonfilename) as json_file:
        print(jsonfilename)
        j_obj = json.load(json_file)
        TE = j_obj['EchoTime']
        TR = j_obj['RepetitionTime']
        FA = j_obj['FlipAngle']
        FA = j_obj['FlipAngle']
    print(TE)
    print(FA)
    print(TR)

    pass

##
# json testing
# # This does not work
# scan_dir = os.path.join(base_dir, 'Experiment_' + exp_num)
# filename = os.path.join(
#     scan_dir, 'Exp-02_scan-02_fl3d_spiral_vibe_cor_2.1x2.1x2.5i_NuFT_ins.json')
# json_df = pd.read_json(filename, orient='table')
# json_df
#
