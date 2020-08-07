# Trans Pipeline
# -----------------Imports-------------------------------
import os
import CustomNiPype as cnp
import nipype.pipeline.engine as eng
import nipype.interfaces.fsl as fsl
import nipype.interfaces.spm as spm
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
# -------------------------------------------------------

fsl.FSLCommand.set_default_output_type('NIFTI')

# Want 2 versions, 1 for UTE and one for Non UTE
# UTE version should take option for either hr or fast


def apply_linear_trans(working_dir, subject_list, scan_type):

    # -----------------Inputs--------------------------------
    output_dir = os.path.join(working_dir, 'derivatives/')
    temp_dir = os.path.join(output_dir, 'datasink/')

    fsl_dir = '/opt/fsl/data/standard/'
    MNI_file = os.path.join(fsl_dir, 'MNI152_T1_1mm.nii.gz')
    MNI_brain_file = os.path.join(fsl_dir, 'MNI152_T1_1mm_brain.nii.gz')
    MNI_mask_file = os.path.join(fsl_dir,
                                 'MNI152_T1_1mm_brain_mask_dil.nii.gz')

    filestart = 'sub-{subject_id}_ses-Precon'
    # Transforms
    scanfolder = 'calc_transforms_linear_trans'
    subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}')
    linear_matrix_files = os.path.join(subdirectory,
                                       'rrr' + filestart + '*.mat')

    # * precon T1w from IntersessionCoregister_preconScans
    session = 'Precon'
    filestart = 'sub-{subject_id}_ses-' + session + '_'
    scanfolder = 'pre_to_post_coregister'
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
        'mni_mask': MNI_mask_file,
        'mni_brain': MNI_brain_file,
        'linear_matrix': linear_matrix_files,
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

    # -----------------CropBrainFixNaNs----------------------
    applymask = eng.MapNode(fsl.ApplyMask(),
                            name='applymask',
                            iterfield='in_file')
    applymask.inputs.nan2zeros = True
    applymask.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # -----------------------Merge---------------------------
    merge = eng.Node(utl.Merge(2), name='merge')
    merge.ravel_inputs = True
    # -------------------------------------------------------

    # -----------------LinearTransform--------------------
    apply_linear = eng.MapNode(fsl.ApplyXFM(),
                               name='apply_linear',
                               iterfield=['in_file'])
    apply_linear.inputs.no_resample = True
    # apply_linear.inputs.interp = 'spline'

    apply_linear.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # ----------------------DivideNii------------------------
    plot_dist = eng.Node(interface=cnp.PlotDistribution(), name='plot_dist')
    plot_dist.inputs.plot_xlim_max = 500
    plot_dist.inputs.plot_xlim_min = 10
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
    datasink.inputs.regexp_substitutions = [('_apply_linear.*/', '')]
    # -------------------------------------------------------

    # -----------------NormalizationWorkflow-----------------
    task = 'linear_transfomed_' + scan_type
    trans_wf = eng.Workflow(name=task)
    trans_wf.base_dir = working_dir + '/workflow'

    trans_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id')]),
        (selectfiles, apply_linear, [('mni_brain', 'reference'),
                                     ('linear_matrix', 'in_matrix_file')]),
        (selectfiles, applymask, [('mni_mask', 'mask_file')]),
        (selectfiles, merge, [('postcon_UTE', 'in1'), ('precon_UTE', 'in2')]),
        (merge, maths, [('out', 'in_file')]),
        # (merge, apply_linear, [('out', 'in_file')]),
        (maths, apply_linear, [('out_file', 'in_file')]),
        (apply_linear, datasink, [('out_file', task + '.@con')]),
        (apply_linear, applymask, [('out_file', 'in_file')]),
        (applymask, plot_dist, [('out_file', 'in_files')]),
        (plot_dist, datasink, [('out_fig', task + '_plots.@con')])
    ])
    # -------------------------------------------------------

    return trans_wf


