
# Interscan Coregister Pipeline
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
working_dir = os.path.abspath('/run/media/mri/4e43a4f6-7402-4881-bcf5-d280e54cc385/Analysis/DCM2BIDS2')
output_dir = os.path.join(working_dir, 'derivatives/')
temp_dir = os.path.join(output_dir, 'datasink/')

#subject_list = ['02', '03', '04', '06', '08', '09', '10', '11']
subject_list = ['11']
# session_list = ['Precon', 'Postcon']

# * realigned precontrast average
scantype = 'qutece'
# * raw postcontrast images
session = 'Postcon'
subdirectory = os.path.join(working_dir,
                            'sub-{subject_id}', 'ses-'+session, scantype)
filestart = 'sub-{subject_id}_ses-'+ session +'_'
qutece_hr_postcon_files = os.path.join(subdirectory,
                                       filestart+'*hr*UTE.nii')


# directory: '\WorkingBIDS\derivatives\datasink\IntrasessionCoregister_T1w\sub-11\ses-Precon'

# * precon IntrasessionCoregister_T1w
scantype = 'anat'
session = 'Precon'
subdirectory = os.path.join(working_dir,
                            'sub-{subject_id}', 'ses-'+session, scantype)
filestart = 'sub-{subject_id}_ses-'+ session +'_'
tof_files  = os.path.join(subdirectory,
                                       filestart+'*TOF*.nii')



templates = {'qutece_postcon': qutece_hr_postcon_files,
             'tof':            tof_files}


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

# -----------------------Merge---------------------------
merge = eng.Node(utl.Merge(2), name = 'merge')
merge.ravel_inputs = True
# -------------------------------------------------------

# -----------------------FFTNode-----------------
fft = eng.MapNode(interface = cnp.FFTNii(),
                         name = 'fft', iterfield=['in_file'])
# -------------------------------------------------------

# ------------------------Output-------------------------
# Datasink - creates output folder for important outputs
datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                         container=temp_dir),
                name="datasink")
# Use the following DataSink output substitutions
substitutions = [('_subject_id_', 'sub-')]

datasink.inputs.substitutions = substitutions
datasink.inputs.regexp_substitutions = [('_fft[0123456789].','')]

# -------------------------------------------------------

# -----------------CoregistrationWorkflow----------------
task = 'FFT'
fft_wf = eng.Workflow(name = task)
fft_wf.base_dir = working_dir + '/workflow'

fft_wf.connect([(infosource, selectfiles, [('subject_id', 'subject_id')])])
fft_wf.connect([(selectfiles, merge, [('qutece_postcon', 'in1'),
                                        ('tof', 'in2')])])
fft_wf.connect([(merge, fft, [('out', 'in_file')])])
fft_wf.connect([(fft, datasink,
                      [('out_file', task+'.@con')])])


# -------------------------------------------------------

# -------------------WorkflowPlotting--------------------
fft_wf.write_graph(graph2use='flat')
# -------------------------------------------------------

#fft_wf.run(plugin = 'MultiProc', plugin_args = {'n_procs' : 5})
fft_wf.run()