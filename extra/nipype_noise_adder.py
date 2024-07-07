# Preprocessing Pipeline
# -----------------Imports-------------------------------
import os

import CustomNiPype as cnp
# import nipype.interfaces.spm as spm
# import nipype.interfaces.freesurfer as fs
# import nipype.interfaces.fsl as fsl
import nipype.interfaces.ants as ants
import nipype.interfaces.io as nio
import nipype.interfaces.utility as utl
import nipype.pipeline.engine as eng

# -------------------------------------------------------

# -----------------Inputs--------------------------------
# Define subject list, session list and relevent file types
# Define subject list, session list and relevent file types
# Assuming BIDs format (code in 'code/nipype' folder)
# we can navigate to the relative path
upper_dir = os.path.realpath('../..')
working_dir = os.path.abspath(upper_dir)
output_dir = os.path.join(working_dir, 'derivatives/')
temp_dir = os.path.join(output_dir, 'datasink/')

subject_list = ['3', '4', '5', '6', '8']
# subject_list = ['5']
# session_list = ['Precon', 'Postcon']
session_list = ['Post']

subdirectory = os.path.join('sub-{subject_id}', 'ses-{session_id}')
filestart = 'sub-{subject_id}_ses-{session_id}'

# TODO: probably best to run all of the non-UTE scans through these
# same corrections makes it more fair and also might technically help coreg

scantype = 'qutece'
qutece_highres_files = os.path.join(subdirectory, scantype,
                                    filestart + '_SPIRiT_norm_HR_UTE.nii')
# templates = {'qutece_hr': qutece_highres_files}

qutece_breathhold_files = os.path.join(subdirectory, scantype,
                                       filestart + '_*_norm_DIS3D_*UTE.nii')
# templates = {'qutece_breathhold': qutece_breathhold_files}

qutece_files = os.path.join(subdirectory, scantype, filestart + '_*UTE.nii')
templates = {'qutece': qutece_files}

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
                       name="selectfiles")
# -------------------------------------------------------

# -----------------------NoiseAdder----------------------
noise_adder = eng.MapNode(cnp.LowerSNRNii(),
                          name='noise_adder',
                          iterfield=['in_file'])
noise_adder.inputs.std = 100
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
datasink.inputs.regexp_substitutions = [('_noise_adder.', '')]
# -------------------------------------------------------

# -----------------PreprocWorkflow------------------------
task = 'LowerSNR'
preproc_wf = eng.Workflow(name=task, base_dir=working_dir + '/workflow')
preproc_wf.connect([(infosource, selectfiles, [('subject_id', 'subject_id'),
                                               ('session_id', 'session_id')]),
                    (selectfiles, noise_adder, [('qutece', 'in_file')]),
                    (noise_adder, datasink, [('out_file', task + '.@con')])])
# -------------------------------------------------------

# -------------------WorkflowPlotting--------------------
preproc_wf.write_graph(graph2use='flat')
from IPython.display import Image

Image(filename=working_dir + "/workflow/" + task + "/graph_detailed.png")
# -------------------------------------------------------

#preproc_wf.run()
preproc_wf.run(plugin='MultiProc')