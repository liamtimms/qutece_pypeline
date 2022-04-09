import os
import glob
import json
import numpy as np
import pandas as pd
# import dask.dataframe as dd
import nibabel as nib
import nilearn as nil
from nipype.utils.filemanip import split_filename
base_dir = os.path.abspath('../../..')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
manualwork_dir = os.path.join(base_dir, 'derivatives', 'manualwork')


def roi_cut(scan_img, roi_img, t, r):
    """
    Crop part of image using roi, give back crop and values.

    Parameters
    ----------
    scan_img : numpy array
    roi_img : numpy array
    t : string
        string denoting type of crop
    r : value of region of interest from the roi_img

    Returns
    -------
    crop_img : numpy array
    vals_df : pandas DataFrame

    """
    if t == 'equal':
        roi = (roi_img == r).astype(int)
    elif t == 'greater':
        roi = (roi_img >= r).astype(int)
    else:
        print('need valid roi cut type')

    roi = roi.astype('float')
    # zero can be a true value so mask with nan
    roi[roi == 0] = np.nan
    crop_img = np.multiply(scan_img, roi)

    vals = np.reshape(crop_img, -1)
    vals_df = pd.DataFrame()
    vals_df[r] = vals
    vals_df.dropna(inplace=True)
    vals_df.reset_index(drop=True, inplace=True)
    return crop_img, vals_df


def roi_extract(scan_img, roi_img, fname, seg_type, save_dir):
    """
    Extract, save and summarize every region in an roi image.resample_to_img

    Mostly calls roi_cut and df.describe

    Parameters
    ----------
    scan_img : numpy array
    roi_img : numpy array
    seg_type : string
    save_dir : string

    Returns
    -------
    summary_df : pandas DataFrame

    """

    t = 'greater'
    r = -1000
    crop_img, vals_df = roi_cut(scan_img, roi_img, t, r)
    summary_df = vals_df.describe()
    unique_roi = np.unique(roi_img)
    print(unique_roi)

    t = 'equal'
    for r in unique_roi:
        crop_img, vals_df = roi_cut(scan_img, roi_img, t, r)
        r_summary_df = vals_df.describe()
        summary_df = pd.merge(summary_df,
                              r_summary_df,
                              left_index=True,
                              right_index=True)
        vals_df = vals_df.round(3)
        print('Head is :')
        print(vals_df.head())
        print('Tail is :')
        print(vals_df.tail())
        print(r_summary_df.head())
        save_name = (fname + '_DATA_' + 'seg-{}_r-' + str(int(r)) +
                     '.csv').format(seg_type)
        vals_df.to_csv(os.path.join(save_dir, save_name), index=False)
        print('Data saved as:')
        print(os.path.join(save_dir, save_name))

    # UNTESTED
    # t = 'greater'
    # r = 0
    # crop_img, vals_df = roi_cut(scan_img, roi_img, t, r)
    # r_summary_df = vals_df.describe()
    # r_summary_df.rename(columns={0: 'all'}, inplace=True)
    # summary_df = pd.merge(summary_df,
    #                       r_summary_df,
    #                       left_index=True,
    #                       right_index=True)

    return summary_df


