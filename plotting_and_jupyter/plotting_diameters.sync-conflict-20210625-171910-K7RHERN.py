import glob
import os

# import matplotlib
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import pandas as pd
# from mpl_toolkits.mplot3d import Axes3D
import plotter
import seaborn as sns

base_dir = os.path.abspath('../../..')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
manualwork_dir = os.path.join(base_dir, 'derivatives', 'manualwork')


def voxaltor(df, vessel):
    """rounds everything to 1 mm
    must be applied to only one vessel in one subject at a time
    """
    pass
    df['distance (mm) vox'] = df['distance (mm)'].astype(int)
    df = df.groupby('distance (mm) vox').mean()
    df['vessel'] = vessel
    return df


def relandreg_plot(x_axis, y_axis, hue, proc_df):
    sns.set_theme(style="whitegrid", font_scale=1.5)
    # sns.set_theme()

    ave_df_list = []

    for s in proc_df['subject'].unique():
        s_df = proc_df.loc[(proc_df['subject'] == s)]
        s_ave_df = proc_df
        s_ave_df = s_ave_df.rolling(10).mean()
        ave_df_list.append(s_ave_df)

    ave_df = pd.concat(ave_df_list)

    # cmap = sns.diverging_palette(240, 10, l=65, center="dark", as_cmap=True)
    sns_plot = sns.relplot(
        x=x_axis,
        y=y_axis,
        # hue=hue,
        # palette='inferno',
        # col='subject',
        # size="Weight(kg)", sizes=(50,150),
        # size="Cyst_Vol.(ml)", sizes=(50,150),
        # style="Side", # sizes=(100,150),
        height=8,
        aspect=1.25,
        s=24,
        legend=False,
        data=ave_df)
    # sns_plot.axes[0, 0].invert_xaxis()

    # sns.lineplot(x=x_axis,
    #              y=y_axis,
    #              data=ave_df,
    #              ax=sns_plot.axes[0, 0],
    #              color='black',
    #              # s=1,
    #              legend=False)
    sns_plot.axes[0, 0].set_ylim(0, 6)

    # sns.regplot(
    #     x=x_axis,
    #     y=y_axis,
    #     data=proc_df,
    #     scatter=False,
    #     # style='subject',
    #     ci=None,
    #     color='lightgray',
    #     ax=sns_plot.axes[0, 0],
    #     order=9,
    #     truncate=True)

    # print(p.get_children()[1].get_paths())
    # plt.ylim(0, None)
    return sns_plot


def load_artery_vein(output_dir):
    """TODO: Docstring for load_artery_vein.

    :function: TODO
    :returns: TODO

    """
    vessel_types = ['artery', 'vein']
    full_summary_df = pd.DataFrame()
    for vessel_type in vessel_types:
        Diameter_SUMMARY_csv = os.path.join(
            output_dir, f"SUMMARY-diameter_of_{vessel_type}.csv")
        diameter_df = pd.read_csv(Diameter_SUMMARY_csv)
        full_summary_df = pd.concat([full_summary_df, diameter_df])

    full_summary_df.rename(columns={'diameter': 'diameter (mm)'}, inplace=True)
    full_summary_df = full_summary_df.replace(to_replace='left_vert_artery',
                                              value='LVA')
    full_summary_df = full_summary_df.replace(to_replace='right_vert_artery',
                                              value='RVA')
    full_summary_df = full_summary_df.replace(to_replace='basilar_artery',
                                              value='BA')
    return full_summary_df


def artery_vein_plot():
    """plotting artery vein vmtk diameter results

    """
    base_dir = os.path.abspath('../')
    output_dir = os.path.join(base_dir, 'derivatives', 'manualwork',
                              'vmtk_artery_vein')

    full_summary_df = load_artery_vein(output_dir)

    sns.set_theme(style="whitegrid", palette="colorblind", font_scale=1.1)

    x = 'vessel'
    hue = 'vessel'
    sns_plot = sns.catplot(
        x=x,
        y='diameter (mm)',
        hue=hue,
        kind='swarm',
        # palette=['#007CC7', '#12232E', '#4DA8DA'],
        height=8,
        aspect=6 / 4,
        s=3.5,
        data=full_summary_df)
    # sns_plot.set_axis_labels('subject number', 'diameter (mm)')
    # matplotlib.rcParams.update({'font.size': 20})
    # sns_plot = sns.relplot(
    #     x=x,
    #     y='diameter',
    #     hue=hue,
    #     style='vessel_type',
    #     kind="scatter",
    #     jitter=True,
    #     height=8,
    #     aspect=6 / 4,
    #     data=full_summary_df)

    figure_path = os.path.join(output_dir,
                               f"SUMMARY-diam_vs_{x}_full_Plot.png")
    plt.savefig(figure_path, dpi=300, bbox_inches='tight')

    x = 'distance'
    hue = 'vessel'
    sns_plot = sns.relplot(
        x=x,
        y='diameter (mm)',
        hue=hue,
        col='vessel_type',
        kind='line',
        # palette=['#007CC7', '#12232E', '#4DA8DA'],
        height=8,
        aspect=6 / 4,
        # s=3.5,
        data=full_summary_df)
    # sns_plot.axes[0,0].set_ylim(0,6)
    figure_path = os.path.join(output_dir,
                               f"SUMMARY-diam_vs_{x}_arteries-veins_Plot.png")
    plt.savefig(figure_path, dpi=300, bbox_inches='tight')
    pass


