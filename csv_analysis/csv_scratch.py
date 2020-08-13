import os
import numpy as np
import pandas as pd
import nibabel as nib
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import sklearn.preprocessing as preproc


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


def diff_stats(precon_df, postcon_df, atlas_df):
    # calculate difference in the means
    region_num = list(postcon_df['region'])
    # region_name = list(atlas_df['name'])
    region_name = atlas_df['region_name'].astype(str)
    postcon_mean = list(postcon_df['mean'])
    postcon_std = list(postcon_df['std'])
    precon_mean = list(precon_df['mean'])
    precon_std = list(precon_df['std'])
    diff_df = pd.DataFrame({
        'region': region_num,
        'name': region_name,
        'postcon_mean': postcon_mean,
        'postcon_std': postcon_std,
        'precon_mean': precon_mean,
        'precon_std': precon_std
    })
    diff_df['diff'] = postcon_df['mean'] - precon_df['mean']
    # wm_df = diff_df.loc[diff_df['name'].str.contains('White_Matter')]
    # wm_diff_mean = wm_df['diff'].mean()
    diff_mean = diff_df['diff'].mean()
    diff_df['rdiff'] = diff_df['diff'] / diff_mean
    return diff_df


def session_summary(subject_list, session_list, scan_type):
    for sub_num in subject_list:
        for session in session_list:
            data_dir = os.path.join(
                datasink_dir, 'nonlinear_transfomed_{}_csv'.format(scan_type),
                'sub-{}'.format(sub_num), 'ses-{}'.format(session))

            csv_files = [
                os.path.join(data_dir, f) for f in os.listdir(data_dir)
                if os.path.isfile(os.path.join(data_dir, f))
            ]
            stats_df = intensity_stats(csv_files)

            save_dir = os.path.join(datasink_dir, 'csv_work',
                                    'sub-{}'.format(sub_num),
                                    'ses-{}'.format(session))

            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            save_name = ('sub-{}_ses-{}_' + scan_type +
                         '-proc_Neuromorphometrics.csv').format(
                             sub_num, session)

            stats_df.to_csv(os.path.join(save_dir, save_name), index=False)
            # print(save_name)
            # print(stats_df.head(10))


base_dir = os.path.abspath('../..')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')

save_dir = os.path.join(datasink_dir, 'csv_work')
if not os.path.exists(save_dir):
    os.mkdir(save_dir)

sub_num = '11'
session = 'Precon'

# csv_fn =
# 'r_rrrsub-{}_ses-{}_hr_run-01_UTE_desc-processed_Neuromorphometrics'.format(
#     sub_num, session)

subject_list = ['02', '03', '04', '06', '08', '11', '12', '13', '14', '15']
session_list = ['Precon', 'Postcon']
scan_type = 'hr'
atlas_df = pd.read_csv('Neuromorphometrics.csv')
# print(atlas_df.head())

session_summary(subject_list, session_list, scan_type)
scan_type = 'hr'


def difference_summary(subject_list, scan_type, atlas_df):
    for sub_num in subject_list:
        session = 'Precon'
        data_dir = os.path.join(datasink_dir, 'csv_work',
                                'sub-{}'.format(sub_num),
                                'ses-{}'.format(session))
        load_name = os.path.join(data_dir,
                                 ('sub-{}_ses-{}_' + scan_type +
                                  '-proc_Neuromorphometrics.csv').format(
                                      sub_num, session))
        precon_df = pd.read_csv(load_name)

        session = 'Postcon'
        data_dir = os.path.join(datasink_dir, 'csv_work',
                                'sub-{}'.format(sub_num),
                                'ses-{}'.format(session))
        load_name = os.path.join(data_dir,
                                 ('sub-{}_ses-{}_' + scan_type +
                                  '-proc_Neuromorphometrics.csv').format(
                                      sub_num, session))
        postcon_df = pd.read_csv(load_name)
        diff_df = diff_stats(precon_df, postcon_df, atlas_df)

        save_dir = os.path.join(datasink_dir, 'csv_work',
                                'sub-{}'.format(sub_num))

        save_name = ('sub-{}_' + scan_type +
                     '-proc_Neuromorphometrics_DIFF.csv').format(sub_num)

        diff_df.to_csv(os.path.join(save_dir, save_name), index=False)
        # print(save_name)
        # print(diff_df.head())


difference_summary(subject_list, scan_type, atlas_df)

region_num = list(atlas_df['region_num'])
region_name = atlas_df['region_name'].astype(str)
summary_df = atlas_df
for sub_num in subject_list:
    data_dir = os.path.join(datasink_dir, 'csv_work', 'sub-{}'.format(sub_num))

    load_name = ('sub-{}_' + scan_type +
                 '-proc_Neuromorphometrics_DIFF.csv').format(sub_num)
    diff_df = pd.read_csv(os.path.join(data_dir, load_name))
    diff_df = diff_df.drop(columns=[
        'postcon_mean', 'postcon_std', 'precon_mean', 'precon_std', 'diff'
    ])
    rdiff = list(diff_df['rdiff'])
    summary_df[sub_num + '_rdiff'] = rdiff

transpose_df = summary_df
transpose_df = transpose_df.drop(columns=['region_num', 'region_name'])
transpose_df = transpose_df.transpose()
desc_df = transpose_df.describe()
desc_df = desc_df.transpose()
summary_df['mean_rdiff'] = list(desc_df['mean'])
summary_df['std_rdiff'] = list(desc_df['std'])

save_dir = os.path.join(datasink_dir, 'csv_work')
save_name = ('summary_' + scan_type + '-proc_Neuromorphometrics_rDIFF.csv')
summary_df.to_csv(os.path.join(save_dir, save_name), index=False)

# save_dir = os.path.join(datasink_dir, 'csv_work')
# save_name = ('summaryTranpose_' + scan_type + '-proc_Neuromorphometrics_rDIFF.csv')
# transpose_df.to_csv(os.path.join(save_dir, save_name), index=False)

print(summary_df.head())
# print(desc_df.head())
