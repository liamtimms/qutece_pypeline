# tissue and WMH analysis Pipeline
# -----------------Imports-------------------------------
import os
import CustomNiPype as cnp
import nipype.pipeline.engine as eng
import nipype.interfaces.fsl as fsl
import nipype.interfaces.spm as spm
import nipype.interfaces.ants as ants
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
# -------------------------------------------------------

fsl.FSLCommand.set_default_output_type('NIFTI')


def tissue_wmh_analysis(working_dir, subject_list):

    # -----------------Inputs--------------------------------
    output_dir = os.path.join(working_dir, 'derivatives/')
    temp_dir = os.path.join(output_dir, 'datasink/')

    # UTE precon
    session = 'Precon'
    filestart = 'sub-{subject_id}_ses-' + session + '_'
    scanfolder = 'pre_to_post_coregister'
    subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}')

    precon_UTE_files = os.path.join(
        subdirectory, 'rrr' + filestart + '*' + 'hr' + '*UTE*.nii')

    # UTE postcon
    session = 'Postcon'
    scanfolder = 'preprocessing'
    subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}',
                                'ses-' + session)
    filestart = 'sub-{subject_id}_ses-' + session + '_'
    postcon_UTE_files = os.path.join(
        subdirectory, 'qutece', 'r' + filestart + '*' + 'hr' + '*UTE*.nii')

    # FAST tissue segmentation
    filestart = 'sub-{subject_id}_ses-Precon'
    scanfolder = 'calc_transforms_FAST_outs'
    subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}')
    fast_seg_files = os.path.join(subdirectory,
                                  'rrr' + filestart + '*T1w*' + '_seg.nii')

    # wmh segmentation
    filestart = 'sub-{subject_id}_ses-Precon'
    subdirectory = os.path.join(output_dir, 'manualwork', 'segmentations',
                                'WMH')
    wmh_seg_files = os.path.join(subdirectory,
                                 'rrr' + filestart + '*WMH*' + '.nii')

    # Vesselness
    filestart = 'sub-{subject_id}_ses-Postcon'
    subdirectory = os.path.join(output_dir, 'manualwork',
                                'vesselness_filtered', 'to_use')
    vesselness_files = os.path.join(subdirectory,
                                    'r' + filestart + '*' + '.nii')

    templates = {
        'wmh_seg': wmh_seg_files,
        'fast_seg': fast_seg_files,
        'vesselness': vesselness_files,
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

    # ------------------Combine_Labels-----------------------
    combine_labels_wmh = eng.Node(interface=cnp.CombineLabels(),
                                  name='combine_labels_wmh')
    combine_labels_wmh.inputs.multiplication_factor = 1000
    # -------------------------------------------------------

    # FSL
    # ---------------------FixNANs----------------------
    maths = eng.Node(fsl.maths.MathsCommand(), name='maths')
    maths.inputs.nan2zeros = True
    maths.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # -----------------------ThresholdImage-------------
    threshold = eng.Node(ants.ThresholdImage(), name='threshold')
    threshold.inputs.dimension = 3
    threshold.inputs.th_low = 0.3
    threshold.inputs.th_high = 1
    threshold.inputs.inside_value = 2
    threshold.inputs.outside_value = 1
    # -------------------------------------------------------

    # ------------------Combine_Labels-----------------------
    combine_labels_vesselness = eng.Node(interface=cnp.CombineLabels(),
                                         name='combine_labels_vesselness')
    combine_labels_vesselness.inputs.multiplication_factor = 10000
    # -------------------------------------------------------

    # -------------------ROI_Analyze-------------------------
    roi_analyze = eng.MapNode(interface=cnp.ROIAnalyze(),
                              name='roi_analyze',
                              iterfield=['scan_file'])
    # -------------------------------------------------------

    # -----------------CSV_Concatenate-----------------------
    concat = eng.Node(interface=cnp.CSVConcatenate(), name='concat')
    # -------------------------------------------------------

    # ------------------------Output-------------------------
    # Datasink - creates output folder for important outputs
    datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                     container=temp_dir),
                        name="datasink")
    # Use the following DataSink output substitutions
    substitutions = [('_subject_id_', 'sub-'),
                     ('T1w_corrected_masked_seg', 'tissue-segmentation')]
    subjFolders = [('sub-%s' % (sub), 'sub-%s' % (sub))
                   for sub in subject_list]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions
    datasink.inputs.regexp_substitutions = [
        ('_roi_analyze.*/', ''),
        ('ROI-rrrsub-..-Precon_tissue-segmentation-ADD-rrrsub-..-Precon_WMHs-segmentation-ADD-rsub-..-Postcon_hr_run-..-preproc_AutoVesselness_sblobs=25_splates=25_maths_resampled',
         'segment-tissue-WMH-Vesselness_stats')
    ]

    # -------------------------------------------------------

    # -----------------NormalizationWorkflow-----------------
    task = 'tissue_wmh_analysis'
    tissue_wf = eng.Workflow(name=task)
    tissue_wf.base_dir = working_dir + '/workflow'

    tissue_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id')]),
        (selectfiles, merge, [('precon_UTE', 'in1')]),
        (selectfiles, merge, [('postcon_UTE', 'in2')]),
        (selectfiles, maths, [('vesselness', 'in_file')]),
        (maths, threshold, [('out_file', 'input_image')]),
        (selectfiles, combine_labels_wmh, [('fast_seg', 'in_file_fixed'),
                                           ('wmh_seg', 'in_file_modifier')]),
        (combine_labels_wmh, combine_labels_vesselness, [('out_file',
                                                          'in_file_fixed')]),
        (threshold, combine_labels_vesselness, [('output_image',
                                                 'in_file_modifier')]),
        (combine_labels_vesselness, roi_analyze, [('out_file', 'roi_file')]),
        (merge, roi_analyze, [('out', 'scan_file')]),
        (roi_analyze, datasink, [('out_file', task + '_csv.@con')])
    ])
    # -------------------------------------------------------

    return tissue_wf
