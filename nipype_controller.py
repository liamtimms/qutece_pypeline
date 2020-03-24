import os
from nipype_preproc import Preproc_workflow
from nipype_coreg import IntrasesCoreg_workflow
from nipype_coreg2 import IntersesCoreg_workflow
from nipype_scan_diff import ScanDiff_workflow
from textme import textme

upper_dir = os.path.realpath('../..')
working_dir = os.path.abspath(upper_dir)
session_list = ['Precon', 'Postcon']

subject_list = ['03', '11']
subject_list = ['02', '04', '08', '10', '11']
subject_list = ['02', '03', '04', '06', '08', '09', '10', '11']
# subject_list = ['06', '11']

num_cores = 1
Preproc_workflow(working_dir, subject_list, session_list, num_cores)
os.system("notify-send Preprocessing done")
# textme("done with Preprocessing")

# Extremely important to not start too many FLIRTs in parrallel
IntrasesCoreg_workflow(working_dir, subject_list, session_list, num_cores)
os.system("notify-send IntrasessionCoregistration done")
# textme("done with IntrasessionCoregistration")

IntersesCoreg_workflow(working_dir, subject_list, num_cores)
os.system("notify-send IntrasessionCoregistration done")

scan_type='hr'
ScanDiff_workflow(working_dir, subject_list, session_list, num_cores, scan_type)
scan_type='fast'
ScanDiff_workflow(working_dir, subject_list, session_list, num_cores, scan_type)
