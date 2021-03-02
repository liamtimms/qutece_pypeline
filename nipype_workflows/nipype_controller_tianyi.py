import os
import CustomNiPype as cnp
from nipype_initial_braincrop import initial_braincrop
from nipype_preproc import preproc
from nipype_preproc_nofast import preproc_nofast
# from nipype_preproc_nofast import PreprocNoFast_workflow
from nipype_preproc_08 import preproc_08
from nipype_preproc_10 import preproc_10
from nipype_intrasession_coregister import intrasession_coregister
from nipype_pre_to_post_coregister import pre_to_post_coregister
from nipype_braincrop import braincrop
from nipype_calc_transforms import calc_transforms
from nipype_post_pre_difference import post_pre_difference
from nipype_apply_transforms import apply_linear_trans
from nipype_apply_transforms import apply_nonlinear_trans
from nipype_tissue_wmh_analysis import tissue_wmh_analysis
from nipype_wm_analysis import wm_analysis
from nipype_vessel_density import vessel_density
# from nipype_normalize_semiauto_postFLIRT import fnirt_and_fast
# from nipype_normalize_applytrans_nonUTE import ApplyTransAnat_workflow
# from nipype_timeseries_roi import TimeSeries_ROI_workflow
# from nipype_cbv_whbrain import CBV_WholeBrain_workflow
# from textme import textme

# TODO:  check if run, seperate into higher level functions?

upper_dir = os.path.realpath('../..')
working_dir = os.path.abspath(upper_dir)
session_list = ['Precon', 'Postcon']
workflow_list = []
workflow_list_2 = []

# # Subjects with both hr and fast scans
# # subject_list = ['02', '03', '04', '06', '11']
# subject_list = [
#     '02', '03', '04', '05', '06', '07', '08',
#     '10', '11', '12', '13', '14', '15'
# ]
# initial_braincrop_wf = initial_braincrop(working_dir, subject_list,
#                                          session_list)
# # workflow_list.append(initial_braincrop_wf)
#
#
# # Subjects with all main scan types, pre and post
# subject_list = ['02', '03', '04', '06', '11', '12', '15']
# preproc_wf = preproc(working_dir, subject_list, session_list)
# workflow_list.append(preproc_wf)
#
# # Subjects without Fast Scans
# subject_list = ['05', '07', '09']
# preproc_nofast_wf = preproc_nofast(working_dir, subject_list, session_list)
# workflow_list.append(preproc_nofast_wf)
#
# # Subjects with Fast Scans but only one precon scan
# subject_list = ['08', '13', '14']
# session_list = ['Precon']
# preproc_08_pre_wf = preproc_08(working_dir, subject_list, session_list)
# workflow_list.append(preproc_08_pre_wf)
# session_list = ['Postcon']
# preproc_08_post_wf = preproc(working_dir, subject_list, session_list)
# workflow_list.append(preproc_08_post_wf)
#
# Subject with only one precon scan, also missing Fast
# subject_list = ['10']
# session_list = ['Precon']
# preproc_10_pre_wf = preproc_10(working_dir, subject_list, session_list)
# workflow_list.append(preproc_10_pre_wf)
# session_list = ['Postcon']
# preproc_10_post_wf = preproc(working_dir, subject_list, session_list)
# workflow_list.append(preproc_10_post_wf)