def sss_lts_rts_plot():
    """plotting artery vein vmtk diameter results

    """
    base_dir = os.path.abspath('../')
    output_dir = os.path.join(base_dir, 'derivatives', 'manualwork',
                              'vmtk_superficial-veins')

    Diameter_SUMMARY_csv = os.path.join(output_dir,
                                        'SUMMARY-diameter_of_veins.csv')
    diameter_df = pd.read_csv(Diameter_SUMMARY_csv)
    print(diameter_df.groupby('subject').describe())
    diameter_df.rename(columns={'diameter': 'diameter (mm)'}, inplace=True)

    sns.set_theme(style="whitegrid", palette="colorblind", font_scale=1.5)

    x = 'vessel'
    hue = 'subject'
    sns_plot = sns.catplot(
        x=x,
        y='diameter (mm)',
        hue=hue,
        # col='subject',
        kind='bar',
        # palette=['#007CC7', '#12232E', '#4DA8DA'],
        height=8,
        # aspect=6 / 4,
        # s=3.5,
        data=diameter_df)
    # sns_plot.set_axis_labels('subject number', 'diameter (mm)')
    # matplotlib.rcParams.update({'font.size': 20})

    figure_path = os.path.join(output_dir,
                               f"SUMMARY-diam_vs_{x}_veins_Plot.png")
    plt.savefig(figure_path, dpi=300, bbox_inches='tight')

    x = 'distance'
    hue = 'vessel'
    sns_plot = sns.relplot(
        x=x,
        y='diameter (mm)',
        hue=hue,
        col='subject',
        kind='line',
        # palette=['#007CC7', '#12232E', '#4DA8DA'],
        height=8,
        aspect=6 / 4,
        # s=3.5,
        data=diameter_df)
    # sns_plot.axes[0,0].set_ylim(0,6)
    figure_path = os.path.join(output_dir,
                               f"SUMMARY-diam_vs_{x}_veins_Plot.png")
    plt.savefig(figure_path, dpi=300, bbox_inches='tight')

    pass


