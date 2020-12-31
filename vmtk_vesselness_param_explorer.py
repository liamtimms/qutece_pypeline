# import vmtk
from vmtk import pypes
import os
import nibabel as nib
import glob


def SetAlpha(suppressPlates):
    return 0.000 + 3.0 * pow(suppressPlates / 100.0, 2)


def SetBeta(suppressBlobs):
    return 0.001 + 1.0 * pow((100.0 - suppressBlobs) / 100.0, 2)


def SetGamma(mean):
    return mean * .25


def GetPixelSpacing(nii_filename):
    # minimum spacing is used in vmtkSlicerExtension
    nii = nib.load(nii_filename)
    pixdim = nii.header['pixdim']
    return min(pixdim[1:3])


# ----------------------- Input ------------------------------------------
subject_list = [
    '02', '03', '04', '05', '06', '07', '08', '10', '11', '12', '13', '14', '15'
]
# subject_list = ['05', '07']
# subject_list = ['10']

ute_sub_means = {
    '02': 177,
    '03': 372,
    '04': 378,
    '05': 231,
    '06': 272,
    '07': 174,
    '08': 314,
    '10': 335,
    '11': 326,
    '12': 467,
    '13': 431,
    '14': 441,
    '15': 419
}

tof_sub_means = {
    '02': 59,
    '03': 93,
    '04': 92,
    '05': 66,
    '06': 107,
    '07': 14,
    '08': 89,
    '09': 99,
    '10': 106,
    '11': 62,
    '14': 116
}

TOF_subjects = [
    '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '14'
]

scan_type = 'hr'
# scan_type = 'TOF'
# subject_list = TOF_subjects

for subject_num in subject_list:

    upper_dir = os.path.realpath('../..')
    basefolder = os.path.abspath(os.path.join(upper_dir, 'derivatives'))

    if scan_type == 'hr':
        scanfolder = os.path.join(basefolder, 'datasink', 'preprocessing',
                                  'sub-' + subject_num, 'ses-Postcon',
                                  'qutece')
        infile = '*sub-' + subject_num + '_ses-Postcon_hr_run-*-preproc'

        outfolder = os.path.join(basefolder, 'manualwork',
                                 'vesselness_filtered_3', 'sub-' + subject_num)
        sub_means = ute_sub_means
    elif scan_type == 'TOF':
        scanfolder = os.path.join(basefolder, 'datasink',
                                  'pre_to_post_coregister',
                                  'sub-' + subject_num)
        infile = '*sub-' + subject_num + '_ses-Precon_TOF*angio_corrected'

        outfolder = os.path.join(basefolder, 'manualwork',
                                 'vesselness_filtered_3', 'sub-' + subject_num)
        sub_means = tof_sub_means

    print(outfolder)
    if not os.path.exists(outfolder):
        os.makedirs(outfolder)

    # infile= 'rsub-' + subject_num + '_ses-Postcon_hr_run-01_UTE_desc-preproc'
    # inVesselness = os.path.join(basefolder, scanfolder, infile + '.nii')
    # print(inVesselness)

    inVesselness_pattern = os.path.join(basefolder, scanfolder,
                                        infile + '.nii')
    inVesselness_list = glob.glob(inVesselness_pattern)
    print(inVesselness_list)

    suppressPlates = 25
    suppressBlobs = 40
    alpha = SetAlpha(suppressPlates)
    beta = SetBeta(suppressBlobs)

    gamma = 75
    mean = sub_means[subject_num]
    gamma = SetGamma(mean)
    print(gamma)

    # --------------------- Param Space --------------------------------------
    suppressPlates_list = [25]
    suppressBlobs_list = [40]
    voxelmax_list = [3]
    # gamma_list = [50, 100]
    # params_space = [(vmax, g) for vmax in voxelmax_list for g in gamma_list]
    # params_space =[(suppressBlobs, g) for suppressBlobs in suppressBlobs_list
    #                 for g in gamma_list]
    params_space = [(suppressPlates, suppressBlobs)
                    for suppressPlates in suppressPlates_list
                    for suppressBlobs in suppressBlobs_list]

    for inVesselness in inVesselness_list:
        print(inVesselness)
        pixelspacing = GetPixelSpacing(inVesselness)
        voxelmin = 1
        voxelmax = 3  # default = 5
        sigmamin = pixelspacing * voxelmin
        sigmamax = pixelspacing * voxelmax
        sigmasteps = 5  # default = 5 in vmtkSlicerExtension
        outfile = os.path.basename(inVesselness)
        outfile = os.path.splitext(outfile)[0]

        for params in params_space:
            suppressPlates, suppressBlobs = params
            sigmamax = pixelspacing * voxelmax

            alpha = SetAlpha(suppressPlates)
            beta = SetBeta(suppressBlobs)
            outVesselness = os.path.join(
                outfolder, outfile + '_AutoVess' + '_g=' + str(round(gamma)) +
                '_sb=' + str(suppressBlobs) + '_sp=' + str(suppressPlates) +
                '_sig=' + str(voxelmax) + '_ss=' + str(sigmasteps) + '.nii')
            print(outVesselness)

            cmdVesselness = (
                'vmtkimagecast -type float -ifile {} ' +
                '--pipe vmtkimagevesselenhancement -ofile {} ' +
                '-method frangi -sigmamin {} -sigmamax {} -sigmasteps {} ' +
                '-alpha {} -beta {} -gamma {} -iterations 10').format(
                    inVesselness, outVesselness, sigmamin, sigmamax,
                    sigmasteps, alpha, beta, gamma)

            pypes.PypeRun(cmdVesselness)

        # outVesselness =os.path.join(outfolder, outfile+ '_AutoVess_sato.nii')
        # cmdVesselness = (
        #     'vmtkimagecast -type float -ifile {} ' +
        #     '--pipe vmtkimagevesselenhancement -ofile {} ' +
        #     '-method sato -sigmamin {} -sigmamax {} -sigmasteps {}').format(
        #         inVesselness, outVesselness, sigmamin, sigmamax, sigmasteps)

        # pypes.PypeRun(cmdVesselness)

# TOF brain data
# 02:75%,74
# 02:75%,72
# 03:75%,121
# 04:75%,117
# 05:75%,82
# 06:75%,140
# 07:75%,17
# 08:75%,110
# 09:75%,128
# 10:75%,134
# 11:75%,79
# 14:75%,148

# 02:mean,59
# 02:mean,58
# 03:mean,93
# 04:mean,92
# 05:mean,66
# 06:mean,107
# 07:mean,14
# 08:mean,89
# 09:mean,99
# 10:mean,106
# 11:mean,62
# 14:mean,116