# ----------------------------------------------------------------------------
# Manual manipulation here:
# * copy sub-09_ses-Postcon_run-03_T1w.nii as sub-09_ses-Postcon_T1w.nii
# * rename sub-10_ses-Precon_hr_UTE_desc-preproc.nii
#           to rsub-10_ses-Precon_hr_UTE_desc-preproc.nii
# * copy rsub-10_ses-Precon_hr_UTE_desc-preproc.nii
#           as rmeansub-10_ses-Precon_hr_UTE_desc-preproc.nii
# ----------------------------------------------------------------------------
#
# # All Preproc'd Subjects
# subject_list = ['02', '03', '04', '05', '06', '07', '08', '10', '11', '12', '13', '14', '15']
# session_list = ['Precon']
# coreg_wf = intrasession_coregister(working_dir, subject_list, session_list)
# workflow_list.append(coreg_wf)
#
# # Subjects with nonT1w postcon scans
# subject_list = ['02', '03', '04', '05', '06', '07', '08', '10', '11']
# session_list = ['Postcon']
# coreg_wf = intrasession_coregister(working_dir, subject_list, session_list)
# workflow_list.append(coreg_wf)
#
# # Subjects without nonT1w postcon scans
# # subject_list = ['12', '13', '14', '15']
# # coreg_wf = intrasession_coregister(working_dir, subject_list, session_list)
# # workflow_list.append(coreg_wf)
#
# # All Coreg'd Subjects
# subject_list = ['02', '03', '04', '05', '06', '07', '08', '10', '11', '12', '13', '14', '15']
#
# # subject_list = ['02', '03', '04', '06', '11', '12', '15']
# coreg2_wf = pre_to_post_coregister(working_dir, subject_list)
# workflow_list.append(coreg2_wf)
#
# braincrop_wf = braincrop(working_dir, subject_list)
# workflow_list.append(braincrop_wf)
#
# ----------------------------------------------------------------------------
# # AT THIS POINT MANUAL MASKS MUST BE COMPLETED USING THE BRAIN CROPPED IMAGES
# ----------------------------------------------------------------------------
# # subject_list = ['08', '09', '10']
# # subject_list = ['02', '03', '04', '05', '06', '07', '08', '09', '10', '11']
#
# subject_list = ['02', '03', '04', '06', '08', '11', '12', '13', '14', '15']
# calc_transforms_wf = calc_transforms(working_dir, subject_list)
# workflow_list_2.append(calc_transforms_wf)
#
# session_list = ['Precon', 'Postcon']
# scan_type = 'hr'
#
# apply_transforms_hr_wf = apply_linear_trans(working_dir, subject_list, scan_type)
# workflow_list_2.append(apply_transforms_hr_wf)
#
# apply_nonlinear_transforms_hr_wf = apply_nonlinear_trans(working_dir, subject_list, session_list, scan_type)
# workflow_list_2.append(apply_nonlinear_transforms_hr_wf)
#
# ----------------------------------------------------------------------------
# # Vesselness parameters should be dicided with vmtk_vesselness_param_explorer.py
# #   and final vesselness segmentation should be organized in to_use folder
# ----------------------------------------------------------------------------
#
# subject_list = ['02', '03', '04', '05', '06', '07', '08', '10', '11', '12','13', '14', '15']
# tissue_wf = tissue_wmh_analysis(working_dir, subject_list)
# workflow_list_2.append(tissue_wf)

# subject_list = ['02', '06','11']
# wm_wf = wm_analysis(working_dir, subject_list)
# workflow_list_2.append(wm_wf)
# scan_type = 'fast'
# apply_transforms_fast_wf = apply_linear_trans(working_dir, subject_list, scan_type)
# workflow_list_2.append(apply_transforms_fast_wf)
#
# apply_nonlinear_transforms_fast_wf = apply_nonlinear_trans(working_dir, subject_list, session_list, scan_type)
# workflow_list_2.append(apply_nonlinear_transforms_fast_wf)
#
# ROI_types = ['brain', 'blood']
# scan_types = ['hr']
# subject_list = ['11']
# session_list = ['Precon', 'Postcon']
# num_cores = 1
# for ROI_type in ROI_types:
#     for scan_type in scan_types:
#         TimeSeries_ROI_workflow(working_dir, subject_list, session_list,
#                                 num_cores, scan_type, ROI_type)
#
# subject_list = ['02', '03', '04', '05', '06', '07', '09', '11']
# subject_list = ['02', '03', '04', '06', '09', '11']
#
# scan_type = 'hr'
# CBV_WholeBrain_workflow(working_dir, subject_list, num_cores, scan_type)

# subject_list = ['02', '03', '04', '05', '06', '07', '08', '11', '12','13', '14', '15']
# density_wf = vessel_density(working_dir, subject_list)
# workflow_list_2.append(density_wf)

subject_list = ['02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12','13', '14', '15']
diff_wf = post_pre_difference(working_dir, subject_list, scan_type='hr', scanfolder='nonlinear_transfomed_hr')
workflow_list_2.append(diff_wf)

# num_cores = 1
#
# for workflow in workflow_list:
#     cnp.workflow_runner(workflow, num_cores)
#
num_cores = 12

for workflow in workflow_list_2:
    cnp.workflow_runner(workflow, num_cores)

os.system("espeak 'pipeline run done'")
