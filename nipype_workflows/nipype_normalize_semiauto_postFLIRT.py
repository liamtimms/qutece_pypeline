# Nonlinear Transform Calculation Pipeline
# -----------------Imports-------------------------------
import os
import nipype.pipeline.engine as eng
import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio

fsl.FSLCommand.set_default_output_type('NIFTI')

# -------------------------------------------------------


def fnirt_and_fast(working_dir, subject_list):

    # -----------------Inputs--------------------------------
    output_dir, temp_dir, workflow_dir, _, _ = cnp.set_common_dirs(working_dir)

    scantype = 'anat'
    subdirectory = os.path.join(
        temp_dir, 'NormalizationTransform_' + scantype + '_linear',
        'sub-{subject_id}')
    # subdirectory = os.path.join('sub-{subject_id}', 'ses-Precon')
    filestart = 'sub-{subject_id}_ses-Precon'
    T1w_files = os.path.join(subdirectory,
                             '_rrr' + filestart + '_T1w_corrected_flirt.nii')

    subdirectory = os.path.join(output_dir, 'manualwork',
                                'WholeBrainSeg_PostFLIRT')
    brain_mask_files = os.path.join(subdirectory,
                                    '_rrr' + filestart + '*_T1w*-label.nii')

    MNI_file = os.path.abspath('/opt/fsl/data/standard/MNI152_T1_1mm.nii.gz')
    MNI_brain_file = os.path.abspath(
        '/opt/fsl/data/standard/MNI152_T1_1mm_brain.nii.gz')
    MNI_mask_file = os.path.abspath(
        '/opt/fsl/data/standard/MNI152_T1_1mm_brain_mask_dil.nii.gz')

    templates = {
        'T1w_precon': T1w_files,
        'brain_mask': brain_mask_files,
        'mni_head': MNI_file,
        'mni_mask': MNI_mask_file,
        'mni_brain': MNI_brain_file
    }

    infosource = eng.Node(utl.IdentityInterface(fields=['subject_id']),
                          name="infosource")
    infosource.iterables = [('subject_id', subject_list)]

    # Selectfiles to provide specific scans within a subject to other functions
    selectfiles = eng.Node(nio.SelectFiles(templates,
                                           base_directory=working_dir,
                                           sort_filelist=True,
                                           raise_on_empty=True),
                           name="SelectFiles")
    # -------------------------------------------------------

    # FSL
    # ---------------------FixNANs----------------------
    applymask = eng.Node(fsl.ApplyMask(), name='applymask')
    applymask.inputs.nan2zeros = True
    applymask.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # FSL
    # ---------------------FixNANs----------------------
    maths = eng.Node(fsl.maths.MathsCommand(), name='maths')
    maths.inputs.nan2zeros = True
    maths.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # -----------------LinearRegistration--------------------
    flirt = eng.Node(fsl.FLIRT(), name='flirt')
    flirt.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # -----------------NonlinearRegistration--------------------
    fnirt = eng.Node(fsl.FNIRT(), name='fnirt')
    fnirt.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # -----------------------FAST----------------------------
    fast = eng.Node(fsl.FAST(), name='fast')
    fast.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # ----------------------FIRST----------------------------
    first = eng.Node(fsl.FIRST(), name='first')
    first.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # -----------------------Merge---------------------------
    merge_for_png = eng.Node(utl.Merge(6), name='merge_for_png')
    merge_for_png.ravel_inputs = True
    # -------------------------------------------------------

    # -----------------------Merge---------------------------
    merge_FAST = eng.Node(utl.Merge(8), name='merge_FAST')
    merge_FAST.ravel_inputs = True
    # -------------------------------------------------------

    # ----------------------PNGSlicer------------------------
    png_slice = eng.MapNode(fsl.Slicer(),
                            name='png_slice',
                            iterfield=['in_file'])
    png_slice.inputs.middle_slices = True
    # -------------------------------------------------------

    # ------------------------Output-------------------------
    # Datasink - creates output folder for important outputs
    datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                     container=temp_dir),
                        name="datasink")
    # Use the following DataSink output substitutions
    substitutions = [('_subject_id_', 'sub-')]

    subjFolders = [('sub-%s' % (sub), 'sub-%s' % (sub))
                   for sub in subject_list]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions
    datasink.inputs.regexp_substitutions = [('_png_slice.', '')]
    # -------------------------------------------------------

    # -----------------NormalizationWorkflow-----------------
    task = 'SpatialNormalization_SemiAuto_PostFLIRT'
    norm_wf = eng.Workflow(name=task)
    norm_wf.base_dir = workflow_dir

    norm_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id')]),
        # (selectfiles, flirt, [('mni_brain', 'reference')]),
        (selectfiles, maths, [('T1w_precon', 'in_file')]),
        (selectfiles, fnirt, [('mni_head', 'ref_file'),
                              ('mni_mask', 'refmask_file')]),
        (maths, fnirt, [('out_file', 'in_file')]),
        (selectfiles, applymask, [('T1w_precon', 'in_file'),
                                  ('brain_mask', 'mask_file')]),
        (applymask, fast, [('out_file', 'in_files')]),
        # (flirt, fnirt, [('out_file', 'in_file')]),
        # (flirt, datasink, [('out_file', task + '_flirt.@con'),
        #                   ('out_matrix_file', task + '_flirt_transform.@con')
        #                    ]),
        (fnirt, datasink, [('warped_file', task + '_fnirt_dil.@con'),
                           ('field_file', task + '_fnirt_transform.@con')]),
        (fast, merge_FAST, [('bias_field', 'in1'), ('mixeltype', 'in2'),
                            ('partial_volume_files', 'in3'),
                            ('partial_volume_map', 'in4'),
                            ('probability_maps', 'in5'),
                            ('restored_image', 'in6'),
                            ('tissue_class_files', 'in7'),
                            ('tissue_class_map', 'in8')]),
        (merge_FAST, datasink, [('out', task + '_FAST_outs.@con')])
        # (robustFOV, merge_for_png, [('out_roi', 'in1')]),
        # (nosestrip, merge_for_png, [('out_file', 'in2')]),
        # (skullstrip, merge_for_png, [('out_file', 'in')]),
        # (flirt, merge_for_png, [('out_file', 'in4')]),
        # (fnirt, merge_for_png, [('warped_file', 'in5')]),
        # (selectfiles, merge_for_png, [('mni_brain', 'in6')]),
        # (merge_for_png, png_slice, [('out', 'in_file')]),
        # (png_slice, datasink, [('out_file', task + '_pngs.@con')])
    ])
    # -------------------------------------------------------

    return norm_wf
