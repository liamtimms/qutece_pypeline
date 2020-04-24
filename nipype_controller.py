import os
from nipype_preproc import Preproc_workflow
from nipype_coreg import IntrasesCoreg_workflow
from nipype_coreg2 import IntersesCoreg_workflow
from nipype_scan_diff import ScanDiff_workflow
from nipype_normalize_braincrop import BrainCrop_workflow
from nipype_normalize_semiauto import Normalization_workflow
from nipype_normalize_applytrans import ApplyTrans_workflow
from textme import textme

upper_dir = os.path.realpath('../..')
working_dir = os.path.abspath(upper_dir)
session_list = ['Precon', 'Postcon']

subject_list = ['03', '11']
subject_list = ['02', '04', '08', '10', '11']
# subject_list = ['02', '03', '04', '06', '08', '09', '10', '11']
subject_list = ['03', '04', '06', '11']
#subject_list = ['11']

num_cores = 1
# Preproc_workflow(working_dir, subject_list, session_list, num_cores)
# os.system("notify-send Preprocessing done")

num_cores = 1
# Extremely important to not start too many FLIRTs in parrallel
IntrasesCoreg_workflow(working_dir, subject_list, session_list, num_cores)
os.system("notify-send IntrasessionCoregistration done")

IntersesCoreg_workflow(working_dir, subject_list, num_cores)
os.system("notify-send IntersessionCoregistration done")

scan_type = 'hr'
ScanDiff_workflow(working_dir, subject_list, session_list, num_cores,
                  scan_type)
scan_type = 'fast'
ScanDiff_workflow(working_dir, subject_list, session_list, num_cores,
                  scan_type)
os.system("notify-send ScanDiff done")

BrainCrop_workflow(working_dir, subject_list, num_cores)
os.system("notify-send BrainCrop done")

## AT THIS POINT MANUAL MASKS MUST BE COMPLETED USING THE BRAIN CROPPED IMAGES
num_cores = 4
Normalization_workflow(working_dir, subject_list, num_cores)
os.system("notify-send Norm done")

num_cores = 4
scan_type = 'hr'
ApplyTrans_workflow(working_dir, subject_list, session_list, num_cores,
                    scan_type)
# # scan_type = 'fast'
# # ApplyTrans_workflow(working_dir, subject_list, session_list, num_cores,
# #                     scan_type)
#
# os.system("notify-send Transforms done")
