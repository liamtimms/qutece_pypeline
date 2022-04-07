import os
import glob
import numpy as np
import nibabel as nib
import pandas as pd
import seaborn as sns
import plotter
from plotting_snr_cnr_clean import cleaning
from sklearn.neighbors import KernelDensity
import matplotlib.pyplot as plt

base_dir = os.path.abspath('../..')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
manualwork_dir = os.path.join(base_dir, 'derivatives', 'manualwork')
img_dir = os.path.join(manualwork_dir, 'renderings', 'figure-making',
                       'sub-02_hr_brain_thresholded_rendering')


def load_imgs():
    f = os.path.join(
        img_dir, 'fe', 'rsub-02_ses-Postcon_hr_run-03' +
        '_UTE_desc-preproc_refined-brain-cropped.nii')
    scan_file_name = f
    scan_file_nii = nib.load(scan_file_name)
    qutece_img = np.array(scan_file_nii.get_fdata())

    f = os.path.join(img_dir, 'gd',
                     'sub-02_ses-Post_Sag_T1_MPRAGE_t1w-masked.nii')
    scan_file_name = f
    scan_file_nii = nib.load(scan_file_name)
    gd_img = np.array(scan_file_nii.get_fdata())

    f = os.path.join(base_dir, 'sub-02', 'ses-Precon', 'anat',
                     'sub-02_ses-Precon_TOF_run-01_angio.nii')
    scan_file_name = f
    scan_file_nii = nib.load(scan_file_name)
    tof_img = np.array(scan_file_nii.get_fdata())

    return qutece_img, gd_img, tof_img


def load_csvs(sub_num):
    """loads specific the specific brain CSVs underconsideration
    :returns: dataframes for each scan type

    """
    seg_type = 'brain'
    region = '1'

    session = 'Postcon'
    scan_type = 'hr'
    qutece_scans_df = load_data(sub_num, session, scan_type, seg_type, region)
    qutece_scans_df['scan type'] = "QUTE-CE"

    scan_type = 'T1w'
    mprage_scans_df = load_data(sub_num, session, scan_type, seg_type, region)
    mprage_scans_df['scan type'] = "MPRAGE"

    session = 'Precon'
    scan_type = 'TOF'
    tof_scans_df = load_data(sub_num, session, scan_type, seg_type, region)
    tof_scans_df['scan type'] = "TOF"

    return qutece_scans_df, mprage_scans_df, tof_scans_df


def load_data(sub_num, session, scan_type, seg_type, region):
    """General function for loading `.csv` files created by the pipeline
    :returns:

    """
    csv_dir = os.path.join(datasink_dir, 'csv_work_' + scan_type,
                           'sub-' + sub_num, 'ses-' + session)

    # data extracted by 'plotter.py'
    csv_pattern = f"*{session}*{scan_type}*DATA*{seg_type}*{region}.csv"
    path_pattern = os.path.join(csv_dir, csv_pattern)
    csv_files = glob.glob(path_pattern)
    print(csv_files)
    scans_df = pd.DataFrame()
    n = 0
    for f in csv_files:
        # convert to integers for faster processing
        vals_df = pd.read_csv(f).round(0)
        vals_df['1.0'] = pd.to_numeric(vals_df['1.0'], downcast='integer')
        n = n + vals_df.size

        if len(vals_df.columns) != 0:
            vals_df.rename(columns={vals_df.columns[0]: "intensity"},
                           inplace=True)

        hist_df = hist_data(vals_df)
        save_path = os.path.join(datasink_dir, 'csv_test/',
                                 f.replace("DATA", "HIST"))
        hist_df.to_csv(save_path, index=False)

        vals_df['filename'] = f
        scans_df = pd.concat([scans_df, vals_df])

    m = scans_df.size / 2
    if n != int(m):
        print(f"ERROR: n is {n}, m is {m}")

    return scans_df


def filt_norm_data(scans_df):
    """TODO: Docstring for filt_data.

    :function: TODO
    :returns: TODO

    """
    if 'intensity' not in scans_df:
        return scans_df
    else:
        scans_df = scans_df.loc[(scans_df['intensity'] > 10)]
        # scans_df['intensity'] = (100 * scans_df['intensity'] /
        #                          scans_df['intensity'].median())
        return scans_df


def extract(scan_img, scan_type):
    save_name = scan_type + '_data.csv'
    save_path = os.path.join(datasink_dir, 'csv_test', save_name)

    if not os.path.isfile(save_path):
        t = 'greater'
        r = 10
        roi_img = scan_img
        crop_img, vals_df = plotter.roi_cut(scan_img, roi_img, t, r)
        vals_df['scan type'] = scan_type
        vals_df.to_csv(save_path, index=False)
    else:
        vals_df = pd.read_csv(save_path)

    vals_df.rename(columns={
        vals_df.columns[0]: "intensity",
        vals_df.columns[1]: "scan type"
    },
                   inplace=True)
    vals_df = vals_df.round(0)
    vals_df['intensity'] = pd.to_numeric(vals_df['intensity'],
                                         downcast='integer')

    save_name = scan_type + '_hist.csv'
    save_path = os.path.join(datasink_dir, 'csv_test', save_name)
    hist_df = hist_data(vals_df)
    hist_df.to_csv(save_path, index=False)
    return vals_df, hist_df


