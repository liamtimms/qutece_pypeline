import pandas as pd
import seaborn as sns


# Human ---------------------------------------------------
def load_dfs():
    hr_csv_fname = 'FULL_SUMMARY_seg-CNR_withmotion_hr.csv'
    hr_df = pd.read_csv(hr_csv_fname)
    TOF_csv_fname = 'FULL_SUMMARY_seg-CNR_withmotion_TOF.csv'
    TOF_df = pd.read_csv(TOF_csv_fname)
    TOF_df = TOF_df.drop(columns=['index_x', 'index_y', 'index'])
    T1w_csv_fname = 'FULL_SUMMARY_seg-CNR_withmotion_T1w.csv'
    T1w_df = pd.read_csv(T1w_csv_fname)
    T1w_df = T1w_df.drop(columns=['level_0', 'index_x', 'index_y', 'index'])
    weight_df_fname = 'subject_weight.csv'
    weight_df = pd.read_csv(weight_df_fname)
    return hr_df, TOF_df, T1w_df, weight_df


def concat_and_merge_dfs(hr_df, TOF_df, T1w_df, weight_df):
    """TODO: Docstring for merge_dfs.

    :arg1: TODO
    :returns: TODO

    """
    df = pd.concat([hr_df, TOF_df])
    df = df.drop(columns=['level_0'])
    T1w_UTE_TOF_df = pd.concat([T1w_df, df])
    out_df = pd.merge(
        T1w_UTE_TOF_df,
        weight_df,
        how="inner",
        on='sub_num',
        left_index=False,
        right_index=False,
        sort=True,
        suffixes=("_x", "_y"),
        copy=True,
        indicator=False,
        validate=None,
    )
    return out_df


def post_pre_cnr(df_post, df_pre, scan_type):
    """TODO: Docstring for post_pre_cnr.
    :returns: TODO

    """
    cnr_series = df_post.loc[(df_post['scan_type'] == scan_type)].groupby(
        ['subject'])['SNR'].mean().round(3) - df_pre.loc[
            (df_pre['scan_type'] == scan_type)].groupby(
                ['subject'])['SNR'].mean().round(3)

    cnr_df = cnr_series.to_frame()
    cnr_df['scan_type'] = scan_type
    cnr_df.rename(columns={'SNR': 'post-pre CNR'}, inplace=True)
    return cnr_df


def filtering(full_df):
    """TODO: Docstring for filtering.

    :arg1: TODO
    :returns: TODO

    """
    df_tof = full_df.loc[(full_df['scan_type'] == 'TOF')
                         & (full_df['session'] == 'Precon')]

    df_post = full_df.loc[(full_df['session'] == 'Postcon')]
    df_post_qutece = full_df.loc[(full_df['session'] == 'Postcon')
                                 & (full_df['scan_type'] == 'QUTE-CE')]
    df_pre = full_df.loc[(full_df['session'] == 'Precon')]

    cnr_df = pd.concat([
        post_pre_cnr(df_post, df_pre, 'QUTE-CE'),
        post_pre_cnr(df_post, df_pre, 'MPRAGE')
    ])

    filt_df = full_df.loc[(full_df['session'] == 'Postcon') |
                          (full_df['scan_type'] == 'TOF')]
    filt_df = pd.merge(
        filt_df,
        cnr_df,
        how="left",
        on=['subject', 'scan_type'],
        left_index=False,
        right_index=False,
        sort=True,
        suffixes=("_x", "_y"),
        copy=True,
        indicator=False,
        validate=None,
    )

    filt_df['scan_type'] = pd.Categorical(filt_df['scan_type'],
                                          ["QUTE-CE", "MPRAGE", "TOF"])
    # y_axis = 'post-pre CNR'
    # stats = filt_df.groupby(['scan_type',
    #                          'session'])[y_axis].describe().round(3)

    # we only want to graph subjects with both useful QUTE-CE and TOF
    subjects = set(list(df_post_qutece['subject'])).intersection(
        list(df_tof['subject']))
    subjects = list(df_post_qutece['subject'])

    subjects = [s for s in subjects if s != 10]
    filt_df = filt_df[filt_df['subject'].isin(subjects)]
    return filt_df


