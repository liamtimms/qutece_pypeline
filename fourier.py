import nibabel as nib
import numpy as np
import os

base_path = '/run/media/mri/4e43a4f6-7402-4881-bcf5-d280e54cc385/Analysis/DCM2BIDS2/derivatives'

subject_list = ['02', '03', '05', '06', '08', '10', '11']
#sub_num = '11'

fastfourier = np.fft.fftn(postcon_img)

# -----------------------------------------------------------------------------

        postminuspre_nii = nib.load(postminuspre_filename)
        postminuspre_nii.set_data_dtype(np.double)
        postminuspre_img = np.array(postminuspre_nii.get_data())

        brain_crop_img = np.multiply(postminuspre_img, brain_ROI_img)
        brain_vals = np.reshape(brain_crop_img, -1)
        brain_ave = np.nanmean(brain_vals[np.nonzero(brain_vals)])


# -----------------------------------------------------------------------------
        diff_img = file2_img - file1_img
        diff_nii = nib.Nifti1Image(diff_img, file1_nii.affine, file2_nii.header)

        # from https://nipype.readthedocs.io/en/latest/devel/python_interface_devel.html
        pth, fname1, ext = split_filename(file1_name)
        pth, fname2, ext = split_filename(file2_name)
        diff_file_name = os.path.join(fname2 + '_minus_' + fname1 + '.nii')
        nib.save(diff_nii, diff_file_name)
