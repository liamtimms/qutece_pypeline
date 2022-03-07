import glob
import os

import pandas as pd
import seaborn as sns

base_dir = os.path.abspath('../../..')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
manualwork_dir = os.path.join(base_dir, 'derivatives', 'manualwork')


def wavg(df, avg_name, weight_name):
    d = df[avg_name]
    w = df[weight_name]
    try:
        return (d * w).sum() / w.sum()
    except ZeroDivisionError:
        return d.mean()


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
        data_dir = os.path.join(datasink_dir, in_folder,
                                'sub-{}'.format(sub_num))

    session_pattern = '*' + session + '*' + scan_type + '*'
    seg_pattern = '*' + seg_type + '*'
    path_pattern = os.path.join(data_dir, session_pattern + seg_pattern)
    csv_files = glob.glob(path_pattern)
    # print('Selected files are: ')
    # print(csv_files)

    stats_df = intensity_stats(csv_files)

    save_dir = os.path.join(datasink_dir, 'csv_work', seg_type,
                            'sub-{}'.format(sub_num), 'ses-{}'.format(session))

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    save_name = ('sub-{}_ses-{}_' + scan_type + '_proc_' +
                 'seg-{}.csv').format(sub_num, session, seg_type)

    stats_df.to_csv(os.path.join(save_dir, save_name), index=False)
    return stats_df


def diff_stats(precon_df, postcon_df, atlas_df):
    postcon_df = postcon_df.merge(atlas_df,
                                  left_on='region',
                                  right_on='region_num')
    # calculate difference in the means
    region_num = list(postcon_df['region'])
    region_name = postcon_df['region_name'].astype(str)
    postcon_mean = list(postcon_df['mean'])
    postcon_std = list(postcon_df['std'])
    precon_mean = list(precon_df['mean'])
    precon_std = list(precon_df['std'])
    N = list(precon_df['N'])

    diff_df = pd.DataFrame({
        'region': region_num,
        'name': region_name,
        'postcon_mean': postcon_mean,
        'postcon_std': postcon_std,
        'precon_mean': precon_mean,
        'precon_std': precon_std,
        'N': N
    })
    diff_df['diff'] = postcon_df['mean'] - precon_df['mean']
    # filt_df = diff_df.loc[~diff_df['name'].str.contains('background')]
    # filt_df = diff_df.loc[(diff_df['name'] == 'White_Matter') |
    #                       (diff_df['name'] == 'Grey_Matter')]
    filt_df = diff_df.loc[(diff_df['name'] == 'Small_Vessels&White_Matter')]
    wm_mean = filt_df['postcon_mean'].mean()
    # diff_mean = filt_df['diff'].mean()
    diff_mean = wavg(filt_df, 'diff', 'N')
    # print(diff_mean)
    diff_df['rmean'] = diff_df['postcon_mean'] / wm_mean
    diff_df['rdiff'] = diff_df['diff'] / diff_mean
    return diff_df


def difference_summary(sub_num, scan_type, seg_type):
    session = 'Precon'
    data_dir = os.path.join(datasink_dir, 'csv_work', seg_type,
                            'sub-{}'.format(sub_num), 'ses-{}'.format(session))
    path_pattern = os.path.join(data_dir,
                                '*' + scan_type + '*' + seg_type + '*.csv')
    load_files = glob.glob(path_pattern)
    # print(load_files)
    precon_df = pd.read_csv(load_files[0])

    session = 'Postcon'
    data_dir = os.path.join(datasink_dir, 'csv_work', seg_type,
                            'sub-{}'.format(sub_num), 'ses-{}'.format(session))
    path_pattern = os.path.join(data_dir,
                                '*' + scan_type + '*' + seg_type + '*.csv')
    load_files = glob.glob(path_pattern)
    postcon_df = pd.read_csv(load_files[0])

    atlas_file = os.path.join(base_dir, 'code', 'nipype', seg_type + '.csv')
    atlas_df = pd.read_csv(atlas_file)

    # print(atlas_df.head(20))
    # print(postcon_df.head(20))

    diff_df = diff_stats(precon_df, postcon_df, atlas_df)

    save_dir = os.path.join(datasink_dir, 'csv_work', seg_type,
                            'sub-{}'.format(sub_num))

    save_name = ('sub-{}_' + scan_type + '-proc_' + seg_type +
                 '_DIFF.csv').format(sub_num)

    diff_df.to_csv(os.path.join(save_dir, save_name), index=False)

    return diff_df


def desc_trans(summary_df):
    transpose_df = summary_df
    transpose_df = transpose_df.drop(columns=['region_num', 'region_name'])
    transpose_df = transpose_df.transpose()
    desc_df = transpose_df.describe()
    desc_df = desc_df.transpose()
    summary_df['mean'] = list(desc_df['mean'])
    summary_df['std'] = list(desc_df['std'])
    return summary_df


