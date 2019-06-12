import os
import subprocess
dcm_dir = '/mnt/hgfs/VMshare/DCM/'
bids_dir = '/mnt/hgfs/VMshare/DCM2BIDS/'
CONFIG_FILE = '/mnt/hgfs/VMshare/ConfigV1.json'
os.chdir(bids_dir)
os.getcwd()
pat_folders = os.listdir(dcm_dir)
bids_folders = os.listdir(bids_dir)

for pat_folder in pat_folders:
    pat_dir = dcm_dir + pat_folder + '/'
    #nii_dir = data_dir + pat + '/'
    contents = os.listdir(pat_dir)

    for f in contents:

        if not "." in f:
            sess_dcm_dir = pat_dir + f
            session_type = f
            patient_num = pat_folder[2:4]

            if ("sub-" + patient_num) not in bids_folders:
                #To keep it consistent with Dcm2Bids conventions
                DICOM_DIR = sess_dcm_dir
                PARTICIPANT_ID = patient_num
                SESSION_ID = session_type
                command = 'dcm2bids -d ' + DICOM_DIR + ' -p ' + PARTICIPANT_ID
                          + ' -s ' + SESSION_ID + ' -c ' + CONFIG_FILE
                #print(command)
                os.system(command)
