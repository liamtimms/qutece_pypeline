import glob
import os

import matplotlib
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import pandas as pd
import seaborn as sns
import sklearn.preprocessing as preproc

base_dir = os.path.abspath('../..')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
manualwork_dir = os.path.join(base_dir, 'derivatives', 'manualwork')


def intensity_stats(in_files):
    df_from_each_in_file = (pd.read_csv(in_file) for in_file in in_files)
    concatenated_df = pd.concat(df_from_each_in_file, ignore_index=True)
    concatenated_df.columns = ['ind', 'label', 'mean', 'std']
    concatenated_df = concatenated_df.astype({'label': 'int'})
    mean_df = concatenated_df.groupby(by='label').mean()
    std_df = concatenated_df.groupby(by='label').std()

    # std_df.rename(columns={'mean': 'mean_std', 'std': 'std_std'})
    # stats_df.columns = ['label', 'mean' 'std']
    # stats_df['label'] = mean_df['label']
    # stats_df['mean'] = mean_df['mean']
    # stats_df['std'] = std_df['mean']

    region_num = list(concatenated_df['label'].unique())
    region_mean = list(mean_df['mean'])
    region_std = list(std_df['mean'])

    # data = [mean_df['label'], mean_df['mean'], std_df['mean_std']]

    stats_df = pd.DataFrame({
        'region': region_num,
        'mean': region_mean,
        'std': region_std
    })

    return stats_df


def session_summary(subject_list, session_list, seg_type):
    for sub_num in subject_list:
        for session in session_list:
            data_dir = os.path.join(datasink_dir, 'tissue_wmh_analysis_csv',
                                    'sub-{}'.format(sub_num))

            session_pattern = '*' + session + '_hr*'
            seg_pattern = '*' + seg_type + '*'
            path_pattern = os.path.join(data_dir,
                                        session_pattern + seg_pattern)
            csv_files = glob.glob(path_pattern)

            stats_df = intensity_stats(csv_files)

            save_dir = os.path.join(manualwork_dir, 'csv_analysis_tissue_wmh',
                                    'sub-{}'.format(sub_num),
                                    'ses-{}'.format(session))
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            save_name = ('sub-{}_ses-{}_' + 'proc_' + 'seg-{}.csv').format(
                sub_num, session, seg_type)

            stats_df.to_csv(os.path.join(save_dir, save_name), index=False)


subject_list = [
    '02', '03', '04', '06', '07', '08', '11', '12', '13', '14', '15'
]
session_list = ['Precon', 'Postcon']
seg_type = 'WMH'  # WMH segmentation
#seg_type = 'T1w'    # FAST tissue segmentation

session_summary(subject_list, session_list, seg_type)
