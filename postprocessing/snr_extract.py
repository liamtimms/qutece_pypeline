import nibabel as nib
import numpy as np
import pandas as pd
import os
import json
import CustomNiPype as cnp
import nipype.pipeline.engine as eng
from nipype.utils.filemanip import split_filename

base_path = '/home/liam/LaptopSync/DCM2BIDS_Kidney'
subject_list = ['3', '4', '5', '6']
#subject_list = ['3', '4']

for sub_num in subject_list:
    data_dir = os.path.join(base_path, 'sub-' + sub_num, 'ses-Post', 'qutece')
    snr_mask_dir = os.path.join(base_path, 'derivatives', 'manual-work', 'snr',
                                'sub-' + sub_num)
    n = 0

    sub_vals = [[
        'Scan Name', 'Blood Intensity', 'Intraluminal Signal Homogeneity',
        'SNR', 'CNR', 'Voxel Size', 'TE', 'TR', 'FA'
    ]]

    for filename in os.listdir(data_dir):
        if filename.endswith(".nii"):
            scan_filename = os.path.join(data_dir, filename)

            scan_nii = nib.load(scan_filename)
            scan_img = np.array(scan_nii.get_fdata())
            scan_hdr = scan_nii.header

            pixdim = scan_hdr['pixdim']
            voxelsize = pixdim[1] * pixdim[2] * pixdim[3]
            path, fname, ext = split_filename(filename)
            jsonfilename = os.path.join(data_dir, fname + '.json')

            with open(jsonfilename) as json_file:
                j_obj = json.load(json_file)
                TE = j_obj['EchoTime']
                TR = j_obj['RepetitionTime']
                FA = j_obj['FlipAngle']

            snr_fname = 'SNR_' + fname + '_Segmentation-label.nii'
            print(snr_fname)

            snr_filename = os.path.join(snr_mask_dir, snr_fname)
            snr_ROI_nii = nib.load(snr_filename)
            snr_ROI_img = np.array(snr_ROI_nii.get_fdata())

            corr_fname = fname + '_corrected.nii'
            snr_ROI_nii = nib.load(snr_filename)
            snr_ROI_img = np.array(snr_ROI_nii.get_fdata())

            out = ([int(sub_num), n])

            for r in np.unique(snr_ROI_img):
                roi = (snr_ROI_img == r).astype(int)
                roi = roi.astype('float')
                roi[roi ==
                    0] = np.nan  #zero can be true value so mask with nan

                crop_img = np.multiply(scan_img, roi)
                vals = np.reshape(crop_img, -1)
                ave = np.nanmean(vals)
                std = np.nanstd(vals)
                print('for ' + str(r))
                print('ave = ' + str(ave) + ' with ' + str(len(vals)) +
                      ' points')
                print('std = ' + str(std))
                out.append([ave, std])
                if r == 1:
                    blood_signal = ave
                    blood_noise = std
                elif r == 2:
                    noise = std
                elif r == 3:
                    tissue = ave

            snr = blood_signal / noise
            ish = blood_noise / blood_signal
            snr_tissue = tissue / noise
            cnr = snr - snr_tissue
            scan_vals = [fname, blood_signal, ish, snr, cnr, voxelsize, TE, TR, FA]
            sub_vals.append(scan_vals)
            print('for ' + snr_fname)
            print('SNR = ' + str(snr))  #+ '\n')
            print('CNR = ' + str(cnr) + '\n')
            del blood_signal, ish, noise, tissue
            n = n + 1

        scan_vals_csv_filename = os.path.join(snr_mask_dir,
                                              'snr_sub-' + sub_num + '.csv')
        export = pd.DataFrame(sub_vals)
        export.to_csv(scan_vals_csv_filename, index=False)