def cleaning(df):
    """TODO: Docstring for cleaning.

    :arg1: TODO
    :returns: TODO

    """
    df = df[df['severe_motion'] == 0]
    df.rename(columns={'sub_num': 'subject'}, inplace=True)
    df.rename(columns={'CNR': 'blood-tissue CNR'}, inplace=True)
    df = df.replace(to_replace="hr", value="QUTE-CE")
    df = df.replace(to_replace="T1w", value="MPRAGE")

    # "Categorical" type lets you set the order when sorted
    df['scan_type'] = pd.Categorical(df['scan_type'],
                                     ["QUTE-CE", "MPRAGE", "TOF"])
    return df


def subjects_plot(filt_df, y_axis):
    """TODO: Docstring for plot.
    :returns: TODO
    """

    filt_df.reset_index(drop=True, inplace=True)
    filt_df = filt_df.sort_values(by=['scan_type'], ascending=True)
    a = filt_df['subject'].nunique() / 7

    # print()
    # print(f"description of {y_axis}")
    # stats = filt_df.groupby(['scan_type',
    #                          'session'])[y_axis].describe().round(3)
    # print(stats)

    if filt_df['scan_type'].nunique() == 3:
        p = ['darkorange', 'mediumseagreen', 'slateblue']
    elif filt_df['scan_type'].nunique() == 2:
        p = ['darkorange', 'mediumseagreen']

    sns.set_theme(font_scale=1.5)
    sns_plot = sns.catplot(x="subject",
                           y=y_axis,
                           hue="scan_type",
                           kind="bar",
                           height=7,
                           aspect=a,
                           palette=p,
                           data=filt_df)

    return sns_plot


def relative_plot(filt_df, y_axis):
    filt_df.reset_index(drop=True, inplace=True)
    filt_df = filt_df.sort_values(by=['scan_type'], ascending=True)
    a = filt_df['subject'].nunique() / 7
    if filt_df['scan_type'].nunique() == 3:
        p = ['darkorange', 'mediumseagreen', 'slateblue']
    elif filt_df['scan_type'].nunique() == 2:
        p = ['darkorange', 'mediumseagreen']
    sns.set_theme(font_scale=1.5)

    sns_plot = sns.relplot(x="SNR",
                           y=y_axis,
                           hue="scan_type",
                           kind="scatter",
                           height=7,
                           aspect=a,
                           palette=p,
                           data=filt_df)
    return sns_plot


# Phantoms ------------------------------------------------
def load_phantom_df():
    """TODO: Docstring for load_phantom_dfs.

    :arg1: TODO
    :returns: TODO

    """
    csv_fname = 'QUTE-CE_T1w_Blood.csv'
    phantom_df = pd.read_csv(csv_fname)
    return phantom_df


def cleaning_phantom(phantom_df):
    """TODO: Docstring for load_phantom.

    :arg1: TODO
    :returns: TODO

    """

    filt_df = phantom_df.loc[~(phantom_df['Segment'] == 'Air')]
    filt_df = filt_df.replace(to_replace="UTE", value="QUTE-CE")
    filt_df = filt_df.replace(to_replace="T1w", value="MPRAGE")
    filt_df = filt_df.replace(to_replace="CE_Blood", value="CE Blood")
    filt_df['scan_type'] = pd.Categorical(filt_df['scan_type'],
                                          ["QUTE-CE", "MPRAGE"])

    filt_df.rename(columns={'Segment': 'ROI'}, inplace=True)
    return filt_df


