# Normalization Pipeline '
# -----------------Imports-------------------------------
import os
# import CustomNiPype as cnp
import nipype.pipeline.engine as eng
import nipype.interfaces.spm as spm
# import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
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
session_list = ['Precon', 'Postcon']

subdirectory = os.path.join('sub-{subject_id}', 'ses-{session_id}')
filestart = 'sub-{subject_id}_ses-{session_id}'
scantype = 'anat'
T1w_files = os.path.join(subdirectory, scantype, filestart + '_T1w.nii')

MNI_file = os.abspath('/opt/fsl/data/standard/MNI152_T1_1mm.nii.gz')

templates = {'T1w': T1w_files, 'mni_head': MNI_file}

infosource = eng.Node(
    utl.IdentityInterface(fields=['subject_id', 'session_id']),
    name="infosource")
infosource.iterables = [('subject_id', subject_list),
                        ('session_id', session_list)]

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
bias_norm.inputs.save_bias = True
bias_norm.inputs.rescale_intensities = True
# -------------------------------------------------------

# SPM
# -----------------------NormalizeNode-------------------
normalize = eng.Node(spm.Normalize12(), name='normalize')
normalize.inputs.write_interp = 7
normalize.inputs.write_voxel_sizes = [1, 1, 1]
# -------------------------------------------------------

# -------------NormalizeNodeAfterStrip-------------------
normalize_strip = eng.Node(spm.Normalize12(), name='normalize_strip')
normalize_strip.inputs.write_interp = 7
normalize_strip.inputs.write_voxel_sizes = [1, 1, 1]
# -------------------------------------------------------

# FSL
# -----------------------RobustFOV----------------------
robustFOV = eng.Node(fsl.RobustFOV(), name='robustFOV')
robustFOV.inputs.output_type = 'NIFTI'
# -------------------------------------------------------

# -----------------------NoseStrip----------------------
nosestrip = eng.Node(fsl.BET(), name='nosestrip')
nosestrip.inputs.frac = 0.3
nosestrip.inputs.mask = True
nosestrip.inputs.robust = True
nosestrip.inputs.output_type = 'NIFTI'
# -------------------------------------------------------

# -----------------------SkullStrip----------------------
skullstrip = eng.Node(fsl.BET(), name='skullstrip')
skullstrip.inputs.mask = True
skullstrip.inputs.robust = True
skullstrip.inputs.output_type = 'NIFTI'
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
fast.inputs.no_bias = True
fast.inputs.segment_iters = 45
fast.inputs.output_type = 'NIFTI'
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
    (selectfiles, flirt, [('T1w_precon', 'in_file'),
                          ('mni_head', 'reference')]),
    (selectfiles, normalize, [('T1w_precon', 'in_file')]),
    (flirt, fnirt, [('out_file', 'in_file')]),
    (selectfiles, fnirt, [('mni_head', 'reference')]),
    (normalize, datasink, [('normalized_image', task + '_spm.@con')]),
    (flirt, datasink, [('out_file', task + '_flirt.@con')]),
    (fnirt, datasink, [('warped_file', task + '_flirt.@con')]),
])
# -------------------------------------------------------

# -------------------WorkflowPlotting--------------------
norm_wf.write_graph(graph2use='flat')
# -------------------------------------------------------

norm_wf.run(plugin='MultiProc')
# norm_wf.run()
