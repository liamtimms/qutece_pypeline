# Need to optimize parameters for atlas fit,
# may not be a Pipeline due to data size issues

# -----------------Imports-------------------------------
import os

import CustomNiPype as cnp
import nibabel as nib
import nilearn as nil
import nipype.interfaces.io as nio
import nipype.interfaces.spm as spm
# import nipype.interfaces.freesurfer as fs
# import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as utl
import nipype.pipeline.engine as eng

# -------------------------------------------------------

# -----------------Inputs--------------------------------
# Define subject list, session list and relevent file types
upper_dir = os.path.realpath('../..')
working_dir = os.path.abspath('/mnt/hgfs/VMshare/WorkingBIDS/')

output_dir = os.path.join(working_dir, 'derivatives/')
temp_dir = os.path.join(output_dir, 'datasink/')
subject_list = ['02', '03', '05', '06', '08', '10', '11']
subject_list = ['03', '11']

# Atlas Label
atlas_file = os.path.abspath('/opt/spm12/tpm/mask_ICV.nii/')

# Precon T1w brain-label Ju made

# Precon T1w scan from which she made the label

# precon T1w brain label cropped out from Ju's manual work and now normalized
scanfolder = 'ManualBrainCrop'
session = 'Precon'
filestart = 'sub-{subject_id}_ses-' + session + '_'
subdirectory = os.path.join(temp_dir, scanfolder)
precon_T1w_brain_label_files = os.path.join(
    subdirectory, 'rr' + filestart + 'T1w_brain-label.nii')

# precon T1w brain coregistered to postcon
scanfolder = 'IntersessionCoregister_preconScans'
session = 'Precon'
filestart = 'sub-{subject_id}_ses-' + session + '_'
subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}')
precon_T1w_file = os.path.join(subdirectory, 'rr' + filestart + 'T1w.nii')

templates = {
    'atlas': atlas_file,
    'T1w_precon_brain_label': precon_T1w_brain_label_files,
    'T1w_precon': precon_T1w_file
}

# Infosource - a function free node to iterate over the list of subject names
infosource = eng.Node(utl.IdentityInterface(fields=['subject_id']),
                      name="infosource")
infosource.iterables = [('subject_id', subject_list)]

# Selectfiles to provide specific scans with in a subject to other functions
selectfiles = eng.Node(nio.SelectFiles(templates,
                                       base_directory=working_dir,
                                       sort_filelist=True,
                                       raise_on_empty=True),
                       name="SelectFiles")
# -------------------------------------------------------

# ------------------DifferenceFunction-------------------
# TODO: I really just need a very general nifti image subtractor
# TODO: address the fact that files may have different resolutions/matrix sizes


def scan_subtract(file1, file2):
    nii1 = nib.load(file1)
    nii2 = nib.load(file2)

    nii2 = nil.resample_to_img(nii2, nii1)

    img1 = nii1.get_fdata()
    img2 = nii2.get_fdata()

    diff_img = img2 - img1
    diff_nii = nib.Nifti1Image(diff_img, nii1.affine, nii1.header)
    return diff_img, diff_nii


difference = eng.Node(utl.Function(), name='difference')
# -------------------------------------------------------

# -----------------------NormalizeNode-------------------
normalize = eng.Node(spm.Normalize12(), name='normalize')
normalize.inputs.write_interp = 7
normalize.inputs.write_voxel_sizes = [1, 1, 1]
normalize.inputs.sampling_distance = 2

def factorlist1(f):
    matrix = [1, 1, 1, 1, 1]
    for i in matrix.size():
        factors = matrix(i) * f

