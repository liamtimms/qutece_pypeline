
from nipype.workflows.smri.freesurfer import create_reconall_workflow

working_dir = os.path.abspath('/mnt/hgfs/VMshare/WorkingBIDS/')
output_dir = os.path.join(working_dir, 'derivatives/')
temp_dir = os.path.join(output_dir, 'datasink/')
#subject_list = ['02', '03', '05', '06', '08', '10', '11']
#subject_list =['11']
subject = 11

session = 'Precon'
# * precon T1w from IntersessionCoregister_preconScans
scanfolder = 'IntersessionCoregister_preconScans'
subdirectory = os.path.join(temp_dir, scanfolder)
filestart = 'sub-'+ subject +'_ses-'+ session +'_'
precon_T1w_files  = 'rr'+filestart+'T1w.nii'

recon_all = create_reconall_workflow()
recon_all.inputs.inputspec.subject_id = 'sub-'+subject
recon_all.inputs.inputspec.subjects_dir = subdirectory
recon_all.inputs.inputspec.T1_files = precon_T1w_files 
recon_all.run()
