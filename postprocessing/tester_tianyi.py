import os

import nibabel as nib
import numpy as np
from skimage.filters import frangi

base_dir = os.path.abspath('../..')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
manualwork_dir = os.path.join(base_dir, 'derivatives', 'manualwork')

def SetAlpha(suppressPlates):
    return 0.000 + 3.0 * pow(suppressPlates / 100.0, 2)


def SetBeta(suppressBlobs):
    return 0.001 + 1.0 * pow((100.0 - suppressBlobs) / 100.0, 2)

subject_list = ['02']
for subject_num in subject_list:
    scan_dir = os.path.join(datasink_dir, 'preprocessing',
                            'sub-' + subject_num, 'ses-Postcon', 'qutece')
    scan_file_name = 'rsub-' + subject_num + '_ses-Postcon_hr_run-03_UTE_desc-preproc.nii'
    scan_file = os.path.join(scan_dir, scan_file_name)
    scan_nii = nib.load(scan_file)
    scan_img = np.array(scan_nii.get_fdata())
    scan_img[np.isnan(scan_img)] = 0
    scan_img[scan_img < 0] = 0
    scan_nii = nib.Nifti1Image(scan_img, scan_nii.affine, scan_nii.header)

    #suppressBlobs = 40
    #suppressPlates = 25
    suppressBlobs_list = [40]
    suppressPlates_list = [25]

    #alpha = SetAlpha(suppressPlates)
    #beta = SetBeta(suppressBlobs)
    gamma_list = [p * 177 for p in [0.25]]
    sigma_max_list = [3]
    sigma_step_list = [0.4]

    params_space = [(suppressPlates, suppressBlobs, gamma, sigma_max,
                     sigma_step) for suppressPlates in suppressPlates_list
                    for suppressBlobs in suppressBlobs_list
                    for gamma in gamma_list for sigma_max in sigma_max_list
                    for sigma_step in sigma_step_list]

    #for gamma in gamma_list:
    for params in params_space:
        suppressPlates, suppressBlobs, gamma, sigma_max, sigma_step = params
        alpha = SetAlpha(suppressPlates)
        beta = SetBeta(suppressBlobs)
        print('running frangi with gamma = ' + str(gamma) )
        vesselness_img = frangi(scan_img,
                                sigmas=range(1, sigma_max, sigma_step),
                                alpha=alpha,
                                beta=beta,
                                gamma=gamma,
                                black_ridges=False)
        print('finished')

save_name = 'rsub-02_ses-Postcon_hr_run-03_UTE_desc-preproc_maths_flirt_Vesselness.nii'
save_nii = nib.Nifti1Image(vesselness_img, header=scan_nii.header, affine=scan_nii.affine)
nib.save(save_nii, save_name)
