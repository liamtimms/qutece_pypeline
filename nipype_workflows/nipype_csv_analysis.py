# CSV Pipeline
# -----------------Imports-------------------------------
import os

import CustomNiPype as cnp
import nipype.interfaces.fsl as fsl
import nipype.interfaces.io as nio
import nipype.interfaces.spm as spm
import nipype.interfaces.utility as utl
import nipype.pipeline.engine as eng

# -------------------------------------------------------

fsl.FSLCommand.set_default_output_type('NIFTI')


def csv_analyze(working_dir, subject_list, session_list, scan_type):

    # -----------------Inputs--------------------------------
    output_dir, temp_dir, workflow_dir, _, _ = cnp.set_common_dirs(working_dir)

    # UTE Files, split into pre and post for easier processing
    scanfolder = 'nonlinear_transfomed_' + scan_type + '_csv'
    subdirectory = os.path.join(temp_dir, scanfolder, 'sub-{subject_id}')

    filestart = 'sub-{subject_id}_ses-{session_id}'
    UTE_files = os.path.join(subdirectory,
                             '_r*' + filestart + '*' + scan_type + '*UTE*.nii')

    templates = {
        'mni_head': MNI_file,
        'mni_mask': MNI_mask_file,
        'mni_brain': MNI_brain_file,
        'spm_atlas': SPM_atlas_file,
        'warp_field': warp_field_files,
        'UTE': UTE_files
    }

    # Infosource - function free node to iterate over the list of subject names
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
                           name="SelectFiles")
    # -------------------------------------------------------

    # FSL
    # ---------------------FixNANs----------------------
    maths = eng.MapNode(fsl.maths.MathsCommand(),
                        name='maths',
                        iterfield=['in_file'])
    maths.inputs.nan2zeros = True
    maths.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # -----------------CropBrainFixNaNs----------------------
    applymask = eng.MapNode(fsl.ApplyMask(),
                            name='applymask',
                            iterfield='in_file')
    applymask.inputs.nan2zeros = True
    applymask.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # -----------------LinearTransform--------------------
    apply_nonlinear = eng.MapNode(fsl.ApplyWarp(),
                                  name='apply_nonlinear',
                                  iterfield=['in_file'])

    apply_nonlinear.inputs.interp = 'spline'
    apply_nonlinear.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # ----------------------DivideNii------------------------
    plot_dist = eng.Node(interface=cnp.PlotDistribution(), name='plot_dist')
    plot_dist.inputs.plot_xlim_max = 500
    plot_dist.inputs.plot_xlim_min = 10
    # -------------------------------------------------------

    # --------------SPM_Reslice-------------------
    reslice = eng.MapNode(interface=spm.Reslice(),
                          name='reslice',
                          iterfield=['in_file'])
    # -------------------------------------------------------

    # --------------ROI_Analyze_WholeBrain-------------------
    roi_analyze_region = eng.MapNode(interface=cnp.ROIAnalyze(),
                                     name='roi_analyze_region',
                                     iterfield=['scan_file'])
    # -------------------------------------------------------

    # -----------------CSV_Concatenate-----------------------
    concat_brain = eng.Node(interface=cnp.CSVConcatenate(),
                            name='concat_brain')
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
    datasink.inputs.regexp_substitutions = [('apply_nonlinear.*/', ''),
                                            ('_roi_analyze_region.*/', '')]
    # -------------------------------------------------------

    # -----------------NormalizationWorkflow-----------------
    task = 'nonlinear_transfomed_' + scan_type
    trans_wf = eng.Workflow(name=task)
    trans_wf.base_dir = workflow_dir

    trans_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id'),
                                   ('session_id', 'session_id')]),
        (selectfiles, apply_nonlinear, [('mni_brain', 'ref_file'),
                                        ('warp_field', 'field_file')]),
        (selectfiles, maths, [('UTE', 'in_file')]),
        (selectfiles, reslice, [('spm_atlas', 'space_defining')]),
        (selectfiles, applymask, [('mni_mask', 'mask_file')]),
        (maths, apply_nonlinear, [('out_file', 'in_file')]),
        (apply_nonlinear, datasink, [('out_file', task + '.@con')]),
        (apply_nonlinear, applymask, [('out_file', 'in_file')]),
        (applymask, plot_dist, [('out_file', 'in_files')]),
        (apply_nonlinear, reslice, [('out_file', 'in_file')]),
        (selectfiles, roi_analyze_region, [('spm_atlas', 'roi_file')]),
        (reslice, roi_analyze_region, [('out_file', 'scan_file')]),
        (roi_analyze_region, datasink, [('out_file', task + '_csv.@con')]),
        (roi_analyze_region, concat_brain, [('out_file', 'in_files')]),
        (concat_brain, datasink, [('out_csv', task + '_concatcsv.@con')]),
        (concat_brain, datasink, [('out_mean_csv', task + '_meancsv.@con'),
                                  ('out_std_csv', task + '_stdcsv.@con')]),
        (plot_dist, datasink, [('out_fig', task + '_plots.@con')])
    ])
    # -------------------------------------------------------

    return trans_wf
