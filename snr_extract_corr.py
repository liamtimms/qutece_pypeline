import nibabel as nib
import numpy as np
import pandas as pd
import os
import json
from nipype.utils.filemanip import split_filename

base_path = '../..'
subject_list = ['3', '4', '5', '6']

for sub_num in subject_list:
    data_dir = os.path.join(base_path, 'derivatives', 'manual-work',
                            'masked_bias_correction', 'sub-' + sub_num)
    bias_mask_dir = os.path.join(base_path, 'derivatives', 'manual-work', 'segmentation-4bias')
    snr_mask_dir = os.path.join(base_path, 'derivatives', 'manual-work', 'snr',
                                'sub-' + sub_num)
    av_mask_dir = os.path.join(base_path, 'derivatives', 'manual-work',
                               'segmentation-vesselness_ArteryAndVein',
                               'sub-' + sub_num)
    n = 0

    sub_vals = [[
        'Scan Name', 'Artery Intensity', 'Artery ISH', 'Artery SNR',
        'Artery CNR', 'Vein Intensity', 'Vein ISH', 'Vein SNR', 'Vein CNR',
    ]]

    for filename in os.listdir(data_dir):
        if filename.endswith(".nii"):
            scan_filename = os.path.join(data_dir, filename)

            scan_nii = nib.load(scan_filename)
            scan_img = np.array(scan_nii.get_fdata())
            scan_hdr = scan_nii.header

            path, fname, ext = split_filename(filename)

            snr_fname = 'SNR_' + fname + '_Segmentation-label.nii'
            print(snr_fname)
            av_fname = fname + '_VesselnessFiltered_final_Segmentation-label.nii'
            bias_fname = fname + '_Segmentation-label.nii'

            snr_filename = os.path.join(snr_mask_dir, snr_fname)
            snr_ROI_nii = nib.load(snr_filename)
            snr_ROI_img = np.array(snr_ROI_nii.get_fdata())

            av_filename = os.path.join(av_mask_dir, av_fname)
            av_ROI_nii = nib.load(av_filename)
            av_ROI_img = np.array(av_ROI_nii.get_fdata())

            bias_filename = os.path.join(bias_mask_dir, bias_fname)
            bias_ROI_nii = nib.load(bias_filename)
            bias_ROI_img = np.array(bias_ROI_nii.get_fdata())

            av_ROI_img = np.multiply(av_ROI_img, bias_ROI_img)

            # snr_ROI_img is labelmap for blood, noise and tissue
            #   av_ROI_img is labelmap for aorta and IVC
            #   4bias_ROI_img is labelmap for biascorrection mask
            out = ([int(sub_num), n])

            for r in np.unique(snr_ROI_img):
                print('Now processing noise & tissue labelmap......')
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

            for r in np.unique(av_ROI_img):
                print('Now processing artery & vein labelmap......')
                roi = (av_ROI_img == r).astype(int)
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
                    artery_signal = ave
                    artery_noise = std
                elif r == 2:
                    vein_signal = ave
                    vein_noise = std

            snr_artery = artery_signal / noise
            snr_vein = vein_signal / noise
            ish_artery = artery_noise / artery_signal
            ish_vein = vein_noise / vein_signal

            snr_tissue = tissue / noise
            cnr_artery = snr_artery - snr_tissue
            cnr_vein = snr_vein - snr_tissue
            scan_vals = [
                fname, artery_signal, ish_artery, snr_artery, cnr_artery,
                vein_signal, ish_vein, snr_vein, cnr_vein,
            ]
            sub_vals.append(scan_vals)

            del artery_signal, artery_noise, vein_signal, vein_noise, noise, tissue
            n = n + 1

        scan_vals_csv_filename = os.path.join(
            av_mask_dir, 'sub-' + sub_num + '_snr_corrected_arteryvein.csv')
        export = pd.DataFrame(sub_vals)
        export.to_csv(scan_vals_csv_filename, index=False)
