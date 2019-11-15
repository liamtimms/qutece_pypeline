import nibabel as nib
import numpy as np
import pandas as pd
from scipy import spatial
from nipype.utils.filemanip import split_filename
import os

base_path = '/run/media/mri/4e43a4f6-7402-4881-bcf5-d280e54cc385/Analysis/DCM2BIDS2/derivatives'

subject_list = ['04', '06', '08', '10', '11']
#sub_num = '11'

for sub_num in subject_list:
    fft_directory = os.path.join(base_path, 'datasink','FFT','sub-' + sub_num)
    for name in os.listdir(fft_directory):
        if os.path.isfile(os.path.join(fft_directory, name)):
                fft_filename = os.path.join(fft_directory, name)
                print(fft_filename)
                fft_nii = nib.load(fft_filename)
                fft_nii.set_data_dtype(np.double)
                fft_img = np.array(fft_nii.get_data())
                dim_max = fft_img.shape
                center = [round(q/2) for q in dim_max]
                n=0
                fft_vals = [[0]*2 for i in range(np.size(fft_img))]
                for index, value in np.ndenumerate(fft_img):
                    p1 = np.array(index)
                    p2 = np.array(center)
                    dist = spatial.distance.euclidean(p1,p2)
#                    dist = np.linalg.norm(p1-p2)
#                    value = fft_img (index)
                    fft_vals[n][0] = dist
                    fft_vals[n][1] = value
                    n=n+1
                pth, fname, ext = split_filename(fft_filename)
                fft_filename = os.path.join(base_path, 'manualwork', 'fftdist',
                        fname + '.csv')
                export = pd.DataFrame(fft_vals)
                export.to_csv(fft_filename, index=False)

