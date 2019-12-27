import time
import nibabel as nib
import numpy as np
import pandas as pd
from scipy import spatial
from nipype.utils.filemanip import split_filename
import os

base_path = os.path.abspath(
    '/mnt/4e43a4f6-7402-4881-bcf5-d280e54cc385/Analysis/DCM2BIDS2/derivatives')

subject_list = ['04', '06', '08', '10', '11']
subject_list = ['11']
# sub_num = '11'
start_time = time.time()
for sub_num in subject_list:
    fft_directory = os.path.join(base_path, 'datasink', 'FFT',
                                 'sub-' + sub_num)
    for name in os.listdir(fft_directory):
        if os.path.isfile(os.path.join(fft_directory, name)):
            fft_filename = os.path.join(fft_directory, name)
            if "TOF" in fft_filename:
                print(fft_filename)
                fft_nii = nib.load(fft_filename)
                fft_nii.set_data_dtype(np.double)
                fft_img = np.array(fft_nii.get_data())
                dim_max = fft_img.shape
                center = [round(q / 2) for q in dim_max]
                fft_vals = [[0] * 2 for x in range(np.size(fft_img))]
                pth, fname, ext = split_filename(fft_filename)
                fft_csv_filename = os.path.join(base_path, 'manualwork',
                                                'fftdist', fname + '.csv')

                # Only do calculation if outout is not found
                if not os.path.isfile(fft_csv_filename):
                    n = 0  # get all values
                    elapsed_time = time.time() - start_time
                    print(elapsed_time)
                    for index, value in np.ndenumerate(fft_img):
                        p1 = np.array(index)
                        p2 = np.array(center)
                        dist = spatial.distance.euclidean(p1, p2)
                        fft_vals[n][0] = dist
                        fft_vals[n][1] = value
                        n = n + 1
                        if n == 100 or n == 1000 or n == 10000 or n == 100000:
                            print(n)

                    fft_unique_dist = np.unique(np.asarray(fft_vals)[:, 0])
                    print(np.size(fft_unique_dist))
                    n = 0

                    fft_sum_vals = [[0] * 2
                                    for y in range(np.size(fft_unique_dist))]

                    elapsed_time = time.time() - start_time
                    print(elapsed_time)
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

                    elapsed_time = time.time() - start_time
                    print(elapsed_time)

                    export = pd.DataFrame(fft_sum_vals)
                    export.to_csv(fft_csv_filename, index=False)
