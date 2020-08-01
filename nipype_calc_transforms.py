# Linear and Nonlinear Calculation Pipeline
# -----------------Imports-------------------------------
import os
import nipype.pipeline.engine as eng
import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio

fsl.FSLCommand.set_default_output_type('NIFTI')

# -------------------------------------------------------


def calc_transforms(working_dir, subject_list):

    # -----------------Inputs--------------------------------
    output_dir = os.path.join(working_dir, 'derivatives/')
    temp_dir = os.path.join(output_dir, 'datasink/')

    session = 'Precon'
    subdirectory = os.path.join(temp_dir, 'pre_to_post_coregister',
                                'sub-{subject_id}')
    # subdirectory = os.path.join('sub-{subject_id}', 'ses-Precon')
    filestart = 'sub-{subject_id}_ses-' + session

    T1w_files = os.path.join(subdirectory, 'rrr' + filestart + '*_T1w*.nii')

    subdirectory = os.path.join(output_dir, 'manualwork', 'segmentations',
                                'brain_preFLIRT')
    brain_mask_files = os.path.join(subdirectory,
                                    'rrr' + filestart + '*_T1w*-label.nii')
    fsl_dir = '/opt/fsl/data/standard/'

    MNI_file = os.path.join(fsl_dir, 'MNI152_T1_1mm.nii.gz')
    MNI_brain_file = os.path.join(fsl_dir, 'MNI152_T1_1mm_brain.nii.gz')
    MNI_mask_file = os.path.join(fsl_dir,
                                 'MNI152_T1_1mm_brain_mask_dil.nii.gz')

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
    # -----------------CropBrainFixNaNs----------------------
    applymask = eng.Node(fsl.ApplyMask(), name='applymask')
    applymask.inputs.nan2zeros = True
    applymask.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # ---------------------FixNANs---------------------------
    maths = eng.Node(fsl.maths.MathsCommand(), name='maths')
    maths.inputs.nan2zeros = True
    maths.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # -----------------LinearRegistration--------------------
    flirt = eng.Node(fsl.FLIRT(), name='flirt')
    flirt.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # ------------------LinearTransform----------------------
    apply_linear = eng.Node(fsl.ApplyXFM(), name='apply_linear')
    apply_linear.inputs.no_resample = True
    apply_linear.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # --------------NonlinearRegistration--------------------
    fnirt = eng.Node(fsl.FNIRT(), name='fnirt')
    fnirt.inputs.field_file = True
    fnirt.inputs.output_type = 'NIFTI'
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
    task = 'calc_transforms'
    norm_wf = eng.Workflow(name=task)
    norm_wf.base_dir = working_dir + '/workflow'

    norm_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id')]),
        (selectfiles, applymask, [('T1w_precon', 'in_file'),
                                  ('brain_mask', 'mask_file')]),
        (selectfiles, flirt, [('mni_brain', 'reference')]),
        (applymask, flirt, [('out_file', 'in_file')]),
        (flirt, datasink, [('out_file', task + '_linear.@con'),
                           ('out_matrix_file', task + '_linear_trans.@con')]),
        (selectfiles, apply_linear, [('mni_brain', 'reference')]),
        (flirt, apply_linear, [('out_matrix_file', 'in_matrix_file')]),
        (selectfiles, maths, [('T1w_precon', 'in_file')]),
        (maths, apply_linear, [('out_file', 'in_file')]),
        (selectfiles, fnirt, [('mni_head', 'ref_file'),
                              ('mni_mask', 'refmask_file')]),
        (apply_linear, fnirt, [('out_file', 'in_file')]),
        (fnirt, datasink, [('warped_file', task + '_nonlinear.@con'),
                           ('field_file', task + '_nonlinear_trans.@con')])
    ])
    # -------------------------------------------------------

    return norm_wf
