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
        vals_df_list.append(vals_df)
        # h = sns.distplot(vals_df)

        # ave = np.nanmean(vals)
        # std = np.nanstd(vals)
        # N = np.count_nonzero(~np.isnan(vals))
        # out_data[n][0] = r
        # out_data[n][1] = ave
        # out_data[n][2] = std
        # out_data[n][3] = N
        n = n + 1

    extracted_df = pd.concat(vals_df_list, ignore_index=True, axis=1)

    return extracted_df


def hist_plots(df, save_dir):
    sns.set(color_codes=True)
    sns.set(style="white", palette="muted")
    # plot_xlim_min = 0
    # plot_xlim_max = 1000

    for i, col in enumerate(df.columns):
        vals = df[col].to_numpy()
        w = 20
        n = math.ceil((np.nanmax(vals) - np.nanmin(vals)) / w)

        if n > 0:
            plt.figure(i)
            save_name = str(col) + '.png'
            out_fig_name = os.path.join(save_dir, save_name)
            sns.distplot(df[col],
                         kde=False,
                         bins=n,
                         hist_kws={
                             'histtype': 'step',
                             'linewidth': 1
                         })
            plt.xlim(-10, 1990)

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


def hist_plot_both(postcon_df, precon_df):
    return


def session_summary(in_folder, sub_num, session, scan_type, seg_type):
    data_dir = os.path.join(datasink_dir, in_folder, 'sub-{}'.format(sub_num),
                            'ses-{}'.format(session))

    if not os.path.exists(data_dir):
        data_dir = os.path.join(datasink_dir, in_folder,
                                'sub-{}'.format(sub_num))

    if seg_type == 'Neuromorphometrics':
        ROI_file_name = '/opt/spm12/tpm/labels_Neuromorphometrics.nii'

    ROI_file_nii = nib.load(ROI_file_name)
    roi_img = np.array(ROI_file_nii.get_fdata())

    session_pattern = '*' + session + '*' + scan_type + '*'
    path_pattern = os.path.join(data_dir, session_pattern)
    nii_files = glob.glob(path_pattern)
    print('Selected files are: ')
    print(nii_files)

    for f in nii_files:
        scan_file_name = f
        scan_file_nii = nib.load(scan_file_name)
        scan_img = np.array(scan_file_nii.get_fdata())

        if scan_img.size != roi_img.size:
            resampled_nii = nil.image.resample_to_img(scan_file_nii,
                                                      ROI_file_nii)
            scan_img = np.array(resampled_nii.get_fdata())

        extracted_df = roi_extract(scan_img, roi_img)

        save_dir = os.path.join(datasink_dir, 'plots',
                                'sub-{}'.format(sub_num),
                                'ses-{}'.format(session))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        hist_plots(extracted_df, save_dir)

        summary_df = extracted_df.describe()
        print(summary_df)

        save_dir = os.path.join(datasink_dir, 'csv_work_2',
                                'sub-{}'.format(sub_num),
                                'ses-{}'.format(session))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        pth, fname, ext = split_filename(f)

        # save_name = ('sub-{}_ses-{}_' + scan_type + '_data_' +
        save_name = (fname + '_DATA_' +
                     'seg-{}.csv').format(seg_type)
        extracted_df.to_csv(os.path.join(save_dir, save_name), index=False)

        save_name = (fname + '_SUMMARY_' +
                     'seg-{}.csv').format(sub_num, session, seg_type)
        summary_df.to_csv(os.path.join(save_dir, save_name), index=False)

        return summary_df


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
# subject_list = ['11']
session_list = ['Postcon', 'Precon']
scan_type = 'hr'
seg_type = 'Neuromorphometrics'
in_folder = 'nonlinear_transfomed_hr'

for sub_num in subject_list:
    for session in session_list:
        session_summary(in_folder, sub_num, session, scan_type, seg_type)
#     roi_nii
#     exclude_nii
#     scan_list
