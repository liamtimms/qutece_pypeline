# Normalization Pipeline
# -----------------Imports-------------------------------
import os

import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
import nipype.interfaces.io as nio
import nipype.interfaces.spm as spm
import nipype.interfaces.utility as utl
import nipype.pipeline.engine as eng

import CustomNiPype as cnp

# -------------------------------------------------------

# -----------------Inputs--------------------------------
# Define subject list, session list and relevent file types
working_dir = os.path.abspath("/mnt/hgfs/VMshare/WorkingBIDS/")
output_dir, temp_dir, workflow_dir, _, _ = cnp.set_common_dirs(working_dir)
subject_list = ["02", "03", "05", "06", "08", "10", "11"]
subject_list = ["02", "03", "05", "06", "10"]
# subject_list =['11']

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
session = "Precon"
# * precon T1w from IntersessionCoregister_preconScans
filestart = "sub-{subject_id}_ses-" + session + "_"
scanfolder = "IntersessionCoregister_preconScans"
subdirectory = os.path.join(temp_dir, scanfolder, "sub-{subject_id}")
precon_T1w_files = os.path.join(subdirectory, "rr" + filestart + "T1w.nii")

# * precon nonT1w (includes UTE) from IntersessionCoregister_preconScans
subdirectory = os.path.join(temp_dir, scanfolder, "sub-{subject_id}")
precon_nonT1w_files = os.path.join(subdirectory,
                                   "rr" + filestart + "??[!w]*.nii")

# * precon T1w brain cropped out from Ju's manual work
scanfolder = "ManualBrainCrop"
subdirectory = os.path.join(temp_dir, scanfolder)
precon_T1w_brain_files = os.path.join(subdirectory,
                                      "rr" + filestart + "T1w_brain.nii")

precon_T1w_brain_label_files = os.path.join(
    subdirectory, "rr" + filestart + "T1w_brain-label.nii")

# + postcon scans
#   * IntrasessionCoregister_nonT1w
session = "Postcon"
scanfolder = "IntrasessionCoregister_nonT1w"  # note that this also includes T1w for some reason right now
subdirectory = os.path.join(temp_dir, scanfolder, "sub-{subject_id}",
                            "ses-" + session)
filestart = "sub-{subject_id}_ses-" + session + "_"
postcon_nonUTE_files = os.path.join(subdirectory, "r" + filestart + "*.nii")

# * preprocessing (sub-??, ses-Postcon, qutece)
scanfolder = "Preprocessing"
subdirectory = os.path.join(temp_dir, scanfolder, "sub-{subject_id}",
                            "ses-" + session)
filestart = "sub-{subject_id}_ses-" + session + "_"
postcon_UTE_files = os.path.join(subdirectory, "qutece",
                                 "r" + filestart + "hr_run*.nii")

templates = {
    "nonUTE_postcon": postcon_nonUTE_files,
    "qutece_postcon": postcon_UTE_files,
    "T1w_precon": precon_T1w_files,
    "nonT1w_precon": precon_nonT1w_files,
    "T1w_precon_brain": precon_T1w_brain_files,
    "T1w_precon_brain_label": precon_T1w_brain_label_files,
}

# Infosource - a function free node to iterate over the list of subject names
infosource = eng.Node(utl.IdentityInterface(fields=["subject_id"]),
                      name="infosource")
infosource.iterables = [("subject_id", subject_list)]

# Selectfiles to provide specific scans with in a subject to other functions
selectfiles = eng.Node(
    nio.SelectFiles(templates,
                    base_directory=working_dir,
                    sort_filelist=True,
                    raise_on_empty=True),
    name="SelectFiles",
)
# -------------------------------------------------------

# -----------------------NormalizeNode-------------------
normalize = eng.Node(spm.Normalize12(), name="normalize")
normalize.inputs.write_interp = 7
normalize.inputs.write_voxel_sizes = [1, 1, 1]
# -------------------------------------------------------

# -----------------------Merge---------------------------
merge = eng.Node(utl.Merge(5), name="merge")
merge.ravel_inputs = True
# -------------------------------------------------------

# -----------------------FAST----------------------------
fast = eng.Node(fsl.FAST(), name="fast")
fast.inputs.no_bias = True
fast.inputs.segment_iters = 45
fast.inputs.output_type = "NIFTI"
# -------------------------------------------------------

# -----------------------Merge---------------------------
merge2 = eng.Node(utl.Merge(8), name="merge2")
merge2.ravel_inputs = True
# -------------------------------------------------------

# ------------------------Output-------------------------
# Datasink - creates output folder for important outputs
datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                 container=temp_dir),
                    name="datasink")
# Use the following DataSink output substitutions
substitutions = [("_subject_id_", "sub-")]

subjFolders = [("sub-%s" % (sub), "sub-%s" % (sub)) for sub in subject_list]
substitutions.extend(subjFolders)
datasink.inputs.substitutions = substitutions
# datasink.inputs.regexp_substitutions = [('_coreg_to_postcon.','')]
# -------------------------------------------------------

# -----------------NormalizationWorkflow-----------------
task = "SpatialNormalization"
norm_wf = eng.Workflow(name=task)
norm_wf.base_dir = workflow_dir

norm_wf.connect([(infosource, selectfiles, [("subject_id", "subject_id")])])
norm_wf.connect([(
    selectfiles,
    merge,
    [
        ("nonUTE_postcon", "in1"),
        ("qutece_postcon", "in2"),
        ("nonT1w_precon", "in3"),
        ("T1w_precon_brain_label", "in4"),
        ("T1w_precon", "in5"),
    ],
)])

norm_wf.connect([(selectfiles, normalize, [("T1w_precon_brain",
                                            "image_to_align")])])
norm_wf.connect([(merge, normalize, [("out", "apply_to_files")])])
norm_wf.connect([(
    normalize,
    datasink,
    [
        ("normalized_image", task + "_preconT1w.@con"),
        ("normalized_files", task + "_allOtherScans.@con"),
    ],
)])

norm_wf.connect([
    (selectfiles, fast, [("T1w_precon_brain", "in_files")]),
    (
        fast,
        merge2,
        [
            ("tissue_class_map", "in1"),
            ("tissue_class_files", "in2"),
            ("restored_image", "in3"),
            ("mixeltype", "in4"),
            ("partial_volume_map", "in5"),
            ("partial_volume_files", "in6"),
            ("bias_field", "in7"),
            ("probability_maps", "in8"),
        ],
    ),
])

norm_wf.connect([(merge2, datasink, [("out", task + "_FAST.@con")])])
# -------------------------------------------------------
