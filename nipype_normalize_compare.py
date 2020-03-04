# Normalization Pipeline '
# -----------------Imports-------------------------------
import os
# import CustomNiPype as cnp
import nipype.pipeline.engine as eng
import nipype.interfaces.spm as spm
# import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
import nipype.interfaces.ants as ants
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio

fsl.FSLCommand.set_default_output_type('NIFTI')

# -------------------------------------------------------

# -----------------Inputs--------------------------------
# Define subject list, session list and relevent file types
upper_dir = os.path.realpath('../..')
working_dir = os.path.abspath(upper_dir)
output_dir = os.path.join(working_dir, 'derivatives/')
temp_dir = os.path.join(output_dir, 'datasink/')

subject_list = ['03', '11']
subject_list = ['02', '03', '04', '06', '08', '09', '10', '11']

# session_list = ['Precon', 'Postcon']

subdirectory = os.path.join('sub-{subject_id}', 'ses-Precon')
filestart = 'sub-{subject_id}_ses-Precon'

scantype = 'anat'
T1w_files = os.path.join(subdirectory, scantype, filestart + '*_T1w.nii')
MNI_file = os.path.abspath('/opt/fsl/data/standard/MNI152_T1_1mm.nii.gz')
MNI_brain_file = os.path.abspath(
    '/opt/fsl/data/standard/MNI152_T1_1mm_brain.nii.gz')

templates = {
    'T1w_precon': T1w_files,
    'mni_head': MNI_file,
    'mni_brain': MNI_brain_file
}

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

# Preprocessing
# -----------------------BiasFieldCorrection-------------
bias_norm = eng.Node(ants.N4BiasFieldCorrection(), name='bias_norm')
# bias_norm.inputs.save_bias = True
bias_norm.inputs.rescale_intensities = True
# -------------------------------------------------------

# SPM
# -----------------------NormalizeNode-------------------
normalize = eng.Node(spm.Normalize12(), name='normalize')
normalize.inputs.write_interp = 7
normalize.inputs.write_voxel_sizes = [1, 1, 1]
# -------------------------------------------------------

# FSL
# ---------------------Reorient----------------------
reorient = eng.Node(fsl.Reorient2Std(), name='reorient')
reorient.inputs.output_type = 'NIFTI'
# -------------------------------------------------------

# -----------------------RobustFOV----------------------
robustFOV = eng.Node(fsl.RobustFOV(), name='robustFOV')
robustFOV.inputs.output_type = 'NIFTI'
# -------------------------------------------------------

frac_list = [0.01, 0.15, 0.3, 0.5]

# -----------------------NoseStrip----------------------
nosestrip = eng.Node(fsl.BET(), name='nosestrip')
nosestrip.inputs.vertical_gradient = -0.5
nosestrip.inputs.output_type = 'NIFTI'
nosestrip.iterables = ('frac', frac_list)
# -------------------------------------------------------

# -----------------------SkullStrip----------------------
skullstrip = eng.Node(fsl.BET(), name='skullstrip')
skullstrip.inputs.frac = 0.15
skullstrip.inputs.vertical_gradient = -0.5
skullstrip.inputs.robust = True
skullstrip.inputs.output_type = 'NIFTI'
skullstrip.iterables = ('frac', frac_list)
# -------------------------------------------------------

# -----------------LinearRegistration--------------------
flirt = eng.Node(fsl.FLIRT(), name='flirt')
flirt.inputs.output_type = 'NIFTI'
# -------------------------------------------------------

# -----------------NonlinearRegistration--------------------
fnirt = eng.Node(fsl.FNIRT(), name='fnirt')
fnirt.inputs.output_type = 'NIFTI'
# -------------------------------------------------------

# -----------------------FAST----------------------------
fast = eng.Node(fsl.FAST(), name='fast')
fast.inputs.output_type = 'NIFTI'
# -------------------------------------------------------

# -----------------------Merge---------------------------
merge1 = eng.Node(utl.Merge(2), name='merge')
merge1.ravel_inputs = True
# -------------------------------------------------------

# ----------------------FIRST----------------------------
first = eng.Node(fsl.FIRST(), name='first')
first.inputs.output_type = 'NIFTI'
# -------------------------------------------------------

# -----------------------Merge---------------------------
merge2 = eng.Node(utl.Merge(2), name='merge')
merge2.ravel_inputs = True
# -------------------------------------------------------

# ----------------------PNGSlicer------------------------
png_slice = eng.MapNode(fsl.Slicer(), name='png_slice', iterfield=['in_file'])
png_slice.inputs.middle_slices = True
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
# -------------------------------------------------------

# -----------------NormalizationWorkflow-----------------
task = 'SpatialNormalization'
norm_wf = eng.Workflow(name=task)
norm_wf.base_dir = working_dir + '/workflow'

norm_wf.connect([
    (infosource, selectfiles, [('subject_id', 'subject_id')]),
    (selectfiles, flirt, [('mni_brain', 'reference')]),
    (selectfiles, fnirt, [('mni_brain', 'ref_file')]),
    (selectfiles, reorient, [('T1w_precon', 'in_file')]),
    (reorient, robustFOV, [('out_file', 'in_file')]),
    #    (robustFOV, flirt, [('out_roi', 'in_file')]),
    #    (robustFOV, normalize, [('out_roi', 'image_to_align')]),
    (robustFOV, nosestrip, [('out_roi', 'in_file')]),
    (nosestrip, skullstrip, [('out_file', 'in_file')]),
    (skullstrip, flirt, [('out_file', 'in_file')]),
    #    (skullstrip, normalize, [('out_file', 'image_to_align')]),
    (flirt, fnirt, [('out_file', 'in_file')]),
    # (flirt, fast, [('out_file', 'in_files')]),
    # (fast, first, [('out_file', 'in_files')]),
    (flirt, datasink, [('out_file', task + '_flirt.@con'),
                       ('out_matrix_file', task + '_flirt_transform.@con')]),
    #    (normalize, datasink, [('normalized_image', task + '_spm.@con')]),
    (fnirt, datasink, [('warped_file', task + '_fnirt.@con'),
                       ('field_file', task + '_fnirt_transform.@con')]),
    (robustFOV, merge1, [('out_roi', 'in1')]),
    (nosestrip, merge1, [('out_file', 'in2')]),
    (skullstrip, merge1, [('out_file', 'in3')]),
    (flirt, merge1, [('out_file', 'in4')]),
    (fnirt, merge1, [('warped_file', 'in5')]),
    (merge1, png_slice, [('out', 'in_file')]),
    (png_slice, datasink, [('out_file', task + '_pngs.@con')])
])
# -------------------------------------------------------

# -------------------WorkflowPlotting--------------------
norm_wf.write_graph(graph2use='flat')
# -------------------------------------------------------

norm_wf.run(plugin='MultiProc', plugin_args={'n_procs': 3})
os.system('notify-send SpatialNormalization done')
# norm_wf.run()