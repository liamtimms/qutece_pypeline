
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
working_dir = os.path.abspath('/mnt/hgfs/VMshare/WorkingBIDS/')
output_dir = os.path.join(working_dir, 'derivatives/')
temp_dir = os.path.join(output_dir, 'datasink/')

subject_list = ['02', '03', '06', '07', '08', '09', '10', '11']
session_list = ['Precon'] 

subdirectory = os.path.join('sub-{subject_id}', 'ses-{session_id}')
filestart = 'sub-{subject_id}_ses-{session_id}'

scantype = 'anat'
T1w_files = os.path.join(subdirectory, scantype,
                                    filestart + '_T1w.nii')

FLAIR_files = os.path.join(subdirectory, scantype,
                                    filestart + '_FLAIR.nii')

SWI_files = os.path.join(subdirectory, scantype,
                                    filestart + '_SWI_angio.nii')

templates = {'T1w': T1w_files,
             'FLAIR': FLAIR_files,
             'SWI': SWI_files}

# Infosource - a function free node to iterate over the list of subject names
infosource = eng.Node(utl.IdentityInterface(fields=['subject_id', 'session_id']),
                  name="infosource")
infosource.iterables = [('subject_id', subject_list),
                        ('session_id', session_list)]

# Selectfiles to provide specific scans with in a subject to other functions
selectfiles = eng.Node(nio.SelectFiles(templates,
                               base_directory=working_dir,
                               sort_filelist=True, raise_on_empty=True),
                   name="SelectFiles")
# -------------------------------------------------------

# -----------------------CoregisterNode------------------
coreg = eng.MapNode(spm.Coregister(), name = "Coregister", iterfield = 'source')
coreg.inputs.write_interp = 7
coreg.inputs.separation = [6, 3, 2]
# -------------------------------------------------------

# ------------------------Output-------------------------
# Datasink - creates output folder for important outputs
datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                         container=temp_dir),
                name="datasink")
# Use the following DataSink output substitutions
substitutions = [('_subject_id_', 'sub-'), ('_session_id_', 'ses-')]

subjFolders = [('ses-%ssub-%s' % (ses, sub), 
                'sub-%s/ses-%s' % (sub, ses))
               for ses in session_list
               for sub in subject_list]
substitutions.extend(subjFolders)
datasink.inputs.substitutions = substitutions
# -------------------------------------------------------

# -----------------CoregistrationWorkflow----------------
task = 'CoregisterPrecon'
coreg_wf = eng.Workflow(name = task)
coreg_wf.base_dir = working_dir + '/workflow'

# I don't expect this to work... TODO: make select files pass a list of non-T1w 
# files to the coreg mapnode and then use source as the iterable
coreg_wf.connect([(infosource, selectfiles, [('subject_id', 'subject_id'),
                                              ('session_id', 'session_id')])])

coreg_wf.connect([(selectfiles, coreg, [('T1w', 'target'),
                                          'FLAIR', 'source'])])
coreg_wf.connect([(selectfiles, coreg, [('T1w', 'target'),
                                          'SWI', 'source'])])
coreg_wf.connect([(coreg, datasink,
                     [('coregistered_source', task+'.@con')])])
# -------------------------------------------------------

