import glob
import math
import os

# import dask.dataframe as dd
import matplotlib.pyplot as plt
import nibabel as nib
import nilearn as nil
import numpy as np
import pandas as pd
import seaborn as sns
from nipype.utils.filemanip import split_filename

# sns.set_theme()

base_dir = os.path.abspath('../..')
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
    vals[vals == 0] = np.nan
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


def hist_plots(df, seg_type, save_dir):
    # Not working currently
    for i, col in enumerate(df.columns):
        sns.set(color_codes=True)
        sns.set(style="white", palette="muted")
        vals = df[col].to_numpy()
        w = 10
        n = math.ceil((np.nanmax(vals) - np.nanmin(vals)) / w)

        if n > 0:
            plt.figure(i)
            save_name = seg_type + '-' + str(int(col)) + '.png'
            out_fig_name = os.path.join(save_dir, save_name)
            sns.distplot(df[col],
                         kde=False,
                         bins=n,
                         hist_kws={
                             'histtype': 'step',
                             'linewidth': 1
                         })
            plt.xlim(-10, 4000)

            plt.savefig(out_fig_name, dpi=300, bbox_inches='tight')
            # plt.close(i)

            # sns.distplot(df[col_id],
            #              bins=plot_bins,
            #              kde=False,
            #              norm_hist=True,
            #              hist_kws={
            #                  'histtype': 'step',
            #                  'linewidth': 1
            #              })

    # out_fig_name = os.path.join(save_dir, save_name)
    return


def hist_plot_alt(df, seg_type, save_dir):
    """
    Should make a histrogram for each region.

    Currently BROKEN

    Parameters
    ----------

    Returns
    -------

    """

    vals_list = []
    for i, col in enumerate(df.columns):
        vals = df[[col]]
        vals.columns = ['intensity']
        vals['region'] = int(col)
        print(vals.head())
        vals_list.append(vals)
    plot_df = pd.concat(vals_list, ignore_index=True)
    sns_plot = sns.displot(plot_df,
                           x='intensity',
                           hue='region',
                           stat="density",
                           common_norm=False)
    save_name = ('seg-' + seg_type + '.png')
    out_fig_name = os.path.join(save_dir, save_name)
    sns_plot.savefig(out_fig_name)
    return


def category_plot(postcon_df, precon_df, save_dir, sub_num, seg_type, x_axis,
                  y_axis):
    """
    Plot precontrast vs postcontrast data.

    Applies to a specific subject with a specific seg type,
    x and y axes are not set. Saves the resulting graph in save_dir.

    Parameters
    ----------
    postcon_df : pandas DataFrame
    precon_df : pandas DataFrame
    save_dir : string
    sub_num : string
    seg_type : string
    x_axis : string
    y_axis : string

    Returns
    -------
    crop_img : numpy array
    vals_df : pandas DataFrame

    """
    sns.set_theme()
    plot_df = pd.concat([postcon_df, precon_df])
    plot_df = plot_df.reset_index()
    a = plot_df[x_axis].nunique() / 4
    sns_plot = sns.catplot(x=x_axis,
                           y=y_axis,
                           hue="session",
                           kind="bar",
                           height=8,
                           aspect=a,
                           data=plot_df)

    save_name = ('sub-' + sub_num + '_' + y_axis + '_seg-' + seg_type + '.png')
    print('Saving category_plot as :')
    print(os.path.join(save_dir, save_name))
    sns_plot.savefig(os.path.join(save_dir, save_name))
    return


def subjects_plot(filt_df, save_dir, seg_type, y_axis):
    """
    Plot a parameter across subjects in both precontrast and postcontrast.

    Parameters
    ----------
    filt_df : pandas DataFrame
    save_dir : string
    seg_type : string
    y_axis : string

    Returns
    -------

    """
    sns.set_theme()
    # filt_df = filt_df.reset_index()
    print(filt_df.head())
    a = filt_df['sub_num'].nunique() / 8
    sns_plot = sns.catplot(x="sub_num",
                           y=y_axis,
                           hue="session",
                           kind="bar",
                           height=8,
                           aspect=a,
                           data=filt_df)

    # sns_plot.set_size_inches(11.7, 8.27)

    save_name = (y_axis + '_seg-' + seg_type + '.png')
    sns_plot.savefig(os.path.join(save_dir, save_name))

    return


