import os
from nipype_preproc import Preproc_workflow
from nipype_preproc_nofast import PreprocNoFast_workflow
from nipype_preproc_08 import Preproc08_workflow
# from nipype_preproc_10 import Preproc10_workflow
from nipype_coreg import IntrasesCoreg_workflow
from nipype_coreg2 import IntersesCoreg_workflow
from nipype_scan_diff import ScanDiff_workflow
from nipype_normalize_braincrop import BrainCrop_workflow
from nipype_normalize_semiauto import Normalization_workflow
from nipype_normalize_applytrans import ApplyTrans_workflow
from nipype_normalize_applytrans_nonUTE import ApplyTransAnat_workflow
from nipype_timeseries_roi import TimeSeries_ROI_workflow
from textme import textme

upper_dir = os.path.realpath('../..')
working_dir = os.path.abspath(upper_dir)
session_list = ['Precon', 'Postcon']

num_cores = 1
# Subjects with both hr and fast scans
subject_list = ['02', '03', '04', '06', '11']
# Preproc_workflow(working_dir, subject_list, session_list, num_cores)

# Subjects without Fast Scans
subject_list = ['05', '07', '09']
# PreprocNoFast_workflow(working_dir, subject_list, session_list, num_cores)

# Subjects with only 1 precon
session_list = ['Postcon']
subject_list = ['08', '10']
# Preproc_workflow(working_dir, subject_list, session_list, num_cores)

# num_cores = 5
subject_list = ['08']
session_list = ['Precon']
# Preproc08_workflow(working_dir, subject_list, session_list, num_cores)
# subject_list = ['10']
# # Preproc10_workflow(working_dir, subject_list, session_list, num_cores)
# os.system("notify-send Preprocessing done")

# need further modifications to account for 8 and 10

# num_cores = 4
subject_list = ['02', '03', '04', '05', '06', '07', '09', '11']
# subject_list = ['02', '03', '04', '06', '11']
# Extremely important to not start too many FLIRTs in parrallel
# IntrasesCoreg_workflow(working_dir, subject_list, session_list, num_cores)
# os.system("notify-send IntrasessionCoregistration done")

# IntersesCoreg_workflow(working_dir, subject_list, num_cores)
# os.system("notify-send IntersessionCoregistration done")
# os.system("espeak 'Intersession Coregistration done' > /dev/null")

# scan_type = 'hr'
# ScanDiff_workflow(working_dir, subject_list, session_list, num_cores,
#                   scan_type)
# scan_type = 'fast'
# ScanDiff_workflow(working_dir, subject_list, session_list, num_cores,
#                   scan_type)
# os.system("notify-send ScanDiff done")

# num_cores = 3
# BrainCrop_workflow(working_dir, subject_list, num_cores)
# os.system("notify-send 'BrainCrop done'")
#
# # AT THIS POINT MANUAL MASKS MUST BE COMPLETED USING THE BRAIN CROPPED IMAGES
# # Normalization_workflow(working_dir, subject_list, num_cores)
# # os.system("notify-send 'Norm done'")
#
# scan_type = 'hr'
# ApplyTrans_workflow(working_dir, subject_list, session_list, num_cores,
#                     scan_type)
#
# ApplyTransAnat_workflow(working_dir, subject_list, session_list, num_cores)
#
# num_cores = 1
# subject_list = ['02', '03', '04', '06', '11']
# scan_type = 'fast'
# ApplyTrans_workflow(working_dir, subject_list, session_list, num_cores,
#                     scan_type)
#
# os.system("notify-send Transforms done")

ROI_types = ['brain', 'blood']
scan_types = ['hr']
subject_list = ['11']
session_list = ['Precon', 'Postcon']
num_cores = 1
for ROI_type in ROI_types:
    for scan_type in scan_types:
        TimeSeries_ROI_workflow(working_dir, subject_list, session_list,
                                num_cores, scan_type, ROI_type)

# os.system("espeak 'pipeline run done'")
