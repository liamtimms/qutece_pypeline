
# Preprocessing Pipeline
# -----------------Imports-------------------------------
import os
import CustomNiPype as cnp
import nipype.pipeline.engine as eng
import nipype.interfaces.spm as spm
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
# -------------------------------------------------------

# -----------------Inputs--------------------------------
# Define subject list, session list and relevent file types
working_dir = os.path.abspath('/mnt/hgfs/VMshare/WorkingBIDS/')
output_dir = os.path.join(working_dir, 'derivatives/')
temp_dir = os.path.join(output_dir, 'datasink/')

subject_list = ['02', '03', '05', '06', '08', '10', '11']
session_list = ['Precon']

subdirectory = os.path.join('sub-{subject_id}', 'ses-{session_id}')
filestart = 'sub-{subject_id}_ses-{session_id}'

scantype = 'anat'
T1w_files = os.path.join(subdirectory, scantype,
                                    filestart + '_T1w.nii')

nonT1w_files = os.path.join(subdirectory, scantype,
                                    filestart + '_[!T1w]*.nii')


subdirectory = os.path.join(temp_dir, 'realignmean',
                            'sub-{subject_id}', 'ses-{session_id}')
filestart = 'mean'+'sub-{subject_id}_ses-{session_id}_'

scantype = 'qutece'
qutece_highres_files = os.path.join(subdirectory,
                                    filestart+'hr_run*.nii')

templates = {'qutece_mean': qutece_highres_files,
             'T1w': T1w_files,
             'nonT1w': nonT1w_files}


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

# -----------------------CoregisterNodes-----------------
coreg1 = eng.MapNode(spm.Coregister(), name = 'coreg1', iterfield = 'source')
coreg1.inputs.write_interp = 7
coreg1.inputs.separation = [6, 3, 2]

coreg2 = eng.JoinNode(spm.Coregister(), name = 'coreg2', joinsource = 'Coregister1', joinfield = 'apply_to_files')
coreg2.inputs.write_interp = 7
coreg2.inputs.separation = [6, 3, 2]
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
task = 'IntrasessionCoregister'
coreg_wf = eng.Workflow(name = task)
coreg_wf.base_dir = working_dir + '/workflow'

coreg_wf.connect([(infosource, selectfiles, [('subject_id', 'subject_id'),
                                              ('session_id', 'session_id')])])

coreg_wf.connect([(selectfiles, coreg1, [('T1w', 'target'),
                                        ('nonT1w', 'source')])])
coreg_wf.connect([(selectfiles, coreg2, [('qutece_mean', 'target'),
                                          ('T1w', 'source')])])
coreg_wf.connect([(coreg1, coreg2,
                [('coregistered_source', 'apply_to_files')])])
coreg_wf.connect([(coreg2, datasink,
                     [('coregistered_source', task+'.@con'),
                     ('coregistered_files', task+'2.@con')])])

# -------------------------------------------------------