def subjects_plot_compare(filt_df, save_dir, seg_type, y_axis):
    """
    Plot a parameter across subjects in both UTE and TOF.

    Must be pre-filtered to only have scans of interest.

    Parameters
    ----------
    filt_df : pandas DataFrame
    save_dir : string
    seg_type : string
    y_axis : string

    Returns
    -------

    """

    sns.set_theme()
    filt_df = filt_df.reset_index()
    a = filt_df['sub_num'].nunique() / 10
    sns_plot = sns.catplot(
        x="sub_num",
        y=y_axis,
        hue="scan_type",
        # col="session",
        # hue="session",
        # col="scan_type",
        kind="bar",
        height=8,
        aspect=a,
        data=filt_df)

    save_name = (y_axis + '_compare_seg-' + seg_type + '.png')
    sns_plot.savefig(os.path.join(save_dir, save_name))
    return


def session_summary(in_folder, sub_num, session, scan_type, seg_type):
    """
    Summarize a single session for a single subject for a given seg_type.

    Loads appropriate nifti data for ROI of seg_type, loads scan data.
    Then calls roi_extract to get the relevant data for each scan.
    Saves the summaries and returns a list of them.

    Parameters
    ----------
    in_folder : string
        Directory where the scan images are saved.
    sub_num : string
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

    data_dir = os.path.join(datasink_dir, in_folder, 'sub-{}'.format(sub_num),
                            'ses-{}'.format(session), 'qutece')

    csv_dir = 'csv_work_' + scan_type
    # plots_dir = 'plots_' + scan_type

    if not os.path.exists(data_dir):
        data_dir = os.path.join(datasink_dir, in_folder,
                                'sub-{}'.format(sub_num),
                                'ses-{}'.format(session))

    if not os.path.exists(data_dir):
        data_dir = os.path.join(datasink_dir, in_folder,
                                'sub-{}'.format(sub_num))

    roi_dir = os.path.join(manualwork_dir, 'segmentations', seg_type)

    if seg_type == 'Neuromorphometrics':
        ROI_file_name = '/opt/spm12/tpm/labels_Neuromorphometrics.nii'
    elif seg_type == 'noise':
        ROI_file_name = os.path.join(
            roi_dir,
            'rsub-' + sub_num + '_ses-Postcon_hr_run-01_UTE_desc-preproc' +
            '_noise-Segmentation-label.nii')
        if scan_type == 'TOF':
            ROI_file_name = os.path.join(
                roi_dir, 'TOF',
                'rrrsub-' + sub_num + '_ses-Precon_TOF_angio_corrected' +
                '_noise-Segmentation-label.nii')
        if scan_type == 'T1w':
            ROI_file_name = os.path.join(
                roi_dir, 'T1w',
                'rsub-' + sub_num + '_ses-Postcon_T1w_corrected' +
                '_noise-Segmentation-label.nii')

    elif seg_type == 'tissue':
        ROI_file_name = os.path.join(
            roi_dir,
            'rsub-' + sub_num + '_ses-Postcon_hr_run-01_UTE_desc-preproc' +
            '_tissue-Segmentation-label.nii')
        if scan_type == 'TOF':
            ROI_file_name = os.path.join(
                roi_dir, 'TOF',
                'rrrsub-' + sub_num + '_ses-Precon_TOF_angio_corrected' +
                '_tissue-Segmentation-label.nii')

    elif seg_type == 'brain_preFLIRT':
        ROI_file_name = os.path.join(
            roi_dir, 'rrrsub-' + sub_num + '_ses-Precon_T1w_*brain*' +
            '_Segmentation-label.nii')
        ROI_file_names = glob.glob(ROI_file_name)
        ROI_file_name = ROI_file_names[0]
        print(ROI_file_names[0])
    elif seg_type == 'vesselness':
        print('Switch to session_summary_vesselness')
    else:
        print('need valid segmentation type')

    ROI_file_nii = nib.load(ROI_file_name)
    roi_img = np.array(ROI_file_nii.get_fdata())
    session_pattern = '*' + session + '*' + scan_type + '*'
    path_pattern = os.path.join(data_dir, session_pattern)
    nii_files = glob.glob(path_pattern)
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

        if scan_type == 'TOF':
            scan_img[np.abs(scan_img) <= 0.2] = np.nan

        save_dir = os.path.join(datasink_dir, csv_dir,
                                'sub-{}'.format(sub_num),
                                'ses-{}'.format(session))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        summary_df = roi_extract(scan_img, roi_img, fname, seg_type, save_dir)

        save_name = (fname + '_SUMMARY_' + 'seg-{}.csv').format(seg_type)
        summary_df.to_csv(os.path.join(save_dir, save_name))
        print('Saved SUMMARY as : ' + os.path.join(save_dir, save_name))

        summary_df_list.append(summary_df)

    plt.close('all')
    return summary_df_list


def session_summary_vesselness(in_folder, sub_num, session, scan_type,
                               seg_type):
    """
    Summarize a single session for a single subject for only vesselness.

    Loads appropriate nifti data for vesselness, loads scan data.
    Constructs and saves an ROI based on vesselness for given cut_off value(s).
    Then calls roi_extract to get the relevant data for each scan.
    Saves the summaries and returns a list of them.

    Parameters
    ----------
    in_folder : string
        Directory where the scan images are saved.
    sub_num : string
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

    if seg_type != 'vesselness':
        print('switch to normal session_summary function')

    data_dir = os.path.join(datasink_dir, in_folder, 'sub-{}'.format(sub_num),
                            'ses-{}'.format(session), 'qutece')
    csv_dir = 'csv_work_' + scan_type
    # plots_dir = 'plots_' + scan_type

    if not os.path.exists(data_dir):
        data_dir = os.path.join(datasink_dir, in_folder,
                                'sub-{}'.format(sub_num),
                                'ses-{}'.format(session))

    if not os.path.exists(data_dir):
        data_dir = os.path.join(datasink_dir, in_folder,
                                'sub-{}'.format(sub_num))

    print('data dir is :')
    print(data_dir)
    # load brain mask
    roi_dir = os.path.join(manualwork_dir, 'segmentations', 'brain_dil')
    ROI_file_name = os.path.join(
        roi_dir, 'rrrsub-' + sub_num + '_ses-Precon_T1w_*brain*' +
        '_Segmentation-label.nii')

    ROI_file_names = glob.glob(ROI_file_name)
    ROI_file_name = ROI_file_names[0]
    print(ROI_file_names[0])
    ROI_file_nii = nib.load(ROI_file_name)
    roi_img = np.array(ROI_file_nii.get_fdata())

    session_pattern = '*rsub*' + session + '*' + scan_type + '*'
    path_pattern = os.path.join(data_dir, session_pattern)
    nii_files = glob.glob(path_pattern)
    print('Selected files are: ')
    print(nii_files)

    summary_df_list = []

    vesselness_dir = os.path.join(manualwork_dir, 'vesselness_filtered_2',
                                  'sub-{}'.format(sub_num))

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

        end_str = '_sb=25_sp=10_sig=3_ss=1'
        end_str = '_sb=25_sp=10'

        # load vesselness for scan
        if (session == 'Postcon' and scan_type == 'hr') or scan_type == 'TOF':
            vessel_fname = fname + '_AutoVess_g=*' + end_str + '.nii'

        elif (session == 'Precon' and scan_type == 'hr') or scan_type == 'T1w':
            vessel_fname = ('rsub-' + sub_num +
                            '_ses-Postcon_hr_run-01_UTE_desc-preproc' +
                            '_AutoVess_g=*' + end_str + '.nii')

        vessel_file_name_pattern = os.path.join(vesselness_dir, vessel_fname)
        vessel_file_name = glob.glob(vessel_file_name_pattern)
        print(fname)
        print('possible vesselness:')
        print(vessel_file_name_pattern)
        print(vessel_file_name)
        vessel_file_name = vessel_file_name[0]
        vessel_nii = nib.load(vessel_file_name)
        vessel_img = np.array(vessel_nii.get_fdata())

        # crop initial brain from both scan and vesselness
        t = 'equal'
        r = 1
        scan_img, __ = roi_cut(scan_img, roi_img, t, r)
        vessel_img, __ = roi_cut(vessel_img, roi_img, t, r)

        # construct vesselness roi
        cut_off = 0.95
        med_cut_off = 0.85
        small_cut_off = 0.20
        large_vess = (vessel_img >= cut_off).astype(int) * 1
        med_vess = ((vessel_img < cut_off) &
                    (vessel_img >= med_cut_off)).astype(int) * 2
        small_vess = ((vessel_img < med_cut_off) &
                      (vessel_img >= small_cut_off)).astype(int) * 3
        no_vess = (vessel_img < 0.1).astype(int) * 4
        # So we have
        # ['no_vess':4, 'small_vess':3, 'med_vess':2, 'large_vess':1]

        vessel_roi_img = no_vess + med_vess + small_vess + large_vess
        vessel_roi_nii = nib.Nifti1Image(vessel_roi_img, vessel_nii.affine,
                                         vessel_nii.header)

        save_dir = os.path.join(datasink_dir, 'vessel_roi',
                                'sub-{}'.format(sub_num))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        save_name = (fname + '_' + 'seg-{}.nii').format(seg_type)
        nib.save(vessel_roi_nii, os.path.join(save_dir, save_name))

        save_dir = os.path.join(datasink_dir, csv_dir,
                                'sub-{}'.format(sub_num),
                                'ses-{}'.format(session))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        summary_df = roi_extract(scan_img, vessel_roi_img, fname, seg_type,
                                 save_dir)

        save_name = (fname + '_SUMMARY_' + 'seg-{}.csv').format(seg_type)
        summary_df.to_csv(os.path.join(save_dir, save_name))
        print('Saved SUMMARY as : ' + os.path.join(save_dir, save_name))

        summary_df_list.append(summary_df)

    plt.close('all')
    return summary_df_list


