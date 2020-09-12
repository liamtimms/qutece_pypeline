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


def preproc(working_dir, subject_list, session_list):

    # -----------------Inputs--------------------------------
    output_dir = os.path.join(working_dir, 'derivatives/')
    temp_dir = os.path.join(output_dir, 'datasink/')
    filestart = 'sub-{subject_id}_ses-{session_id}'

    subdirectory = os.path.join('sub-{subject_id}', 'ses-{session_id}')

    # UTE Files
    scantype = 'qutece'
    qutece_fast_files = os.path.join(
        subdirectory, scantype, filestart + '*fast*_run-*[0123456789]_UTE.nii')

    qutece_hr_files = os.path.join(
        subdirectory, scantype, filestart + '*hr*_run-*[0123456789]_UTE.nii')

    # biasmask File
    biasmask_dir = os.path.join(
        output_dir, 'manualwork', 'segmentations', 'brainmask_4bias', 'sub-{subject_id}')
    biasmask_hr_file = os.path.join(
        biasmask_dir, '*' + filestart + '*T1w_hr_mask*' + 'Segmentation-label.nii')
    biasmask_fast_file = os.path.join(
        biasmask_dir, '*' + filestart + '*T1w_fast_mask*' + 'Segmentation-label.nii')

    templates = {
        'qutece_fast': qutece_fast_files,
        'qutece_hr': qutece_hr_files,
        'biasmask_hr': biasmask_hr_file,
        'biasmask_fast': biasmask_fast_file,
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

    # FAST
    # -----------------------UnringNode----------------------
    unring_nii_fast = eng.MapNode(interface=cnp.UnringNii(),
                                name='unring_nii_fast',
                                iterfield=['in_file'])
    # -------------------------------------------------------

    # -----------------------AverageImages-------------
    average_niis_fast = eng.Node(ants.AverageImages(), name='average_niis_fast')
    average_niis_fast.inputs.dimension = 3
    average_niis_fast.inputs.normalize = False
    # -------------------------------------------------------

    # -----------------------BiasFieldCorrection-------------
    bias_norm_fast = eng.Node(ants.N4BiasFieldCorrection(),
                               name='bias_norm_fast')
    bias_norm_fast.inputs.bias_image = 'bias_fast.nii'
    bias_norm_fast.inputs.rescale_intensities = True
    # -------------------------------------------------------

    # -----------------BiasFieldRescale----------------------
    bias_scale_fast = eng.Node(interface=cnp.ImageRescale(),
                               name='bias_scale_fast')
    # -------------------------------------------------------

    # ----------------------DivideNii------------------------
    divide_bias_fast = eng.MapNode(interface=cnp.DivNii(),
                                 name='divide_bias_fast',
                                 iterfield=['file1'])
    # -------------------------------------------------------


    # ------------------------RealignNode--------------------
    xyz = [0, 1, 0]
    realign_hr = eng.Node(spm.Realign(), name="realign_hr")
    realign_hr.inputs.register_to_mean = True
    realign_hr.inputs.quality = 0.95
    realign_hr.inputs.wrap = xyz
    realign_hr.inputs.write_wrap = xyz
    realign_hr.inputs.interp = 7
    realign_hr.inputs.write_interp = 7
    # -------------------------------------------------------

    # MERGING
    # -----------------------Merge---------------------------
    merge = eng.Node(utl.Merge(4), name='merge')
    merge.ravel_inputs = True
    # -------------------------------------------------------
    # -----------------------Merge---------------------------
    merge2 = eng.Node(utl.Merge(2), name='merge2')
    merge2.ravel_inputs = True
    # -------------------------------------------------------
    # -----------------------Merge---------------------------
    merge3 = eng.Node(utl.Merge(2), name='merge3')
    merge3.ravel_inputs = True
    # -------------------------------------------------------

    # ------------------------RealignNode--------------------
    xyz = [0, 1, 0]
    realign = eng.Node(spm.Realign(), name="realign")
    realign.inputs.register_to_mean = False
    realign.inputs.quality = 0.95
    realign.inputs.wrap = xyz
    realign.inputs.write_wrap = xyz
    realign.inputs.interp = 7
    realign.inputs.write_interp = 7
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
                      'desc-preproc'),
                     ('divby_bias_fast_rescaled_reoriented',
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
    task = 'preprocessing'
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
        (divide_bias_hr, realign_hr, [('out_file', 'in_files')]),
        (realign_hr, merge2, [('mean_image', 'in1')]),
        (realign_hr, merge3, [('realigned_files', 'in1')]),

        # fast scan processing
        (selectfiles, unring_nii_fast, [('qutece_fast', 'in_file')]),
        (unring_nii_fast, average_niis_fast, [('out_file', 'images')]),
        (average_niis_fast, bias_norm_fast, [('output_average_image',
                                          'input_image')]),
        (selectfiles, bias_norm_fast, [('biasmask_fast', 'mask_image')]),
        (bias_norm_fast, bias_scale_fast, [('bias_image', 'in_file')]),
        (selectfiles, bias_scale_fast, [('biasmask_fast', 'mask_file')]),
        (selectfiles, divide_bias_fast, [('qutece_fast', 'file1')]),
        (bias_scale_fast, divide_bias_fast, [('out_file', 'file2')]),
        (divide_bias_fast, merge2, [('out_file', 'in2')]),
        (merge2, realign, [('out', 'in_files')]),
        (realign, merge3, [('realigned_files', 'in2')]),
        (merge3, reorient, [('out', 'in_file')]),
        (reorient, datasink, [('out_file', task + '.@con')]),

        (divide_bias_hr, merge, [('out_file', 'in1')]),
        (bias_scale_hr, merge, [('out_file', 'in2')]),
        (divide_bias_fast, merge, [('out_file', 'in3')]),
        (bias_scale_fast, merge, [('out_file', 'in4')]),
        (merge, datasink, [('out', task + '_biascorrection.@con')]),
    ])
    # -------------------------------------------------------

    return preproc_wf
