
# Preprocessing Pipeline
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
working_dir = os.path.abspath('/mnt/hgfs/VMshare/WorkingBIDS/')
output_dir = os.path.join(working_dir, 'derivatives/')
temp_dir = os.path.join(output_dir, 'datasink/')
subject_list = ['02', '03', '05', '06', '08', '10', '11']
#subject_list =['11']

# Select files:
# + precon scans
#   * IntersessionCoregister_preconScans
#       -T1w -> image to align (all else must go to merge and then 'apply_to_files')
#       -non T1w
# + postcon scans
#   * IntrasessionCoregister_nonT1w
#   * IntrasessionCoregister_T1w
#   * preprocessing (sub-??, ses-Postcon, qutece)

# directory: '\WorkingBIDS\derivatives\datasink\IntrasessionCoregister_T1w\sub-11\ses-Precon'
session = 'Precon'
# * precon T1w from IntersessionCoregister_preconScans
filestart = 'sub-{subject_id}_ses-'+ session +'_'
scanfolder = 'IntersessionCoregister_preconScans'
subdirectory = os.path.join(temp_dir, scanfolder,
                            'sub-{subject_id}')
precon_T1w_files  = os.path.join(subdirectory,
                                       'rr'+filestart+'T1w.nii')

# * precon nonT1w (includes UTE) from IntersessionCoregister_preconScans
subdirectory = os.path.join(temp_dir, scanfolder,
                            'sub-{subject_id}')
precon_nonT1w_files  = os.path.join(subdirectory,
                                       'rr'+filestart+'??[!w]*.nii')

# + postcon scans
#   * IntrasessionCoregister_nonT1w
session = 'Postcon'
scanfolder = 'IntrasessionCoregister_nonT1w' # note that this also includes T1w for some reason right now
subdirectory = os.path.join(temp_dir, scanfolder,
                            'sub-{subject_id}', 'ses-'+session)
filestart = 'sub-{subject_id}_ses-'+ session +'_'
postcon_nonUTE_files = os.path.join(subdirectory,
                                       'r'+filestart+'*.nii')


# * preprocessing (sub-??, ses-Postcon, qutece)
scanfolder = 'Preprocessing'
subdirectory = os.path.join(temp_dir, scanfolder,
                            'sub-{subject_id}', 'ses-'+session)
filestart = 'sub-{subject_id}_ses-'+ session +'_'
postcon_UTE_files = os.path.join(subdirectory, 'qutece',
                                       'r'+filestart+'hr_run*.nii')


templates = {'nonUTE_postcon': postcon_nonUTE_files,
             'qutece_postcon': postcon_UTE_files,
             'T1w_precon': precon_T1w_files,
             'nonT1w_precon': precon_nonT1w_files}


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

# -----------------------SkullStrip----------------------
bet = eng.Node(fsl.BET(), name = 'bet')
bet.inputs.mask = True
bet.inputs.robust = True
bet.inputs.output_type = 'NIFTI'
# -------------------------------------------------------

# -----------------------NormalizeNode-------------------
normalize = eng.Node(spm.Normalize12(), name = 'normalize')
normalize.inputs.write_interp = 7
normalize.inputs.write_voxel_sizes = [1, 1, 1]
# -------------------------------------------------------

# -----------------------Merge---------------------------
merge = eng.Node(utl.Merge(4), name = 'merge')
merge.ravel_inputs = True
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
task = 'SpatialNormalization'
norm_wf = eng.Workflow(name = task)
norm_wf.base_dir = working_dir + '/workflow'

norm_wf.connect([(infosource, selectfiles, [('subject_id', 'subject_id')])])

norm_wf.connect([(selectfiles, merge, [('nonUTE_postcon', 'in1'),
                                        ('qutece_postcon', 'in2'),
                                        ('nonT1w_precon', 'in3'),
                                        ('T1w_precon', 'in4')])])

norm_wf.connect([(selectfiles, bet, [('T1w_precon', 'in_file')])])
norm_wf.connect([(bet, datasink,
                     [('out_file', task+'_skullstripT1w.@con'),
                      ('mask_file', task+'_skullstripMask.@con')])])

norm_wf.connect([(bet, normalize, [('out_file', 'image_to_align')])])
norm_wf.connect([(merge, normalize, [('out', 'apply_to_files')])])
norm_wf.connect([(normalize, datasink,
                     [('normalized_image', task+'_preconT1w.@con'),
                      ('normalized_files', task+'_allOtherScans.@con')])])
# -------------------------------------------------------