def thrombus_plot():
    """TODO: Docstring for thrombus_plot.

    """
    base_dir = os.path.abspath('../')
    output_dir = os.path.join(base_dir, 'derivatives', 'manualwork',
                              'vmtk_artery_vein')
    full_summary_df = load_artery_vein(output_dir)

    output_dir = os.path.join(base_dir, 'derivatives', 'manualwork',
                              'vmtk_thrombus')

    Diameter_SUMMARY_csv_thromb = os.path.join(output_dir,
                                               'SUMMARY-diameter_of_vein.csv')
    diameter_df_thromb = pd.read_csv(Diameter_SUMMARY_csv_thromb)
    diameter_df_thromb.rename(columns={'diameter': 'diameter (mm)'},
                              inplace=True)
    diameter_df_thromb['distance (mm)'] = (
        diameter_df_thromb['distance'].max() - diameter_df_thromb['distance'])

    print(diameter_df_thromb.head(30))
    print(diameter_df_thromb.tail(30))

    print(
        '-----------------------------------------------------------------------'
    )

    full_summary_df = full_summary_df.loc[(full_summary_df['vessel'] == 'SSS')]
    # full_summary_df = full_summary_df.rolling(3, win_type='hamming').mean()
    diameter_df_thromb = diameter_df_thromb.loc[(
        diameter_df_thromb['vessel'] == 'SSS')]
    diameter_df_thromb = voxaltor(diameter_df_thromb, 'SSS')

    print(diameter_df_thromb.head(30))
    print(diameter_df_thromb.tail(30))

    full_summary_df = pd.concat([diameter_df_thromb, full_summary_df])

    filt_df = full_summary_df.copy().dropna()

    filt_df['subject'] = filt_df['subject'].astype(int).apply(str)
    print(filt_df.head())

    sns.set_theme(style="whitegrid", font_scale=1.5)

    cmap = sns.diverging_palette(240, 10, l=65, center="dark", as_cmap=True)
    # cmap=sns.diverging_palette(220, 20, as_cmap=True)

    x = 'distance (mm)'
    hue = 'diameter (mm)'
    y = 'diameter (mm)'
    sns_plot = relandreg_plot(x, y, hue, diameter_df_thromb)

    # sns_plot = sns.relplot(
    #     x=x,
    #     y='diameter (mm)',
    #     hue=hue,
    #     style='subject',
    #     # col='vessel',
    #     # order=9,
    #     # kind='line',
    #     # ci='sd',
    #     # palette=['#007CC7', '#12232E', '#4DA8DA'],
    #     palette=cmap,
    #     # cmap = cmap,
    #     height=8,
    #     aspect=6 / 4,
    #     # s=3.5,
    #     data=diameter_df_thromb)

    # sns.lineplot( x = 'Date',
    #          y = '7day_rolling_avg',
    #          data = data,
    #          label = 'Rollingavg')

    # sns_plot.axes[0,0].set_ylim(0,6)
    figure_path = os.path.join(output_dir,
                               f"SUMMARY-diam_vs_{x}_veins_Plot_sub-03.png")
    sns_plot.savefig(figure_path, dpi=300, bbox_inches='tight')
    return


def centerline_plotting_old():
    # -----------------------------------------------------------------
    # # Plotting
    #
    fig1 = plt.figure(figsize=(6, 4))
    ax1 = fig1.add_subplot(111, projection='3d')
    ax1.set_xlim3d(-50, 120)
    ax1.set_ylim3d(-50, 120)
    ax1.set_zlim3d(-50, 120)
    ax1.set_xlabel('x')
    ax1.set_ylabel('y')
    ax1.set_zlabel('z')
    ax1.title.set_text('Radius distribution in space')
    im1 = ax1.scatter(points[:, 0], points[:, 1], points[:, 2], c=radius, s=1)
    fig1.colorbar(im1)

    fig1_path = vmtkfolder + "sub-{}_".format(
        num) + side + "-artery-radius_in_space.png"
    plt.savefig(fig1_path)

    for segId in range(numSegments):
        segment = segPointIds[segId]

        fig2 = plt.figure(figsize=(12, 4))

        ax1 = fig2.add_subplot(121, projection='3d')
        ax1.title.set_text(
            'segment {} point ID distribution in space'.format(segId))
        ax1.set_xlim3d(-50, 120)
        ax1.set_ylim3d(-50, 120)
        ax1.set_zlim3d(-50, 120)
        ax1.set_xticklabels([])
        ax1.set_yticklabels([])
        ax1.set_zticklabels([])
        im1 = ax1.scatter(points[segment, 0],
                          points[segment, 1],
                          points[segment, 2],
                          c=segment,
                          s=1)
        fig2.colorbar(im1)

        ax2 = fig2.add_subplot(122)
        ax2.title.set_text(
            'segment {} radius distribution along vessel'.format(segId))
        ax2.set_xlabel('Point ID')
        ax2.set_ylabel('Radius(mm)')
        ax2.scatter(segment, radius[segment], s=1)

        fig2_path = vmtkfolder + "sub-{}_".format(
            num) + side + "-artery_segment-{}.png".format(segId)
        plt.savefig(fig2_path)

    fig3 = plt.figure(figsize=(12, 4))

    ax1 = fig3.add_subplot(121, projection='3d')
    ax2 = fig3.add_subplot(122)

    for segId in range(numSegments):
        segment = segPointIds[segId]
        #ax.plot(range(len(segment)),radius[segment],marker='.',label='segment {}'.format(segId))
        ax1.scatter(points[segment, 0],
                    points[segment, 1],
                    points[segment, 2],
                    s=1,
                    label='segment {}'.format(segId))
        ax2.plot(range(len(segment)),
                 radius[segment],
                 marker='.',
                 label='segment {}'.format(segId))

    ax1.set_xlim3d(-50, 120)
    ax1.set_ylim3d(-50, 120)
    ax1.set_zlim3d(-50, 120)
    ax1.set_xticklabels([])
    ax1.set_yticklabels([])
    ax1.set_zticklabels([])
    ax1.title.set_text('Vessel segment in space')
    ax1.legend()

    ax2.title.set_text('Radius distribution along vessel segments')
    ax2.set_xlabel('Centerline Point Count')
    ax2.set_ylabel('Radius(mm)')
    ax2.legend()

    fig3_path = vmtkfolder + "sub-{}_".format(
        num) + side + "-artery-radius.png"
    plt.savefig(fig3_path)

    #plt.show()

    # Save data to csv
    frames = []
    for segId in range(numSegments):
        segment = segPointIds[segId]
        segData = pd.DataFrame({
            'pointId':
            segment,
            'segId':
            segId * np.ones(len(segment), dtype=int),
            'x':
            points[segment, 0],
            'y':
            points[segment, 1],
            'z':
            points[segment, 2],
            'radius':
            radius[segment]
        })
        frames.append(segData)
    CenterlineData = pd.concat(frames)
    print(CenterlineData)
    outDataframe = vmtkfolder + "sub-{}_".format(
        num) + side + "-artery-clData.csv"
    CenterlineData.to_csv(outDataframe, index=False)
    pass


