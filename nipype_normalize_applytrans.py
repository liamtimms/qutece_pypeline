# Trans Pipeline
# -----------------Imports-------------------------------
import os
import nipype.pipeline.engine as eng
import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
# -------------------------------------------------------

fsl.FSLCommand.set_default_output_type('NIFTI')

# Want 2 versions, 1 for UTE and one for Non UTE
# UTE version should take option for either hr or fast


def apply_linear_trans(working_dir, subject_list, session_list, num_cores,
                       scan_type):

    # -----------------Inputs--------------------------------
    output_dir = os.path.join(working_dir, 'derivatives/')
    temp_dir = os.path.join(output_dir, 'datasink/')

    MNI_file = os.path.abspath('/opt/fsl/data/standard/MNI152_T1_1mm.nii.gz')
    MNI_brain_file = os.path.abspath(
        '/opt/fsl/data/standard/MNI152_T1_1mm_brain.nii.gz')

    # Mask
    filestart = 'sub-{subject_id}_ses-Precon'
    subdirectory = os.path.join(output_dir, 'manualwork',
                                'WholeBrainSeg_FromNoseSkullStrip')
    brain_mask_files = os.path.join(subdirectory,
                                    'rrr' + filestart + '*_T1w*-label.nii')
    # Transforms
    scanfolder = 'SpatialNormalization_SemiAuto_flirt_transform'
    subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}')
    linear_matrix_files = os.path.join(subdirectory,
                                       'rrr' + filestart + '*.mat')

    # * precon T1w from IntersessionCoregister_preconScans
    session = 'Precon'
    filestart = 'sub-{subject_id}_ses-' + session + '_'
    scanfolder = 'IntersessionCoregister_preconScansSPM_SPM'
    subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}')

    precon_UTE_files = os.path.join(
        subdirectory, 'rrr' + filestart + '*' + scan_type + '*UTE*.nii')

    # UTE Files
    session = 'Postcon'
    scanfolder = 'preprocessing'
    subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}',
                                'ses-' + session)
    filestart = 'sub-{subject_id}_ses-' + session + '_'
    postcon_UTE_files = os.path.join(
        subdirectory, 'qutece',
        'r' + filestart + '*' + scan_type + '*UTE*.nii')

    templates = {
        'mni_head': MNI_file,
        'mni_brain': MNI_brain_file,
        'linear_matrix': linear_matrix_files,
        'brain_mask': brain_mask_files,
        'postcon_UTE': postcon_UTE_files,
        'precon_UTE': precon_UTE_files
    }

    # Infosource - function free node to iterate over the list of subject names
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
    maths = eng.MapNode(fsl.maths.MathsCommand(),
                        name='maths',
                        iterfield=['in_file'])
    maths.inputs.nan2zeros = True
    maths.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # ---------------------ApplyMask----------------------
    applymask = eng.MapNode(fsl.ApplyMask(),
                            name='applymask',
                            iterfield=['in_file'])
    applymask.inputs.nan2zeros = True
    applymask.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # -----------------------Merge---------------------------
    merge = eng.Node(utl.Merge(2), name='merge')
    merge.ravel_inputs = True
    # -------------------------------------------------------

    # -----------------------Merge---------------------------
    merge2 = eng.Node(utl.Merge(2), name='merge2')
    merge2.ravel_inputs = True
    # -------------------------------------------------------

    # -----------------LinearTransform--------------------
    apply_linear = eng.MapNode(fsl.ApplyXFM(),
                               name='apply_linear',
                               iterfield=['in_file'])
    apply_linear.inputs.no_resample = True
    # apply_linear.inputs.interp = 'spline'

    apply_linear.inputs.output_type = 'NIFTI'
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
    datasink.inputs.regexp_substitutions = [('apply_linear.*/', '')]
    # -------------------------------------------------------

    # -----------------NormalizationWorkflow-----------------
    task = 'NormalizationTransform_' + scan_type
    trans_wf = eng.Workflow(name=task)
    trans_wf.base_dir = working_dir + '/workflow'

    trans_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id')]),
        (selectfiles, apply_linear, [('mni_brain', 'reference'),
                                     ('linear_matrix', 'in_matrix_file')]),
        (selectfiles, merge, [('postcon_UTE', 'in1'), ('precon_UTE', 'in2')]),
        (selectfiles, applymask, [('brain_mask', 'mask_file')]),
        (merge, applymask, [('out', 'in_file')]),
        (merge, merge2, [('out', 'in1')]),
        (applymask, merge2, [('out_file', 'in2')]),
        (merge2, apply_linear, [('out', 'in_file')]),
        (apply_linear, datasink, [('out_file', task + '_linear.@con')])
    ])
    # -------------------------------------------------------

    return trans_wf
