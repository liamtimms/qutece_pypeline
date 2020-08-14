import os
import csv_functions as cf

base_dir = os.path.abspath('../../..')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
manualwork_dir = os.path.join(base_dir, 'derivatives', 'manualwork')

subject_list = ['02', '03', '04', '06', '07', '08', '11', '12', '13', '14', '15']
session_list = ['Precon', 'Postcon']
scan_type = 'hr'
seg_type = 'WMH'    # WMH segmentation
in_folder = 'tissue_wmh_analysis_csv'
#seg_type = 'T1w'    # FAST tissue segmentation

for sub_num in subject_list:
    for session in session_list:
        cf.session_summary(in_folder, sub_num, session, scan_type, seg_type)





# base_dir = os.path.abspath('../..')
# datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
#
# save_dir = os.path.join(datasink_dir, 'csv_work')
# if not os.path.exists(save_dir):
#     os.mkdir(save_dir)
#
# sub_num = '11'
# session = 'Precon'
