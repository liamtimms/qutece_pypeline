import os
import glob
import numpy as np
import pandas as pd
import seaborn as sns
import nibabel as nib

base_dir = os.path.abspath('../..')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
manualwork_dir = os.path.join(base_dir, 'derivatives', 'manualwork')


def roi_extract(img, roi_img):

    vals_df_list = []
    unique_roi = np.unique(roi_img)
    out_data = np.empty([np.size(unique_roi), 4])
    n = 0
    for r in unique_roi:
        # r is label in roi
        # n counts for number of labels

        roi = (ROI_file_img == r).astype(int)
        roi = roi.astype('float')
        # zero can be a true value so mask with nan
        roi[roi == 0] = np.nan
        crop_img = np.multiply(scan_img, roi)
        vals = np.reshape(crop_img, -1)
        vals_df = pd.DataFrame(vals)

        ave = np.nanmean(vals)
        std = np.nanstd(vals)
        N = np.count_nonzero(~np.isnan(vals))
        out_data[n][0] = r
        out_data[n][1] = ave
        out_data[n][2] = std
        out_data[n][3] = N
        n = n + 1


    return extracted_df


def hist_plot(postcon_df, precon_df):
    return

def hist_plot(postcon_df, precon_df):
    return