base_params=[0, 0.0001, 0.5, 0.005, 0.02]
warp_list = []
warp_list.append(base_params)
for f in (.01, .1, 10, 100):
    factors = [1, 1 * f, 1, 1, 1]
    factors = [1, 1, 1 * f, 1, 1]
    factors = [1, 1, 1, 1 * f, 1]
    factors = [1, 1, 1, 1, 1 * f]

    factors = [1, 1 * f, 1 * f, 1, 1]
    factors = [1, 1, 1 * f, 1 * f, 1]
    factors = [1, 1, 1, 1 * f, 1 * f]
    factors = [1, 1 * f, 1, 1, 1 * f]

    factors = [1, 1 * f, 1 * f, 1 * f, 1]
    factors = [1, 1, 1 * f, 1 * f, 1 * f]
    factors = [1, 1 * f, 1, 1 * f, 1 * f]
    factors = [1, 1 * f, 1 * f, 1, 1 * f]

    factors = [1, 1 * f, 1 * f, 1 * f, 1 * f]

warp_list.append([0, 0.0001 * 100, 0.5, 0.005, 0.02])
warp_list.append([0, 0.0001, 0.5 * 100, 0.005, 0.02])
warp_list.append([0, 0.0001, 0.5, 0.005 * 100, 0.02])
warp_list.append([0, 0.0001, 0.5, 0.005, 0.02 * 100])
warp_list.append([0, 0.0001 / 100, 0.5, 0.005, 0.02])
warp_list.append([0, 0.0001, 0.5 / 100, 0.005, 0.02])
warp_list.append([0, 0.0001, 0.5, 0.005 / 100, 0.02])
warp_list.append([0, 0.0001, 0.5, 0.005, 0.02 / 100])
warp_list.append([1, 0.0001, 0.5, 0.005, 0.02])
warp_list.append([0, 0.0001 * 1000, 0.5, 0.005, 0.02])
warp_list.append([0, 0.0001, 0.5, 0.005, 0.02 / 1000])

warp_list.append([0, 0.0001 * 100, 0.5 * 100, 0.005, 0.02])
warp_list.append([0, 0.0001, 0.5 * 100, 0.005 * 100, 0.02])
warp_list.append([0, 0.0001, 0.5, 0.005 * 100, 0.02 * 100])
warp_list.append([0, 0.0001 * 100, 0.5, 0.005, 0.02 * 100])

warp_list.append([0, 0.0001 * 1000, 0.5, 0.005, 0.02 * 1000])
warp_list.append([0, 0.0001 * 1000, 0.5, 0.005, 0.02 * 100])
warp_list.append([0, 0.0001 * 100, 0.5, 0.005, 0.02 * 1000])

normalize.iterables = ('warping_regularization', warp_list)

# -------------------------------------------------------

# -----------------------Merge---------------------------
merge = eng.Node(utl.Merge(2), name='merge')
merge.ravel_inputs = True
# -------------------------------------------------------

# ------------------------Output-------------------------
# Datasink - creates output folder for important outputs
datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                 container=temp_dir),
                    name="datasink")
# Use the following DataSink output substitutions
substitutions = [('_subject_id_', 'sub-')]

subjFolders = [('sub-%s' % (sub), 'sub-%s' % (sub)) for sub in subject_list]
substitutions.extend(subjFolders)
datasink.inputs.substitutions = substitutions
# datasink.inputs.regexp_substitutions = [('_coreg_to_postcon.','')]
# -------------------------------------------------------

# -----------------NormalizationWorkflow-----------------
task = 'AtlasOptimizing'
atlas_opt_wf = eng.Workflow(name=task)
atlas_opt_wf.base_dir = working_dir + '/workflow'

atlas_opt_wf.connect([(infosource, selectfiles, [('subject_id', 'subject_id')])
                      ])

atlas_opt_wf.connect([(selectfiles, merge, [('T1w_precon_brain_label', 'in1'),
                                            ('T1w_precon', 'in2')])])

atlas_opt_wf.connect([(selectfiles, normalize,
                       [('T1w_precon', 'image_to_align'),
                        ('T1w_precon_brain_label', 'apply_to_files')])])

atlas_opt_wf.connect([(normalize, datasink,
                       [('normalized_image', task + '_preconT1w.@con'),
                        ('normalized_files', task + '_allOtherScans.@con')])])
# -------------------------------------------------------
