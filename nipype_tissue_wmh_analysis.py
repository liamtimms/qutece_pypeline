# tissue and WMH analysis Pipeline
# -----------------Imports-------------------------------
import os
import CustomNiPype as cnp
import nipype.pipeline.engine as eng
import nipype.interfaces.fsl as fsl
import nipype.interfaces.spm as spm
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
        subdirectory, 'qutece',
        'r' + filestart + '*' + 'hr' + '*UTE*.nii')

    # FAST tissue segmentation
    filestart = 'sub-{subject_id}_ses-Precon'
    scanfolder = 'calc_transforms_FAST_outs'
    subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}')
    fast_seg_files = os.path.join(
        subdirectory, 'rrr' + filestart + '*T1w*' + '_seg.nii')

    # wmh segmentation
    filestart = 'sub-{subject_id}_ses-Precon'
    subdirectory = os.path.join(
        output_dir, 'manualwork', 'segmentations', 'WMH')
    wmh_seg_files = os.path.join(
        subdirectory, 'rrr' + filestart + '*WMH*' + '.nii')

    templates = {
        'wmh_seg': wmh_seg_files,
        'fast_seg': fast_seg_files,
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

    # -------------------ROI_Analyze-------------------------
    roi_analyze_tissue = eng.MapNode(interface=cnp.ROIAnalyze(),
                                     name='roi_analyze_tissue',
                                     iterfield=['scan_file'])
    # -------------------------------------------------------

    # -------------------ROI_Analyze-------------------------
    roi_analyze_wmh = eng.MapNode(interface=cnp.ROIAnalyze(),
                                     name='roi_analyze_wmh',
                                     iterfield=['scan_file'])
    # -------------------------------------------------------

    # -----------------CSV_Concatenate-----------------------
    concat_tissue = eng.Node(interface=cnp.CSVConcatenate(),
                            name='concat_tissue')
    # -------------------------------------------------------

    # -----------------CSV_Concatenate-----------------------
    concat_wmh = eng.Node(interface=cnp.CSVConcatenate(),
                            name='concat_wmh')
    # -------------------------------------------------------

    # ------------------------Output-------------------------
    # Datasink - creates output folder for important outputs
    datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                     container=temp_dir),
                        name="datasink")
    # Use the following DataSink output substitutions
    substitutions = [('_subject_id_', 'sub-'),
                     ('desc-preproc_maths_flirt_maths_warp_ROI-labels_',
                      'desc-processed_')]
    subjFolders = [('sub-%s' % (sub), 'sub-%s' % (sub))
                   for sub in subject_list]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions
    datasink.inputs.regexp_substitutions = [('_roi_analyze_tissue.*/', ''),
                                            ('_roi_analyze_wmh.*/', '')]
    # -------------------------------------------------------

    # -----------------NormalizationWorkflow-----------------
    task = 'tissue_wmh_analysis'
    tissue_wf = eng.Workflow(name=task)
    tissue_wf.base_dir = working_dir + '/workflow'

    tissue_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id')]),
        (selectfiles, merge, [('precon_UTE', 'in1')]),
        (selectfiles, merge, [('postcon_UTE', 'in2')]),
        (selectfiles, roi_analyze_tissue, [('fast_seg', 'roi_file')]),
        (merge, roi_analyze_tissue, [('out', 'scan_file')]),
        (selectfiles, roi_analyze_wmh, [('wmh_seg', 'roi_file')]),
        (merge, roi_analyze_wmh, [('out', 'scan_file')]),

        (roi_analyze_tissue, merge2, [('out_file', 'in1')]),
        (roi_analyze_wmh, merge2, [('out_file', 'in2')]),
        # (roi_analyze_tissue, concat_tissue, [('out_file', 'in_files')]),
        # (roi_analyze_wmh, concat_wmh, [('out_file', 'in_files')]),
        # (concat_tissue, merge3, [('out_csv', 'in1')]),
        # (concat_wmh, merge3, [('out_csv', 'in2')]),
        (merge2, datasink, [('out', task + '_csv.@con')])
        # (merge3, datasink, [('out', task + '_concatcsv.@con')])
    ])
    # -------------------------------------------------------

    return tissue_wf
