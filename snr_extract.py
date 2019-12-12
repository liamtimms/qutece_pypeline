import nibabel as nib
import numpy as np
import pandas as pd
import os
import CustomNiPype as cnp
import nipype.pipeline.engine as eng
from nipype.utils.filemanip import split_filename

base_path = '/home/liam/LaptopSync/DCM2BIDS_Kidney'
subject_list = ['3', '4', '5', '6']
subject_list = ['3', '4']

for sub_num in subject_list:
    data_dir = os.path.join(base_path, 'sub-' + sub_num, 'ses-Post', 'qutece')
    snr_mask_dir = os.path.join(base_path, 'derivatives', 'manual-work', 'snr','sub-' + sub_num)
#    workbook = xlwt.Workbook()
#    worksheet = workbook.add_sheet('snr')
    n=0
    for filename in os.listdir(data_dir):
        if filename.endswith(".nii"):
            scan_filename = os.path.join(data_dir, filename)
            scan_nii = nib.load(scan_filename)
            scan_img = np.array(scan_nii.get_data())
#            worksheet.write(0, n,

            path, fname, ext = split_filename(filename)
            snr_fname = 'SNR_' + fname + '_Segmentation-label.nii'

            snr_filename = os.path.join(snr_mask_dir, snr_fname)
            snr_ROI_nii = nib.load(snr_filename)
            snr_ROI_img = np.array(snr_ROI_nii.get_data())
            out = ([int(sub_num), n])

            for r in np.unique(snr_ROI_img):
                roi = (snr_ROI_img == r).astype(int)
                roi = roi.astype('float')
                roi[roi == 0] = np.nan #zero can be true value so mask with nan

                crop_img = np.multiply(scan_img, roi)
                vals = np.reshape(crop_img, -1)
                ave = np.nanmean(vals)
                std = np.nanstd(vals)
                print('for '+str(r)+' in '+ snr_fname)
                print('ave = '+str(ave)+' with '+str(len(vals))+' points')
                print('std = '+str(std))
                out.append([ave, std])
                if r == 1:
                    signal = ave
                elif r==2:
                    noise = std

            snr = signal/noise
            print('for '+ snr_fname)
            print('SNR = '+str(snr)+ '\n\n')

            n=n+1

