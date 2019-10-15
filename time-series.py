import nibabel as nib
import numpy as np
import pandas as pd 
import os

base_path = '/run/media/mri/4e43a4f6-7402-4881-bcf5-d280e54cc385/Analysis/DCM2BIDS2/derivatives'

sub_num = '11'
brain_ROI_filename = os.path.join(base_path, 'manualwork', 'brain_seg', 'sub-' + sub_num +
        '_ses-Difference_fast-task-rest_brain-label.nii')
brain_ROI_nii = nib.load(brain_ROI_filename)
brain_ROI_img = np.array(brain_ROI_nii.get_data())

postminuspre_directory = os.path.join(base_path, 'datasink','postminuspre','sub-' + sub_num)
num_runs = len([name for name in os.listdir(postminuspre_directory) if os.path.isfile(os.path.join(postminuspre_directory, name))])
precon_scan = 'rmeansub-'+sub_num+'-Precon_fast-task-rest_run-01_desc-unring_UTE_corrected.nii'
brain_aves = []
for run_num in range(1,num_runs):
    if run_num < 10:
        str_run_num = '0' + str(run_num)
    else:
        str_run_num = str(run_num)

    postminuspre_filename = os.path.join(postminuspre_directory, 'rsub-' + 
            sub_num + '_ses-Postcon_fast-task-rest_run-' + str_run_num + 
            '_desc-unring_UTE_corrected_minus_'+ precon_scan)
            
    postminuspre_nii = nib.load(postminuspre_filename)
    postminuspre_nii.set_data_dtype(np.double)
    postminuspre_img = np.array(postminuspre_nii.get_data())

    brain_crop_img = postminuspre_img @ brain_ROI_img
    brain_vals = np.reshape(brain_crop_img, -1)
    brain_ave = brain_vals[np.nonzero(brain_vals)].mean()
    brain_aves.append(brain_ave)

ave_filename = os.path.join(base_path, 'manualwork', 'timeseries', 
        'sub-' + sub_num + '_brain-aves.csv')
export = pd.DataFrame(brain_aves)
export.to_csv(ave_filename, index=False)


