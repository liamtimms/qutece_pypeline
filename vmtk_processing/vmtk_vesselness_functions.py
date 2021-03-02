import os
# import glob
import nibabel as nib
from vmtk import pypes


def SetAlpha(suppressPlates):
    return 0.000 + 3.0 * pow(suppressPlates / 100.0, 2)


def SetBeta(suppressBlobs):
    return 0.001 + 1.0 * pow((100.0 - suppressBlobs) / 100.0, 2)


def SetGamma(mean):
    return mean * .75


def GetPixelSpacing(nii_filename):
    # minimum spacing is used in vmtkSlicerExtension
    nii = nib.load(nii_filename)
    pixdim = nii.header['pixdim']
    return min(pixdim[1:3])


def vmtk_vesselness(image_file_name,
                    outfolder,
                    mean,
                    suppressBlobs=25,
                    suppressPlates=25,
                    voxelmax=5,
                    sigmasteps=5):

    alpha = SetAlpha(suppressPlates)
    beta = SetBeta(suppressBlobs)
    gamma = SetGamma(mean)
    pixelspacing = GetPixelSpacing(image_file_name)
    voxelmin = 1
    sigmamin = pixelspacing * voxelmin
    sigmamax = pixelspacing * voxelmax

    outfile = os.path.basename(image_file_name)
    outfile = os.path.splitext(outfile)[0]
    save_name = os.path.join(
        outfolder, outfile + '_Vess' + '_g=' + str(gamma) + '_sb=' +
        str(suppressBlobs) + '_sp=' + str(suppressPlates) + '_sig=' +
        str(voxelmax) + '_ss=' + str(sigmasteps) + '.nii')

    cmdVesselness = (
        'vmtkimagecast -type float -ifile {} ' +
        '--pipe vmtkimagevesselenhancement -ofile {} ' +
        '-method frangi -sigmamin {} -sigmamax {} -sigmasteps {} ' +
        '-alpha {} -beta {} -gamma {} -iterations 10').format(
            image_file_name, save_name, sigmamin, sigmamax, sigmasteps, alpha,
            beta, gamma)

    pypes.PypeRun(cmdVesselness)

    return save_name
