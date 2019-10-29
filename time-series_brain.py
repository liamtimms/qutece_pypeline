import nibabel as nib
import numpy as np
import pandas as pd
import os

base_path = '/run/media/mri/4e43a4f6-7402-4881-bcf5-d280e54cc385/Analysis/DCM2BIDS2_NoBiasCorr/derivatives'

subject_list = ['02', '03', '05', '06', '08', '10', '11']
#sub_num = '11'
#subject_list = ['11']

for sub_num in subject_list:
#    brain_ROI_filename = os.path.join(base_path, 'manualwork', 'brain_seg', 'sub-' + sub_num +
#            '_ses-Difference_fast-task-rest_brain-label.nii')
    brain_ROI_filename = '/opt/spm12/tpm/mask_ICV.nii'
    brain_ROI_nii = nib.load(brain_ROI_filename)
    brain_ROI_img = np.array(brain_ROI_nii.get_data())

    scan_directory = os.path.join(base_path, 'datasink','SpatialNoramlization_allOtherScans','sub-' + sub_num)
    num_runs = len([name for name in os.listdir(scan_directory) if os.path.isfile(os.path.join(scan_directory, name))])
    precon_scan = 'rmeansub-'+sub_num+'_ses-Precon_fast-task-rest_run-01_desc-unring_UTE.nii'
    brain_aves = [[0]*2 for i in range(num_runs)]
    print(num_runs)
    for run_num in range(1,num_runs+1):
        if run_num < 10:
            str_run_num = '0' + str(run_num)
        else:
            str_run_num = str(run_num)

        print(str_run_num)

        scan_filename = os.path.join(scan_directory, 'rsub-' +
                sub_num + '_ses-Postcon_fast-task-rest_run-' + str_run_num +
                '_desc-unring_UTE_minus_'+ precon_scan)

        scan_nii = nib.load(scan_filename)
        scan_nii.set_data_dtype(np.double)
        scan_img = np.array(scan_nii.get_data())

        brain_crop_img = np.multiply(scan_img, brain_ROI_img)
        brain_vals = np.reshape(brain_crop_img, -1)
        brain_ave = np.nanmean(brain_vals[np.nonzero(brain_vals)])
    #    brain_aves.append(brain_ave)
        brain_aves[run_num-1][1]=brain_ave
        brain_aves[run_num-1][0]=run_num

    ave_filename = os.path.join(base_path, 'manualwork', 'timeseries',
            'sub-' + sub_num + '_brain-aves.csv')
    export = pd.DataFrame(brain_aves)
    export.to_csv(ave_filename, index=False)


