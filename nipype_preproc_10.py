# Preprocessing Pipeline
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


def preproc_10(working_dir, subject_list, session_list):

    # -----------------Inputs--------------------------------
    output_dir = os.path.join(working_dir, 'derivatives/')
    temp_dir = os.path.join(output_dir, 'datasink/')
    filestart = 'sub-{subject_id}_ses-{session_id}'

    subdirectory = os.path.join('sub-{subject_id}', 'ses-{session_id}')

    scantype = 'qutece'
    qutece_hr_files = os.path.join(subdirectory, scantype,
                                   filestart + '*hr_UTE.nii')

    # biasmask File
    biasmask_dir = os.path.join(
        output_dir, 'manualwork', 'segmentations', 'brain_mask4bias', 'sub-{subject_id}')
    biasmask_hr_file = os.path.join(
        biasmask_dir, '*' + filestart + '*T1w_hr_mask*' + 'Segmentation-label.nii')

    templates = {
        'qutece_hr': qutece_hr_files,
        'biasmask_hr': biasmask_hr_file,
    }

    # Infosource - a function free node to iterate over the list of subjects
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
                           name="selectfiles")
    # -------------------------------------------------------

    # HR
    # -----------------------UnringNode----------------------
    unring_nii_hr = eng.MapNode(interface=cnp.UnringNii(),
                                name='unring_nii_hr',
                                iterfield=['in_file'])
    # -------------------------------------------------------

    # -----------------------AverageImages-------------
    average_niis_hr = eng.Node(ants.AverageImages(), name='average_niis_hr')
    average_niis_hr.inputs.dimension = 3
    average_niis_hr.inputs.normalize = False
    # -------------------------------------------------------

    # -----------------------BiasFieldCorrection-------------
    bias_norm_hr = eng.Node(ants.N4BiasFieldCorrection(),
                               name='bias_norm_hr')
    bias_norm_hr.inputs.bias_image = 'bias_hr.nii'
    bias_norm_hr.inputs.rescale_intensities = True
    # -------------------------------------------------------

    # -----------------BiasFieldRescale----------------------
    bias_scale_hr = eng.Node(interface=cnp.ImageRescale(),
                               name='bias_scale_hr')
    # -------------------------------------------------------

    # ----------------------DivideNii------------------------
    divide_bias_hr = eng.MapNode(interface=cnp.DivNii(),
                                 name='divide_bias_hr',
                                 iterfield=['file1'])
    # -------------------------------------------------------

    # -----------------------Merge---------------------------
    merge = eng.Node(utl.Merge(2), name='merge')
    merge.ravel_inputs = True
    # -------------------------------------------------------

    # ---------------------Reorient----------------------
    reorient = eng.MapNode(fsl.Reorient2Std(),
                           name='reorient',
                           iterfield=['in_file'])
    reorient.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # ------------------------Output-------------------------
    # Datasink - creates output folder for important outputs
    datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                     container=temp_dir),
                        name="datasink")
    # Use the following DataSink output substitutions
    substitutions = [('_subject_id_', 'sub-'), ('_session_id_', 'ses-'),
                     ('divby_bias_hr_rescaled_reoriented',
                      'desc-preproc')]
    subjFolders = [('ses-%ssub-%s' % (ses, sub),
                    ('sub-%s/ses-%s/' + scantype) % (sub, ses))
                   for ses in session_list for sub in subject_list]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions
    datasink.inputs.regexp_substitutions = [('_BiasCorrection.', ''),
                                            ('_bias_norm.*/', ''),
                                            ('_divide_bias.*/', ''),
                                            ('_reorient.*/', '')]
    # -------------------------------------------------------

    # -----------------PreprocWorkflow------------------------
    task = 'preprocessing10'
    preproc_wf = eng.Workflow(name=task, base_dir=working_dir + '/workflow')
    preproc_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id'),
                                   ('session_id', 'session_id')]),
        # hr scan processing
        (selectfiles, unring_nii_hr, [('qutece_hr', 'in_file')]),
        (unring_nii_hr, average_niis_hr, [('out_file', 'images')]),
        (average_niis_hr, bias_norm_hr, [('output_average_image',
                                          'input_image')]),
        (selectfiles, bias_norm_hr, [('biasmask_hr', 'mask_image')]),
        (bias_norm_hr, bias_scale_hr, [('bias_image', 'in_file')]),
        (selectfiles, bias_scale_hr, [('biasmask_hr', 'mask_file')]),
        (selectfiles, divide_bias_hr, [('qutece_hr', 'file1')]),
        (bias_scale_hr, divide_bias_hr, [('out_file', 'file2')]),
        (divide_bias_hr, reorient, [('out_file', 'in_file')]),
        (reorient, datasink, [('out_file', 'preprocessing.@con')]),

        (divide_bias_hr, merge, [('out_file', 'in1')]),
        (bias_scale_hr, merge, [('out_file', 'in2')]),
        (merge, datasink, [('out', 'preprocessing_biascorrection.@con')])

    ])
    # -------------------------------------------------------

    return preproc_wf
