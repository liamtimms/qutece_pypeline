import os
import CustomNiPype as cnp
from nipype_initial_braincrop import initial_braincrop
from nipype_preproc import preproc
from nipype_preproc_nofast import preproc_nofast
from nipype_preproc_08 import preproc_08
from nipype_preproc_10 import preproc_10
from nipype_intrasession_coregister import intrasession_coregister
from nipype_intrasession_coregister import intrasession_coregister_onlyT1w
from nipype_pre_to_post_coregister import pre_to_post_coregister
from nipype_braincrop import braincrop
from nipype_calc_transforms import calc_transforms
from nipype_post_pre_difference import post_pre_difference
from nipype_apply_transforms import apply_linear_trans
from nipype_apply_transforms import apply_linear_trans_morph
from nipype_apply_transforms import apply_nonlinear_trans
from nipype_tissue_wmh_analysis import tissue_wmh_analysis
from nipype_wm_analysis import wm_analysis
from nipype_vessel_density import vessel_density


def get_preproc_wfs(working_dir):
    session_list = ['Precon', 'Postcon']
    workflow_list = []
    subject_list = []
    # Subjects with both hr and fast scans
    # subject_list = [
    #     '02', '03', '04', '05', '06', '07', '08', '10', '11', '12', '13', '14',
    #     '15'
    # ]
    initial_braincrop_wf = initial_braincrop(working_dir, subject_list,
                                             session_list)
    # workflow_list.append(initial_braincrop_wf)

    # Subjects with all main scan types, pre and post
    # subject_list = ['02', '03', '04', '06', '11', '12', '15']
    preproc_wf = preproc(working_dir, subject_list, session_list)
    # workflow_list.append(preproc_wf)

    # Subjects without Fast Scans
    # subject_list = ['05', '07', '09']
    preproc_nofast_wf = preproc_nofast(working_dir, subject_list, session_list)
    # workflow_list.append(preproc_nofast_wf)

    # Subjects with Fast Scans but only one precon scan
    # subject_list = ['08', '13', '14']
    session_list = ['Postcon']
    preproc_wf = preproc(working_dir, subject_list, session_list)
    # workflow_list.append(preproc_wf)
    session_list = ['Precon']
    preproc_08_wf = preproc_08(working_dir, subject_list, session_list)
    # workflow_list.append(preproc_08_wf)

    # Subject with only one precon scan, also missing Fast
    # subject_list = ['10']
    session_list = ['Precon']
    preproc_10_pre_wf = preproc_10(working_dir, subject_list, session_list)
    # workflow_list.append(preproc_10_pre_wf)

    return workflow_list


def get_coreg_wfs(working_dir):
    subject_list = []
    workflow_list = []

    # # Subjects with nonT1w precon scans
    # subject_list = [
    #   '02', '03', '04', '05', '06', '07', '08', '11', '12', '13', '14', '15'
    # ]
    # # subject_list = ['05', '07', '09']
    # subject_list = ['14']

    session_list = ['Precon']
    coreg_wf = intrasession_coregister(working_dir, subject_list, session_list)
    # workflow_list.append(coreg_wf)

    # # Subjects with nonT1w postcon scans
    # subject_list = ['02', '03', '04', '05', '06', '07', '08', '11']
    # # subject_list = ['05', '07', '09']
    session_list = ['Postcon']
    # coreg_wf = intrasession_coregister(working_dir, subject_list, session_list)
    # workflow_list.append(coreg_wf)

    # Subjects without nonT1w postcon scans
    # subject_list = ['12', '13', '14', '15']
    coreg_wf = intrasession_coregister_onlyT1w(working_dir, subject_list,
                                               session_list)
    # workflow_list.append(coreg_wf)

    # All Coreg'd Subjects
    # subject_list = [
    #     '02', '03', '04', '05', '06', '07', '08', '11', '12', '13', '14', '15'
    # ]
    # # subject_list = ['05', '07', '09']

    # # subject_list = ['02', '03', '04', '06', '11', '12', '15']
    coreg2_wf = pre_to_post_coregister(working_dir, subject_list)
    # workflow_list.append(coreg2_wf)

    braincrop_wf = braincrop(working_dir, subject_list)
    # workflow_list.append(braincrop_wf)
    return workflow_list


