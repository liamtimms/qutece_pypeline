import os

from nipype.workflows.smri.freesurfer import create_reconall_workflow

working_dir = os.path.abspath('/mnt/hgfs/VMshare/WorkingBIDS/')
output_dir, temp_dir, workflow_dir, _, _ = cnp.set_common_dirs(working_dir)
#subject_list = ['02', '03', '05', '06', '08', '10', '11']
#subject_list =['11']
subject = '11'

session = 'Precon'
# * precon T1w from IntersessionCoregister_preconScans
scanfolder = 'IntersessionCoregister_preconScans'
subdirectory = os.path.join(temp_dir, scanfolder)
filestart = 'sub-' + subject + '_ses-' + session + '_'
precon_T1w_files = os.path.join(subdirectory, 'sub-' + subject,
                                'rr' + filestart + 'T1w.nii')

recon_all = create_reconall_workflow()
recon_all.inputs.inputspec.subject_id = 'sub-' + subject
recon_all.inputs.inputspec.subjects_dir = subdirectory
recon_all.inputs.inputspec.T1_files = precon_T1w_files
