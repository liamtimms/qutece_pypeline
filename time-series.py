import nibabel as nib
import numpy as np
import pandas as pd
import os

upper_dir = os.path.realpath('../../derivatives/')
base_path = os.path.abspath(upper_dir)

subject_list = ['02', '03', '05', '06', '08', '10', '11']
subject_list = ['02', '03', '04', '06', '09', '10', '11']
subject_list = ['08']
#sub_num = '11'

# # Difference files
# '/mnt/4e43a4f6-7402-4881-bcf5-d280e54cc385/Analysis/DCM2BIDS3/derivatives/datasink/postminuspre_hr/sub-11'
#
# 'rsub-11_ses-Postcon_hr_run-03_UTE_divby_average_bias_reoriented_minus_average.nii'
#
# # Mask files
# '/mnt/4e43a4f6-7402-4881-bcf5-d280e54cc385/Analysis/DCM2BIDS3/derivatives/manualwork/WholeBrainSeg_FromNoseSkullStrip'
#
# 'rrrsub-02_ses-Precon_T1w_corrected_maths_reoriented_ROI_brain_brain_Segmentation-label.nii'

scan_type = 'fast'

for sub_num in subject_list:
    brain_ROI_filename = os.path.join(
        base_path, 'manualwork', 'WholeBrainSeg_FromNoseSkullStrip',
        'rrrsub-' + sub_num +
        '_ses-Precon_T1w_corrected_maths_reoriented_ROI_brain_brain_Segmentation-label.nii'
    )
    brain_ROI_nii = nib.load(brain_ROI_filename)
    brain_ROI_img = np.array(brain_ROI_nii.get_fdata())

    postminuspre_directory = os.path.join(base_path, 'datasink',
                                          'postminuspre_' + scan_type,
                                          'sub-' + sub_num)
    num_runs = len([
        name for name in os.listdir(postminuspre_directory)
        if os.path.isfile(os.path.join(postminuspre_directory, name))
    ])

    # precon_scan = 'rmeansub-' + sub_num + '_ses-Precon_fast-task-rest_run-01_desc-unring_UTE_corrected.nii'
    brain_aves = [[0] * 2 for i in range(num_runs)]
    print('sub-'+sub_num)
    print(num_runs)
    for run_num in range(1, num_runs + 1):
        if run_num < 10:
            str_run_num = '0' + str(run_num)
        else:
            str_run_num = str(run_num)

        print(str_run_num)

        if scan_type == 'fast':
            st = 'fast-task-rest'
            dsc = 'desc-preproc'
        else:
            st = scan_type
            dsc = 'divby_average_bias_reoriented'

        postminuspre_filename = os.path.join(
            postminuspre_directory, 'rsub-' + sub_num + '_ses-Postcon_' + st +
            '_run-' + str_run_num + '_UTE_' + dsc + '_minus_average.nii')

        postminuspre_nii = nib.load(postminuspre_filename)
        postminuspre_nii.set_data_dtype(np.double)
        postminuspre_img = np.array(postminuspre_nii.get_fdata())

        brain_crop_img = np.multiply(postminuspre_img, brain_ROI_img)
        brain_vals = np.reshape(brain_crop_img, -1)
        brain_ave = np.nanmean(brain_vals[np.nonzero(brain_vals)])
        #    brain_aves.append(brain_ave)
        brain_aves[run_num - 1][1] = brain_ave
        brain_aves[run_num - 1][0] = run_num

    ave_filename = os.path.join(
        base_path, 'manualwork', 'timeseries',
        'sub-' + sub_num + '_' + scan_type + '_brain-aves.csv')
    export = pd.DataFrame(brain_aves)
    export.to_csv(ave_filename, index=False)
