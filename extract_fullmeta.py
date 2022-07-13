import json
import os

import dicom_parser as dcmp

base_dir = os.path.abspath("../../..")
# dcm_dir = os.path.join(base_dir, "DCM")
# nii_dir = os.path.join(base_dir, "DCM2NII_NEU")


def add_private_tag_keys(header_df):
    """TODO: Docstring for add_private_tag_keys.

    :arg1: TODO
    :returns: TODO

    """
    private_tags = {
        ("0019", "1017"): "SliceResolution",
        ("0051", "100a"): "TimeOfAcquisition",
        ("0051", "100c"): "Field of View",
        ("0051", "100e"): "Slice Orientation",
        ("0051", "1017"): "Interpolated Slice Thickness",
        ("0051", "1019"): "Scan options",
    }

    for t in private_tags:
        header_df.loc[header_df["Tag"] == t, "Keyword"] = private_tags[t]

    return header_df


def get_scan_series(dir):
    """TODO: Docstring for load_scan_series.

    :arg1: TODO
    :returns: TODO

    """
    dcm_series = dcmp.Series(dir)
    return dcm_series


def get_dicom_dirs(exp_num):
    """TODO: Docstring for get_dicom_dirs.

    :arg1: TODO
    :returns: TODO

    """
    exp_dir = os.path.join(dcm_dir, f"E_{exp_num}")
    dirs = []
    for f in os.listdir(exp_dir):
        full_path = os.path.join(exp_dir, f)
        if os.path.isdir(full_path):
            dirs.append(full_path)
    return dirs


def save_pretty_json(dc, save_path):
    with open(save_path, mode="w") as f:
        json.dump(dc, f, default=str)

    command = f"prettier --write {save_path}"
    os.system(command)
    return


def save_headers(exp_num, header_df, header_dc, header_csa):
    """TODO: Docstring for save_headers.

    :arg1: TODO
    :returns: TODO

    """

    save_dir = os.path.join(nii_dir, f"Experiment_{exp_num}", "headers")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # fstring = f"Exp-{exp_num}_scan-%2s_%d"

    s = (header_df.loc[header_df["Keyword"] == "SeriesNumber"]["Value"].astype(
        str).values[0]).zfill(2)
    d = (header_df.loc[header_df["Keyword"] == "SeriesDescription"]
         ["Value"].astype(str).values[0]).replace(" ", "_")
    fstring = f"Exp-{exp_num}_scan-{s}_{d}"
    print()
    print(f"Saving headers for {fstring}")
    save_path = os.path.join(save_dir, f"{fstring}_header-df.pickle")
    header_df.to_pickle(save_path)

    save_path = os.path.join(save_dir, f"{fstring}_header-dc.json")
    save_pretty_json(header_dc, save_path)

    save_path = os.path.join(save_dir, f"{fstring}_header-csa.json")
    save_pretty_json(header_csa, save_path)
    return 0


def get_first_image_headers(dcm_series):
    """TODO: Docstring for get_first_image_headers.

    :arg1: TODO
    :returns: TODO

    """
    header_df = dcm_series[0].header.to_dataframe().reset_index()
    header_dc = dcm_series[0].header.to_dict()
    header_csa = dcm_series[0].header.get("CSASeriesHeaderInfo")
    return header_df, header_dc, header_csa


def run_exp(exp_num):
    """TODO: Docstring for run_exp.

    :arg1: TODO
    :returns: TODO

    """
    dirs = get_dicom_dirs(exp_num)
    print(f"found dicom directories: {dirs}")
    for dir in dirs:
        dcm_series = get_scan_series(dir)
        header_df, header_dc, header_csa = get_first_image_headers(dcm_series)
        header_df = add_private_tag_keys(header_df)
        print(header_df.head())
        save_headers(exp_num, header_df, header_dc, header_csa)
    pass


def main():
    # exp_num = "22"
    subs = ["22", "20", "18"]
    # exps = ["22"]
    for exp_num in exps:
        run_exp(exp_num)


if __name__ == "__main__":
    main()
