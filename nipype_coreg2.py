
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
subject_list = ['11']


# session_list = ['Precon', 'Postcon']

# * realigned precontrast average
scantype = 'qutece'
session = 'Precon'
subdirectory = os.path.join(temp_dir, 'realignmean',
                            'sub-{subject_id}', 'ses-'+session, scantype)
filestart = 'sub-{subject_id}_ses-'+ session +'_'
qutece_mean_precon_file = os.path.join(subdirectory,
                                       'mean'+filestart+'hr_run*.nii')

# * realigned precontrast scans
subdirectory = os.path.join(temp_dir, 'preprocessing',
                            'sub-{subject_id}', 'ses-'+session, scantype)
filestart = 'sub-{subject_id}_ses-'+ session +'_'
qutece_precon_files = os.path.join(subdirectory,
                                       'r'+filestart+'hr_run*.nii')

# * realigned postcontrast average
session = 'Postcon'
subdirectory = os.path.join(temp_dir, 'realignmean',
                            'sub-{subject_id}', 'ses-'+session, scantype)
filestart = 'sub-{subject_id}_ses-'+ session +'_'
qutece_mean_postcon_file = os.path.join(subdirectory,
                                       'mean'+filestart+'hr_run*.nii')


# directory: '\WorkingBIDS\derivatives\datasink\IntrasessionCoregister_T1w\sub-11\ses-Precon'

# * precon IntrasessionCoregister_nonT1w
scantype = 'anat'
session = 'Precon'
subdirectory = os.path.join(temp_dir, 'IntrasessionCoregister_T1w',
                            'sub-{subject_id}', 'ses-'+session)
filestart = 'sub-{subject_id}_ses-'+ session +'_'
T1w_files  = os.path.join(subdirectory,
                                       'r'+filestart+'*.nii')

# * precon IntrasessionCoregister_T1w
subdirectory = os.path.join(temp_dir, 'IntrasessionCoregister_nonT1w',
                            'sub-{subject_id}', 'ses-'+session)
nonT1w_files  = os.path.join(subdirectory,
                                       'r'+filestart+'*.nii')



templates = {'qutece_precon_mean': qutece_mean_precon_file,
             'qutece_precon'      : qutece_precon_files, 
             'qutece_postcon_mean': qutece_mean_postcon_file,
             'T1w': T1w_files,
             'nonT1w': nonT1w_files}


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

# -----------------------CoregisterNodes-----------------
#coreg_to_postcon = eng.JoinNode(spm.Coregister(), name = 'coreg_to_postcon', joinsource= 'selectfiles', joinfield = 'apply_to_files')
coreg_to_postcon = eng.Node(spm.Coregister(), name = 'coreg_to_postcon') 
coreg_to_postcon.inputs.write_interp = 7
coreg_to_postcon.inputs.separation = [6, 3, 2]
# -------------------------------------------------------

# -----------------------Merge---------------------------
merge = eng.Node(utl.Merge(3), name = 'merge')
merge.ravel_inputs = True
# -------------------------------------------------------


# ------------------------Output-------------------------
# Datasink - creates output folder for important outputs
datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                         container=temp_dir),
                name="datasink")
# Use the following DataSink output substitutions
substitutions = [('_subject_id_', 'sub-')]

datasink.inputs.substitutions = substitutions
# -------------------------------------------------------

# -----------------CoregistrationWorkflow----------------
task = 'IntersessionCoregister'
coreg_wf = eng.Workflow(name = task)
coreg_wf.base_dir = working_dir + '/workflow'

coreg_wf.connect([(infosource, selectfiles, [('subject_id', 'subject_id')])])

coreg_wf.connect([(selectfiles, merge, [('qutece_precon', 'in1'),
                                        ('T1w', 'in2'),
                                        ('nonT1w', 'in3')])])


coreg_wf.connect([(selectfiles, coreg_to_postcon, [('qutece_precon_mean', 'target'),
                                                   ('qutece_postcon_mean', 'source')
                                                   ])])

coreg_wf.connect([(merge, coreg_to_postcon, [('out', 'apply_to_files')])])

coreg_wf.connect([(coreg_to_postcon, datasink,
                     [('coregistered_source', task+'_preconUTEmean.@con'),
                      ('coregistered_files', task+'_preconScans.@con')])])


# -------------------------------------------------------