def get_norm_wfs(working_dir):
    workflow_list = []
    subject_list = []
    # AT THIS POINT MANUAL MASKS MUST BE COMPLETED ON THE BRAIN CROPPED IMAGES
    # subject_list = ['08', '09', '10']
    # subject_list =['02','03','04', '05', '06', '07', '08', '09', '10', '11']

    # subject_list = ['02', '03', '04', '06', '08', '11', '12', '13', '14', '15']
    calc_transforms_wf = calc_transforms(working_dir, subject_list)
    # workflow_list.append(calc_transforms_wf)

    session_list = ['Precon', 'Postcon']
    scan_type = 'hr'

    apply_transforms_hr_wf = apply_linear_trans(working_dir, subject_list,
                                                scan_type)
    # workflow_list.append(apply_transforms_hr_wf)

    apply_nonlinear_transforms_hr_wf = apply_nonlinear_trans(
        working_dir, subject_list, session_list, scan_type)
    # workflow_list.append(apply_nonlinear_transforms_hr_wf)

    apply_transforms_morph_wf = apply_linear_trans_morph(
        working_dir, subject_list, scan_type)
    workflow_list.append(apply_transforms_morph_wf)

    scan_type = 'fast'
    # apply_transforms_fast_wf = apply_linear_trans(working_dir, subject_list,
    # scan_type)

    scan_type = 'fast'
    apply_transforms_fast_wf = apply_linear_trans(working_dir, subject_list,
                                                  scan_type)
    # workflow_list.append(apply_transforms_fast_wf)

    apply_nonlinear_transforms_fast_wf = apply_nonlinear_trans(
        working_dir, subject_list, session_list, scan_type)
    # workflow_list.append(apply_nonlinear_transforms_fast_wf)

    return workflow_list


def get_proc_wfs(working_dir):
    subject_list = []
    workflow_list = []

    # subject_list = [
    #     '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13',
    #     '14', '15'
    # ]
    diff_wf = post_pre_difference(working_dir,
                                  subject_list,
                                  scan_type='hr',
                                  scanfolder='nonlinear_transfomed_hr')
    # workflow_list.append(diff_wf)

    # subject_list = ['02', '03', '04', '06', '08', '11', '12', '13', '14', '15']
    tissue_wf = tissue_wmh_analysis(working_dir, subject_list)
    # workflow_list.append(tissue_wf)

    # subject_list = ['02', '06', '11']
    wm_wf = wm_analysis(working_dir, subject_list)
    # workflow_list.append(wm_wf)

    # subject_list = [
    #     '02', '03', '04', '05', '06', '07', '08', '11', '12', '13', '14', '15'
    # ]

    density_wf = vessel_density(working_dir, subject_list)
    # workflow_list.append(density_wf)

    return workflow_list


def main():
    # The github repository must be cloned
    upper_dir = os.path.realpath('../../../../')
    working_dir = os.path.abspath(upper_dir)
    print(f"Working BIDS directory is {working_dir}")

    num_cores = 4  # a resonable default

    # Define sections to define whether things have run correctly
    preprocessing = False
    coregister = False
    manual_manipulation = False
    spatial_normalization = True
    manual_masks_good = True
    vesselness_segmented = True
    processing = False
    # Define sections to do define whether things have run correctly
    preprocessing = True
    coregister = True
    manual_manipulation = True
    spatial_normalization = True
    manual_masks_good = True
    vesselness_segmented = True
    processing = True

    if preprocessing:
        print("--- Starting PREPROCESSING ---")
        preproc_workflows = get_preproc_wfs(working_dir)
        for workflow in preproc_workflows:
            cnp.workflow_runner(workflow, num_cores)

    # --------------------------------------------------------------------------
    # Manual manipulation here:
    # * copy sub-09_ses-Postcon_run-03_T1w.nii as sub-09_ses-Postcon_T1w.nii
    # * rename sub-10_ses-Precon_hr_UTE_desc-preproc.nii
    #           to rsub-10_ses-Precon_hr_UTE_desc-preproc.nii
    # * copy rsub-10_ses-Precon_hr_UTE_desc-preproc.nii
    #           as rmeansub-10_ses-Precon_hr_UTE_desc-preproc.nii
    # --------------------------------------------------------------------------

    if coregister and manual_manipulation:
        print("--- Starting COREGISTRATION ---")
        coreg_workflows = get_coreg_wfs(working_dir)
        for workflow in coreg_workflows:
            cnp.workflow_runner(workflow, num_cores)

    # --------------------------------------------------------------------------
    # Manual manipulation here:
    # * Refine all automatic masks, verify manual masks look good
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # Vesselness parameters dicided via vmtk_vesselness_param_explorer.py
    # and final vesselness segmentation should be organized in 'to_use' folder
    # --------------------------------------------------------------------------

    if manual_masks_good and vesselness_segmented:
        if spatial_normalization:
            print("--- Starting NORMALIZATION ---")
            normalization_workflows = get_norm_wfs(working_dir)
            for workflow in normalization_workflows:
                cnp.workflow_runner(workflow, num_cores)

        if processing:
            print("--- Starting PROCESSING ---")
            processing_workflows = get_proc_wfs(working_dir)
            for workflow in processing_workflows:
                cnp.workflow_runner(workflow, num_cores)

    return


if __name__ == "__main__":
    main()
