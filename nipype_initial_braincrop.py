# BrainCrop Pipeline
# -----------------Imports-------------------------------
import os
import nipype.pipeline.engine as eng
import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
import nipype.interfaces.ants as ants
import nipype.interfaces.spm as spm
# -------------------------------------------------------

fsl.FSLCommand.set_default_output_type('NIFTI')


def initial_braincrop(working_dir, subject_list, session_list, scan_type):

    # -----------------Inputs--------------------------------
    output_dir = os.path.join(working_dir, 'derivatives/')
    temp_dir = os.path.join(output_dir, 'datasink/')
    filestart = 'sub-{subject_id}_ses-{session_id}'

    # T1w Files
    scantype = 'anat'
    subdirectory = os.path.join(working_dir, 'sub-{subject_id}', 'ses-{session_id}')
    T1w_files = os.path.join(subdirectory, scantype, filestart + '_T1w.nii')

    # UTE Files
    scantype = 'qutece'
    subdirectory = os.path.join(working_dir, 'sub-{subject_id}', 'ses-{session_id}')
    qutece_files = os.path.join(
        subdirectory, scantype, filestart + '*' + scan_type + '*_run-*[0123456789]_UTE.nii')

    # for subjects with only one hr scan
    if not os.path.exists(qutece_files):
        qutece_files = os.path.join(
                subdirectory, scantype, filestart + '*' + scan_type + '*UTE.nii')

    templates = {
        'T1w': T1w_files,
        'qutece': qutece_files
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

    # -----------------------AverageImages-------------
    average_niis= eng.Node(ants.AverageImages(),
                                 name='average_niis')
    average_niis.inputs.dimension = 3
    average_niis.inputs.normalize = False
    # -------------------------------------------------------

    # -----------------------CoregisterNodes-----------------
    coreg_to_ute = eng.Node(spm.Coregister(), name='coreg_to_ute')
    coreg_to_ute.inputs.write_interp = 7
    coreg_to_ute.inputs.separation = [6, 3, 2]
    # -------------------------------------------------------

    # FSL
    # ---------------------FixNANs----------------------
    maths = eng.Node(fsl.maths.MathsCommand(), name='maths')
    maths.inputs.nan2zeros = True
    maths.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # ---------------------Reorient----------------------
    reorient = eng.Node(fsl.Reorient2Std(), name='reorient')
    reorient.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # -----------------------RobustFOV----------------------
    robustFOV = eng.Node(fsl.RobustFOV(), name='robustFOV')
    robustFOV.inputs.output_type = 'NIFTI'
    # -------------------------------------------------------

    # -----------------------NoseStrip----------------------
    nosestrip = eng.Node(fsl.BET(), name='nosestrip')
    nosestrip.inputs.vertical_gradient = 0
    nosestrip.inputs.robust = True
    nosestrip.inputs.output_type = 'NIFTI'
    nosestrip.inputs.frac = 0.2
    # -------------------------------------------------------

    # -----------------------SkullStrip----------------------
    skullstrip = eng.Node(fsl.BET(), name='skullstrip')
    skullstrip.inputs.vertical_gradient = -0.5
    skullstrip.inputs.robust = True
    skullstrip.inputs.output_type = 'NIFTI'
    skullstrip.inputs.frac = 0.2
    skullstrip.inputs.mask = True
    # -------------------------------------------------------

    # -----------------------Merge---------------------------
    merge = eng.Node(utl.Merge(2), name='merge')
    merge.ravel_inputs = True
    # -------------------------------------------------------

    # ------------------------Output-------------------------
    # Datasink - creates output folder for important outputs
    datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                     container=temp_dir),
                        name="datasink")
    # Use the following DataSink output substitutions
    substitutions = [('_subject_id_', 'sub-'), ('_session_id_', 'ses-'),
                     ('_corrected_maths_reoriented_ROI_brain_brain',
                      '_desc-preproc-braincrop')]

    subjFolders = [('ses-%ssub-%s' % (ses, sub),
                    ('sub-%s/ses-%s/') % (sub, ses))
                   for ses in session_list for sub in subject_list]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions
    datasink.inputs.regexp_substitutions = [('_skullstrip*/', ''),
                                            ('maths_reoriented_ROI_brain_brain',
                                              scan_type)]
    # -------------------------------------------------------

    # -----------------NormalizationWorkflow-----------------
    task = 'initial_braincrop'
    braincrop_wf = eng.Workflow(name=task)
    braincrop_wf.base_dir = working_dir + '/workflow'

    braincrop_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id'),
                                   ('session_id', 'session_id')]),
        (selectfiles, average_niis, [('qutece', 'images')]),
        (average_niis, coreg_to_ute, [('output_average_image', 'target')]),
        (selectfiles, coreg_to_ute, [('T1w', 'source')]),
        (coreg_to_ute, maths, [('coregistered_source', 'in_file')]),
        (maths, reorient, [('out_file', 'in_file')]),
        (reorient, robustFOV, [('out_file', 'in_file')]),
        (robustFOV, nosestrip, [('out_roi', 'in_file')]),
        (nosestrip, skullstrip, [('out_file', 'in_file')]),
        (skullstrip, merge, [('mask_file', 'in1')]),
        (coreg_to_ute, merge, [('coregistered_source', 'in2')]),
        (merge, datasink, [('out', task + '.@con')])
    ])
    # -------------------------------------------------------

    return braincrop_wf
