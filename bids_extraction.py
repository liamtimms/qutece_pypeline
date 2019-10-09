import shutil
import os
import subprocess
parent_path = '/home/liam/Documents/GoogleDrive/VMware/VMshare'
dcm_dir = os.path.join(parent_path,'DCM')
bids_dir = os.path.join(parent_path,'DCM2BIDS2')
CONFIG_FILE = os.path.join(parent_path,'ConfigV2.json')

if not os.path.exists(bids_dir):
    os.mkdir(bids_dir)

os.chdir(bids_dir)
os.getcwd()

command = 'dcm2bids_scaffold'
os.system(command)
print('Created BIDS folders inside:'+os.getcwd())

pat_folders = os.listdir(dcm_dir)
bids_folders = os.listdir(bids_dir)

for pat_folder in pat_folders:
    pat_dir = os.path.join(dcm_dir, pat_folder)
    #nii_dir = data_dir + pat + '/'
    contents = os.listdir(pat_dir)

    for f in contents:

        if not "." in f:
            sess_dcm_dir = os.path.join(pat_dir, f)
            session_type = f
            subject_num = pat_folder[2:4] # extract subject number

            if ("sub-" + subject_num) not in bids_folders:
                # To keep it consistent with Dcm2Bids conventions:
                DICOM_DIR = sess_dcm_dir
                PARTICIPANT_ID = subject_num
                SESSION_ID = session_type

                # Now the actual command
                command = 'dcm2bids -d ' + DICOM_DIR + ' -p ' + PARTICIPANT_ID \
                           + ' -s ' + SESSION_ID + ' -c ' + CONFIG_FILE
                #print(command)
                os.system(command)

command = 'gunzip -r ' + bids_dir
os.system(command)
