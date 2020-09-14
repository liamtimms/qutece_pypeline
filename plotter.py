import os
import math
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import nibabel as nib
import nilearn as nil
from nipype.utils.filemanip import split_filename

base_dir = os.path.abspath('../..')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
manualwork_dir = os.path.join(base_dir, 'derivatives', 'manualwork')


def roi_extract(scan_img, roi_img):

    vals_df_list = []
    unique_roi = np.unique(roi_img)
    # out_data = np.empty([np.size(unique_roi), 4])
    n = 0
    extracted_df = pd.DataFrame()
    for r in unique_roi:
        # r is label in roi
        # n counts for number of labels

        roi = (roi_img == r).astype(int)
        roi = roi.astype('float')
        # zero can be a true value so mask with nan
        roi[roi == 0] = np.nan
        crop_img = np.multiply(scan_img, roi)
        vals = np.reshape(crop_img, -1)
        vals_df = pd.DataFrame(vals)
        vals_df.dropna(inplace=True)
        vals_df.reset_index(drop=True, inplace=True)
        vals_df_list.append(vals_df)

        extracted_df[r] = vals_df[0]

        # ave = np.nanmean(vals)
        # std = np.nanstd(vals)
        # N = np.count_nonzero(~np.isnan(vals))
        # out_data[n][0] = r
        # out_data[n][1] = ave
        # out_data[n][2] = std
        # out_data[n][3] = N
        n = n + 1

    # extracted_df = pd.concat(vals_df_list, ignore_index=True, axis=1)

    return extracted_df


def hist_plots(df, seg_type, save_dir):
    sns.set(color_codes=True)
    sns.set(style="white", palette="muted")
    # plot_xlim_min = 0
    # plot_xlim_max = 1000

    for i, col in enumerate(df.columns):
        vals = df[col].to_numpy()
        w = 1
        n = math.ceil((np.nanmax(vals) - np.nanmin(vals)) / w)

        if n > 0:
            plt.figure(i)
            save_name = seg_type + '-' + str(col) + '.png'
            out_fig_name = os.path.join(save_dir, save_name)
            sns.distplot(df[col],
                         kde=False,
                         bins=n,
                         hist_kws={
                             'histtype': 'step',
                             'linewidth': 1
                         })
            plt.xlim(-5, 50)

            plt.savefig(out_fig_name, dpi=300, bbox_inches='tight')
            # plt.close(i)

            # sns.distplot(df[col_id],
            #              bins=plot_bins,
            #              kde=False,
            #              norm_hist=True,
            #              hist_kws={
            #                  'histtype': 'step',
            #                  'linewidth': 1
            #              })

    # out_fig_name = os.path.join(save_dir, save_name)
    return


def category_plot(postcon_df, precon_df, save_dir, sub_num, seg_type):
    plot_df = pd.concat([postcon_df, precon_df])
    plot_df = plot_df.reset_index()
    # print(plot_df.head())
    sns_plot = sns.catplot(x="index",
                           y="mean",
                           hue="session",
                           kind="bar",
                           height=8,
                           aspect=1,
                           data=plot_df)

    # sns_plot.set_size_inches(11.7, 8.27)

    save_name = ('sub-' + sub_num + '_' + seg_type + '-summary.png')
    sns_plot.savefig(os.path.join(save_dir, save_name))

    return

def swarm_plot(filt_df, save_dir, seg_type):
    filt_df = filt_df.reset_index()
    print(filt_df.head())
    sns_plot = sns.catplot(x="sub_num",
                           y="mean",
                           hue="session",
                           kind="bar",
                           height=8,
                           aspect=1,
                           data=filt_df)

    # sns_plot.set_size_inches(11.7, 8.27)

    save_name = (seg_type + '-summary.png')
    sns_plot.savefig(os.path.join(save_dir, save_name))

    return

def session_summary(in_folder, sub_num, session, scan_type, seg_type):
    data_dir = os.path.join(datasink_dir, in_folder, 'sub-{}'.format(sub_num),
                            'ses-{}'.format(session), 'qutece')

    if not os.path.exists(data_dir):
        data_dir = os.path.join(datasink_dir, in_folder,
                                'sub-{}'.format(sub_num),
                                'ses-{}'.format(session))

    if not os.path.exists(data_dir):
        data_dir = os.path.join(datasink_dir, in_folder,
                                'sub-{}'.format(sub_num))

    roi_dir = os.path.join(manualwork_dir, 'segmentations', seg_type)

    if seg_type == 'Neuromorphometrics':
        ROI_file_name = '/opt/spm12/tpm/labels_Neuromorphometrics.nii'
    elif seg_type == 'noise':
        ROI_file_name = os.path.join(
            roi_dir,
            'rsub-' + sub_num + '_ses-Postcon_hr_run-01_UTE_desc-preproc' +
            '_noise-Segmentation-label.nii')
    elif seg_type == 'brain_preFLIRT':
        ROI_file_name = os.path.join(
            roi_dir,
            'rrrsub-' + sub_num + '_ses-Precon_T1w_*brain*' +
            '_Segmentation-label.nii')
        ROI_file_names = glob.glob(ROI_file_name)
        ROI_file_name = ROI_file_names[0]
        print(ROI_file_names[0])
    else:
        print('need valid segmentation type')

    ROI_file_nii = nib.load(ROI_file_name)
    roi_img = np.array(ROI_file_nii.get_fdata())
    session_pattern = '*' + session + '*' + scan_type + '*'
    path_pattern = os.path.join(data_dir, session_pattern)
    nii_files = glob.glob(path_pattern)
    print('Selected files are: ')
    print(nii_files)

    summary_df_list = []

    for f in nii_files:
        scan_file_name = f
        scan_file_nii = nib.load(scan_file_name)
        scan_img = np.array(scan_file_nii.get_fdata())

        if scan_img.size != roi_img.size:
            print('RESAMPLING')
            resampled_nii = nil.image.resample_to_img(scan_file_nii,
                                                      ROI_file_nii)
            scan_img = np.array(resampled_nii.get_fdata())

        extracted_df = roi_extract(scan_img, roi_img)

        save_dir = os.path.join(datasink_dir, 'plots',
                                'sub-{}'.format(sub_num),
                                'ses-{}'.format(session))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        hist_plots(extracted_df, seg_type, save_dir)

        summary_df = extracted_df.describe()
        print(summary_df)

        save_dir = os.path.join(datasink_dir, 'csv_work_2',
                                'sub-{}'.format(sub_num),
                                'ses-{}'.format(session))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        pth, fname, ext = split_filename(f)

        # save_name = ('sub-{}_ses-{}_' + scan_type + '_data_' +
        save_name = (fname + '_DATA_' + 'seg-{}.csv').format(seg_type)
        extracted_df.to_csv(os.path.join(save_dir, save_name), index=False)

        save_name = (fname + '_SUMMARY_' + 'seg-{}.csv').format(seg_type)
        summary_df.to_csv(os.path.join(save_dir, save_name))

        summary_df_list.append(summary_df)

    plt.close('all')
    return summary_df_list


