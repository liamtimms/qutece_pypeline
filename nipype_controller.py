import os
from nipype_preproc import Preproc_workflow
from nipype_coreg import IntrasesCoreg_workflow

upper_dir = os.path.realpath('../..')
working_dir = os.path.abspath(upper_dir)
session_list = ['Precon', 'Postcon']

subject_list = ['03', '11']
subject_list = ['02', '04', '08', '10', '11']
subject_list = ['02', '03', '04', '06', '08', '09', '10', '11']
subject_list = ['03', '04', '06', '08', '11']
num_cores = 7

Preproc_workflow(working_dir, subject_list, session_list, num_cores)
os.system("notify-send Preprocessing done")
IntrasesCoreg_workflow(working_dir, subject_list, session_list, num_cores)
os.system("notify-send IntrasessionCoregistration done")
