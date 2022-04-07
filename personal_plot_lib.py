import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Need:
# 1. bar graphs per-subject (SNR, CNRs, ISH)
# 2. bar graphs pre-vs-post
# 2. histograms - per-region
# 3. histograms per-modality for a given region

# ------- From 'plotter.py' -------


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

    possibly irrelevant after plotting_snr_cnr_clean.py

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


# From 'distibution.py' ---------------------

def plot_dis(full_df, t):
    # calc_kde(full_df)
    save_name = 'hist.png'
    if t == 'seaborn':
        sns.set_theme()
        sns_fig = sns.displot(data=full_df,
                              x="intensity",
                              hue="scan_type",
                              kde=True,
                              log_scale=True)
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


# From 'plotting_snr_cnr_clean.py' -------------------

def subjects_plot(filt_df, y_axis):
    """TODO: Docstring for plot.
    :returns: TODO
    """

    filt_df.reset_index(drop=True, inplace=True)
    filt_df = filt_df.sort_values(by=['scan_type'], ascending=True)
    a = filt_df['subject'].nunique() / 7
    print(filt_df['subject'].unique())
    print(filt_df['scan_type'].unique())

    sns.set_theme()
    sns_plot = sns.catplot(
        x="subject",
        y=y_axis,
        hue="scan_type",
        kind="bar",
        height=7,
        aspect=a,
        palette=['darkorange', 'mediumseagreen', 'slateblue'],
        data=filt_df)
    return sns_plot


# From 'CustomNipype.py'


# -------------- Plot Distribution --------------------
class PlotDistribution(BaseInterface):
    input_spec = PlotDistributionInputSpec
    output_spec = PlotDistributionOutputSpec

    def _run_interface(self, runtime):
        in_files = self.inputs.in_files
        plot_xlim_min = self.inputs.plot_xlim_min
        plot_xlim_max = self.inputs.plot_xlim_max
        plot_bins = self.inputs.plot_bins
        in_files = sorted(in_files)
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))

        for nii_filename in in_files:
            nii = nib.load(nii_filename)
            img = np.array(nii.get_fdata())
            vals = np.reshape(img, -1)
            vals[vals == 0] = np.nan
            np.warnings.filterwarnings('ignore')
            sns.distplot(vals,
                         bins=plot_bins,
                         kde=False,
                         norm_hist=True,
                         ax=ax,
                         hist_kws={
                             'histtype': 'step',
                             'linewidth': 1
                         })

        ax.set_title('Distribution')
        ax.set_xlabel('Values')
        ax.set_ylabel('Normalized Voxel Count')
        ax.set_xlim([plot_xlim_min, plot_xlim_max])

        # matplotlib.rcParams.update({'font.size': 16})
        pth, fname, ext = split_filename(in_files[0])
        out_fig_name = os.path.join(fname + '_DistributionPlot.png')
        plt.savefig(out_fig_name, dpi=300, bbox_inches='tight')

        setattr(self, '_out_fig', out_fig_name)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        in_files = self.inputs.in_files
        pth, fname, ext = split_filename(in_files[0])
        out_fig_name = os.path.join(fname + '_DistributionPlot.png')
        outputs['out_fig'] = os.path.abspath(out_fig_name)
        return outputs


# -----------------------------------------------


# -------------- CSV Concatenate --------------------
class CSVConcatenateInputSpec(BaseInterfaceInputSpec):
    in_files = InputMultiObject(exists=True,
                                mandatory=True,
                                desc='list of csvs')


class CSVConcatenateOutputSpec(TraitedSpec):
    out_csv = File(exists=True, desc='concatenated csv')
    out_mean_csv = File(exists=True, desc='mean csv')
    out_std_csv = File(exists=True, desc='std csv')
    out_fig = File(exists=True, disc='timeseries plots')


class CSVConcatenate(BaseInterface):
    input_spec = CSVConcatenateInputSpec
    output_spec = CSVConcatenateOutputSpec

    def _run_interface(self, runtime):
        in_files = self.inputs.in_files
        df_from_each_in_file = (pd.read_csv(in_file) for in_file in in_files)
        concatenated_df = pd.concat(df_from_each_in_file, ignore_index=True)
        concatenated_df.columns = ['ind', 'label', 'mean', 'std', 'N']
        concatenated_df = concatenated_df.astype({'label': 'int'})
        mean_df = concatenated_df.groupby(by='label').mean()
        std_df = concatenated_df.groupby(by='label').std()

        # grab fname info from first file in the input list
        pth, fname, ext = split_filename(in_files[0])
        out_csv_name = os.path.join(fname + '_concatenated.csv')
        concatenated_df.to_csv(out_csv_name)

        out_mean_csv_name = os.path.join(fname + '_mean.csv')
        mean_df.to_csv(out_mean_csv_name)

        out_std_csv_name = os.path.join(fname + '_std.csv')
        std_df.to_csv(out_std_csv_name)

        # plot time series
        unique_label = np.unique(concatenated_df['label'])
        fig = plt.figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        for n in unique_label:
            condition = concatenated_df['label'] == n
            mean = concatenated_df[condition]['mean']
            std = concatenated_df[condition]['std']
            plt.errorbar(range(1,
                               len(mean) + 1),
                         mean,
                         yerr=std,
                         label='label = ' + str(n))
            ax.set_xlabel('Index of runs')
            ax.set_ylabel('S.I.')
            ax.legend()
        out_fig_name = os.path.join(fname + '_timeseries.png')
        plt.savefig(out_fig_name, bbox_inches='tight')

        setattr(self, '_out_csv', out_csv_name)
        setattr(self, '_out_mean_csv', out_mean_csv_name)
        setattr(self, '_out_std_csv', out_std_csv_name)
        setattr(self, '_out_fig', out_fig_name)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        in_files = self.inputs.in_files
        pth, fname, ext = split_filename(in_files[0])
        out_csv_name = os.path.join(fname + '_concatenated.csv')
        out_mean_csv_name = os.path.join(fname + '_mean.csv')
        out_std_csv_name = os.path.join(fname + '_std.csv')
        out_fig_name = os.path.join(fname + '_timeseries.png')
        outputs['out_csv'] = os.path.abspath(out_csv_name)
        outputs['out_mean_csv'] = os.path.abspath(out_mean_csv_name)
        outputs['out_std_csv'] = os.path.abspath(out_std_csv_name)
        outputs['out_fig'] = os.path.abspath(out_fig_name)
        return outputs


# -----------------------------------------------