def load_summary_dfs(csv_dir, sub_num, session, seg_type):
    data_dir = os.path.join(datasink_dir, csv_dir, 'sub-{}'.format(sub_num),
                            'ses-{}'.format(session))
    path_pattern = os.path.join(
        data_dir, '*' + scan_type + '*_SUMMARY_seg-' + seg_type + '*.csv')
    load_files = glob.glob(path_pattern)
    df_list = []
    for f in load_files:
        df = pd.read_csv(f)
        pth, fname, ext = split_filename(f)
        df.rename(columns={'Unnamed: 0': 'name'}, inplace=True)
        df = df.set_index('name').T
        df['session'] = session
        df['file'] = fname
        df_list.append(df)

    return df_list


def subject_summary(sub_num, scan_type, seg_type):
    csv_dir = 'csv_work_2'
    session = 'Precon'
    precon_df_list = load_summary_dfs(csv_dir, sub_num, session, seg_type)
    precon_df = pd.concat(precon_df_list)

    session = 'Postcon'
    postcon_df_list = load_summary_dfs(csv_dir, sub_num, session, seg_type)
    postcon_df = pd.concat(postcon_df_list)

    save_dir = os.path.join(datasink_dir, 'plots', 'sub-{}'.format(sub_num))
    category_plot(postcon_df, precon_df, save_dir, sub_num, seg_type)

    # print(postcon_df.head())

    return postcon_df, precon_df


def full_summary(datasink_dir, subject_list, scan_type, seg_type):
    csv_dir = 'csv_work_2'
    df_list = []
    for sub_num in subject_list:
        postcon_df, precon_df = subject_summary(sub_num, scan_type, seg_type)
        postcon_df['sub_num'] = sub_num
        precon_df['sub_num'] = sub_num
        print(postcon_df.head())
        df_list.append(postcon_df)
        df_list.append(precon_df)

    full_df = pd.concat(df_list)
    full_df = full_df.reset_index()
    print('full_df : ' )
    print(full_df.head())
    filt_df = full_df.loc[(full_df['index'] == '1.0')]
    print(filt_df.head())
    save_dir = os.path.join(datasink_dir, 'plots')
    swarm_plot(filt_df, save_dir, seg_type)
#
#     stats_df = intensity_stats(csv_files)
#
#     save_dir = os.path.join(datasink_dir, 'csv_work', seg_type,
#                 'sub-{}'.format(sub_num), 'ses-{}'.format(session))
#
#     if not os.path.exists(save_dir):
#         os.makedirs(save_dir)
#
#     save_name = ('sub-{}_ses-{}_' + scan_type + '_proc_' +
#                  'seg-{}.csv').format(sub_num, session, seg_type)
#
#     stats_df.to_csv(os.path.join(save_dir, save_name), index=False)
#     return stats_df
#
#

subject_list = [
    '02', '03', '04', '05', '06', '07', '08', '10', '11', '12', '13', '14',
    '15'
]
# subject_list = ['04', '05', '06', '07', '08', '10', '12', '13', '14', '15']
# subject_list = ['02', '11', '15']
# subject_list = ['11']
session_list = ['Postcon', 'Precon']
scan_type = 'hr'
# seg_type = 'Vesselness'
in_folder = 'nonlinear_transfomed_hr'

# seg_type = 'Neuromorphometrics'
# for sub_num in subject_list:
#     for session in session_list:
#         session_summary(in_folder, sub_num, session, scan_type, seg_type)
#     subject_summary(sub_num, scan_type, seg_type)

# subject_list = ['11', '12', '13', '14', '15']
# subject_list = ['08', '10']
# subject_list = ['11']

seg_type = 'noise'
# seg_type = 'brain_preFLIRT'
# for sub_num in subject_list:
#     session = 'Precon'
#     in_folder = 'pre_to_post_coregister'
#     session_summary(in_folder, sub_num, session, scan_type, seg_type)
#
#     session = 'Postcon'
#     in_folder = 'preprocessing'
#     session_summary(in_folder, sub_num, session, scan_type, seg_type)
#
#     subject_summary(sub_num, scan_type, seg_type)
full_summary(datasink_dir, subject_list, scan_type, seg_type)

#     roi_nii
#     exclude_nii
#     scan_list