def session_summary(in_folder, exp_num, seg_type):
    """
    Summarize a single session for a single subject for a given seg_type.

    Loads appropriate nifti data for ROI of seg_type, loads scan data.
    Then calls roi_extract to get the relevant data for each scan.
    Saves the summaries and returns a list of them.

    Parameters
    ----------
    in_folder : string
        Directory where the scan images are saved.
    exp_num : string
    session : string
        Precon or Postcon
    scan_type : string
        hr or TOF
        TODO: add fast support
    seg_type : string

    Returns
    -------
    summary_df_list : list of pandas DataFrames

    """

    data_dir = os.path.join(base_dir, 'Experiment_' + exp_num)
    csv_dir = 'csv_work'
    roi_dir = os.path.join(manualwork_dir, 'segmentations')

    ROI_file_name = os.path.join(roi_dir,
                                 'E_' + exp_num + '_Segmentation-label_hr.nii')
    ROI_file_nii = nib.load(ROI_file_name)
    roi_img = np.array(ROI_file_nii.get_fdata())
    session_pattern = 'Exp-' + exp_num + '_scan-*_FA_Test*.nii'
    path_pattern = os.path.join(data_dir, session_pattern)
    nii_files = glob.glob(path_pattern)
    print(path_pattern)
    print('Selected files are: ')
    print(nii_files)

    summary_df_list = []

    for f in nii_files:
        scan_file_name = f
        scan_file_nii = nib.load(scan_file_name)
        scan_img = np.array(scan_file_nii.get_fdata())
        pth, fname, ext = split_filename(f)

        if scan_img.size != roi_img.size:
            print('RESAMPLING')
            resampled_nii = nil.image.resample_to_img(scan_file_nii,
                                                      ROI_file_nii)
            scan_img = np.array(resampled_nii.get_fdata())

        save_dir = os.path.join(datasink_dir, csv_dir)

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        summary_df = roi_extract(scan_img, roi_img, fname, seg_type, save_dir)

        save_name = (fname + '_SUMMARY_' + 'seg-{}.csv').format(seg_type)
        summary_df.to_csv(os.path.join(save_dir, save_name))
        print('Saved SUMMARY as : ' + os.path.join(save_dir, save_name))

        summary_df_list.append(summary_df)

    return summary_df_list


def load_summary_dfs(csv_dir, exp_num, seg_type):
    """
    Load the summary csv files made by session_summary functions.

    Does some processing on the dfs to add session, file name fields.
    Transposes data from original such that 'mean', 'std' etc. are columns.

    Parameters
    ----------
    csv_dir : string
        Directory where the SUMMARY csv files for each scan are saved.
    exp_num : string
    session : string
        Precon or Postcon
    scan_type : string
        hr or TOF
        TODO: add fast support
    seg_type : string

    Returns
    -------
    df_list : list of pandas DataFrames

    """

    data_dir = os.path.join(datasink_dir, csv_dir, 'exp-{}'.format(exp_num))
    path_pattern = os.path.join(
        data_dir, '*_SUMMARY_seg-' + seg_type + '*.csv')
    load_files = glob.glob(path_pattern)
    df_list = []
    for f in load_files:
        df = pd.read_csv(f)
        pth, fname, ext = split_filename(f)
        df.rename(columns={'Unnamed: 0': 'name'}, inplace=True)
        df = df.set_index('name').T
        df['file'] = fname
        df_list.append(df)

    return df_list


