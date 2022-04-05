import os
import glob
import nibabel as nib
import nilearn as nil
import numpy as np
from nipype.utils.filemanip import split_filename
from skimage.morphology import skeletonize_3d

base_dir = os.path.abspath('../..')
datasink_dir = os.path.join(base_dir, 'derivatives', 'datasink')
manualwork_dir = os.path.join(base_dir, 'derivatives', 'manualwork')


def skeletonize_nii(scan_nii, threshold):

    # Use target affine to define resolution:
    # https://nilearn.github.io/manipulating_images/manipulating_images.html
    target_affine = np.diag((0.25, 0.25, 0.25))
    target_affine = np.diag((0.5, 0.5, 0.5))
    resampled_nii = nil.image.resample_img(scan_nii,
                                           target_affine=target_affine,
                                           target_shape=None,
                                           interpolation='nearest',
                                           copy=True,
                                           order='F',
                                           clip=True,
                                           fill_value=0,
                                           force_resample=False)

    # resampled_nii=nib.resample_to_output(scan_nii, voxel_sizes=0.25, order=3)

    scan_img = np.array(resampled_nii.get_fdata())
    bin_img = (scan_img >= threshold).astype(int)
    # bin_img = 1.0 * (scan_img > threshold)

    skele_img = skeletonize_3d(bin_img)

    skele_nii = nib.Nifti1Image(skele_img, resampled_nii.affine,
                                resampled_nii.header)

    return skele_nii


def skeles(in_folder, sub_num, session, scan_type):
    skele_dir = 'skeletonized'

    # data_dir = os.path.join(datasink_dir, in_folder, 'sub-{}'.format(sub_num),
    #                         'ses-{}'.format(session), 'qutece')
    # if not os.path.exists(data_dir):
    #     data_dir = os.path.join(datasink_dir, in_folder,
    #                             'sub-{}'.format(sub_num),
    #                             'ses-{}'.format(session))
    # if not os.path.exists(data_dir):
    #     data_dir = os.path.join(datasink_dir, in_folder,
    #                             'sub-{}'.format(sub_num))

    # session_pattern = '*' + session + '*' + scan_type + '*'
    # path_pattern = os.path.join(data_dir, session_pattern)
    # nii_files = glob.glob(path_pattern)
    # print('Selected files are: ')
    # print(nii_files)

    data_dir = os.path.join(manualwork_dir, in_folder, 'sub-{}'.format(sub_num),
                            'ses-{}'.format(session), 'qutece')
    if not os.path.exists(data_dir):
        data_dir = os.path.join(manualwork_dir, in_folder,
                                'sub-{}'.format(sub_num),
                                'ses-{}'.format(session))
    if not os.path.exists(data_dir):
        data_dir = os.path.join(manualwork_dir, in_folder,
                                'sub-{}'.format(sub_num))

    session_pattern = '*' + session + '*' + scan_type + '*'
    vesselness_pattern = '*' + 'sb=25_sp=10' + '*'
    path_pattern = os.path.join(data_dir, session_pattern + vesselness_pattern)
    nii_files = glob.glob(path_pattern)
    print('Selected files are: ')
    print(nii_files)

    for f in nii_files:
        scan_file_name = f
        scan_nii = nib.load(scan_file_name)
        pth, fname, ext = split_filename(f)

        save_dir = os.path.join(datasink_dir, skele_dir,
                                'sub-{}'.format(sub_num))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        threshold = 0.15
        skele_nii = skeletonize_nii(scan_nii, threshold)

        save_name = (fname + '_skeleton-' + str(threshold) + '.nii')
        nib.save(skele_nii, os.path.join(save_dir, save_name))

    return


def main():
    # in_folder = 'preprocessing'
    in_folder = 'vesselness_filtered_2'
    # in_folder = 'intrasession_coregister'
    sub_num = '14'
    session = 'Precon'
    scan_type = 'TOF'
    skeles(in_folder, sub_num, session, scan_type)

    # subject_list = [
    #   '02', '03', '04', '05', '06', '07', '08', '10', '11', '12', '13', '14',
    #     '15'
    # ]

    return


if __name__ == "__main__":
    main()
