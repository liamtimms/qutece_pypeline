import nibabel as nib
import numpy as np
from skimage.filters import frangi


def SetAlpha(suppressPlates):
    return 0.000 + 3.0 * pow(suppressPlates / 100.0, 2)


def SetBeta(suppressBlobs):
    return 0.001 + 1.0 * pow((100.0 - suppressBlobs) / 100.0, 2)


scan_file_name = 'rsub-02_ses-Postcon_hr_run-03_UTE_desc-preproc_maths_flirt.nii'
scan_nii = nib.load(scan_file_name)
scan_img = np.array(scan_nii.get_fdata())
scan_img[np.isnan(scan_img)] = 0
scan_img[scan_img < 0] = 0
scan_nii = nib.Nifti1Image(scan_img, scan_nii.affine, scan_nii.header)

suppressBlobs = 50
suppressPlates = 10

alpha = SetAlpha(suppressPlates)
beta = SetBeta(suppressBlobs)
gamma = 177 * 0.75

vesselness_img = frangi(scan_img,
                        sigmas=range(1, 5, 1),
                        alpha=alpha,
                        beta=beta,
                        gamma=gamma,
                        black_ridges=False)

save_name = 'rsub-02_ses-Postcon_hr_run-03_UTE_desc-preproc_maths_flirt_Vesselness_liam.nii'
save_nii = nib.Nifti1Image(vesselness_img,
                           header=scan_nii.header,
                           affine=scan_nii.affine)
nib.save(save_nii, save_name)
