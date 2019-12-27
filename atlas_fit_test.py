# Need to check atlas fit, may not be a Pipeline
# -----------------Imports-------------------------------
import os
import CustomNiPype as cnp
import nibabel as nib
import nilearn as nil
import nipype.pipeline.engine as eng
import nipype.interfaces.spm as spm
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
# -------------------------------------------------------

# -----------------Inputs--------------------------------
# Define subject list, session list and relevent file types
working_dir = os.path.abspath('/mnt/hgfs/VMshare/WorkingBIDS/')
output_dir = os.path.join(working_dir, 'derivatives/')
temp_dir = os.path.join(output_dir, 'datasink/')
subject_list = ['02', '03', '05', '06', '08', '10', '11']
subject_list = ['02', '03', '05', '06', '10']
#subject_list =['11']

# Atlas Label
atlas_file = '/home/liam/Documents/MATLAB/MatlabToolboxes/spm12/tpm/mask_ICV.nii'

# * precon T1w brain label cropped out from Ju's manual work and now normalized
scanfolder = 'SpatialNormalization_allOtherScans'
session = 'Precon'
filestart = 'sub-{subject_id}_ses-' + session + '_'
subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}')
precon_T1w_brain_label_files = os.path.join(
    subdirectory, 'wrr' + filestart + 'T1w_brain-label.nii')

templates = {
    'atlas_file': atlas_file,
    'T1w_precon_brain_label': precon_T1w_brain_label_files
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
    diff_nii = nib.Nifti1Image(diff_img, postcon_nii.affine,
                               postcon_nii.header)

    return diff_img, diff_nii

difference = eng.Node(utl.Function(), name='difference')
# -------------------------------------------------------

# -----------------------Merge---------------------------
merge = eng.Node(utl.Merge(5), name='merge')
merge.ravel_inputs = True
# -------------------------------------------------------

# -----------------------FAST----------------------------
fast = eng.Node(fsl.FAST(), name='fast')
fast.inputs.no_bias = True
fast.inputs.segment_iters = 45
fast.inputs.output_type = 'NIFTI'
# -------------------------------------------------------

# -----------------------Merge---------------------------
merge2 = eng.Node(utl.Merge(8), name='merge2')
merge2.ravel_inputs = True
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
task = 'SpatialNormalization'
norm_wf = eng.Workflow(name=task)
norm_wf.base_dir = working_dir + '/workflow'

norm_wf.connect([(infosource, selectfiles, [('subject_id', 'subject_id')])])
norm_wf.connect([(selectfiles, merge, [('nonUTE_postcon', 'in1'),
                                       ('qutece_postcon', 'in2'),
                                       ('nonT1w_precon', 'in3'),
                                       ('T1w_precon_brain_label', 'in4'),
                                       ('T1w_precon', 'in5')])])

norm_wf.connect([(selectfiles, normalize, [('T1w_precon_brain',
                                            'image_to_align')])])
norm_wf.connect([(merge, normalize, [('out', 'apply_to_files')])])
norm_wf.connect([(normalize, datasink,
                  [('normalized_image', task + '_preconT1w.@con'),
                   ('normalized_files', task + '_allOtherScans.@con')])])

norm_wf.connect([(selectfiles, fast, [('T1w_precon_brain', 'in_files')]),
                 (fast, merge2, [('tissue_class_map', 'in1'),
                                 ('tissue_class_files', 'in2'),
                                 ('restored_image', 'in3'),
                                 ('mixeltype', 'in4'),
                                 ('partial_volume_map', 'in5'),
                                 ('partial_volume_files', 'in6'),
                                 ('bias_field', 'in7'),
                                 ('probability_maps', 'in8')])])

norm_wf.connect([(merge2, datasink, [('out', task + '_FAST.@con')])])
# -------------------------------------------------------
