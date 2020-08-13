# import vmtk
from vmtk import pypes
import os
import nibabel as nib


def SetAlpha(suppressPlates):
    return 0.000 + 3.0 * pow(suppressPlates / 100.0, 2)


def SetBeta(suppressBlobs):
    return 0.001 + 1.0 * pow((100.0 - suppressBlobs) / 100.0, 2)


def GetPixelSpacing(nii_filename):
    # minimum spacing is used in vmtkSlicerExtension
    nii = nib.load(nii_filename)
    pixdim = nii.header['pixdim']
    return min(pixdim[1:3])


# ----------------------- Input ------------------------------------------
subject_list = ['02', '03', '04', '06', '08', '11', '12', '13', '14', '15']

for subject_num in subject_list:

    upper_dir = os.path.realpath('../..')
    basefolder = os.path.abspath(os.path.join(upper_dir, 'derivatives'))

    scanfolder = os.path.join(basefolder, 'datasink', 'preprocessing',
                              'sub-' + subject_num, 'ses-Postcon', 'qutece')

    outfolder = os.path.join(basefolder, 'manualwork', 'vesselness_filtered',
                             'sub-' + subject_num)

    print(outfolder)
    if not os.path.exists(outfolder):
        os.makedirs(outfolder)

    infile = 'rsub-' + subject_num + '_ses-Postcon_hr_run-01_UTE_desc-preproc'
    inVesselness = os.path.join(basefolder, scanfolder, infile + '.nii')
    print(inVesselness)

    pixelspacing = GetPixelSpacing(inVesselness)
    voxelmin = 1
    voxelmax = 4
    sigmamin = pixelspacing * voxelmin
    sigmamax = pixelspacing * voxelmax
    sigmasteps = 5  # default = 5 in vmtkSlicerExtension

    suppressPlates = 25
    suppressBlobs = 25
    alpha = SetAlpha(suppressPlates)
    beta = SetBeta(suppressBlobs)
    gamma = 300

    # --------------------- Param Space --------------------------------------
    suppressBlobs_list = [5, 25, 100]
    gamma_list = [50, 100, 200]
    # params_space = [(vmax, g) for vmax in voxelmax_list for g in gamma_list]
    params_space = [(suppressBlobs, g) for suppressBlobs in suppressBlobs_list
                    for g in gamma_list]

    for params in params_space:
        suppressBlobs, gamma = params
        sigmamax = pixelspacing * voxelmax

        beta = SetBeta(suppressBlobs)
        outVesselness = os.path.join(
            outfolder, infile + '_AutoVesselness' + '_sblobs=' +
            str(suppressBlobs) + '_gamma=' + str(gamma) + '.nii')
        print(outVesselness)

        cmdVesselness = (
            'vmtkimagecast -type float -ifile {} --pipe vmtkimagevesselenhancement -ofile {} '
            +
            '-method frangi -sigmamin {} -sigmamax {} -sigmasteps {} -alpha {} -beta {} -gamma {}'
        ).format(inVesselness, outVesselness, sigmamin, sigmamax, sigmasteps,
                 alpha, beta, gamma)

        pypes.PypeRun(cmdVesselness)
