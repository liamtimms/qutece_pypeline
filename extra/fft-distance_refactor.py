import os
import time

import nibabel as nib
import numpy as np
import pandas as pd
from nipype.utils.filemanip import split_filename
from scipy import spatial


def calc_dist_from_center(img):
    dim_max = img.shape
    center = [round(q / 2) for q in dim_max]
    vals = [[0] * 2 for x in range(np.size(img))]
    n = 0  # get all values
    for index, value in np.ndenumerate(img):
        p1 = np.array(index)
        p2 = np.array(center)
        dist = spatial.distance.euclidean(p1, p2)
        vals[n][0] = dist
        vals[n][1] = value
        n = n + 1
    return vals


base_path = os.path.abspath(
    '/mnt/4e43a4f6-7402-4881-bcf5-d280e54cc385/Analysis/DCM2BIDS4/derivatives')
subject_list = ['02', '03', '05', '04', '06', '07', '08', '10', '11']
# subject_list = ['11']
# sub_num = '11'
start_time = time.time()
for sub_num in subject_list:
    fft_directory = os.path.join(base_path, 'datasink', 'FFT',
                                 'sub-' + sub_num)
    for name in os.listdir(fft_directory):
        if os.path.isfile(os.path.join(fft_directory, name)):
            fft_filename = os.path.join(fft_directory, name)
            if "TOF" in fft_filename or "UTE" in fft_filename:
                print(fft_filename)

                pth, fname, ext = split_filename(fft_filename)
                fft_csv_filename = os.path.join(base_path, 'manualwork',
                                                'fftdist', fname + '.csv')
                # Only do calculation if outout is not found
                if not os.path.isfile(fft_csv_filename):
                    fft_nii = nib.load(fft_filename)
                    fft_nii.set_data_dtype(np.double)
                    fft_img = np.array(np.double(fft_nii.get_fdata()))
                    fft_vals = calc_dist_from_center(fft_img)
                    fft_vals = np.round(fft_vals, 3)

                    fft_unique_dist = np.unique(np.asarray(fft_vals)[:, 0])
                    print(np.size(fft_unique_dist))
                    n = 0

                    fft_sum_vals = [[0] * 2
                                    for y in range(np.size(fft_unique_dist))]

                    curr_time = time.time()
                    for dist in fft_unique_dist:
                        dist_index = np.where(
                            np.asarray(fft_vals)[:, 0] == dist)
                        curr_val = 0
                        for j in dist_index:
                            for i in j:
                                i = int(i)
                                curr_val = curr_val + fft_vals[i][1]
                            fft_sum_vals[n][0] = dist
                            fft_sum_vals[n][1] = curr_val
                            n = n + 1
                            if (n % 100) == 0:
                                print(n)
                                elapsed_time = time.time() - start_time
                                print(elapsed_time)

                    export = pd.DataFrame(fft_sum_vals)
                    export.to_csv(fft_csv_filename, index=False)