def subjects_summary_alt(datasink_dir, subject_list, scan_type, seg_type):
    diff_df_list = []
    for sub_num in subject_list:

        data_dir = os.path.join(datasink_dir, 'csv_work', seg_type,
                                'sub-{}'.format(sub_num))
        load_name = ('sub-{}_' + scan_type + '-proc_' + seg_type +
                     '_DIFF.csv').format(sub_num)
        diff_df = pd.read_csv(os.path.join(data_dir, load_name))
        diff_df['subject'] = sub_num
        diff_df_list.append(diff_df)
        print(diff_df.head())

    concatenated_df = pd.concat(diff_df_list, ignore_index=True)
    # print(concatenated_df.head())

    concatenated_df.sort_values(by=['subject', 'region'],
                                inplace=True,
                                ignore_index=True)

    # concatenated_df.dropna(inplace=True)

    save_dir = os.path.join(datasink_dir, 'csv_work', seg_type)
    save_name = ('summary.png')

    # plot_df['region_num'] = summary_df['region_num']
    # print(plot_df.head())
    sns_plot = sns.catplot(x='region',
                           y='rmean',
                           hue=concatenated_df.subject.tolist(),
                           legend=True,
                           data=concatenated_df)
    sns_plot.savefig(os.path.join(save_dir, save_name))

    return concatenated_df


def subjects_summary(datasink_dir, subject_list, scan_type, seg_type):

    # region_num = list(atlas_df['region_num'])
    # region_name = atlas_df['region_name'].astype(str)
    atlas_file = os.path.join(base_dir, 'code', 'nipype', seg_type + '.csv')
    atlas_df = pd.read_csv(atlas_file)
    summary_df = atlas_df
    summary_post_df = atlas_df
    for sub_num in subject_list:

        data_dir = os.path.join(datasink_dir, 'csv_work', seg_type,
                                'sub-{}'.format(sub_num))
        load_name = ('sub-{}_' + scan_type + '-proc_' + seg_type +
                     '_DIFF.csv').format(sub_num)
        diff_df = pd.read_csv(os.path.join(data_dir, load_name))
        postcon_mean = list(diff_df['postcon_mean'])
        N = list(diff_df['N'])
        diff_df = diff_df.drop(columns=[
            'postcon_mean', 'postcon_std', 'precon_mean', 'precon_std', 'diff',
            'N'
        ])
        rdiff = list(diff_df['rdiff'])
        summary_df[sub_num + '_rdiff'] = rdiff
        summary_post_df[sub_num + '_postcon_mean'] = postcon_mean
        summary_post_df[sub_num + '_N'] = N

    summary_df = desc_trans(summary_df)

    save_dir = os.path.join(datasink_dir, 'csv_work', seg_type)
    save_name = ('summary_' + scan_type + '-proc_' + seg_type + '_rDIFF.csv')
    summary_df.to_csv(os.path.join(save_dir, save_name), index=False)

    summary_post_df = desc_trans(summary_post_df)

    save_dir = os.path.join(datasink_dir, 'csv_work', seg_type)
    save_name = ('summary_' + scan_type + '-proc_' + seg_type + '_Post.csv')
    summary_post_df.to_csv(os.path.join(save_dir, save_name), index=False)

    print(summary_df.head())
    print(summary_post_df.head())


def sub_stats(precon_df, postcon_df, atlas_df):
    postcon_df = postcon_df.merge(atlas_df,
                                  left_on='region',
                                  right_on='region_num')

    region_num = list(postcon_df['region'])
    region_name = postcon_df['region_name'].astype(str)
    postcon_mean = list(postcon_df['mean'])
    postcon_std = list(postcon_df['std'])
    precon_mean = list(precon_df['mean'])
    precon_std = list(precon_df['std'])
    N = list(precon_df['N'])

    sub_df = pd.DataFrame({
        'region': region_num,
        'name': region_name,
        'postcon_mean': postcon_mean,
        'postcon_std': postcon_std,
        'precon_mean': precon_mean,
        'precon_std': precon_std,
        'N': N
    })
    nWM_df = sub_df.loc[sub_df['name'].str.contains('nWM')]
    WMH_df = sub_df.loc[sub_df['name'].str.contains('WMH')]

    nWM_mean = nWM_df.mean()
    WMH_mean = WMH_df.mean()

    nWM_mean['name'] = 'nWM_mean'
    WMH_mean['name'] = 'WMH_mean'

    sub_df = sub_df.append(nWM_mean, ignore_index=True)
    sub_df = sub_df.append(WMH_mean, ignore_index=True)

    return sub_df


def sub_summary(sub_num, scan_type, seg_type):
    session = 'Precon'
    data_dir = os.path.join(datasink_dir, 'csv_work', seg_type,
                            'sub-{}'.format(sub_num), 'ses-{}'.format(session))
    path_pattern = os.path.join(data_dir,
                                '*' + scan_type + '*' + seg_type + '*.csv')
    load_files = glob.glob(path_pattern)
    # print(load_files)
    precon_df = pd.read_csv(load_files[0], skiprows=[1], nrows=20)

    session = 'Postcon'
    data_dir = os.path.join(datasink_dir, 'csv_work', seg_type,
                            'sub-{}'.format(sub_num), 'ses-{}'.format(session))
    path_pattern = os.path.join(data_dir,
                                '*' + scan_type + '*' + seg_type + '*.csv')
    load_files = glob.glob(path_pattern)
    postcon_df = pd.read_csv(load_files[0], skiprows=[1], nrows=20)

    atlas_file = os.path.join(base_dir, 'code', 'nipype', seg_type + '.csv')
    atlas_df = pd.read_csv(atlas_file)

    # print(atlas_df.head(20))
    # print(postcon_df.head(20))

    sub_df = sub_stats(precon_df, postcon_df, atlas_df)

    save_dir = os.path.join(datasink_dir, 'csv_work', seg_type,
                            'sub-{}'.format(sub_num))

    save_name = ('sub-{}_' + scan_type + '-proc_' + seg_type +
                 '_DIFF.csv').format(sub_num)

    sub_df.to_csv(os.path.join(save_dir, save_name), index=False)

    return sub_df
