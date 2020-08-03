import os
import CustomNiPype as cnp
from nipype_initial_braincrop import initial_braincrop
from nipype_preproc import preproc
from nipype_preproc_nofast import preproc_nofast
# from nipype_preproc_nofast import PreprocNoFast_workflow
from nipype_preproc_08 import preproc_08
# from nipype_preproc_10 import Preproc10_workflow
from nipype_intrasession_coregister import intrasession_coregister
from nipype_pre_to_post_coregister import pre_to_post_coregister
from nipype_braincrop import braincrop
from nipype_calc_transforms import calc_transforms
from nipype_post_pre_difference import post_pre_difference
from nipype_apply_transforms import apply_linear_trans
from nipype_apply_transforms import apply_nonlinear_trans
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

# Subjects with both hr and fast scans
# subject_list = ['02', '03', '04', '06', '11']
subject_list = [
    '02', '03', '04', '05', '06', '07', '08',
    '10', '11', '12', '13', '14', '15'
]
initial_braincrop_wf = initial_braincrop(working_dir, subject_list,
                                         session_list)
# workflow_list.append(initial_braincrop_wf)


# Subjects with all main scan types, pre and post
subject_list = ['02', '03', '04', '06', '11', '12', '15']
preproc_wf = preproc(working_dir, subject_list, session_list)
workflow_list.append(preproc_wf)

# Subjects without Fast Scans
subject_list = ['05', '07', '09']
preproc_nofast_wf = preproc_nofast(working_dir, subject_list, session_list)
workflow_list.append(preproc_nofast_wf)

# Subjects with Fast Scans but only one precon scan
subject_list = ['08', '13', '14']
session_list = ['Postcon']
preproc_wf = preproc(working_dir, subject_list, session_list)
workflow_list.append(preproc_wf)
session_list = ['Precon']
preproc_08_wf = preproc_08(working_dir, subject_list, session_list)
workflow_list.append(preproc_08_wf)

# Subject with only one precon scan, also missing Fast
#subject_list = ['10']
#Preproc10_workflow(working_dir, subject_list, session_list, num_cores)

# All Preproc'd Subjects
subject_list = ['02', '03', '04', '05', '06', '07', '08', '11', '12', '13', '14', '15']
session_list = ['Precon']
coreg_wf = intrasession_coregister(working_dir, subject_list, session_list)
workflow_list.append(coreg_wf)

# Subjects with nonT1w postcon scans
subject_list = ['02', '03', '04', '05', '06', '07', '08', '11']
session_list = ['Postcon']
coreg_wf = intrasession_coregister(working_dir, subject_list, session_list)
workflow_list.append(coreg_wf)

# Subjects without nonT1w postcon scans
# subject_list = ['12', '13', '14', '15']
# coreg_wf = intrasession_coregister(working_dir, subject_list, session_list)
# workflow_list.append(coreg_wf)

# All Coreg'd Subjects
subject_list = ['02', '03', '04', '05', '06', '07', '08', '11', '12', '13', '14', '15']

# subject_list = ['02', '03', '04', '06', '11', '12', '15']
coreg2_wf = pre_to_post_coregister(working_dir, subject_list)
workflow_list.append(coreg2_wf)

braincrop_wf = braincrop(working_dir, subject_list)
workflow_list.append(braincrop_wf)

# AT THIS POINT MANUAL MASKS MUST BE COMPLETED USING THE BRAIN CROPPED IMAGES
# subject_list = ['08', '09', '10']
# subject_list = ['02', '03', '04', '05', '06', '07', '08', '09', '10', '11']

subject_list = ['02', '03', '04', '06', '11']
calc_transforms_wf = calc_transforms(working_dir, subject_list)
workflow_list_2.append(calc_transforms_wf)

scan_type = 'hr'

apply_transforms_hr_wf = apply_linear_trans(working_dir, subject_list, scan_type)
workflow_list_2.append(apply_transforms_hr_wf)

apply_nonlinear_transforms_hr_wf = apply_nonlinear_trans(working_dir, subject_list, scan_type)
workflow_list_2.append(apply_nonlinear_transforms_hr_wf)

scan_type = 'fast'
apply_transforms_fast_wf = apply_linear_trans(working_dir, subject_list, scan_type)
workflow_list_2.append(apply_transforms_fast_wf)

apply_nonlinear_transforms_fast_wf = apply_nonlinear_trans(working_dir, subject_list, scan_type)
workflow_list_2.append(apply_nonlinear_transforms_fast_wf)

# num_cores = 1
# scan_type = 'hr'
# ApplyTrans_workflow(working_dir, subject_list, session_list, num_cores,
#                     scan_type)
#
# ApplyTransAnat_workflow(working_dir, subject_list, session_list, num_cores)
#
# Normalization_workflow_PostFLIRT(working_dir, subject_list, num_cores)
#
# num_cores = 1
# subject_list = ['02', '03', '04', '06', '11']
# scan_type = 'fast'
# ApplyTrans_workflow(working_dir, subject_list, session_list, num_cores,
#                     scan_type)
#
# os.system("notify-send Transforms done")
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
#

num_cores = 1

for workflow in workflow_list:
    cnp.workflow_runner(workflow, num_cores)

num_cores = 5

# for workflow in workflow_list_2:
#     cnp.workflow_runner(workflow, num_cores)

# os.system("espeak 'pipeline run done'")
