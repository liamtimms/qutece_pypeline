
# Diff Pipeline
# -----------------Imports-------------------------------
import os
import CustomNiPype as cnp
import nipype.pipeline.engine as eng
import nipype.interfaces.spm as spm
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
# -------------------------------------------------------

# -----------------Inputs--------------------------------
# Define subject list, session list and relevent file types
#working_dir = os.path.abspath('/mnt/hgfs/VMshare/WorkingBIDS/')
working_dir = os.path.abspath('/run/media/mri/4e43a4f6-7402-4881-bcf5-d280e54cc385/Analysis/DCM2BIDS2')
output_dir = os.path.join(working_dir, 'derivatives/')
temp_dir = os.path.join(output_dir, 'datasink/')
subject_list = ['03', '04', '06', '08', '09', '10', '11']
#subject_list =['11']

# directory: '\WorkingBIDS\derivatives\datasink\IntrasessionCoregister_T1w\sub-11\ses-Precon'
session = 'Precon'
# * precon T1w from IntersessionCoregister_preconScans
filestart = 'sub-{subject_id}_ses-'+ session +'_'
scanfolder = 'IntersessionCoregister_preconUTEmean'
subdirectory = os.path.join(temp_dir, scanfolder,
                            'sub-{subject_id}')
precon_UTE_mean  = os.path.join(subdirectory,
                                       'rmean'+filestart+'*fast*UTE*.nii')
# + postcon scans
session = 'Postcon'
# * preprocessing (sub-??, ses-Postcon, qutece)
scanfolder = 'preprocessing'
subdirectory = os.path.join(temp_dir, scanfolder,
                            'sub-{subject_id}', 'ses-'+session)
filestart = 'sub-{subject_id}_ses-'+ session +'_'
postcon_UTE_files = os.path.join(subdirectory, 'qutece',
                                       'r'+filestart+'*fast*UTE*.nii')

templates = {'qutece_precon_mean': precon_UTE_mean,
             'qutece_postcon': postcon_UTE_files}


# Infosource - a function free node to iterate over the list of subject names
infosource = eng.Node(utl.IdentityInterface(fields=['subject_id']),
                  name="infosource")
infosource.iterables = [('subject_id', subject_list)]

# Selectfiles to provide specific scans with in a subject to other functions
selectfiles = eng.Node(nio.SelectFiles(templates,
                               base_directory=working_dir,
                               sort_filelist=True, raise_on_empty=True),
                   name="SelectFiles")
# -------------------------------------------------------

# -----------------------DiffNode-------------------
difference = eng.MapNode(cnp.DiffNii(), name = 'difference', iterfield = 'file2')
#difference.iterables = [('file1', ['precon_UTE_files']), ('file2', ['postcon_UTE_files'])] # this is pseudo code not real
# -------------------------------------------------------

# ------------------------Output-------------------------
# Datasink - creates output folder for important outputs
datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                         container=temp_dir),
                name="datasink")
# Use the following DataSink output substitutions
substitutions = [('_subject_id_', 'sub-')]

subjFolders = [('sub-%s' % (sub),
                'sub-%s' % (sub))
               for sub in subject_list]
substitutions.extend(subjFolders)
datasink.inputs.substitutions = substitutions
# datasink.inputs.regexp_substitutions = [('_coreg_to_postcon.','')]
# -------------------------------------------------------

# -----------------NormalizationWorkflow-----------------
task = 'postminuspre'
diff_wf = eng.Workflow(name = task)
diff_wf.base_dir = working_dir + '/workflow'

diff_wf.connect([(infosource, selectfiles, [('subject_id', 'subject_id')])])
diff_wf.connect([(selectfiles, difference, [('qutece_precon_mean', 'file1'),
                                        ('qutece_postcon', 'file2')])])

diff_wf.connect([(difference, datasink,
                     [('out_file', task+'.@con')])])
# -------------------------------------------------------


# -------------------WorkflowPlotting--------------------
diff_wf.write_graph(graph2use='flat')
# -------------------------------------------------------

diff_wf.run(plugin = 'MultiProc', plugin_args = {'n_procs' : 5})
