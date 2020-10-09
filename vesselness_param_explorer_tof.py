import os
import numpy as np
import pandas as pd
import nibabel as nib
from plotter import roi_cut
from skimage.filters import frangi

base_dir = os.path.abspath('../..')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
manualwork_dir = os.path.join(base_dir, 'derivatives', 'manualwork')


def SetAlpha(suppressPlates):
    return 0.000 + 3.0 * pow(suppressPlates / 100.0, 2)


def SetBeta(suppressBlobs):
    return 0.001 + 1.0 * pow((100.0 - suppressBlobs) / 100.0, 2)


# def load_scan(subject_num, scan_type):
#     upper_dir = os.path.realpath('../..')
#     basefolder = os.path.abspath(os.path.join(upper_dir, 'derivatives'))
#
#     if scan_type == 'hr':
#         scanfolder = os.path.join(basefolder, 'datasink', 'preprocessing',
#                                   'sub-' + subject_num, 'ses-Postcon',
#                                   'qutece')
#         infile = '*sub-' + subject_num + '_ses-Postcon_hr_run-*-preproc'
#
#         outfolder = os.path.join(basefolder, 'manualwork',
#                                  'vesselness_filtered_4', 'sub-'+subject_num)
#     elif scan_type == 'TOF':
#         scanfolder = os.path.join(basefolder, 'datasink',
#                                   'pre_to_post_coregister',
#                                   'sub-' + subject_num)
#         infile = '*sub-' + subject_num + '_ses-Precon_TOF*angio_corrected'
#
#         outfolder = os.path.join(basefolder, 'manualwork',
#                                  'vesselness_filtered_4', 'sub-'+subject_num)
#     if not os.path.exists(outfolder):
#         os.makedirs(outfolder)
#
#     infiles = os.path.join(basefolder, scanfolder, infile + '.nii')
#
#     return


def vess_roi_extract(scan_img, roi_img):
    t = 'greater'
    r = -1000
    crop_img, vals_df = roi_cut(scan_img, roi_img, t, r)
    summary_df = vals_df.describe()
    unique_roi = np.unique(roi_img)

    for r in unique_roi:
        # t = 'equal'
        crop_img, vals_df = roi_cut(scan_img, roi_img, t, r)
        r_summary_df = vals_df.describe()
        summary_df = pd.merge(summary_df,
                              r_summary_df,
                              left_index=True,
                              right_index=True)
        print(r_summary_df.head())

    return summary_df


def run_vess(scan_img, params):
    suppressPlates, suppressBlobs, gamma, sigma_max, sigma_step = params
    alpha = SetAlpha(suppressPlates)
    beta = SetBeta(suppressBlobs)

    # Run FRANGI filter
    vessel_img = frangi(scan_img,
                        sigmas=range(1, sigma_max, sigma_step),
                        alpha=alpha,
                        beta=beta,
                        gamma=gamma,
                        black_ridges=False)

    return vessel_img


