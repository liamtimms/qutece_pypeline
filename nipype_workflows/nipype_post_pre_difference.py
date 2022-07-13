# Diff Pipeline
# -----------------Imports-------------------------------
import os

import nipype.interfaces.ants as ants
import nipype.interfaces.fsl as fsl
import nipype.interfaces.io as nio
import nipype.interfaces.utility as utl
import nipype.pipeline.engine as eng

import CustomNiPype as cnp

# -------------------------------------------------------

fsl.FSLCommand.set_default_output_type("NIFTI")


def post_pre_difference(working_dir, subject_list, scan_type, scanfolder):

    # -----------------Inputs--------------------------------
    # Define subject list, session list and relevent file types
    # working_dir = os.path.abspath(
    #    '/run/media/mri/4e43a4f6-7402-4881-bcf5-d280e54cc385/Analysis/DCM2BIDS2')
    output_dir, temp_dir, workflow_dir, _, _ = cnp.set_common_dirs(working_dir)

    session = "Precon"
    filestart = "*sub-{subject_id}_ses-" + session + "_"
    subdirectory = os.path.join(temp_dir, scanfolder, "sub-{subject_id}",
                                "ses-" + session)
    precon_UTE_files = os.path.join(subdirectory,
                                    filestart + "*" + scan_type + "*UTE*.nii")

    session = "Postcon"
    subdirectory = os.path.join(temp_dir, scanfolder, "sub-{subject_id}",
                                "ses-" + session)
    filestart = "*sub-{subject_id}_ses-" + session + "_"
    postcon_UTE_files = os.path.join(subdirectory,
                                     filestart + "*" + scan_type + "*UTE*.nii")

    templates = {
        "qutece_pre": precon_UTE_files,
        "qutece_post": postcon_UTE_files
    }

    # Infosource - function free node to iterate over the list of subject names
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

    # -----------------------------AverageImages-------------
    average_niis = eng.Node(ants.AverageImages(), name="average_niis")
    average_niis.inputs.dimension = 3
    average_niis.inputs.normalize = False
    # -------------------------------------------------------

    # -----------------------DiffNode-------------------
    difference = eng.MapNode(cnp.DiffNii(),
                             name="difference",
                             iterfield="file2")
    # difference.iterables =
    # [('file1', ['precon_UTE_files']),
    # ('file2', ['postcon_UTE_files'])] # this is pseudo code not real
    # -------------------------------------------------------

    # -----------------------PNGSlices-----------------------
    scan_slicer = eng.MapNode(fsl.Slicer(),
                              name="scan_slicer",
                              iterfield="in_file")
    scan_slicer.inputs.middle_slices = True
    # scan_slicer.inputs.colour_map = '/opt/fsl/etc/luts/renderhot.lut'
    # -------------------------------------------------------

    # ------------------------Output-------------------------
    # Datasink - creates output folder for important outputs
    datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                     container=temp_dir),
                        name="datasink")
    # Use the following DataSink output substitutions
    substitutions = [("_subject_id_", "sub-")]

    subjFolders = [("sub-%s" % (sub), "sub-%s" % (sub))
                   for sub in subject_list]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions
    datasink.inputs.regexp_substitutions = [
        ("_difference.*/", ""),
        ("_scan_slicer.*/", ""),
    ]
    # -------------------------------------------------------

    # -----------------NormalizationWorkflow-----------------
    task = "postminuspre_" + scan_type
    diff_wf = eng.Workflow(name=task)
    diff_wf.base_dir = workflow_dir

    diff_wf.connect([
        (infosource, selectfiles, [("subject_id", "subject_id")]),
        (selectfiles, average_niis, [("qutece_pre", "images")]),
        (average_niis, difference, [("output_average_image", "file1")]),
        (selectfiles, difference, [("qutece_post", "file2")]),
        (difference, datasink, [("out_file", task + ".@con")]),
        (difference, scan_slicer, [("out_file", "in_file")]),
        (scan_slicer, datasink, [("out_file", task + "_PNG.@con")]),
    ])
    # -------------------------------------------------------

    return diff_wf