def plot_from_full():
    """TODO: Docstring for plot_from_full.

    :function: TODO
    :returns: TODO

    """
    sub_num = '02'
    session = 'Postcon'
    scan_type = 'hr'
    in_folder = 'morphometery'
    threshold = '600'

    # scan_type = 'TOF'
    # threshold = '1.0'
    # session = 'Precon'
    # data_dir = os.path.join(datasink_dir, in_folder, 'sub-{}'.format(sub_num),
                            # 'ses-{}'.format(session), 'qutece')
    csv_dir = 'csv_work_diam' + scan_type

    # if not os.path.exists(data_dir):
    #     data_dir = os.path.join(datasink_dir, in_folder,
    #                             'sub-{}'.format(sub_num),
    #                             'ses-{}'.format(session))

    # if not os.path.exists(data_dir):
    #     data_dir = os.path.join(datasink_dir, in_folder,
    #                             'sub-{}'.format(sub_num))
    # if not os.path.exists(data_dir):

    data_dir = os.path.join(datasink_dir, in_folder)

    seg_type = 'named_arteries'
    roi_dir = os.path.join(manualwork_dir, 'segmentations', seg_type)

    if seg_type == 'named_arteries':
        ROI_file_name = os.path.join(
            roi_dir, 'sub-' + sub_num + '_head-vessels-label_1.nii')
        # if scan_type == 'TOF':
        #     ROI_file_name = os.path.join(
        #         roi_dir, 'TOF',
        #         'rrsub-' + sub_num + '_ses-Precon_TOF_angio_corrected' +
        #         '_noise-Segmentation-label.nii')
        # if scan_type == 'T1w':
        #     ROI_file_name = os.path.join(
        #         roi_dir, 'T1w', 'rsub-' + sub_num +
        #         '_ses-Postcon_T1w_corrected' + '_noise-Segmentation-label.nii')

    ROI_file_nii = nib.load(ROI_file_name)
    roi_img = np.array(ROI_file_nii.get_fdata())
    session_pattern = f"*{session}*{scan_type}*-{threshold}_diam*"
    path_pattern = os.path.join(data_dir, session_pattern)
    nii_files = glob.glob(path_pattern)
    print('Selected files are: ')
    print(nii_files)

    summary_df_list = []

    for f in nii_files:
        scan_file_name = f
        scan_file_nii = nib.load(scan_file_name)
        scan_img = np.array(scan_file_nii.get_fdata())
        pth, fname, ext = plotter.split_filename(f)

        if scan_type == 'TOF':
            scan_img[np.abs(scan_img) <= 0.2] = np.nan

        save_dir = os.path.join(datasink_dir, csv_dir,
                                'sub-{}'.format(sub_num),
                                'ses-{}'.format(session))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        summary_df = plotter.roi_extract(scan_img, roi_img, fname, seg_type,
                                         save_dir)

        save_name = (fname + '_SUMMARY_' + 'seg-{}.csv').format(seg_type)
        summary_df.to_csv(os.path.join(save_dir, save_name))
        print('Saved SUMMARY as : ' + os.path.join(save_dir, save_name))

        summary_df_list.append(summary_df)

    plt.close('all')
    return summary_df_list


def main():
    # artery_vein_plot()
    # sss_lts_rts_plot()
    # thrombus_plot()
    plot_from_full()
    pass


if __name__ == "__main__":
    main()
