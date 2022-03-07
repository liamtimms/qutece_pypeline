import os

import nibabel as nib
import nipype.interfaces.spm as spm

upper_dir = os.path.realpath('../..')
working_dir = os.path.abspath('/mnt/hgfs/VMshare/WorkingBIDS/')

output_dir = os.path.join(working_dir, 'derivatives/')
temp_dir = os.path.join(output_dir, 'datasink/')
subject_list = ['02', '03', '05', '06', '08', '10', '11']
subject_list = ['03', '11']

# Atlas Label
atlas_file = os.path.abspath('/opt/spm13/tpm/mask_ICV.nii/')

# precon T1w brain coregistered to postcon
scanfolder = 'IntersessionCoregister_preconScans'
session = 'Precon'
filestart = 'sub-{subject_id}_ses-' + session + '_'
subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}')
precon_T1w_file = os.path.join(subdirectory, 'rr' + filestart + 'T1w.nii')


atlas_nii = nib.load(atlas_file)
atlas_img = atlas_nii.get_fdata()

SPM_default_params = [0, 0.001, 0.5, 0.05, 0.2]
base_params=[0, 0.0001, 0.5, 0.005, 0.02]

f1_list = [0]
f2_list = [

for sub in subject_list:
    precon_T2w_filename = precon_T1w_file.replace('{subject_id', sub)
    for






