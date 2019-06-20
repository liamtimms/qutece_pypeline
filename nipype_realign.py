# This originally had both preproc and realign but I decided to split them up into different workflows

# -----------------Imports-------------------------------
import os
import CustomNipype as cnp
import nipype.pipeline.engine as eng
import nipype.interfaces.spm as spm
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
# -------------------------------------------------------

# From tutorial:
# Let's create a short helper function to plot 3D NIfTI images
def plot_slice(fname):
    # Load the image
    img = nb.load(fname)
    data = img.get_data()
    # Cut in the middle of the brain
    cut = int(data.shape[-1]/2) + 10
    # Plot the data
    plt.imshow(np.rot90(data[..., cut]), cmap="gray")
    plt.gca().set_axis_off()

# -----------------Inputs--------------------------------
# Define subject list, session list and relevent file types
working_dir = os.path.abspath('/mnt/hgfs/VMshare/WorkingBIDS/')
output_dir = os.path.join(working_dir, 'derivatives/')
temp_dir = os.path.join(output_dir, 'datasink/')

subject_list = ['02', '03', '05', '06', '08', '10', '11']
session_list = ['Precon', 'Postcon']

subdirectory = os.path.join(temp_dir, 'preproc', 'sub-{subject_id}', 'ses-{session_id}')
filestart = 'sub-{subject_id}_ses-{session_id}_'

scantype = 'qutece'
qutece_highres_files = os.path.join(subdirectory, scantype,
                                    filestart, 'hr_run*.nii')
templates = {'qutece_hr': qutece_highres_files}

# Infosource - a function free node to iterate over the list of subject names
infosource = eng.Node(utl.IdentityInterface(fields=['subject_id','session_id']),
                  name="infosource")
infosource.iterables = [('subject_id', subject_list),
                        ('session_id', session_list)]

# Selectfiles to provide specific scans with in a subject to other functions
selectfiles = eng.Node(nio.SelectFiles(templates,
                               base_directory=working_dir,
                               sort_filelist=True, raise_on_empty=True),
                   name="selectfiles")
# -------------------------------------------------------

# TODO: motion artifact testing?

#TODO: skip over scans marked skip? maybe add GUI to skip scans

# ------------------------RealignNode--------------------
xyz = [0, 1, 0]
realign = eng.Node(spm.Realign(), name = "Realign")
realign.register_to_mean = True
realign.quality = 0.95
realign.wrap = xyz
realign.write_wrap = xyz
realign.interp = 7
realign.write_interp = 7
# -------------------------------------------------------

# ------------------------Output-------------------------
# Datasink - creates output folder for important outputs
datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                         container=temp_dir),
                name="datasink")
# Use the following DataSink output substitutions
substitutions = [('_subject_id_', 'sub-'), ('_session_id_', 'ses-')]
subjFolders = [('sub-%s_session_id_%s' % (sub, ses), 
                'sub-%s/ses-%s' % (sub, ses))
               for ses in session_list
               for sub in subject_list]
substitutions.extend(subjFolders)
datasink.inputs.substitutions = substitutions
# -------------------------------------------------------

# -----------------RealignmentWorkflow-------------------
task = 'realign'
realign_wf = eng.Workflow(name = task)
realign_wf.base_dir = working_dir + '/workflow'

realign_wf.connect([(infosource, selectfiles, [('subject_id', 'subject_id'),
                                              ('session_id', 'session_id')])])

realign_wf.connect([(selectfiles, realign, [('qutece_hr', 'in_files')])])

realign_wf.connect([(realign, datasink,
                     [('realigned_files', 'realign.@con'),
                      ('mean_image', 'realignmean.@con')])])
# -------------------------------------------------------

# -------------------WorkflowPlotting--------------------
realign_wf.write_graph(graph2use='flat')
from IPython.display import Image
Image(filename=working_dir + "/workflow/"+ task + "/graph_detailed.png")
# -------------------------------------------------------

