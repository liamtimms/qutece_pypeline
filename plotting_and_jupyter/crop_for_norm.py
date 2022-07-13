import glob
import os

import nibabel as nib
import numpy as np

import plotter

base_dir = os.path.abspath("../../../..")
manualwork_dir = os.path.join(base_dir, "derivatives", "manualwork")
roi_dir = os.path.join(manualwork_dir, "for_normalization", "masks")
image_dir = os.path.join(manualwork_dir, "for_normalization", "images")
cropped_dir = os.path.join(manualwork_dir, "for_normalization", "crop")

subject_list = [
    "02", "03", "04", "05", "06", "08", "10", "11", "12", "13", "14", "15"
]


def split_filename(filepath):
    """split a filepath into the full path, filename, and extension
    (works with .nii.gz)"""
    path = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    base, ext = os.path.splitext(filename)
    if ext == ".gz":
        base, ext2 = os.path.splitext(base)
        ext = ext2 + ext
    return path, base, ext


for sub_num in subject_list:
    session_pattern = f"rsub-{sub_num}_ses-Postcon_hr_run-*-preproc.nii"
    path_pattern = os.path.join(image_dir, session_pattern)
    print(path_pattern)
    img_files = sorted(glob.glob(path_pattern))
    print(img_files)
    img_file = img_files[0]
    img_nii = nib.load(img_file)
    scan_img = np.array(img_nii.get_fdata())

    session_pattern = (f"rsub-{sub_num}_ses-Postcon_T1w_hr_mask_Segmentation" +
                       "-label.nii")
    path_pattern = os.path.join(roi_dir, session_pattern)
    roi_files = sorted(glob.glob(path_pattern))
    roi_file_name = roi_files[0]
    roi_nii = nib.load(roi_file_name)
    roi_img = np.array(roi_nii.get_fdata())

    t = "greater"
    r = 0
    crop_img, _ = plotter.roi_cut(scan_img, roi_img, t, r)

    crop_nii = nib.Nifti1Image(crop_img, img_nii.affine, img_nii.header)
    _, base, _ = split_filename(img_file)
    save_name = base + "_crop.nii"
    nib.save(crop_nii, os.path.join(cropped_dir, save_name))