def apply_nonlinear_trans(working_dir, subject_list, session_list, scan_type):

    # -----------------Inputs--------------------------------
    output_dir = os.path.join(working_dir, 'derivatives/')
    temp_dir = os.path.join(output_dir, 'datasink/')

    fsl_dir = '/opt/fsl/data/standard/'
    MNI_file = os.path.join(fsl_dir, 'MNI152_T1_1mm.nii.gz')
    MNI_brain_file = os.path.join(fsl_dir, 'MNI152_T1_1mm_brain.nii.gz')
    MNI_mask_file = os.path.join(fsl_dir,
                                 'MNI152_T1_1mm_brain_mask_dil.nii.gz')

    spm_dir = '/opt/spm12/tpm/'
    SPM_atlas_file = os.path.join(spm_dir, 'labels_Neuromorphometrics.nii')

    filestart = 'sub-{subject_id}_ses-Precon'
    # Transforms
    scanfolder = 'calc_transforms_nonlinear_trans'
    subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}')
    warp_field_files = os.path.join(subdirectory,
                                    'rrr' + filestart + '*_field.nii')

    # * precon T1w from IntersessionCoregister_preconScans
    session = 'Precon'
    filestart = 'sub-{subject_id}_ses-' + session + '_'
    subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}')

    # UTE Files, split into pre and post for easier processing
    scanfolder = 'linear_transfomed_' + scan_type
    subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}')

    filestart = 'sub-{subject_id}_ses-{session_id}'
    UTE_files = os.path.join(subdirectory,
                             'r*' + filestart + '*' + scan_type + '*UTE*.nii')

    templates = {
        'mni_head': MNI_file,
        'mni_mask': MNI_mask_file,
        'mni_brain': MNI_brain_file,
        'spm_atlas': SPM_atlas_file,
        'warp_field': warp_field_files,
        'UTE': UTE_files
    }

    # Infosource - function free node to iterate over the list of subject names
    infosource = eng.Node(
        utl.IdentityInterface(fields=['subject_id', 'session_id']),
        name="infosource")
    infosource.iterables = [('subject_id', subject_list),
                            ('session_id', session_list)]
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

    # -----------------CropBrainFixNaNs----------------------
    applymask = eng.MapNode(fsl.ApplyMask(),
                            name='applymask',
                            iterfield='in_file')
    applymask.inputs.nan2zeros = True
    applymask.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # -----------------LinearTransform--------------------
    apply_nonlinear = eng.MapNode(fsl.ApplyWarp(),
                                  name='apply_nonlinear',
                                  iterfield=['in_file'])

    apply_nonlinear.inputs.interp = 'spline'
    apply_nonlinear.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # ----------------------DivideNii------------------------
    plot_dist = eng.Node(interface=cnp.PlotDistribution(), name='plot_dist')
    plot_dist.inputs.plot_xlim_max = 500
    plot_dist.inputs.plot_xlim_min = 10
    # -------------------------------------------------------

    # --------------SPM_Reslice-------------------
    reslice = eng.MapNode(interface=spm.Reslice(),
                          name='reslice',
                          iterfield=['in_file'])
    # -------------------------------------------------------

    # --------------ROI_Analyze_WholeBrain-------------------
    roi_analyze_region = eng.MapNode(interface=cnp.ROIAnalyze(),
                                     name='roi_analyze_region',
                                     iterfield=['scan_file'])
    # -------------------------------------------------------

    # -----------------CSV_Concatenate-----------------------
    concat_brain = eng.Node(interface=cnp.CSVConcatenate(),
                            name='concat_brain')
    # -------------------------------------------------------

    # ------------------------Output-------------------------
    # Datasink - creates output folder for important outputs
    datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                     container=temp_dir),
                        name="datasink")
    # Use the following DataSink output substitutions
    substitutions = [('_subject_id_', 'sub-'), ('_session_id_', 'ses-'),
                     ('desc-preproc_maths_flirt_maths_warp_ROI-labels_',
                      'desc-processed_')]
    subjFolders = [('ses-%ssub-%s' % (ses, sub),
                    ('sub-%s/ses-%s/') % (sub, ses))
                   for ses in session_list for sub in subject_list]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions
    datasink.inputs.regexp_substitutions = [('_apply_nonlinear.*/', ''),
                                            ('_roi_analyze_region.*/', '')]
    # -------------------------------------------------------

    # -----------------NormalizationWorkflow-----------------
    task = 'nonlinear_transfomed_' + scan_type
    trans_wf = eng.Workflow(name=task)
    trans_wf.base_dir = working_dir + '/workflow'

    trans_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id'),
                                   ('session_id', 'session_id')]),
        (selectfiles, apply_nonlinear, [('mni_brain', 'ref_file'),
                                        ('warp_field', 'field_file')]),
        (selectfiles, maths, [('UTE', 'in_file')]),
        (selectfiles, reslice, [('spm_atlas', 'space_defining')]),
        (selectfiles, applymask, [('mni_mask', 'mask_file')]),
        (maths, apply_nonlinear, [('out_file', 'in_file')]),
        (apply_nonlinear, datasink, [('out_file', task + '.@con')]),
        (apply_nonlinear, applymask, [('out_file', 'in_file')]),
        (applymask, plot_dist, [('out_file', 'in_files')]),
        (apply_nonlinear, reslice, [('out_file', 'in_file')]),
        (selectfiles, roi_analyze_region, [('spm_atlas', 'roi_file')]),
        (reslice, roi_analyze_region, [('out_file', 'scan_file')]),
        (roi_analyze_region, datasink, [('out_file', task + '_csv.@con')]),
        (roi_analyze_region, concat_brain, [('out_file', 'in_files')]),
        (concat_brain, datasink, [('out_csv', task + '_concatcsv.@con')]),
        (concat_brain, datasink, [('out_mean_csv', task + '_meancsv.@con'),
                                  ('out_std_csv', task + '_stdcsv.@con')]),
        (plot_dist, datasink, [('out_fig', task + '_plots.@con')])
    ])
    # -------------------------------------------------------

    return trans_wf
