# Preprocessing Pipeline
# -----------------Imports-------------------------------
import os
import CustomNipype as cnp
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

subject_list = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11']
session_list = ['Precon', 'Postcon', 'Blood']

subdirectory = os.path.join('sub-{subject_id}', 'ses-{session_id}')
filestart = 'sub-{subject_id}_ses-{session_id}_'

scantype = 'qutece'
qutece_highres_files = os.path.join(subdirectory, scantype,
                                    filestart, '_hr_run*_UTE.nii')
qutece_fast_files = os.path.join(subdirectory, scantype,
                                    filestart, '_fast*_UTE.nii')

scantype = 'anat'
anat_files = os.path.join(subdirectory, scantype,
                                    filestart, '_T1w.nii')
swi_files = os.path.join(subdirectory, scantype,
                                    filestart, '_SWI_angio.nii')

templates = {'qutece_hr': qutece_highres_files,
             'qutece_fast': qutece_fast_files,
             'T1w': anat_files,
             'swi': swi_files}

# Infosource - a function free node to iterate over the list of subject names
infosource = eng.Node(utl.IdentityInterface(fields=['subject_id', 'session_id']),
                  name="infosource")
infosource.iterables = [('subject_id', subject_list),
                        ('session_id', session_list)]

# Selectfiles to provide specific scans with in a subject to other functions
selectfiles = eng.Node(nio.SelectFiles(templates,
                               base_directory=working_dir,
                               sort_filelist=True, raise_on_empty=True),
                   name="Select Files")
# -------------------------------------------------------

# -----------------------UnringNode----------------------
unring_nii = eng.MapNode(interface = cnp.UnringNii(),
                         name = 'Unring', iterfield=['in_file'])
# -------------------------------------------------------

# -----------------------BiasFieldCorrection-------------
bias_norm = eng.Node(ants.N4BiasFieldCorrection(),
                     name = 'Bias Correction')
# -------------------------------------------------------

# ------------------------Output-------------------------
# Datasink - creates output folder for important outputs
datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                         container=temp_dir),
                name="datasink")
# Use the following DataSink output substitutions
substitutions = [('_subject_id_', 'sub-'), ('_session_id_', 'ses-')]
subjFolders = [('sub-%s_session_id_%s' % (sub, ses), 'sub-%s/ses-%s' % (sub, ses))
               for ses in session_list
               for sub in subject_list]
substitutions.extend(subjFolders)
datasink.inputs.substitutions = substitutions
# -------------------------------------------------------

# -----------------UnringWorkflow------------------------
preproc_wf = eng.Workflow(name = 'Preprocessing')
preproc_wf.connect([(infosource, selectfiles, [('subject_id', 'subject_id'),
                                             ('session_id', 'session_id')]),
                  (selectfiles, unring_nii, [('qutece_hr', 'in_file'),
                                             ('qutece_fast', 'in_file')]),
                  (unring_nii, bias_norm, [('out_file', 'input_image')]),
                  (bias_norm, datasink, [('output_image', 'preproc.@con')])
                  ])
# -------------------------------------------------------

