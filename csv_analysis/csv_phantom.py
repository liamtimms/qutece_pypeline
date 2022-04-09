import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
%matplotlib inline

base_dir = os.path.abspath('../../..')
base_dir = os.path.join('/mnt/4e43a4f6-7402-4881-bcf5-d280e54cc385/Analysis/NEU_Phantom/DCM2NII_NEU')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
manualwork_dir = os.path.join(base_dir, 'derivatives', 'manualwork')


experiment_list = ['02']


def summarize(in_files, atlas_file):
    dfs_list = (pd.read_csv(in_file, sep='\t') for in_file in in_files)
    dfs_mod_list = []

    # fig, ax = plt.subplots(1,1, figsize=(10,8))

    for df, in_file in zip(dfs_list, in_files):
        df['fname'] = os.path.basename(in_file)
        df = df.drop(columns=[
            'Number of voxels [voxels] (2)', 'Minimum', 'Maximum', 'Median',
            'Volume [mm3] (2)', 'Volume [cm3] (2)', 'Volume [cm3] (1)'
        ])
        df.rename(columns={
            'Number of voxels [voxels] (1)': 'N',
            'Standard Deviation': 'Std'
        },
                  inplace=True)

        atlas_df = pd.read_csv(atlas_file)
        df['region_num'] = atlas_df['region_num']

        filt_df = df.loc[(df['Segment'] == 'Segment_8')]
        std_noise = filt_df['Std'].values[0]

        df['SNR'] = df['Mean'] / std_noise

        # sns.lineplot()

        dfs_mod_list.append(df)

    concatenated_df = pd.concat(dfs_mod_list, ignore_index=True)
    concatenated_df.sort_values(by=['fname', 'region_num'],
                                inplace=True,
                                ignore_index=True)
    concatenated_df.dropna(inplace=True)

    return concatenated_df


for exp_num in experiment_list:
    data_dir = os.path.join(manualwork_dir, 'Experiment_' + exp_num)
    path_pattern = os.path.join(data_dir, 'scan-[0-9][0-9].tsv')
    load_files = glob.glob(path_pattern)

    seg_type = 'exp_' + exp_num
    atlas_file = os.path.join(base_dir, 'code', 'nipype', seg_type + '.csv')

    summary_df = summarize(load_files, atlas_file)
    save_dir = os.path.join(datasink_dir, 'csv_work', 'exp-{}'.format(exp_num))

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    save_name = ('exp-{}_proc_summary.csv').format(exp_num)

    summary_df.to_csv(os.path.join(save_dir, save_name), index=False)
    print(summary_df.head(5))
    # print(summary_df.tail(20))

    save_name = ('exp-{}_proc_summary.png').format(exp_num)

    # plot_df['region_num'] = summary_df['region_num']
    # print(plot_df.head())
    sns_plot = sns.relplot(x='region_num',
                           y='SNR',
                           hue=summary_df.fname.tolist(),
                           kind='line',
                           data=summary_df)
    sns_plot.savefig(os.path.join(save_dir, save_name))
