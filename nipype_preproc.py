
# Preprocessing Pipeline
# -----------------Imports-------------------------------
import os
import CustomNiPype as cnp
import nipype.pipeline.engine as eng
import nipype.interfaces.spm as spm
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
import nipype.interfaces.ants as ants
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
# -------------------------------------------------------

# -----------------Inputs--------------------------------
# Define subject list, session list and relevent file types
working_dir = os.path.abspath('/run/media/mri/4e43a4f6-7402-4881-bcf5-d280e54cc385/Analysis/DCM2BIDS2')
output_dir = os.path.join(working_dir, 'derivatives/')
temp_dir = os.path.join(output_dir, 'datasink/')

subject_list = ['01', '02', '03', '04', '06', '08', '09', '10', '11']
session_list = ['Precon', 'Postcon']

subdirectory = os.path.join('sub-{subject_id}', 'ses-{session_id}')
filestart = 'sub-{subject_id}_ses-{session_id}'

scantype = 'qutece'
qutece_fast_files = os.path.join(subdirectory, scantype,
                                    filestart+'*fast*_run-*[0123456789]_UTE.nii')

qutece_hr_files = os.path.join(subdirectory, scantype,
                                    filestart+'*hr*_run-*[0123456789]_UTE.nii')

templates = {'qutece_fast': qutece_fast_files,
             'qutece_hr': qutece_hr_files}

# Infosource - a function free node to iterate over the list of subject names
infosource = eng.Node(utl.IdentityInterface(fields=['subject_id', 'session_id']),
                  name="infosource")
infosource.iterables = [('subject_id', subject_list),
                        ('session_id', session_list)]

# Selectfiles to provide specific scans with in a subject to other functions
selectfiles = eng.Node(nio.SelectFiles(templates,
                               base_directory=working_dir,
                               sort_filelist=True, raise_on_empty=True),
                   name="selectfiles")
# -------------------------------------------------------

# -----------------------UnringNode----------------------
unring_nii = eng.MapNode(interface = cnp.UnringNii(),
                         name = 'unring_nii', iterfield=['in_file'])
# -------------------------------------------------------

# -----------------------BiasFieldCorrection-------------
bias_norm = eng.MapNode(ants.N4BiasFieldCorrection(),
                     name = 'bias_norm', iterfield=['input_image'])
bias_norm.inputs.save_bias = True
# -------------------------------------------------------

# ------------------------RealignNode--------------------
xyz = [0, 1, 0]
realign = eng.Node(spm.Realign(), name = "realign")
realign.inputs.register_to_mean = True
realign.inputs.quality = 0.95
realign.inputs.wrap = xyz
realign.inputs.write_wrap = xyz
realign.inputs.interp = 7
realign.inputs.write_interp = 7
# -------------------------------------------------------

# ------------------------Output-------------------------
# Datasink - creates output folder for important outputs
datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                         container=temp_dir),
                name="datasink")
# Use the following DataSink output substitutions
substitutions = [('_subject_id_', 'sub-'), ('_session_id_', 'ses-')]
subjFolders = [('ses-%ssub-%s' % (ses, sub),
               ('sub-%s/ses-%s/'+scantype) % (sub, ses))
               for ses in session_list
               for sub in subject_list]
substitutions.extend(subjFolders)
datasink.inputs.substitutions = substitutions
datasink.inputs.regexp_substitutions = [('_BiasCorrection.','')]
# -------------------------------------------------------

# -----------------PreprocWorkflow------------------------
task = 'preprocessing'
preproc_wf = eng.Workflow(name = task, base_dir = working_dir + '/workflow')
preproc_wf.connect([(infosource, selectfiles, [('subject_id', 'subject_id'),
                                             ('session_id', 'session_id')]),
                  (selectfiles, unring_nii, [('qutece_fast', 'in_file')]),
                  (unring_nii, bias_norm, [('out_file', 'input_image')]),
                  (bias_norm, realign, [('output_image', 'in_files')]),
                  (bias_norm, datasink, [('bias_image', task+'_BiasField.@con')]),
                  (realign, datasink,  [('realigned_files', task+'.@con'),
                                        ('mean_image', 'realignmean.@con')])])
# -------------------------------------------------------

# -------------------WorkflowPlotting--------------------
preproc_wf.write_graph(graph2use='flat')
# -------------------------------------------------------

#preproc_wf.run(plugin = 'MultiProc', plugin_args = {'n_procs' : 7})
preproc_wf.run(plugin = 'MultiProc')

