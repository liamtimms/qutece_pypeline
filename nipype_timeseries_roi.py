# Time series pipeline
# -----------------Imports-------------------------------
import os
import CustomNiPype as cnp
import nipype.pipeline.engine as eng
import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
# -------------------------------------------------------

fsl.FSLCommand.set_default_output_type('NIFTI')


def TimeSeries_ROI_workflow(working_dir, subject_list, session_list, num_cores,
                        scan_type, ROI_type):

    # -----------------Inputs--------------------------------
    # Define fast scan files (grab from flirt)
    # _rsub-02_ses-Postcon_fast-task-rest_run-01_UTE_desc-preproc_maths_flirt.nii
    output_dir = os.path.join(working_dir, 'derivatives/')
    temp_dir = os.path.join(output_dir, 'datasink/')

    # subdirectory = os.path.join(temp_dir, 'NormalizationTransform_fast_linear',
    #                            'sub-{subject_id}', 'ses-{session_id}')
    subdirectory = os.path.join(temp_dir, 'NormalizationTransform_fast_linear',
                                'sub-{subject_id}')
    filestart = 'sub-{subject_id}_ses-{session_id}'
    qutece_fast_files = os.path.join(subdirectory,
                                     '_r' + filestart + '*fast*_run-*[0123456789]_*flirt.nii')

    # Define brain masks
    # rrrsub-02_ses-Precon_T1w_corrected_maths_reoriented_ROI_brain_brain_Segmentation-label.nii
    subdirectory = os.path.join(output_dir, 'manualwork',
                                'WholeBrainSeg_FromNoseSkullStrip')
    ROI_brain_files = os.path.join(subdirectory,
                                    'rrr' + 'sub-{subject_id}' + '*_T1w*-label.nii')


    # Define blood masks
    # sub-02_fast_run-01_blood-flirt-label.nii
    subdirectory = os.path.join(output_dir, 'manualwork', 'BloodSeg_fastscans',
                                'sub-{subject_id}')
    ROI_blood_files = os.path.join(subdirectory,
                                    'sub-{subject_id}_*flirt-label.nii')

    # Choose ROI type
    if ROI_type == 'brain':
        ROI_files = ROI_brain_files
    else:
        ROI_files = ROI_blood_files

    # file name substitutions
    templates = {
        'qutece_fast': qutece_fast_files,
        'ROI': ROI_files
                }

    # Infosource - a function free node to iterate over the list of subject names
    infosource = eng.Node(utl.IdentityInterface(fields=['subject_id','session_id']),
                          name="infosource")
    infosource.iterables = [('subject_id', subject_list),
                            ('session_id', session_list)]

    # Selectfiles to provide specific scans with in a subject to other functions
    selectfiles = eng.Node(nio.SelectFiles(templates,
                                           base_directory=working_dir,
                                           sort_filelist=True,
                                           raise_on_empty=True),
                           name="SelectFiles")

    # --------------------ROI_Analyze------------------------
    roi_analyze_fast = eng.MapNode(interface=cnp.ROIAnalyze(),
                                   name='roi_analyze_fast',
                                   iterfield=['scan_file'])
    # -------------------------------------------------------


    # -----------------CSV_Concatenate-----------------------
    csv_concatenate = eng.Node(interface=cnp.CSVConcatenate(),
                                   name='csv_concatenate')
    # -------------------------------------------------------


    # ------------------------Output-------------------------
    # Datasink - creates output folder for important outputs
    datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                     container=temp_dir),
                        name="datasink")
    # Use the following DataSink output substitutions
    substitutions = [('_subject_id_', 'sub-'), ('_session_id_', 'ses-')]
    subjFolders = [('ses-%ssub-%s' % (ses, sub),
                    ('sub-%s/ses-%s/') % (sub, ses))
                   for ses in session_list for sub in subject_list]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions
    datasink.inputs.regexp_substitutions = [('_roi_analyze_fast.*/', ''),
                                            ('_csv_concatenate.*/', '')]
    # -------------------------------------------------------


    # -----------------TimeSeriesWorkflow--------------------
    task = 'timeseries'
    timeseries_wf = eng.Workflow(name=task, base_dir=working_dir + '/workflow')
    timeseries_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id'),
                                   ('session_id', 'session_id')]),
        (selectfiles, roi_analyze_fast, [('ROI', 'roi_file'),
                                         ('qutece_fast', 'scan_file')]),
        (roi_analyze_fast, datasink, [('out_file', task + '_ROI_analyze.@con')]),
        (roi_analyze_fast, csv_concatenate, [('out_file', 'in_files')]),
        (csv_concatenate, datasink, [('out_csv', task + '_conc_csv.@con'),
                                     ('out_fig', task + '_conc_csv_fig.@con') ])
        ])

    # -------------------WorkflowPlotting--------------------
    timeseries_wf.write_graph(graph2use='flat')

    # -------------------------------------------------------

    if num_cores < 2:
        timeseries_wf.run()
    else:
        timeseries_wf.run(plugin='MultiProc', plugin_args={'n_procs': num_cores})