def clean(vals_df):
    ...
    pass


def calc_kde(df):
    x = df['intensity'].to_numpy().reshape(-1, 1)
    kde = KernelDensity(bandwidth=1.0, kernel='gaussian').fit(x)
    print(kde)
    return


def plot_dis(full_df, t, save_name):
    # calc_kde(full_df)
    if full_df['scan type'].nunique() == 3:
        p = ['darkorange', 'mediumseagreen', 'slateblue']
    elif full_df['scan type'].nunique() == 2:
        p = ['darkorange', 'mediumseagreen']
        print(p)

    if t == 'seaborn':
        sns.set_theme(style="ticks", font_scale=1.5)
        sns_fig = sns.displot(
            data=full_df,
            y="intensity",
            # hue="sub_num",
            hue="scan type",
            col="scan type",
            linewidth=3,
            binwidth=0.025,
            # multiple='dodge',
            # kde=True,
            log_scale=True,
            element='step',
            # palette=['darkorange', 'mediumseagreen'],
            palette=p,
            fill=False)
        sns_fig.set(xscale='log')
        sns_fig.savefig(save_name, dpi=300)

    elif t == 'matplot':
        fig, ax = plt.subplot(1, 1)
        sns.histplot(data=full_df,
                     ax=ax,
                     x="intensity",
                     hue="scan_type",
                     binwidth=5,
                     stat='frequency',
                     multiple="fill")
        plt.show()
        fig.savefig(save_name, bbox_inches='tight')

    plt.close('all')
    return


def run_from_csv():
    """TODO: Docstring for main.

    :arg1: TODO
    :returns: TODO

    """
    scan_types = ['hr', 'T1w']
    subject_list = [
        '02', '03', '04', '05', '06', '07', '08', '10', '11', '12', '13', '14',
        '15'
    ]

    scan_types = ['hr', 'T1w', 'TOF']
    TOF_subjects = ['02', '04', '05', '06', '07', '08', '10', '11', '14']
    subject_list = TOF_subjects

    # mega_df = pd.DataFrame()
    hist_dir = 'test_hist'

    # , 'TOF']
    for sub_num in subject_list:
        big_df = pd.DataFrame()
        print(f" Starting subject: {sub_num}")
        for scan_type in scan_types:
            print(f" Starting scan_type: {scan_type}")
            if scan_type == 'TOF':
                session = 'Precon'
            else:
                session = 'Postcon'
            seg_type = 'brain'
            region = '1'
            scans_df = load_data(sub_num, session, scan_type, seg_type, region)
            scans_df = filt_norm_data(scans_df)
            scans_df['scan type'] = scan_type
            print(scans_df.head())
            big_df = pd.concat([big_df, scans_df])

        save_name = os.path.join(hist_dir, f'{sub_num}_hist.png')
        big_df = cleaning(big_df)
        print(big_df['scan type'].unique())
        plot_dis(big_df, 'seaborn', save_name)

        # qutece_scans_df, mprage_scans_df, tof_scans_df = load_csvs(sub_num)
        # qutece_scans_df = filt_norm_data(qutece_scans_df)
        # mprage_scans_df = filt_norm_data(mprage_scans_df)
        # tof_scans_df = filt_norm_data(tof_scans_df)
        # big_df = pd.concat([qutece_scans_df, mprage_scans_df, tof_scans_df])
        # big_df['sub_num'] = sub_num
        # mega_df = pd.concat([mega_df, big_df])

    # if not os.path.exists(hist_dir):
    #     os.mkdir(hist_dir)
    # save_name = os.path.join('test_hist', 'test_mega_norm.png')

    # plot_dis(mega_df, 'seaborn', save_name)

    return


def hist_data(vals_df):
    """TODO: Docstring for hist_data.
    :returns: TODO

    """
    print(vals_df.describe())
    count_df = pd.DataFrame()
    bin_df = pd.DataFrame()
    count_df['counts'], bin_df['bins'] = np.histogram(vals_df['intensity'],
                                                      bins=1000)
    hist_df = pd.concat([count_df, bin_df], ignore_index=True, axis=1)
    print(hist_df.head())
    return hist_df


def run_from_nii():
    qutece_img, gd_img, tof_img = load_imgs()

    scan_type = 'QUTE-CE'
    q_vals_df, _ = extract(qutece_img, scan_type)

    scan_type = 'Gd MPRAGE'
    g_vals_df, _ = extract(gd_img, scan_type)
    # scan_type = 'TOF'
    # t_vals_df = extract(tof_img, scan_type)

    full_df = pd.concat([q_vals_df, g_vals_df])
    print(full_df.head())
    full_df = full_df.round(0)
    full_df['scan type'] = pd.Categorical(full_df['scan type'],
                                          ["QUTE-CE", "Gd MPRAGE"])
    full_df = full_df.sort_values(by=['scan type'], ascending=False)

    save_name = 'test_hist/sub_02.png'
    plot_dis(full_df, 'seaborn', save_name)

    return 0


def main():
    """TODO: Docstring for main.

    :arg1: TODO
    :returns: TODO

    """
    # run_from_nii()
    run_from_csv()
    pass


if __name__ == "__main__":
    main()
