# BrainCrop Pipeline
# -----------------Imports-------------------------------
import os

import nipype.interfaces.fsl as fsl
import nipype.interfaces.io as nio
import nipype.interfaces.utility as utl
import nipype.pipeline.engine as eng

import CustomNiPype as cnp

# -------------------------------------------------------

fsl.FSLCommand.set_default_output_type("NIFTI")


def braincrop(working_dir, subject_list):

    # -----------------Inputs--------------------------------
    output_dir, temp_dir, workflow_dir, _, _ = cnp.set_common_dirs(working_dir)

    subdirectory = os.path.join(temp_dir, "pre_to_post_coregister",
                                "sub-{subject_id}")
    filestart = "sub-{subject_id}_ses-Precon"
    T1w_files = os.path.join(subdirectory, "rrr" + filestart + "*_T1w*.nii")

    templates = {"T1w_precon": T1w_files}

    infosource = eng.Node(utl.IdentityInterface(fields=["subject_id"]),
                          name="infosource")
    infosource.iterables = [("subject_id", subject_list)]

    # Selectfiles to provide specific scans within a subject to other functions
    selectfiles = eng.Node(
        nio.SelectFiles(
            templates,
            base_directory=working_dir,
            sort_filelist=True,
            raise_on_empty=True,
        ),
        name="SelectFiles",
    )
    # -------------------------------------------------------

    # FSL
    # ---------------------FixNANs----------------------
    maths = eng.Node(fsl.maths.MathsCommand(), name="maths")
    maths.inputs.nan2zeros = True
    maths.inputs.output_type = "NIFTI"
    # -------------------------------------------------------

    # ---------------------Reorient----------------------
    reorient = eng.Node(fsl.Reorient2Std(), name="reorient")
    reorient.inputs.output_type = "NIFTI"
    # -------------------------------------------------------

    # -----------------------RobustFOV----------------------
    robustFOV = eng.Node(fsl.RobustFOV(), name="robustFOV")
    robustFOV.inputs.output_type = "NIFTI"
    # -------------------------------------------------------

    # -----------------------NoseStrip----------------------
    nosestrip = eng.Node(fsl.BET(), name="nosestrip")
    nosestrip.inputs.vertical_gradient = 0
    nosestrip.inputs.robust = True
    nosestrip.inputs.output_type = "NIFTI"
    nosestrip.inputs.frac = 0.2
    # -------------------------------------------------------

    # -----------------------SkullStrip----------------------
    skullstrip = eng.Node(fsl.BET(), name="skullstrip")
    skullstrip.inputs.vertical_gradient = -0.5
    skullstrip.inputs.robust = True
    skullstrip.inputs.output_type = "NIFTI"
    skullstrip.inputs.frac = 0.2
    # -------------------------------------------------------

    # ------------------------Output-------------------------
    # Datasink - creates output folder for important outputs
    datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                     container=temp_dir),
                        name="datasink")
    # Use the following DataSink output substitutions
    substitutions = [
        ("_subject_id_", "sub-"),
        ("_corrected_maths_reoriented_ROI_brain_brain",
         "_desc-preproc-braincrop"),
    ]

    subjFolders = [("sub-%s" % (sub), "sub-%s" % (sub))
                   for sub in subject_list]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions
    datasink.inputs.regexp_substitutions = [("_skullstrip*/", "")]
    # -------------------------------------------------------

    # -----------------NormalizationWorkflow-----------------
    task = "braincrop"
    braincrop_wf = eng.Workflow(name=task)
    braincrop_wf.base_dir = workflow_dir

    braincrop_wf.connect([
        (infosource, selectfiles, [("subject_id", "subject_id")]),
        (selectfiles, maths, [("T1w_precon", "in_file")]),
        (maths, reorient, [("out_file", "in_file")]),
        (reorient, robustFOV, [("out_file", "in_file")]),
        (robustFOV, nosestrip, [("out_roi", "in_file")]),
        (nosestrip, skullstrip, [("out_file", "in_file")]),
        (skullstrip, datasink, [("out_file", task + ".@con")]),
    ])
    # -------------------------------------------------------

    return braincrop_wf