def load_summary_dfs(csv_dir, sub_num, session, seg_type, scan_type):
    """
    Load the summary csv files made by session_summary functions.

    Does some processing on the dfs to add session, file name fields.
    Transposes data from original such that 'mean', 'std' etc. are columns.

    Parameters
    ----------
    csv_dir : string
        Directory where the SUMMARY csv files for each scan are saved.
    sub_num : string
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

    data_dir = os.path.join(datasink_dir, csv_dir, 'sub-{}'.format(sub_num),
                            'ses-{}'.format(session))
    path_pattern = os.path.join(
        data_dir, '*' + scan_type + '*_SUMMARY_seg-' + seg_type + '*.csv')
    load_files = glob.glob(path_pattern)
    df_list = []
    for f in load_files:
        df = pd.read_csv(f)
        pth, fname, ext = split_filename(f)
        df.rename(columns={'Unnamed: 0': 'name'}, inplace=True)
        df = df.set_index('name').T
        df['session'] = session
        df['file'] = fname
        df_list.append(df)

    return df_list


def load_full_summary_dfs(seg_type_list, scan_type):
    csv_dir = 'csv_work_' + scan_type
    data_dir = os.path.join(datasink_dir, csv_dir)
    df_list = []
    for seg_type in seg_type_list:
        f = os.path.join(data_dir, 'FULL_SUMMARY_seg-' + seg_type + '.csv')
        df = pd.read_csv(f, index_col=0)
        df.rename(columns={'index': 'region'}, inplace=True)
        pth, fname, ext = split_filename(f)
        scan_names = df['file'].str.rsplit("_", n=2, expand=True)
        df['seg_type'] = seg_type
        df['scan'] = scan_names[0]
        print(df.head())
        df_list.append(df)

    return df_list


def subject_summary(sub_num, scan_type, seg_type):
    """
    Summarize a seg_type's mean and std across sessions for a single subject.

    Loads sessions_summary data output as csv files via load_summary_dfs().
    Concatenates pre and post summaries into larger DataFrames.
    Plots across mean value across region number.

    Parameters
    ----------
    sub_num : string
    scan_type : string
        hr or TOF
        TODO: add fast support
    seg_type : string

    Returns
    -------
    postcon_df : concatenated pandas DataFrame
    precon_df : concatenated pandas DataFrame

    """
    csv_dir = 'csv_work_' + scan_type
    plots_dir = 'plots_' + scan_type
    session = 'Precon'
    precon_df_list = load_summary_dfs(csv_dir, sub_num, session, seg_type,
                                      scan_type)
    precon_df = pd.concat(precon_df_list)
    print(precon_df_list)

    session = 'Postcon'
    postcon_df_list = load_summary_dfs(csv_dir, sub_num, session, seg_type,
                                       scan_type)
    postcon_df = pd.concat(postcon_df_list)
    # print(postcon_df_list)
    # if len(postcon_df_list) > 1:
    #     postcon_df = pd.concat(postcon_df_list)
    # else:
    #     postcon_df = postcon_df_list[0]

    save_dir = os.path.join(datasink_dir, plots_dir, 'sub-{}'.format(sub_num))
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    x_axis = "index"
    y_axis = "mean"
    category_plot(postcon_df, precon_df, save_dir, sub_num, seg_type, x_axis,
                  y_axis)
    y_axis = "std"
    category_plot(postcon_df, precon_df, save_dir, sub_num, seg_type, x_axis,
                  y_axis)

    return postcon_df, precon_df


def snr_subject_summary(sub_num, scan_type):
    """
    Summarize SNR and ISH across sessions for a single subject.

    Reads SNR calculation csv files made by snr_session.
    Plots SNR and ISH values precontrast and postcontrast.
    For TOF, postcon_df is left intentionally empty.

    Parameters
    ----------
    sub_num : string
    scan_type : string
        hr or TOF
        TODO: add fast support

    Returns
    -------
    postcon_df : pandas DataFrame
    precon_df : pandas DataFrame

    """
    csv_dir = 'csv_work_' + scan_type
    plots_dir = 'plots_' + scan_type
    seg_type = 'CNR'
    session = 'Precon'
    data_dir = os.path.join(datasink_dir, csv_dir, 'sub-{}'.format(sub_num),
                            'ses-{}'.format(session))
    f = ('sub-' + sub_num + '_ses-' + session + '_CNR' + '.csv')
    precon_df = pd.read_csv(os.path.join(data_dir, f))

    if scan_type != 'TOF':
        session = 'Postcon'
        data_dir = os.path.join(datasink_dir, csv_dir,
                                'sub-{}'.format(sub_num),
                                'ses-{}'.format(session))
        f = ('sub-' + sub_num + '_ses-' + session + '_CNR' + '.csv')
        postcon_df = pd.read_csv(os.path.join(data_dir, f))
    else:
        postcon_df = pd.DataFrame()

    save_dir = os.path.join(datasink_dir, plots_dir, 'sub-{}'.format(sub_num))
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    x_axis = "index_x"
    y_axis = "SNR"
    category_plot(postcon_df, precon_df, save_dir, sub_num, seg_type, x_axis,
                  y_axis)

    y_axis = "ISH"
    category_plot(postcon_df, precon_df, save_dir, sub_num, seg_type, x_axis,
                  y_axis)

    return postcon_df, precon_df


def full_summary(datasink_dir, subject_list, scan_type, seg_type):
    """
    Summarize a seg_type's mean across subjects.

    Loads precon_df and postcon_df's for each subject via subject_summary.
    Adds a sub_num field to them and concatenates them all together.
    Saves this as FULL_SUMMARY_seg-{}.csv

    Filters for first region of the seg_type ROI. Plots it across subjects.

    Parameters
    ----------
    datasink_dir : string
    subject_list : list of strings
    scan_type : string
        hr or TOF
        TODO: add fast support
    seg_type : string

    Returns
    -------

    """
    csv_dir = 'csv_work_' + scan_type
    plots_dir = 'plots_' + scan_type
    df_list = []
    for sub_num in subject_list:
        postcon_df, precon_df = subject_summary(sub_num, scan_type, seg_type)
        postcon_df['sub_num'] = sub_num
        precon_df['sub_num'] = sub_num
        df_list.append(postcon_df)
        df_list.append(precon_df)

    full_df = pd.concat(df_list)
    full_df = full_df.reset_index()
    full_df['index'] = pd.to_numeric(full_df['index'], downcast='integer')
    full_df['scan_type'] = scan_type
    print(seg_type + ' full_df : ')
    print(full_df.head())
    filt_df = full_df.loc[(full_df['index'] == 1)]
    print(filt_df.head())

    save_dir = os.path.join(datasink_dir, plots_dir)
    y_axis = 'mean'
    if seg_type != 'Neuromorphometrics':
        subjects_plot(filt_df, save_dir, seg_type, y_axis)

    save_name = ('FULL_SUMMARY_seg-{}.csv').format(seg_type)
    save_dir = os.path.join(datasink_dir, csv_dir)
    full_df.to_csv(os.path.join(save_dir, save_name))
    return


def snr_full_summary(datasink_dir, subject_list, scan_type):
    """
    Summarize a SNR results across subjects.

    Loads precon_df and postcon_df's for each subject via snr_subject_summary.
    Adds a sub_num field to them and concatenates them all together.
    Saves this as FULL_SUMMARY_seg-SNR.csv

    Parameters
    ----------
    datasink_dir : string
    subject_list : list of strings
    scan_type : string
        hr or TOF
        TODO: add fast support

    Returns
    -------

    """
    seg_type = 'CNR'
    csv_dir = 'csv_work_' + scan_type
    plots_dir = 'plots_' + scan_type
    df_list = []
    for sub_num in subject_list:
        # note the subsitution of snr_subject_summary vs subject_summary
        postcon_df, precon_df = snr_subject_summary(sub_num, scan_type)
        postcon_df['sub_num'] = sub_num
        precon_df['sub_num'] = sub_num
        df_list.append(postcon_df)
        df_list.append(precon_df)

    full_df = pd.concat(df_list)
    full_df = full_df.reset_index()
    full_df['index'] = pd.to_numeric(full_df['index'], downcast='integer')
    full_df['scan_type'] = scan_type
    print(seg_type + ' full_df : ')
    print(full_df.head())

    save_dir = os.path.join(datasink_dir, plots_dir)
    y_axis = 'SNR'
    subjects_plot(full_df, save_dir, seg_type, y_axis)
    y_axis = 'ISH'
    subjects_plot(full_df, save_dir, seg_type, y_axis)
    y_axis = 'CNR'
    subjects_plot(full_df, save_dir, seg_type, y_axis)

    save_name = ('FULL_SUMMARY_seg-{}.csv').format(seg_type)
    save_dir = os.path.join(datasink_dir, csv_dir)
    full_df.to_csv(os.path.join(save_dir, save_name), index=False)
    return


def calc_snr(signal_df, noise_df):
    """
    Calculate SNR given a DataFrame for signal and one for noise.

    Parameters
    ----------
    signal_df : pandas DataFrame
    noise_df : pandas DataFrame

    Returns
    -------
    cnr_df : pandas DataFrame

    """

    # Grab only region 1
    signal_filt_df = signal_df.filter(
        items=['mean', 'std', 'session', 'file']).filter(regex='^1',
                                                         axis=0).reset_index()
    # Rename columns
    signal_filt_df.rename(columns={
        'mean': 'signal_mean',
        'std': 'signal_std'
    },
                          inplace=True)

    scan_names = signal_filt_df['file'].str.rsplit("_", n=2, expand=True)
    signal_filt_df['scan'] = scan_names[0]

    # Grab only region 1
    noise_filt_df = noise_df.filter(items=['std', 'file']).filter(
        regex='^1', axis=0).reset_index()

    # Rename columns
    noise_filt_df.rename(columns={'std': 'noise_std'}, inplace=True)
    scan_names = noise_filt_df['file'].str.rsplit("_", n=2, expand=True)
    noise_filt_df['scan'] = scan_names[0]

    # combine them so that noise value in each scan is matched with signal
    snr_df = pd.merge(signal_filt_df, noise_filt_df, on='scan')
    snr_df = snr_df.drop(columns=['file_x', 'file_y'])
    snr_df['SNR'] = snr_df['signal_mean'] / snr_df['noise_std']
    snr_df['ISH'] = snr_df['signal_std'] / snr_df['signal_mean']

    return snr_df


def calc_cnr(signal_df, tissue_df, noise_df):
    """
    Calculate CNR given DataFrames for signal, tissue and noise.

    Parameters
    ----------
    signal_df : pandas DataFrame
    tissue_df : pandas DataFrame
    noise_df : pandas DataFrame

    Returns
    -------
    cnr_df : pandas DataFrame

    """

    # Grab only region 1
    signal_filt_df = signal_df.filter(
        items=['mean', 'std', 'session', 'file']).filter(regex='^1',
                                                         axis=0).reset_index()
    tissue_filt_df = tissue_df.filter(items=['mean', 'std', 'file']).filter(
        regex='^1', axis=0).reset_index()
    # Rename columns
    signal_filt_df.rename(columns={
        'mean': 'signal_mean',
        'std': 'signal_std'
    },
                          inplace=True)

    # Rename columns
    tissue_filt_df.rename(columns={
        'mean': 'tissue_mean',
        'std': 'tissue_std'
    },
                          inplace=True)

    print('Tissue df :')
    print(tissue_filt_df.head())

    scan_names = signal_filt_df['file'].str.rsplit("_", n=2, expand=True)
    signal_filt_df['scan'] = scan_names[0]

    scan_names = tissue_filt_df['file'].str.rsplit("_", n=2, expand=True)
    tissue_filt_df['scan'] = scan_names[0]

    # Grab only region 1
    noise_filt_df = noise_df.filter(items=['std', 'file']).filter(
        regex='^1', axis=0).reset_index()

    # Rename columns
    noise_filt_df.rename(columns={'std': 'noise_std'}, inplace=True)
    scan_names = noise_filt_df['file'].str.rsplit("_", n=2, expand=True)
    noise_filt_df['scan'] = scan_names[0]

    # combine them so that noise value in each scan is matched with signal
    cnr_df = pd.merge(signal_filt_df, tissue_filt_df, on='scan')
    cnr_df = pd.merge(cnr_df, noise_filt_df, on='scan')

    cnr_df = cnr_df.drop(columns=['file_x', 'file_y'])
    cnr_df['SNR'] = cnr_df['signal_mean'] / cnr_df['noise_std']
    cnr_df['CNR'] = (cnr_df['signal_mean'] -
                     cnr_df['tissue_mean']) / cnr_df['noise_std']
    cnr_df['ISH'] = cnr_df['signal_std'] / cnr_df['signal_mean']
    cnr_df = cnr_df.round(2)

    return cnr_df


def snr_session(sub_num, session, scan_type):
    """
    Get and save SNR for a single session of a single subject.

    Sets up signal and noise dfs to pass to calc_snr.
    Saves the result.

    Parameters
    ----------
    sub_num : string
    session : string
        Precon or Postcon
    scan_type : string
        hr or TOF
        TODO: add fast support

    Returns
    -------
    snr_df : pandas DataFrame

    """
    csv_dir = 'csv_work_' + scan_type

    seg_type = 'vesselness'
    vessel_df_list = load_summary_dfs(csv_dir, sub_num, session, seg_type,
                                      scan_type)
    vessel_df = pd.concat(vessel_df_list)

    seg_type = 'noise'
    noise_df_list = load_summary_dfs(csv_dir, sub_num, session, seg_type,
                                     scan_type)
    noise_df = pd.concat(noise_df_list)

    snr_df = calc_snr(vessel_df, noise_df)

    seg_type = 'tissue'
    tissue_df_list = load_summary_dfs(csv_dir, sub_num, session, seg_type,
                                      scan_type)
    tissue_df = pd.concat(tissue_df_list)
    cnr_df = calc_cnr(vessel_df, tissue_df, noise_df)

    save_dir = os.path.join(datasink_dir, csv_dir, 'sub-{}'.format(sub_num),
                            'ses-{}'.format(session))

    save_name = ('sub-' + sub_num + '_ses-' + session + '_SNR' + '.csv')
    snr_df.to_csv(os.path.join(save_dir, save_name), index=False)
    print('Calculated SNR :')
    print(snr_df.head())

    print('Calculated CNR :')
    print(cnr_df.head())
    save_name = ('sub-' + sub_num + '_ses-' + session + '_CNR' + '.csv')
    cnr_df.to_csv(os.path.join(save_dir, save_name), index=False)
    return snr_df, cnr_df


def snr_compare():
    """
    Compare SNR (and other values) between hr_UTE and TOF scans.

    Just saves plots.

    Parameters
    ----------

    Returns
    -------

    """
    plots_dir = 'plots_hr'
    seg_type = 'SNR'
    scan_type = 'hr'
    csv_dir = 'csv_work_' + scan_type
    load_file = ('FULL_SUMMARY_seg-{}.csv').format(seg_type)
    data_dir = os.path.join(datasink_dir, csv_dir)
    ute_df = pd.read_csv(os.path.join(data_dir, load_file))

    scan_type = 'TOF'
    csv_dir = 'csv_work_' + scan_type
    load_file = ('FULL_SUMMARY_seg-{}.csv').format(seg_type)
    data_dir = os.path.join(datasink_dir, csv_dir)
    tof_df = pd.read_csv(os.path.join(data_dir, load_file))

    full_df = pd.concat([ute_df, tof_df])
    save_dir = os.path.join(datasink_dir, plots_dir)
    print('full_df: ')
    print(full_df.head())
    print(full_df.tail())
    filt_df = full_df.loc[~((full_df['session'] == 'Precon')
                            & (full_df['scan_type'] == 'hr'))]

    # remove outliers
    print('filt_df: ')
    print(filt_df.head())
    print(filt_df.tail())

    subjects = set(list(ute_df['sub_num'])).intersection(
        list(tof_df['sub_num']))
    print(subjects)

    filt_df = filt_df[filt_df['sub_num'].isin(subjects)]

    y_axis = 'SNR'
    subjects_plot_compare(filt_df, save_dir, seg_type, y_axis)

    y_axis = 'ISH'
    subjects_plot_compare(filt_df, save_dir, seg_type, y_axis)

    y_axis = 'noise_std'
    subjects_plot_compare(filt_df, save_dir, seg_type, y_axis)

    y_axis = 'signal_std'
    subjects_plot_compare(filt_df, save_dir, seg_type, y_axis)

    filt_df.drop(columns=['index', 'index_x', 'index_y', 'scan'], inplace=True)

    print(filt_df.groupby('scan_type').mean())
    print(filt_df.groupby('scan_type').std())
    print(filt_df.groupby('scan_type').count())

    return full_df, filt_df


def compare():
    seg_type_list = ['vesselness', 'noise', 'brain_preFLIRT']

    scan_type = 'hr'
    hr_df_list = load_full_summary_dfs(seg_type_list, scan_type)
    hr_df = pd.concat(hr_df_list, ignore_index=True)
    print(hr_df.head())
    print(hr_df.tail())

    # scan_type = 'TOF'
    # TOF_df_list = load_full_summary_dfs(seg_type_list, scan_type)
    # TOF_df = pd.concat(TOF_df_list, ignore_index=True)
    # print(TOF_df.head())
    # print(TOF_df.tail())

    return


# RUNNING


def base_runner(subject_list, seg_type, scan_type, folder_post, folder_pre):
    for sub_num in subject_list:
        session = 'Precon'
        in_folder = folder_pre
        session_summary(in_folder, sub_num, session, scan_type, seg_type)

        session = 'Postcon'
        in_folder = folder_post
        session_summary(in_folder, sub_num, session, scan_type, seg_type)

        # subject_summary doesn't need to be explicitly called since
        # it is in full_summary
        # subject_summary(sub_num, scan_type, seg_type)
    full_summary(datasink_dir, subject_list, scan_type, seg_type)
    plt.close('all')


def snr_runner(subject_list, scan_type):
    # scan_type = 'hr'
    for sub_num in subject_list:
        session = 'Precon'
        snr_session(sub_num, session, scan_type)

        session = 'Postcon'
        snr_session(sub_num, session, scan_type)

        snr_subject_summary(sub_num, scan_type)

    snr_full_summary(datasink_dir, subject_list, scan_type)
    plt.close('all')
    return


def atlas_runner(subject_list, scan_type):
    seg_type = 'Neuromorphometrics'
    in_folder = 'nonlinear_transfomed_hr'
    base_runner(subject_list, seg_type, scan_type, in_folder, in_folder)


def noise_runner(subject_list, scan_type):
    seg_type = 'noise'

    if scan_type == 'hr':
        folder_post = 'preprocessing'
    elif scan_type == 'T1w':
        folder_post = 'intrasession_coregister'

    folder_pre = 'pre_to_post_coregister'
    base_runner(subject_list, seg_type, scan_type, folder_post, folder_pre)


def tissue_runner(subject_list, scan_type):
    seg_type = 'tissue'
    if scan_type == 'hr':
        folder_post = 'preprocessing'
    elif scan_type == 'T1w':
        folder_post = 'intrasession_coregister'

    folder_pre = 'pre_to_post_coregister'
    base_runner(subject_list, seg_type, scan_type, folder_post, folder_pre)


def brain_runner(subject_list, scan_type):
    seg_type = 'brain_preFLIRT'
    folder_post = 'preprocessing'
    folder_pre = 'pre_to_post_coregister'
    base_runner(subject_list, seg_type, scan_type, folder_post, folder_pre)


def vesselness_runner(subject_list, scan_type):
    seg_type = 'vesselness'
    for sub_num in subject_list:
        session = 'Postcon'
        if scan_type == 'hr':
            in_folder = 'preprocessing'
        elif scan_type == 'T1w':
            in_folder = 'intrasession_coregister'

        session_summary_vesselness(in_folder, sub_num, session, scan_type,
                                   seg_type)

        session = 'Precon'
        in_folder = 'pre_to_post_coregister'
        session_summary_vesselness(in_folder, sub_num, session, scan_type,
                                   seg_type)
        subject_summary(sub_num, scan_type, seg_type)

    full_summary(datasink_dir, subject_list, scan_type, seg_type)
    plt.close('all')


def tof_runner():
    # TIME OF FLIGHT
    scan_type = 'TOF'
    # TOF_subjects = [
    #     '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '14'
    # ]
    TOF_subjects = ['02', '04', '05', '06', '07', '08', '09', '10', '11', '14']
    TOF_subjects = ['02', '04', '05', '06', '07', '08', '10', '11', '14']
    # TOF_subjects = ['02', '04', '05', '06', '07']
    # TOF_subjects = ['08', '09', '10', '11', '14']
    # TOF_subjects = ['14']
    subject_list = TOF_subjects
    for sub_num in subject_list:
        session = 'Precon'
        in_folder = 'pre_to_post_coregister'
        seg_type = 'noise'
        session_summary(in_folder, sub_num, session, scan_type, seg_type)
        seg_type = 'tissue'
        session_summary(in_folder, sub_num, session, scan_type, seg_type)
        seg_type = 'vesselness'
        session_summary_vesselness(in_folder, sub_num, session, scan_type,
                                   seg_type)
        snr_session(sub_num, session, scan_type)
        seg_type = 'brain_preFLIRT'
        session_summary(in_folder, sub_num, session, scan_type, seg_type)
        snr_subject_summary(sub_num, scan_type)
    snr_full_summary(datasink_dir, subject_list, scan_type)
    plt.close('all')


# def load_meta_data(df):
#     for filename in df['file']:
#
#       json_dir=os.path.join(base_path, 'sub-'+sub_num,'ses-Postcon','qutece')
#
#         jsonfilename = os.path.join(json_dir, fname + '.json')
#
#         'rrrsub-02_ses-Precon_hr_run-01_UTE_desc-preproc'
#         'rsub-02_ses-Postcon_hr_run-01_UTE_desc-preproc'
#
#         with open(jsonfilename) as json_file:
#             j_obj = json.load(json_file)
#             FA = j_obj['FlipAngle']
#
#     return summary_df


def main():

    subject_list = [
        '02', '03', '04', '05', '06', '07', '08', '10', '11', '12', '13', '14',
        '15'
    ]
    # subject_list = ['10', '11', '12', '13', '14', '15']
    # subject_list = ['02', '03', '04', '05', '06', '07', '08']
    subject_list = ['02', '03', '04', '05', '06', '07', '08', '10', '11']
    # scan_type = 'hr'
    # subject_list = ['11']
    scan_type = 'T1w'
    # vesselness_runner(subject_list, scan_type)
    # tissue_runner(subject_list, scan_type)
    # noise_runner(subject_list, scan_type)
    # tof_runner()
    # brain_runner(subject_list, scan_type)
    snr_runner(subject_list, scan_type)
    # snr_compare()
    # atlas_runner(subject_list, scan_type)
    # compare()
    return


if __name__ == "__main__":
    main()
