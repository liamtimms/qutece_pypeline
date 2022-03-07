import os
import glob
import numpy as np
import nibabel as nib
import pandas as pd
import seaborn as sns
import plotter
from sklearn.neighbors import KernelDensity
import matplotlib.pyplot as plt

base_dir = os.path.abspath('../../..')
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
    qutece_scans_df['scan type'] = scan_type

    scan_type = 'T1w'
    mprage_scans_df = load_data(sub_num, session, scan_type, seg_type, region)

    session = 'Precon'
    scan_type = 'TOF'
    tof_scans_df = load_data(sub_num, session, scan_type, seg_type, region)

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
    scans_df = pd.DataFrame()
    n = 0
    for f in csv_files:
        # convert to integers for faster processing
        vals_df = pd.read_csv(f).round(0)
        vals_df['1.0'] = pd.to_numeric(vals_df['1.0'], downcast='integer')
        n = n + vals_df.size

        vals_df['filename'] = f
        scans_df = pd.concat([scans_df, vals_df])

    m = scans_df.size / 2
    if n != int(m):
        print(f"ERROR: n is {n}, m is {m}")

    scans_df.rename(
        columns={scans_df.columns[0]: "intensity"}, inplace=True)

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
    if t == 'seaborn':
        sns.set_theme(font_scale=1.15)
        sns_fig = sns.displot(
            data=full_df,
            y="intensity",
            # hue="sub_num",
            hue="scan type",
            # col="scan type",
            linewidth=1,
            # binwidth=0.025,
            binwidth=10,
            # multiple='dodge',
            # kde=True,
            # log_scale=True,
            height=8,
            aspect=.8,
            element='step',
            palette=['darkorange', 'mediumseagreen'],
            # fill=False
            )
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
    subject_list = [
        '02', '03', '04', '05', '06', '07', '08', '10', '11', '12', '13', '14',
        '15'
    ]

    mega_df = pd.DataFrame()
    for sub_num in subject_list:
        qutece_scans_df, mprage_scans_df, tof_scans_df = load_csvs(sub_num)
        qutece_scans_df = qutece_scans_df.loc[(qutece_scans_df['intensity'] >
                                               10)]
        # print(qutece_scans_df.quantile(q=0.75))
        qutece_scans_df['intensity'] = (qutece_scans_df['intensity'] /
                                        qutece_scans_df['intensity'].median())
        qutece_scans_df['sub_num'] = sub_num
        mega_df = pd.concat([mega_df, qutece_scans_df])

    hist_dir = 'test_hist'
    if not os.path.exists(hist_dir):
        os.mkdir(hist_dir)
    save_name = os.path.join('test_hist', 'test_mega_norm.png')
    plot_dis(mega_df, 'seaborn', save_name)

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

    save_name = 'sub_02_new.png'
    save_path = os.path.join(datasink_dir, 'dist_test', save_name)
    plot_dis(full_df, 'seaborn', save_path)

    return 0


def main():
    """TODO: Docstring for main.

    :arg1: TODO
    :returns: TODO

    """
    run_from_nii()
    pass


if __name__ == "__main__":
    main()
