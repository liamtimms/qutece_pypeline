# import os
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


def filtering(full_df):
    """TODO: Docstring for filtering.

    :arg1: TODO
    :returns: TODO

    """
    df_post = full_df.loc[(full_df['scan_type'] == 'QUTE-CE')
                          & (full_df['session'] == 'Postcon')]
    df_tof = full_df.loc[(full_df['scan_type'] == 'TOF')
                         & (full_df['session'] == 'Precon')]

    subjects = set(list(df_post['subject'])).intersection(
        list(df_tof['subject']))
    filt_df = full_df.loc[(full_df['session'] == 'Postcon') |
                          (full_df['scan_type'] == 'TOF')]
    filt_df = filt_df[filt_df['subject'].isin(subjects)]

    return filt_df


def cleaning(df):
    """TODO: Docstring for cleaning.

    :arg1: TODO
    :returns: TODO

    """
    if 'severe_motion' in df.columns:
        df = df[df['severe_motion'] == 0]
    df.rename(columns={'sub_num': 'subject'}, inplace=True)
    df.rename(columns={'scan_type': 'scan type'}, inplace=True)
    df = df.replace(to_replace="hr", value="QUTE-CE")
    df = df.replace(to_replace="T1w", value="MPRAGE")

    # "Categorical" type lets you set the order when sorted
    df['scan type'] = pd.Categorical(df['scan type'],
                                     ["QUTE-CE", "MPRAGE", "TOF"])
    return df


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


def main():
    # Human
    hr_df, TOF_df, T1w_df, weight_df = load_dfs()
    full_df = concat_and_merge_dfs(hr_df, TOF_df, T1w_df, weight_df)
    clean_df = cleaning(full_df)
    filt_df = filtering(clean_df)
    y_axis_list = ['SNR', 'CNR', 'ISH']
    for y_axis in y_axis_list:
        sns_plot = subjects_plot(filt_df, y_axis)
        save_name = (y_axis + '_per-subject_filtered_T1w_TOF.png')
        sns_plot.savefig(save_name, dpi=300)

    # Phantom
    phantom_df = load_phantom_df()
    filt_df = cleaning_phantom(phantom_df)
    y_axis_list = ['SNR', 'ISH']
    for y_axis in y_axis_list:
        sns_plot = phantom_plot(filt_df, y_axis)
        save_name = (y_axis + '_phantom_T1w_TOF.png')
        sns_plot.savefig(save_name, dpi=300)

    return 0


if __name__ == "__main__":
    main()
