# Time series pipeline
# -----------------Imports-------------------------------
import os
import CustomNiPype as cnp
import nipype.pipeline.engine as eng
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

    # TODO: figuring out iterations
    qutece_fast_files = os.path.join(subdirectory,
                                     '_r' + filestart + '*fast*_run-*[0123456789]_*flirt.nii')

    # Define brain masks
    # rrrsub-02_ses-Precon_T1w_corrected_maths_reoriented_ROI_brain_brain_Segmentation-label.nii
    subdirectory = os.path.join(output_dir, 'manualwork',
                                'WholeBrainSeg_FromNoseSkullStrip')
    ROI_brain_files = os.path.join(subdirectory,
                                    'rrr' + filestart + '*_T1w*-label.nii')


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

    # -----------------TimeSeriesWorkflow------------------------
    task = 'timeseries'
    timeseries_wf = eng.Workflow(name=task, base_dir=working_dir + '/workflow')
    timeseries_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id'),
                                   ('session_id', 'session_id')]),
    ])
