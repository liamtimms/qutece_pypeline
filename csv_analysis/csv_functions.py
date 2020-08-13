import os
import glob
import pandas as pd


def intensity_stats(in_files):
    df_from_each_in_file = (pd.read_csv(in_file) for in_file in in_files)
    concatenated_df = pd.concat(df_from_each_in_file, ignore_index=True)
    concatenated_df.columns = ['ind', 'label', 'mean', 'std', 'N']
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
    region_N = list(mean_df['N'])

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


def session_summary(datasink_dir, in_dir, out_dir, subject_list, session_list,
                    scan_type, seg_type):
    for sub_num in subject_list:
        for session in session_list:
            data_dir = os.path.join(datasink_dir, seg_type,
                                    'sub-{}'.format(sub_num),
                                    'ses-{}'.format(session))

            session_pattern = '*' + session + '*' + scan_type + '*'
            seg_pattern = '*' + seg_type + '*'
            path_pattern = os.path.join(data_dir,
                                        session_pattern + seg_pattern)
            csv_files = glob.glob(path_pattern)

            stats_df = intensity_stats(csv_files)

            save_dir = os.path.join(datasink_dir, seg_type,
                                    'sub-{}'.format(sub_num),
                                    'ses-{}'.format(session))
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            save_name = ('sub-{}_ses-{}_' + 'proc_' + 'seg-{}.csv').format(
                sub_num, session, seg_type)

            stats_df.to_csv(os.path.join(save_dir, save_name), index=False)