def experiment_summary(exp_num, seg_type):
    """
    Summarize a seg_type's mean and std across sessions for a single subject.

    Loads sessions_summary data output as csv files via load_summary_dfs().
    Concatenates pre and post summaries into larger DataFrames.
    Plots across mean value across region number.

    Parameters
    ----------
    exp_num : string
    scan_type : string
        hr or TOF
        TODO: add fast support
    seg_type : string

    Returns
    -------
    postcon_df : concatenated pandas DataFrame
    precon_df : concatenated pandas DataFrame

    """
    csv_dir = 'csv_work'
    # plots_dir = 'plots'

    scan_df_list = load_summary_dfs(csv_dir, exp_num, seg_type)
    exp_df = pd.concat(scan_df_list)

    scan_names = exp_df['file'].str.rsplit("_", n=2, expand=True)
    exp_df['scan'] = scan_names[0]

    # scan_param_df = pd.DataFrame()

    scan_param_df = pd.DataFrame(columns=[
        'BodyPartExamined', 'SeriesDescription', 'ScanningSequence',
        'SequenceVariant', 'SequenceName', 'ImageType', 'SeriesNumber',
        'AcquisitionTime', 'AcquisitionNumber', 'SliceThickness', 'SAR',
        'EchoTime', 'RepetitionTime', 'FlipAngle', 'PartialFourier',
        'BaseResolution', 'TxRefAmp', 'PhaseResolution',
        'ReceiveCoilActiveElements', 'PulseSequenceDetails', 'PercentPhaseFOV',
        'PercentSampling', 'PhaseEncodingSteps', 'AcquisitionMatrixPE',
        'ReconMatrixPE', 'PixelBandwidth', 'DwellTime'
    ],
                                 index=exp_df['scan'].unique())

    for f in exp_df['scan'].unique():
        scan_dir = os.path.join(base_dir, 'Experiment_' + exp_num)
        jsons = glob.glob(os.path.join(scan_dir, f + '*.json'))
        jsonfilename = jsons[0]

        with open(jsonfilename) as json_file:
            print(jsonfilename)
            j_obj = json.load(json_file)
            BodyPartExamined = j_obj['BodyPartExamined']
            SeriesDescription = j_obj['SeriesDescription']
            ScanningSequence = j_obj['ScanningSequence']
            SequenceVariant = j_obj['SequenceVariant']
            SequenceName = j_obj['SequenceName']
            ImageType = j_obj['ImageType']
            SeriesNumber = j_obj['SeriesNumber']
            AcquisitionTime = j_obj['AcquisitionTime']
            AcquisitionNumber = j_obj['AcquisitionNumber']
            SliceThickness = j_obj['SliceThickness']
            SAR = j_obj['SAR']
            EchoTime = j_obj['EchoTime']
            RepetitionTime = j_obj['RepetitionTime']
            FlipAngle = j_obj['FlipAngle']
            PartialFourier = j_obj['PartialFourier']
            BaseResolution = j_obj['BaseResolution']
            TxRefAmp = j_obj['TxRefAmp']
            PhaseResolution = j_obj['PhaseResolution']
            ReceiveCoilActiveElements = j_obj['ReceiveCoilActiveElements']
            PulseSequenceDetails = j_obj['PulseSequenceDetails']
            PercentPhaseFOV = j_obj['PercentPhaseFOV']
            PercentSampling = j_obj['PercentSampling']
            PhaseEncodingSteps = j_obj['PhaseEncodingSteps']
            AcquisitionMatrixPE = j_obj['AcquisitionMatrixPE']
            ReconMatrixPE = j_obj['ReconMatrixPE']
            PixelBandwidth = j_obj['PixelBandwidth']
            DwellTime = j_obj['DwellTime']
        pass

        scan_param_df.loc[f] = [
            BodyPartExamined, SeriesDescription, ScanningSequence,
            SequenceVariant, SequenceName, ImageType, SeriesNumber,
            AcquisitionTime, AcquisitionNumber, SliceThickness, SAR, EchoTime,
            RepetitionTime, FlipAngle, PartialFourier, BaseResolution,
            TxRefAmp, PhaseResolution, ReceiveCoilActiveElements,
            PulseSequenceDetails, PercentPhaseFOV, PercentSampling,
            PhaseEncodingSteps, AcquisitionMatrixPE, ReconMatrixPE,
            PixelBandwidth, DwellTime
        ]
        print(f)

    print(scan_param_df.head())

    exp_df = exp_df.join(scan_param_df, how='outer', on='scan')

    # save_dir=os.path.join(datasink_dir, plots_dir, 'exp-{}'.format(exp_num))
    # if not os.path.exists(save_dir):
    #     os.makedirs(save_dir)

    # x_axis = "index"
    # y_axis = "mean"
    # category_plot(postcon_df, precon_df, save_dir, exp_num, seg_type, x_axis,
    #               y_axis)
    # y_axis = "std"
    # category_plot(postcon_df, precon_df, save_dir, exp_num, seg_type, x_axis,
    #               y_axis)

    return exp_df


def main():

    # base_dir = os.path.abspath('../../..')
    # in_folder = base_dir
    exp_num = '01'
    seg_type = 'tube'
    # session_summary(in_folder, exp_num, seg_type)
    csv_dir = 'csv_work'
    exp_df = experiment_summary(exp_num, seg_type)
    save_name = ('exp-' + exp_num + '_' +  'FULL.csv')
    save_dir = os.path.join(datasink_dir, csv_dir)
    exp_df.to_csv(os.path.join(save_dir, save_name))
    print(exp_df.head())
    return


if __name__ == "__main__":
    main()
