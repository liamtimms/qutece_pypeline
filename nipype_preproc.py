# Preprocessing Pipeline
# -----------------Imports-------------------------------
import os
import CustomNiPype as cnp
import nipype.pipeline.engine as eng
import nipype.interfaces.spm as spm
# import nipype.interfaces.freesurfer as fs
# import nipype.interfaces.fsl as fsl
import nipype.interfaces.ants as ants
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
# -------------------------------------------------------

# -----------------Inputs--------------------------------
# Define subject list, session list and relevent file types


def Preproc_workflow(working_dir, subject_list, session_list, num_cores):

    output_dir = os.path.join(working_dir, 'derivatives/')
    temp_dir = os.path.join(output_dir, 'datasink/')

    subdirectory = os.path.join('sub-{subject_id}', 'ses-{session_id}')
    filestart = 'sub-{subject_id}_ses-{session_id}'

    scantype = 'qutece'
    qutece_fast_files = os.path.join(
        subdirectory, scantype, filestart + '*fast*_run-*[0123456789]_UTE.nii')

    qutece_hr_files = os.path.join(
        subdirectory, scantype, filestart + '*hr*_run-*[0123456789]_UTE.nii')

    templates = {
        'qutece_fast': qutece_fast_files,
        'qutece_hr': qutece_hr_files
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

    ### FAST ###
    # -----------------------AverageImages-------------
    average_niis_fast = eng.Node(ants.AverageImages(),
                                 name='average_niis_fast')
    average_niis_fast.inputs.dimension = 3
    average_niis_fast.inputs.normalize = False
    # -------------------------------------------------------

    # -----------------------BiasFieldCorrection-------------
    bias_norm_fast = eng.Node(ants.N4BiasFieldCorrection(),
                              name='bias_norm_fast')
    bias_norm_fast.inputs.save_bias = True
    bias_norm_fast.inputs.rescale_intensities = True
    # -------------------------------------------------------

    # ----------------------DivideNii------------------------
    divide_bias_fast = eng.MapNode(interface=cnp.DivNii(),
                                   name='divide_bias_fast',
                                   iterfield=['file1'])
    # -------------------------------------------------------

    ### HR ####
    # -----------------------AverageImages-------------
    average_niis_hr = eng.Node(ants.AverageImages(), name='average_niis_hr')
    average_niis_hr.inputs.dimension = 3
    average_niis_hr.inputs.normalize = False
    # -------------------------------------------------------

    # -----------------------BiasFieldCorrection-------------
    bias_norm_hr = eng.Node(ants.N4BiasFieldCorrection(), name='bias_norm_hr')
    bias_norm_hr.inputs.save_bias = True
    bias_norm_hr.inputs.rescale_intensities = True
    # -------------------------------------------------------

    # ----------------------DivideNii------------------------
    divide_bias_hr = eng.MapNode(interface=cnp.DivNii(),
                                 name='divide_bias_hr',
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

    ### Merge ###
    # -----------------------Merge---------------------------
    merge = eng.Node(utl.Merge(2), name='merge')
    merge.ravel_inputs = True
    # -------------------------------------------------------
    # -----------------------Merge---------------------------
    merge2 = eng.Node(utl.Merge(2), name='merge2')
    merge2.ravel_inputs = True
    # -------------------------------------------------------

    # -----------------------UnringNode----------------------
    unring_nii = eng.MapNode(interface=cnp.UnringNii(),
                             name='unring_nii',
                             iterfield=['in_file'])
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

    # ------------------------Output-------------------------
    # Datasink - creates output folder for important outputs
    datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                     container=temp_dir),
                        name="datasink")
    # Use the following DataSink output substitutions
    substitutions = [('_subject_id_', 'sub-'), ('_session_id_', 'ses-')]
    subjFolders = [('ses-%ssub-%s' % (ses, sub),
                    ('sub-%s/ses-%s/' + scantype) % (sub, ses))
                   for ses in session_list for sub in subject_list]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions
    datasink.inputs.regexp_substitutions = [('_BiasCorrection.', ''),
                                            ('_bias_norm.*/', '')]
    # -------------------------------------------------------

    # -----------------PreprocWorkflow------------------------
    task = 'preprocessing'
    preproc_wf = eng.Workflow(name=task, base_dir=working_dir + '/workflow')
    preproc_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id'),
                                   ('session_id', 'session_id')]),
        (selectfiles, average_niis_hr, [('qutece_hr', 'images')]),
        (selectfiles, average_niis_fast, [('qutece_fast', 'images')]),
        (average_niis_hr, bias_norm_hr, [('output_average_image',
                                          'input_image')]),
        (selectfiles, divide_bias_hr, [('qutece_hr', 'file1')]),
        (bias_norm_hr, divide_bias_hr, [('bias_image', 'file2')]),
        (bias_norm_hr, datasink, [('bias_image', task + '_hr_BiasField.@con')
                                  ]),
        (divide_bias_hr, realign_hr, [('out_file', 'in_files')]),
        (realign_hr, merge, [('mean_image', 'in1')]),
        (realign_hr, merge2, [('realigned_files', 'in1')]),
        (average_niis_fast, bias_norm_fast, [('output_average_image',
                                              'input_image')]),
        (selectfiles, divide_bias_fast, [('qutece_fast', 'file1')]),
        (bias_norm_fast, divide_bias_fast, [('bias_image', 'file2')]),
        (bias_norm_fast, datasink, [('bias_image',
                                     task + '_fast_BiasField.@con')]),

        # (divide_bias_hr, merge, [('out_file', 'in1')]),
        (divide_bias_fast, merge, [('out_file', 'in2')]),
        (merge, unring_nii, [('out', 'in_file')]),
        (unring_nii, realign, [('out_file', 'in_files')]),
        (realign, merge2, [('realigned_files', 'in2')]),
        (merge2, datasink, [('out', task + '.@con')])
        # ('mean_image', 'realignmean.@con')])
    ])
    # -------------------------------------------------------

    # -------------------WorkflowPlotting--------------------
    preproc_wf.write_graph(graph2use='flat')
    # -------------------------------------------------------

    if num_cores == 1:
        preproc_wf.run()
    else:
        preproc_wf.run(plugin='MultiProc', plugin_args={'n_procs': num_cores})
