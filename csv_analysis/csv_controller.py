import os
import csv_functions as cf

base_dir = os.path.abspath('../../..')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
manualwork_dir = os.path.join(base_dir, 'derivatives', 'manualwork')

#------------------------------------------------------------------------------
# subject_list = ['02', '03', '04', '05', '06', '07', '08', '10', '11', '12', '13', '14', '15']
# session_list = ['Precon', 'Postcon']
# scan_type = 'hr'
# # seg_type = 'WMH'    # WMH segmentation
# seg_type = 'vesselness'
# in_folder = 'tissue_wmh_analysis_csv'
# #seg_type = 'T1w'    # FAST tissue segmentation
#
# for sub_num in subject_list:
#     for session in session_list:
#         cf.session_summary(in_folder, sub_num, session, scan_type, seg_type)
#
#     cf.difference_summary(sub_num, scan_type, seg_type)
#
# cf.subjects_summary_alt(datasink_dir, subject_list, scan_type, seg_type)
#

# base_dir = os.path.abspath('../..')
# datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
#
# save_dir = os.path.join(datasink_dir, 'csv_work')
# if not os.path.exists(save_dir):
#     os.mkdir(save_dir)
#
# sub_num = '11'
# session = 'Precon'

#------------------------------------------------------------------------------

subject_list = ['02', '06','11']
session_list = ['Precon', 'Postcon']
scan_type = 'hr'
seg_type = 'nWM-WMH-vesselness'
in_folder = 'wm_analysis_csv'

for sub_num in subject_list:
    for session in session_list:
        cf.session_summary(in_folder, sub_num, session, scan_type, seg_type)

    cf.sub_summary(sub_num, scan_type, seg_type)

#cf.subjects_summary_alt(datasink_dir, subject_list, scan_type, seg_type)

