# Vessel Density Pipeline
# -----------------Imports-------------------------------
import os
import CustomNiPype as cnp
import nipype.pipeline.engine as eng
import nipype.interfaces.spm as spm
import nipype.interfaces.fsl as fsl
import nipype.interfaces.ants as ants
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
# -------------------------------------------------------

fsl.FSLCommand.set_default_output_type('NIFTI')


def vessel_density(working_dir, subject_list):

    # -----------------Inputs--------------------------------
    output_dir = os.path.join(working_dir, 'derivatives/')
    temp_dir = os.path.join(output_dir, 'datasink/')

    # Vesselness
    filestart = 'sub-{subject_id}_ses-Postcon'
    subdirectory = os.path.join(output_dir, 'manualwork',
                                'vesselness_filtered_3', 'to_use')
    vesselness_files = os.path.join(subdirectory,
                                    'r' + filestart + '*' + '.nii')
    # brain mask
    brainmask_dir = os.path.join(
        output_dir, 'manualwork', 'segmentations', 'brain_mask4bias', 'sub-{subject_id}')
    brainmask_files = os.path.join(
        brainmask_dir, '*' + filestart + '*T1w_hr_mask*' + 'Segmentation-label.nii')


    templates = {
        'vesselness': vesselness_files,
        'brainmask': brainmask_files
    }

    # Infosource - a function free node to iterate over the list of subjects
    infosource = eng.Node(
        utl.IdentityInterface(fields=['subject_id']),
        name="infosource")
    infosource.iterables = [('subject_id', subject_list)]

    # Selectfiles to provide specific scans within a subject to other functions
    selectfiles = eng.Node(nio.SelectFiles(templates,
                                           base_directory=working_dir,
                                           sort_filelist=True,
                                           raise_on_empty=True),
                           name="selectfiles")
    # -------------------------------------------------------
    # ---------------------FixNANs----------------------
    maths = eng.Node(fsl.maths.MathsCommand(), name='maths')
    maths.inputs.nan2zeros = True
    maths.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # -----------------------ThresholdImage-------------
    threshold = eng.Node(ants.ThresholdImage(),
                            name='threshold')
    threshold.inputs.dimension = 3
    threshold.inputs.th_low = 0.05
    threshold.inputs.th_high = 1
    threshold.inputs.inside_value = 1
    threshold.inputs.outside_value = 0
    # -------------------------------------------------------

    # -----------------------ApplyMask-----------------------
    applymask = eng.Node(fsl.ApplyMask(), name='applymask')
    applymask.inputs.nan2zeros = True
    applymask.inputs.output_type = 'NIFTI'
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
    datasink.inputs.regexp_substitutions = [('_BiasCorrection.', ''),
                                            ('_bias_norm.*/', ''),
                                            ('_reorient.*/', '')]
    # -------------------------------------------------------

    # -----------------PreprocWorkflow------------------------
    task = 'vessel_density'
    density_wf = eng.Workflow(name=task, base_dir=working_dir + '/workflow')
    density_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id')]),
        (selectfiles, maths, [('vesselness', 'in_file')]),
        (maths, threshold, [('out_file', 'input_image')]),
        (threshold, applymask, [('output_image', 'in_file')]),
        (selectfiles, applymask, [('brainmask', 'mask_file')]),
        (applymask, datasink, [('out_file', task + '.@con')])
    ])
    # -------------------------------------------------------

    return density_wf
