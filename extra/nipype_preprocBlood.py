# Preprocessing Pipeline
# -----------------Imports-------------------------------
import os

import CustomNiPype as cnp
import nipype.interfaces.ants as ants
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
import nipype.interfaces.io as nio
import nipype.interfaces.spm as spm
import nipype.interfaces.utility as utl
import nipype.pipeline.engine as eng

# -------------------------------------------------------

# -----------------Inputs--------------------------------
# Define subject list, session list and relevent file types
working_dir = os.path.abspath('/mnt/hgfs/VMshare/WorkingBIDS/')
output_dir = os.path.join(working_dir, 'derivatives/')
temp_dir = os.path.join(output_dir, 'datasink/')

#subject_list = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11']
#subject_list = ['02', '03', '06', '07', '08', '09', '10', '11']
subject_list = ['05']
session_list = ['Precon', 'Postcon']

subdirectory = os.path.join('sub-{subject_id}', 'ses-{session_id}')
filestart = 'sub-{subject_id}_ses-{session_id}'

scantype = 'qutece'
qutece_highres_files = os.path.join(subdirectory, scantype,
                                    filestart + '_hr_run-??_UTE.nii')
#qutece_fast_files = os.path.join(subdirectory, scantype,
#                                    filestart + '_fast*_UTE.nii')

templates = {'qutece_hr': qutece_highres_files}
#             'qutece_fast': qutece_fast_files}

# Infosource - a function free node to iterate over the list of subject names
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

# -----------------------UnringNode----------------------
unring_nii = eng.MapNode(interface=cnp.UnringNii(),
                         name='Unring',
                         iterfield=['in_file'])
# -------------------------------------------------------

# -----------------------BiasFieldCorrection-------------
bias_norm = eng.MapNode(ants.N4BiasFieldCorrection(),
                        name='BiasCorrection',
                        iterfield=['input_image'])
# -------------------------------------------------------

# ------------------------Output-------------------------
# Datasink - creates output folder for important outputs
datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                 container=temp_dir),
                    name="datasink")
# Use the following DataSink output substitutions
substitutions = [('_subject_id_', 'sub-'), ('_session_id_', 'ses-')]
subjFolders = [('ses-%ssub-%s' % (ses, sub),
                ('sub-%s/ses-%s/' + scantype) % (sub, ses))
               for ses in session_list for sub in subject_list]
substitutions.extend(subjFolders)
datasink.inputs.substitutions = substitutions
datasink.inputs.regexp_substitutions = [('_BiasCorrection.', '')]
# -------------------------------------------------------

# -----------------UnringWorkflow------------------------
preproc_wf = eng.Workflow(name='Preprocessing',
                          base_dir=working_dir + '/workflow')
preproc_wf.connect([(infosource, selectfiles, [('subject_id', 'subject_id'),
                                               ('session_id', 'session_id')]),
                    (selectfiles, unring_nii, [('qutece_hr', 'in_file')]),
                    (unring_nii, bias_norm, [('out_file', 'input_image')]),
                    (bias_norm, datasink, [('output_image', 'preproc.@con')])])
# -------------------------------------------------------
