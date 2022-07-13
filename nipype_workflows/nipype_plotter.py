# -----------------Imports-------------------------------
import os

import nipype.interfaces.fsl as fsl
import nipype.interfaces.io as nio
import nipype.interfaces.utility as utl
import nipype.pipeline.engine as eng

import CustomNiPype as cnp

# -------------------------------------------------------

fsl.FSLCommand.set_default_output_type("NIFTI")


def plots(working_dir, subject_list, scan_type):

    # -----------------Inputs--------------------------------
    output_dir, temp_dir, workflow_dir, fsl_dir, _ = cnp.set_common_dirs(
        working_dir)

    MNI_file = os.path.join(fsl_dir, "MNI152_T1_1mm.nii.gz")
    MNI_brain_file = os.path.join(fsl_dir, "MNI152_T1_1mm_brain.nii.gz")
    MNI_mask_file = os.path.join(fsl_dir,
                                 "MNI152_T1_1mm_brain_mask_dil.nii.gz")

    filestart = "sub-{subject_id}_ses-Precon"
    # Transforms
    scanfolder = "calc_transforms_linear_trans"
    subdirectory = os.path.join(temp_dir, scanfolder, "sub-{subject_id}")
    linear_matrix_files = os.path.join(subdirectory,
                                       "rrr" + filestart + "*.mat")

    # * precon T1w from IntersessionCoregister_preconScans
    session = "Precon"
    filestart = "sub-{subject_id}_ses-" + session + "_"
    scanfolder = "pre_to_post_coregister"
    subdirectory = os.path.join(temp_dir, scanfolder, "sub-{subject_id}")

    precon_UTE_files = os.path.join(
        subdirectory, "rrr" + filestart + "*" + scan_type + "*UTE*.nii")

    # UTE Files
    session = "Postcon"
    scanfolder = "preprocessing"
    subdirectory = os.path.join(temp_dir, scanfolder, "sub-{subject_id}",
                                "ses-" + session)
    filestart = "sub-{subject_id}_ses-" + session + "_"
    postcon_UTE_files = os.path.join(
        subdirectory, "qutece",
        "r" + filestart + "*" + scan_type + "*UTE*.nii")

    # FAST tissue segmentation
    filestart = "sub-{subject_id}_ses-Precon"
    scanfolder = "calc_transforms_FAST_outs"
    subdirectory = os.path.join(temp_dir, scanfolder, "sub-{subject_id}")
    fast_seg_files = os.path.join(subdirectory,
                                  "rrr" + filestart + "*T1w*" + "_seg.nii")

    # wmh segmentation
    filestart = "sub-{subject_id}_ses-Precon"
    subdirectory = os.path.join(output_dir, "manualwork", "segmentations",
                                "WMH")
    wmh_seg_files = os.path.join(subdirectory,
                                 "rrr" + filestart + "*WMH*" + ".nii")

    # Vesselness
    filestart = "sub-{subject_id}_ses-Postcon"
    subdirectory = os.path.join(output_dir, "manualwork",
                                "vesselness_filtered", "to_use")
    vesselness_files = os.path.join(subdirectory,
                                    "r" + filestart + "*" + ".nii")

    templates = {
        "mni_head": MNI_file,
        "mni_mask": MNI_mask_file,
        "mni_brain": MNI_brain_file,
        "noise_seg": noise_seg_files,
        "wmh_seg": wmh_seg_files,
        "fast_seg": fast_seg_files,
        "vesselness": vesselness_files,
        "postcon_UTE": postcon_UTE_files,
        "precon_UTE": precon_UTE_files,
        "warped_postcon_UTE": warped_postcon_UTE_files,
        "warped_precon_UTE": warped_precon_UTE_files,
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

    # -----------------------ThresholdImage-------------
    threshold = eng.Node(ants.ThresholdImage(), name="threshold")
    threshold.inputs.dimension = 3
    threshold.inputs.th_low = 0.3
    threshold.inputs.th_high = 1
    threshold.inputs.inside_value = 2
    threshold.inputs.outside_value = 1
    # -------------------------------------------------------

    # -----------------CropBrainFixNaNs----------------------
    applymask = eng.MapNode(fsl.ApplyMask(),
                            name="applymask",
                            iterfield="in_file")
    applymask.inputs.nan2zeros = True
    applymask.inputs.output_type = "NIFTI"
    # -------------------------------------------------------

    # --------------ROI_Analyze_WholeBrain-------------------
    roi_analyze_region = eng.MapNode(interface=cnp.ROIAnalyze(),
                                     name="roi_analyze_region",
                                     iterfield=["scan_file"])
    # -------------------------------------------------------

    # -----------------CSV_Concatenate-----------------------
    concat = eng.Node(interface=cnp.CSVConcatenate(), name="concat")
    # -------------------------------------------------------

    # ----------------------DivideNii------------------------
    plot_dist = eng.Node(interface=cnp.PlotDistribution(), name="plot_dist")
    plot_dist.inputs.plot_xlim_max = 500
    plot_dist.inputs.plot_xlim_min = 10
    plot_dist.inputs.plot_bins = 1000
    # -------------------------------------------------------

    # ------------------------Output-------------------------
    # Datasink - creates output folder for important outputs
    datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                     container=temp_dir),
                        name="datasink")
    # Use the following DataSink output substitutions
    substitutions = [
        ("_subject_id_", "sub-"),
        ("ses-Precon_T1w_corrected_masked_seg-ADD", "tissue"),
        ("ses-Precon_WMHs-segmentation-ADD", "WMH"),
        (
            "ses-Postcon_hr_run-01_UTE_desc-preproc_AutoVesselness_sblobs=25_splates=25_maths_resampled",
            "vesselness",
        ),
    ]
    subjFolders = [("sub-%s" % (sub), "sub-%s" % (sub))
                   for sub in subject_list]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions
    datasink.inputs.regexp_substitutions = [("_roi_analyze.*/", "")]

    # -------------------------------------------------------

    # -----------------NormalizationWorkflow-----------------
    task = "plotting"
    plotting_wf = eng.Workflow(name=task)
    plotting_wf.base_dir = workflow_dir

    plotting_wf.connect([
        (infosource, selectfiles, [("subject_id", "subject_id")]),
        (selectfiles, merge, [("precon_UTE", "in1")]),
        (selectfiles, merge, [("postcon_UTE", "in2")]),
        (selectfiles, maths, [("vesselness", "in_file")]),
        (maths, threshold, [("out_file", "input_image")]),
        (
            selectfiles,
            combine_labels_wmh,
            [("fast_seg", "in_file_fixed"), ("wmh_seg", "in_file_modifier")],
        ),
        (
            combine_labels_wmh,
            combine_labels_vesselness,
            [("out_file", "in_file_fixed")],
        ),
        (
            threshold,
            combine_labels_vesselness,
            [("output_image", "in_file_modifier")],
        ),
        (combine_labels_vesselness, roi_analyze, [("out_file", "roi_file")]),
        (merge, roi_analyze, [("out", "scan_file")]),
        (roi_analyze, datasink, [("out_file", task + "_csv.@con")]),
        (threshold, datasink, [("output_image", "vesselness_threshold.@con")]),
    ])
    # -------------------------------------------------------

    return plotter_wf
