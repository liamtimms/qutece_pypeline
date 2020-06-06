# Whole brain CBV Pipeline
# -----------------Imports-------------------------------
import os
import CustomNiPype as cnp
import nipype.pipeline.engine as eng
import nipype.interfaces.fsl as fsl
import nipype.interfaces.ants as ants
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
# -------------------------------------------------------

fsl.FSLCommand.set_default_output_type('NIFTI')


def CBV_WholeBrain_workflow(working_dir, subject_list, num_cores, scan_type):

    # -----------------Inputs--------------------------------
    # Define subject list, session list and relevent file types
    # working_dir = os.path.abspath(
    #    '/run/media/mri/4e43a4f6-7402-4881-bcf5-d280e54cc385/Analysis/DCM2BIDS2')
    output_dir = os.path.join(working_dir, 'derivatives/')
    temp_dir = os.path.join(output_dir, 'datasink/')

    # brain mask
    filestart = 'sub-{subject_id}_ses-Precon'
    subdirectory = os.path.join(output_dir, 'manualwork',
                                'WholeBrainSeg_PostFLIRT')
    brain_mask_files = os.path.join(subdirectory,
                                    '_rrr' + filestart + '*_T1w*-label.nii')

    # blood mask
    subdirectory = os.path.join(output_dir, 'manualwork', 'BloodSeg_fast',
                                'sub-{subject_id}')
    blood_mask_files = os.path.join(subdirectory,
                                    'sub-{subject_id}_*flirt*-label.nii')

    # precon UTE
    scanfolder = 'NormalizationTransform_' + scan_type + '_linear'
    session = 'Precon'
    filestart = 'sub-{subject_id}_ses-' + session + '_'
    fileend = 'UTE_desc-preproc_flirt.nii'
    if scan_type == 'hr':
        fileend = '_UTE_divby_average_bias_reoriented_flirt.nii'

    subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}')
    precon_UTE_files = os.path.join(
        subdirectory, '_rrr' + filestart + '*' + scan_type + '*' + fileend)

    # postcon UTE
    session = 'Postcon'
    subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}')
    filestart = 'sub-{subject_id}_ses-' + session + '_'
    postcon_UTE_files = os.path.join(
        subdirectory, '_r' + filestart + '*' + scan_type + '*' + fileend)

    templates = {
        'brain_mask': brain_mask_files,
        'blood_mask': blood_mask_files,
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

    # -----------------------AverageImages-------------
    average_niis = eng.Node(ants.AverageImages(), name='average_niis')
    average_niis.inputs.dimension = 3
    average_niis.inputs.normalize = False
    # -------------------------------------------------------

    # -----------------------DiffNode-------------------
    difference = eng.MapNode(cnp.DiffNii(),
                             name='difference',
                             iterfield='file2')
    # -------------------------------------------------------

    # --------------ROI_Analyze_WholeBrain-------------------
    roi_analyze_whbrain = eng.MapNode(interface=cnp.ROIAnalyze(),
                                      name='roi_analyze_whbrain',
                                      iterfield=['scan_file'])
    # -------------------------------------------------------

    # -----------------ROI_Analyze_Blood---------------------
    roi_analyze_blood = eng.MapNode(interface=cnp.ROIAnalyze(),
                                    name='roi_analyze_blood',
                                    iterfield=['scan_file'])
    # -------------------------------------------------------

    # -----------------CSV_Concatenate-----------------------
    concat_brain = eng.Node(interface=cnp.CSVConcatenate(),
                            name='concat_brain')
    # -------------------------------------------------------

    # -----------------CSV_Concatenate-----------------------
    concat_blood = eng.Node(interface=cnp.CSVConcatenate(),
                            name='concat_blood')
    # -------------------------------------------------------

    # ----------------------CBV----------------------------
    cbv = eng.Node(interface=cnp.CBVwhBrain(), name='cbv')
    # -------------------------------------------------------

    # ----------------------CBV----------------------------
    cbv_map = eng.MapNode(interface=cnp.CBVmap(),
                          name='cbv_map',
                          iterfield=['difference'])
    # -------------------------------------------------------

    # ------------------------Output-------------------------
    # Datasink - creates output folder for important outputs
    datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                     container=temp_dir),
                        name="datasink")
    # Use the following DataSink output substitutions
    substitutions = [('_subject_id_', 'sub-'), ('_rsub', 'sub'),
                     ('_CBV', '_' + scan_type + '_PostFLIRT_CBV')]

    subjFolders = [('sub-%s' % (sub), 'sub-%s' % (sub))
                   for sub in subject_list]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions
    datasink.inputs.regexp_substitutions = [('_difference.*/', ''),
                                            ('_cbv_map.*/', '')]
    # -------------------------------------------------------

    # -----------------NormalizationWorkflow-----------------
    task = 'CBV_WholeBrain_' + scan_type
    cbv_wf = eng.Workflow(name=task)
    cbv_wf.base_dir = working_dir + '/workflow'

    cbv_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id')]),
        (selectfiles, average_niis, [('precon_UTE', 'images')]),
        (average_niis, difference, [('output_average_image', 'file1')]),
        (selectfiles, difference, [('postcon_UTE', 'file2')]),
        (difference, datasink, [('out_file', task + '_postminuspre.@con')]),
        (difference, roi_analyze_whbrain, [('out_file', 'scan_file')]),
        (selectfiles, roi_analyze_whbrain, [('brain_mask', 'roi_file')]),
        (roi_analyze_whbrain, concat_brain, [('out_file', 'in_files')]),
        (difference, roi_analyze_blood, [('out_file', 'scan_file')]),
        (selectfiles, roi_analyze_blood, [('blood_mask', 'roi_file')]),
        (roi_analyze_blood, concat_blood, [('out_file', 'in_files')]),
        (concat_brain, cbv, [('out_csv', 'in1')]),
        (concat_blood, cbv, [('out_csv', 'in2')]),
        (cbv, datasink, [('out_file', task + '.@con')]),
        (difference, cbv_map, [('out_file', 'difference')]),
        (selectfiles, cbv_map, [('blood_mask', 'blood_mask')]),
        (cbv_map, datasink, [('out_file', task + '_cbvmap.@con')])
    ])
    # -------------------------------------------------------

    # -------------------WorkflowPlotting--------------------
    cbv_wf.write_graph(graph2use='flat')
    # -------------------------------------------------------

    if num_cores < 2:
        cbv_wf.run()
    else:
        cbv_wf.run(plugin='MultiProc', plugin_args={'n_procs': num_cores})
