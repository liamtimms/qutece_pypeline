# BiasFieldCorrection Pipeline
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


def biascorr(working_dir, subject_list, session_list):

    # -----------------Inputs--------------------------------
    output_dir = os.path.join(working_dir, 'derivatives/')
    temp_dir = os.path.join(output_dir, 'datasink/')
    filestart = 'sub-{subject_id}_ses-{session_id}'

    subdirectory = os.path.join('sub-{subject_id}', 'ses-{session_id}')

    # UTE Files
    scantype = 'qutece'
    # qutece_fast_files = os.path.join(
    #     subdirectory, scantype, filestart + '*fast*_run-*[0123456789]_UTE.nii')

    qutece_hr_files = os.path.join(
        subdirectory, scantype, filestart + '*hr*_run-*[0123456789]_UTE.nii')

    # biasmask file
    brainmask_dir = os.path.join(
        output_dir, 'manual_work', 'segmentations', 'brain_biasmask')
    biasmask_hr_file = os.path.join(
        brainmask_dir, '*' + filestart + '*T1w_hr_mask*' + 'Segmentation-label.nii')
    # biasmask_fast_file = os.path.join(
    #     brainmask_dir, '*' + filestart + '*T1w_fast_mask*' + 'Segmentation-label.nii')

    templates = {
    #     'qutece_fast': qutece_fast_files,
        'qutece_hr': qutece_hr_files,
        'biasmask_hr': biasmask_hr_file,
    #     'biasmask_fast': biasmask_fast_file,
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
    bias_norm_hr.inputs.save_bias = True
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
    # -----------------------Merge---------------------------
    merge2 = eng.Node(utl.Merge(2), name='merge2')
    merge2.ravel_inputs = True
    # -------------------------------------------------------
    # -----------------------Merge---------------------------
    merge3 = eng.Node(utl.Merge(2), name='merge3')
    merge3.ravel_inputs = True
    # -------------------------------------------------------
    # -----------------------Merge---------------------------
    merge4 = eng.Node(utl.Merge(2), name='merge4')
    merge4.ravel_inputs = True
    # -------------------------------------------------------
    # -----------------------Merge---------------------------
    merge5 = eng.Node(utl.Merge(2), name='merge5')
    merge5.ravel_inputs = True
    # -------------------------------------------------------
    # -------------------ApplyMask---------------------------
    applymask_hr = eng.MapNode(fsl.ApplyMask(),
                            name='applymask_hr',
                            iterfield='in_file')
    applymask_hr.inputs.nan2zeros = True
    applymask_hr.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # ----------------------PlotDistribution------------------------
    plot_dist_hr = eng.Node(interface=cnp.PlotDistribution(), name='plot_dist_hr')
    plot_dist_hr.inputs.plot_xlim_max = 500
    plot_dist_hr.inputs.plot_xlim_min = 10
    plot_dist_hr.inputs.plot_bins = 150
    # -------------------------------------------------------

    # ------------------------Output-------------------------
    # Datasink - creates output folder for important outputs
    datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                     container=temp_dir),
                        name="datasink")
    # Use the following DataSink output substitutions
    substitutions = [('_subject_id_', 'sub-'), ('_session_id_', 'ses-'),
                     ('divby_average_desc-unring_bias_reoriented',
                      'desc-preproc'),
                     ('divby_average_desc-unring_desc-unring_bias_reoriented',
                      'desc-preproc')]
    subjFolders = [('ses-%ssub-%s' % (ses, sub),
                    ('sub-%s/ses-%s/' + scantype) % (sub, ses))
                   for ses in session_list for sub in subject_list]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions
    datasink.inputs.regexp_substitutions = [('_BiasCorrection.', ''),
                                            ('_bias_norm.*/', ''),
                                            ('_reorient.*/', '')]
    # -------------------------------------------------------

    # -----------------PreprocWorkflow------------------------
    task = 'biascorrection'
    biascorr_wf = eng.Workflow(name=task, base_dir=working_dir + '/workflow')
    biascorr_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id'),
                                   ('session_id', 'session_id')]),
        (selectfiles, unring_nii_hr, [('qutece_hr', 'in_file')]),

        # hr scan processing
        (unring_nii_hr, average_niis_hr, [('out_file', 'images')]),
        (average_niis_hr, bias_norm_hr, [('output_average_image',
                                          'input_image')]),
        (selectfiles, bias_norm_hr, [('biasmask_hr', 'mask_image')]),
        (bias_norm_hr, bias_scale_hr, [('bias_image', 'in_file')]),
        (selectfiles, bias_scale_hr, [('biasmask_hr', 'mask_file')]),
        (selectfiles, divide_bias_hr, [('qutece_hr', 'file1')]),
        (bias_scale_hr, divide_bias_hr, [('out_file', 'file2')]),
        (divide_bias_hr, merge, [('out_file', 'in1')]),
        (bias_scale_hr, merge, [('out_file', 'in2')]),
        (merge, datasink, [('out', task + '.@con')]),

        # # apply mask and plot distribution before and after bias correction
        (unring_nii_hr, merge3, [('out_file', 'in1')]),
        (divide_bias_hr, merge3, [('out_file', 'in2')]),
        (merge3, applymask_hr, [('out', 'in_file')]),
        (selectfiles, applymask_hr, [('biasmask_hr', 'mask_file')]),
        (applymask_hr, plot_dist_hr, [('out_file', 'in_files')]),
        (plot_dist_hr, datasink, [('out_fig', task + '_plots.@con')])
        # (plot_dist_hr, merge5, [('out_fig', 'in1')]),
        # (selectfiles, applymask_fast, [('biasmask_fast', 'mask_file')]),
        # (selectfiles, merge4, [('qutece_fast', 'in1')]),
        # (divide_bias_fast, merge4, [('out_file', 'in2')]),
        # (merge4, applymask_fast, [('out', 'in_file')]),
        # (applymask_fast, plot_dist_fast, [('out_file', 'in_files')]),
        # (plot_dist_fast, merge5, [('out_fig', 'in2')]),
        # (merge5, datasink, [('out', task + '_plots.@con')])
    ])
    # -------------------------------------------------------

    return biascorr_wf


upper_dir = os.path.realpath('../..')
working_dir = os.path.abspath(upper_dir)
subject_list = ['02', '11']
session_list = ['Precon', 'Postcon']
biascorr_wf = biascorr(working_dir, subject_list, session_list)
biascorr_wf.write_graph(graph2use='flat')
biascorr_wf.run(plugin='MultiProc', plugin_args={'n_procs': 4})
