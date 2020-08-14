import os
import glob
import pandas as pd


base_dir = os.path.abspath('../../..')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
manualwork_dir = os.path.join(base_dir, 'derivatives', 'manualwork')

def intensity_stats(in_files):
    """CSV stat calculator

    Takes a list of csv file names output by roi_analyze nodes from
    CustomNipype, concatinates them,

    """

    df_from_each_in_file = (pd.read_csv(in_file) for in_file in in_files)
    concatenated_df = pd.concat(df_from_each_in_file, ignore_index=True)
    concatenated_df.columns = ['ind', 'label', 'mean', 'std', 'N']
    concatenated_df = concatenated_df.astype({'label': 'int'})
    mean_df = concatenated_df.groupby(by='label').mean()
    std_df = concatenated_df.groupby(by='label').std()

    region_num = list(concatenated_df['label'].unique())
    region_mean = list(mean_df['mean'])
    region_std = list(std_df['mean'])
    region_N = list(mean_df['N'])

    # data = [mean_df['label'], mean_df['mean'], std_df['mean_std']]

    stats_df = pd.DataFrame({
        'region': region_num,
        'mean': region_mean,
        'std': region_std,
        'N': region_N
    })

    return stats_df


def session_summary(in_folder, sub_num, session, scan_type, seg_type):
    data_dir = os.path.join(datasink_dir, in_folder, 'sub-{}'.format(sub_num),
                            'ses-{}'.format(session))

    if not os.path.exists(data_dir):
        data_dir = os.path.join(datasink_dir, in_folder, 'sub-{}'.format(sub_num))

    session_pattern = '*' + session + '*' + scan_type + '*'
    seg_pattern = '*' + seg_type + '*'
    path_pattern = os.path.join(data_dir, session_pattern + seg_pattern)
    csv_files = glob.glob(path_pattern)

    stats_df = intensity_stats(csv_files)

    save_dir = os.path.join(datasink_dir, 'csv_work', seg_type, 'sub-{}'.format(sub_num),
                            'ses-{}'.format(session))

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    save_name = ('sub-{}_ses-{}_' + scan_type +'_proc_' + 'seg-{}.csv').format(
        sub_num, session, seg_type)

    stats_df.to_csv(os.path.join(save_dir, save_name), index=False)
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


def difference_summary(in_folder, sub_num, scan_type, seg_type):
    session = 'Precon'
    data_dir = os.path.join(datasink_dir, 'csv_work', seg_type,
                            'sub-{}'.format(sub_num), 'ses-{}'.format(session))
    path_pattern = os.path.join(data_dir,
                                '*' + scan_type + '*' + seg_type + '*.csv')
    load_name = glob.glob(path_pattern)
    precon_df = pd.read_csv(load_name)

    session = 'Postcon'
    data_dir = os.path.join(datasink_dir, 'csv_work', seg_type,
                            'sub-{}'.format(sub_num), 'ses-{}'.format(session))
    path_pattern = os.path.join(data_dir,
                                '*' + scan_type + '*' + seg_type + '*.csv')
    load_name = glob.glob(path_pattern)
    postcon_df = pd.read_csv(load_name)

    atlas_file = os.path.join(base_dir, 'code', 'nipype', seg_type + '.csv')
    atlas_df = pd.read_csv(atlas_file)

    diff_df = diff_stats(precon_df, postcon_df, atlas_df)

    save_dir = os.path.join(datasink_dir, 'csv_work', seg_type, 'sub-{}'.format(sub_num))

    save_name = ('sub-{}_' + scan_type + '-proc_' + seg_type +
                 '_DIFF.csv').format(sub_num)

    diff_df.to_csv(os.path.join(save_dir, save_name), index=False)
    return diff_df


def subjects_summary(datasink_dir, subject_list, atlas_df, scan_type,
                     seg_type):

    # region_num = list(atlas_df['region_num'])
    # region_name = atlas_df['region_name'].astype(str)
    summary_df = atlas_df
    for sub_num in subject_list:

        data_dir = os.path.join(datasink_dir, 'csv_work',
                                'sub-{}'.format(sub_num))
        load_name = ('sub-{}_' + scan_type + '-proc_' + seg_type +
                     '_DIFF.csv').format(sub_num)
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
    save_name = ('summary_' + scan_type + '-proc_' + seg_type + '_rDIFF.csv')
    summary_df.to_csv(os.path.join(save_dir, save_name), index=False)

    print(summary_df.head())