#
#     # FAST SCANS
#     # -----------------------AverageImages-------------
#     average_niis_fast = eng.Node(ants.AverageImages(),
#                                  name='average_niis_fast')
#     average_niis_fast.inputs.dimension = 3
#     average_niis_fast.inputs.normalize = False
#     # -------------------------------------------------------
#
#     # -----------------------BiasFieldCorrection-------------
#     bias_norm_fast = eng.Node(ants.N4BiasFieldCorrection(),
#                               name='bias_norm_fast')
#     bias_norm_fast.inputs.save_bias = True
#     bias_norm_fast.inputs.rescale_intensities = True
#     # -------------------------------------------------------
#
#     # ----------------------DivideNii------------------------
#     divide_bias_fast = eng.MapNode(interface=cnp.DivNii(),
#                                    name='divide_bias_fast',
#                                    iterfield=['file1'])
#     # -------------------------------------------------------
#
#     # HR SCANS
#     # -----------------------AverageImages-------------
#     average_niis_hr = eng.Node(ants.AverageImages(), name='average_niis_hr')
#     average_niis_hr.inputs.dimension = 3
#     average_niis_hr.inputs.normalize = False
#     # -------------------------------------------------------
#
#     # -----------------------BiasFieldCorrection-------------
#     bias_norm_hr = eng.Node(ants.N4BiasFieldCorrection(), name='bias_norm_hr')
#     bias_norm_hr.inputs.save_bias = True
#     bias_norm_hr.inputs.rescale_intensities = True
#     # -------------------------------------------------------
#
#     # ----------------------DivideNii------------------------
#     divide_bias_hr = eng.MapNode(interface=cnp.DivNii(),
#                                  name='divide_bias_hr',
#                                  iterfield=['file1'])
#     # -------------------------------------------------------
#
#     # ------------------------RealignNode--------------------
#     xyz = [0, 1, 0]
#     realign_hr = eng.Node(spm.Realign(), name="realign_hr")
#     realign_hr.inputs.register_to_mean = True
#     realign_hr.inputs.quality = 0.95
#     realign_hr.inputs.wrap = xyz
#     realign_hr.inputs.write_wrap = xyz
#     realign_hr.inputs.interp = 7
#     realign_hr.inputs.write_interp = 7
#     # -------------------------------------------------------
#
#     # MERGING OF HR AND FAST
#     # -----------------------Merge---------------------------
#     merge = eng.Node(utl.Merge(2), name='merge')
#     merge.ravel_inputs = True
#     # -------------------------------------------------------
#     # -----------------------Merge---------------------------
#     merge2 = eng.Node(utl.Merge(2), name='merge2')
#     merge2.ravel_inputs = True
#     # -------------------------------------------------------
#
#     # FSL
#     # ---------------------FixNANs----------------------
#     maths = eng.MapNode(fsl.maths.MathsCommand(),
#                         name='maths',
#                         iterfield=['in_file'])
#     maths.inputs.nan2zeros = True
#     maths.inputs.output_type = 'NIFTI'
#     # -------------------------------------------------------
#
#     # -----------------------UnringNode----------------------
#     unring_nii = eng.MapNode(interface=cnp.UnringNii(),
#                              name='unring_nii',
#                              iterfield=['in_file'])
#
#     unring_nii_hr = eng.MapNode(interface=cnp.UnringNii(),
#                                 name='unring_nii_hr',
#                                 iterfield=['in_file'])
#     # -------------------------------------------------------
#
#     # ------------------------RealignNode--------------------
#     xyz = [0, 1, 0]
#     realign = eng.Node(spm.Realign(), name="realign")
#     realign.inputs.register_to_mean = False
#     realign.inputs.quality = 0.95
#     realign.inputs.wrap = xyz
#     realign.inputs.write_wrap = xyz
#     realign.inputs.interp = 7
#     realign.inputs.write_interp = 7
#     # -------------------------------------------------------
#
#     # ---------------------Reorient----------------------
#     reorient = eng.MapNode(fsl.Reorient2Std(),
#                            name='reorient',
#                            iterfield=['in_file'])
#     reorient.inputs.output_type = 'NIFTI'
#     # -------------------------------------------------------
#
#     # ------------------------Output-------------------------
#     # Datasink - creates output folder for important outputs
#     datasink = eng.Node(nio.DataSink(base_directory=output_dir,
#                                      container=temp_dir),
#                         name="datasink")
#     # Use the following DataSink output substitutions
#     substitutions = [('_subject_id_', 'sub-'), ('_session_id_', 'ses-'),
#                      ('divby_average_desc-unring_bias_reoriented',
#                       'desc-preproc')]
#     subjFolders = [('ses-%ssub-%s' % (ses, sub),
#                     ('sub-%s/ses-%s/' + scantype) % (sub, ses))
#                    for ses in session_list for sub in subject_list]
#     substitutions.extend(subjFolders)
#     datasink.inputs.substitutions = substitutions
#     datasink.inputs.regexp_substitutions = [('_BiasCorrection.', ''),
#                                             ('_bias_norm.*/', ''),
#                                             ('_reorient.*/', '')]
#     # -------------------------------------------------------
#
#     # -----------------PreprocWorkflow------------------------
#     task = 'preprocessing'
#     preproc_wf = eng.Workflow(name=task, base_dir=working_dir + '/workflow')
#     preproc_wf.connect([
#         (infosource, selectfiles, [('subject_id', 'subject_id'),
#                                    ('session_id', 'session_id')]),
#         (selectfiles, average_niis_hr, [('qutece_hr', 'images')]),
#         (selectfiles, average_niis_fast, [('qutece_fast', 'images')]),
#
#         # hr scan processing
#         (average_niis_hr, bias_norm_hr, [('output_average_image',
#                                           'input_image')]),
#         (selectfiles, divide_bias_hr, [('qutece_hr', 'file1')]),
#         (bias_norm_hr, divide_bias_hr, [('bias_image', 'file2')]),
#         (divide_bias_hr, unring_nii_hr, [('out_file', 'in_file')]),
#         (unring_nii_hr, realign_hr, [('out_file', 'in_files')]),
#         (realign_hr, merge, [('mean_image', 'in1')]),
#         (realign_hr, merge2, [('realigned_files', 'in1')]),
#
#         # fast scan processing
#         (average_niis_fast, bias_norm_fast, [('output_average_image',
#                                               'input_image')]),
#         (selectfiles, divide_bias_fast, [('qutece_fast', 'file1')]),
#         (bias_norm_fast, divide_bias_fast, [('bias_image', 'file2')]),
#         (divide_bias_fast, merge, [('out_file', 'in2')]),
#         (merge, unring_nii, [('out', 'in_file')]),
#         (unring_nii, realign, [('out_file', 'in_files')]),
#         (realign, merge2, [('realigned_files', 'in2')]),
#         (merge2, reorient, [('out', 'in_file')]),
#         (reorient, datasink, [('out_file', task + '.@con')])
#     ])
#     # -------------------------------------------------------
#
#     return preproc_wf