def parameter_test(scan_img, mask_img, suppressBlobs_list, suppressPlates_list,
                   gamma_list, sigma_max_list, sigma_step_list):

    # scan_img = scan_img.astype('int32')
    params_space = [(suppressPlates, suppressBlobs, gamma, sigma_max,
                     sigma_step) for suppressPlates in suppressPlates_list
                    for suppressBlobs in suppressBlobs_list
                    for gamma in gamma_list for sigma_max in sigma_max_list
                    for sigma_step in sigma_step_list]

    print('testing parameter combinations : ')
    print(len(params_space))

    N_brain = np.sum(mask_img)

    df_list = []

    for params in params_space:

        # set parameters for Frangi
        suppressPlates, suppressBlobs, gamma, sigma_max, sigma_step = params
        alpha = SetAlpha(suppressPlates)
        beta = SetBeta(suppressBlobs)
        print(params)

        while True:
            try:
                # Run FRANGI filter
                vessel_img = frangi(scan_img,
                                    sigmas=range(1, sigma_max, sigma_step),
                                    alpha=alpha,
                                    beta=beta,
                                    gamma=gamma,
                                    black_ridges=False)
                # crop initial brain from both scan and vesselness
                t = 'equal'
                r = 1
                cropped_img, __ = roi_cut(scan_img, mask_img, t, r)
                vessel_img, __ = roi_cut(vessel_img, mask_img, t, r)

                # Construct Vessel ROI (pulled from plotter.py)
                cut_off = 0.95
                med_cut_off = 0.85
                small_cut_off = 0.05
                large_vess = (vessel_img >= cut_off).astype(int) * 4
                print('large vessel :')
                print(np.sum(large_vess))

                med_vess = ((vessel_img < cut_off) &
                            (vessel_img >= med_cut_off)).astype(int) * 3

                print('med vessel :')
                print(np.sum(med_vess))

                small_vess = ((vessel_img < med_cut_off) &
                              (vessel_img >= small_cut_off)).astype(int) * 2

                print('small vessel :')
                print(np.sum(small_vess))

                no_vess = ((vessel_img < small_cut_off) &
                           (vessel_img > 0)).astype(int) * 1
                # So we have
                # ['no_vess':1, 'small_vess':2, 'med_vess':3, 'large_vess':4]
                vessel_roi_img = no_vess + med_vess + small_vess + large_vess

                summary_df = vess_roi_extract(cropped_img, vessel_roi_img)
                df = summary_df.T

                df['gamma'] = gamma
                df['suppressBlobs'] = suppressBlobs
                df['suppressPlates'] = suppressPlates
                df['sigma_max'] = sigma_max
                df['sigma_step'] = sigma_step

                df['d'] = df['count'] / N_brain
                df['Quality'] = df['mean'] * df['d']
                df_list.append(df)
                print('FINISHED')
                break

            except np.linalg.LinAlgError as err:
                print('FAILED')
                break

        # seg_type = 'vesselness_test'
        # save_dir = os.path.join('temp-vesselness')
        # if not os.path.exists(save_dir):
        #     os.makedirs(save_dir)

        # fname = os.path.join('TEST' + '_g=' + str(round(gamma)) + '_sb=' +
        #                      str(suppressBlobs) + '_sp=' +
        #                      str(suppressPlates) + '_sig=' + str(sigma_max) +
        #                      '_ss=' + str(sigma_step))

    full_df = pd.concat(df_list)
    return full_df, vessel_img, vessel_roi_img


def main():

    subject_list = ['02']
    for subject_num in subject_list:
        scan_dir = os.path.join(datasink_dir, 'pre_to_post_coregister',
                                'sub-' + subject_num)
        scan_file_name = 'rrrsub-' + subject_num + '_ses-Precon_TOF_run-01_angio_corrected.nii'
        scan_file = os.path.join(scan_dir, scan_file_name)

        scan_nii = nib.load(scan_file)
        scan_img = np.array(scan_nii.get_fdata())
        scan_img[np.isnan(scan_img)] = 0
        scan_img[scan_img < 0] = 0
        scan_nii = nib.Nifti1Image(scan_img, scan_nii.affine, scan_nii.header)
        mean = 59

        suppressBlobs_list = [10, 15, 25, 30, 40, 50]
        suppressPlates_list = [10, 15, 25, 30]
        gamma_list = [p * mean for p in [0.1, 0.25, 0.50, 0.75, 1]]

        sigma_max_list = [3]
        sigma_step_list = [1]

        # TODO: actual brain mask filename
        ROI_dir = os.path.join(manualwork_dir, 'segmentations', 'brain_mask4bias',
                               'sub-' + subject_num)
        ROI_file_name = ('rrrsub-' + subject_num +
                        '_ses-Precon_TOF_angio_corrected_Segmentation-label.nii')
        ROI_file = os.path.join(ROI_dir, ROI_file_name)
        ROI_file_nii = nib.load(ROI_file)
        mask_img = np.array(ROI_file_nii.get_fdata())

        full_df, __, __ = parameter_test(scan_img, mask_img, suppressBlobs_list,
                                         suppressPlates_list, gamma_list,
                                         sigma_max_list, sigma_step_list)

        save_dir = os.path.join(manualwork_dir, 'vesselness_optimization')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        save_name = 'sub-' + subject_num + '_TOF_vesselness_testing.csv'
        print(os.path.join(save_dir, save_name))
        full_df.to_csv(os.path.join(save_dir, save_name))

    # save_name = 'sub-' + subject_num + '_UTE_vesselness_testing.nii'
    # vessel_nii = nib.Nifti1Image(vessel_img, scan_nii.affine, scan_nii.header)
    # nib.save(vessel_nii, os.path.join(save_dir, save_name))
    # save_name = 'sub-' + subject_num + '_UTE_vesselness_testing_label.nii'
    # vessel_roi_nii = nib.Nifti1Image(vessel_roi_img, scan_nii.affine, scan_nii.header)
    # nib.save(vessel_roi_nii, os.path.join(save_dir, save_name))

    return


if __name__ == "__main__":
    main()