def phantom_plot(filt_df, y_axis):
    """TODO: Docstring for phantom_plot.

    :arg1: TODO
    :returns: TODO

    """
    filt_df = filt_df.reset_index()
    # a = filt_df['sub_num'].nunique() / 5
    filt_df = filt_df.sort_values(by=['scan_type'], ascending=True)
    sns_plot = sns.catplot(
        x="ROI",
        y=y_axis,
        hue="scan_type",
        kind="bar",
        height=7,
        # aspect=a,
        palette=['darkorange', 'mediumseagreen'],
        data=filt_df)

    return sns_plot


def human_plotting():
    """TODO: Docstring for human_plotting.

    :arg1: TODO
    :returns: TODO

    """
    # Human
    hr_df, TOF_df, T1w_df, weight_df = load_dfs()
    full_df = concat_and_merge_dfs(hr_df, TOF_df, T1w_df, weight_df)
    clean_df = cleaning(full_df)
    # SNR_stats = clean_df.groupby(['scan_type',
    #                               'session'])['SNR'].describe().round(3)

    filt_df = filtering(clean_df)
    y_axis_list = ['SNR', 'blood-tissue CNR', 'post-pre CNR', 'ISH']
    # print(filt_df.head())

    for y_axis in y_axis_list:
        sns_plot = subjects_plot(filt_df, y_axis)
        save_name = (y_axis + '_per-subject_filtered_T1w_TOF.png')
        save_name = save_name.replace(" ", "_")
        sns_plot.savefig(save_name, dpi=300)

        sns_plot = relative_plot(filt_df, y_axis)
        save_name = (y_axis + '_vs_SNR.png')
        save_name = save_name.replace(" ", "_")
        sns_plot.savefig(save_name, dpi=300)

    hr_csv_fname = 'FILT_FULL_SUMMARY_seg-CNR_withmotion.csv'
    filt_df.to_csv(hr_csv_fname, index=False)
    subject_factors(filt_df)

    return clean_df


def subject_factors(filt_df):
    """TODO: Docstring for grouper.
    :returns: TODO

    """
    groups = ['subject', 'scan_type']
    values = ['SNR', 'blood-tissue CNR', 'post-pre CNR', 'ISH']

    full_factor_df = pd.DataFrame()

    for v in values:
        df = filt_df.groupby(groups)[v].describe().round(3).reset_index()
        print(df)
        factor_df = factor(df)
        factor_df['Metric'] = v
        print(factor_df.head())
        full_factor_df = pd.concat([full_factor_df, factor_df])

    facor_csv_fname = 'factors.csv'
    full_factor_df.to_csv(facor_csv_fname, index=False)
    stats = full_factor_df.groupby(['Metric']).describe()
    stats.to_csv('factor_stats.csv')
    return


def factor(df):
    factor_df = pd.DataFrame()
    for s in df['subject'].unique():
        n_df = pd.DataFrame()
        s_df = df.loc[(df['subject'] == s)]
        tof_mean = s_df.loc[(s_df['scan_type'] == 'TOF')]['mean'].to_numpy()
        qutece_mean = s_df.loc[(
            s_df['scan_type'] == 'QUTE-CE')]['mean'].to_numpy()
        mprage_mean = s_df.loc[(
            s_df['scan_type'] == 'MPRAGE')]['mean'].to_numpy()
        n_df['QUTE-CE/TOF'] = qutece_mean / tof_mean
        n_df['QUTE-CE/MPRAGE'] = qutece_mean / mprage_mean
        n_df['subject'] = s
        factor_df = pd.concat([factor_df, n_df])
    return factor_df


def phantom_plotting():
    """TODO: Docstring for phantom_plotting.

    :arg1: TODO
    :returns: TODO

    """
    # Phantom
    phantom_df = load_phantom_df()
    filt_df = cleaning_phantom(phantom_df)
    y_axis_list = ['SNR', 'ISH']
    for y_axis in y_axis_list:
        sns_plot = phantom_plot(filt_df, y_axis)
        save_name = (y_axis + '_phantom_T1w_TOF.png')
        sns_plot.savefig(save_name, dpi=300)

    return filt_df


def main():
    human_plotting()
    # phantom_plotting()

    return 0


if __name__ == "__main__":
    main()
