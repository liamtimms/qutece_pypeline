import vmtk
from vmtk import pypes
import os
import nibabel as nib


def SetAlpha(suppressPlates):
    return 0.000 + 3.0 * pow(suppressPlates/100.0,2)

def SetBeta(suppressBlobs):
    return 0.001 + 1.0 * pow((100.0-suppressBlobs)/100.0,2)

def GetPixelSpacing(nii_filename):
    # minimum spacing is used in vmtkSlicerExtension
    nii = nib.load(nii_filename)
    pixdim = nii.header['pixdim']
    return min(pixdim[1:3])

# ----------------------- Input ------------------------------------------
subject_num= '8'
infile = 'sub-8_ses-Post_SPIRiT_un_DIS3D_run-01_UTE'

basefolder = '/media/tianyi/data/Analysis/DCM2BIDS_Kidney/'
scanfolder = 'sub-' + subject_num + '/ses-Post/qutece/'
outfolder = 'derivatives/manual-work/vesselness-filtered/sub-' + subject_num + '/'

inVesselness = basefolder + scanfolder + infile + '.nii'

pixelspacing = GetPixelSpacing(inVesselness)
voxelmin = 1
voxelmax = 4
sigmamin = pixelspacing * voxelmin
sigmamax = pixelspacing * voxelmax
sigmasteps = 5      # default = 5 in vmtkSlicerExtension

suppressPlates = 25
suppressBlobs = 25
alpha = SetAlpha(suppressPlates)
beta = SetBeta(suppressBlobs)
gamma = 300

# --------------------- Param Space --------------------------------------
voxelmax_list = [4]
gamma_list = [50, 75, 100, 125, 150]
params_space = [(vmax, g) for vmax in voxelmax_list for g in gamma_list]

for params in params_space:
    voxelmax, gamma = params
    sigmamax = pixelspacing * voxelmax

    outVesselness = basefolder + outfolder + infile + '_AutoVesselness' + '_vmax=' + str(voxelmax) + '_gamma=' + str(gamma) + '.nii'

    cmdVesselness = 'vmtkimagecast -type float -ifile {} --pipe vmtkimagevesselenhancement -ofile {} -method frangi -sigmamin {} -sigmamax {} -sigmasteps {} -alpha {} -beta {} -gamma {}'.format(inVesselness,outVesselness,sigmamin,sigmamax,sigmasteps,alpha,beta,gamma)
    pypes.PypeRun(cmdVesselness)




