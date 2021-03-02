# Coregistration Pipeline
# -----------------Imports-------------------------------
import os
import CustomNiPype as cnp
import nipype.pipeline.engine as eng
import nipype.interfaces.spm as spm
import nipype.interfaces.ants as ants
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
# -------------------------------------------------------


def intrasession_coregister(working_dir, subject_list, session_list):

    # -----------------Inputs--------------------------------
    output_dir, temp_dir, workflow_dir, _, _ = cnp.set_common_dirs(working_dir)

    filestart = 'sub-{subject_id}_ses-{session_id}'

    # UTE Mean
    scantype = 'qutece'
    subdirectory = os.path.join(temp_dir, 'preprocessing', 'sub-{subject_id}',
                                'ses-{session_id}', scantype)

    qutece_mean_file = os.path.join(subdirectory,
                                    '*mean' + filestart + '*hr_*UTE*.nii')

    scantype = 'anat'
    subdirectory = os.path.join('sub-{subject_id}', 'ses-{session_id}')
    T1w_files = os.path.join(subdirectory, scantype, filestart + '_T1w.nii')
    nonT1w_files = os.path.join(subdirectory, scantype,
                                filestart + '*_[TFS][OLW]*.nii')

    templates = {
        'qutece_mean': qutece_mean_file,
        'T1w': T1w_files,
        'nonT1w': nonT1w_files
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

    # -----------------------AverageImages-------------
    average_niis_hr = eng.Node(ants.AverageImages(), name='average_niis_hr')
    average_niis_hr.inputs.dimension = 3
    average_niis_hr.inputs.normalize = False
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

    # -----------------------CoregisterNodes-----------------
    coreg_to_ute = eng.Node(spm.Coregister(), name='coreg_to_ute')
    coreg_to_ute.inputs.write_interp = 7
    coreg_to_ute.inputs.separation = [6, 3, 2]

    coreg_to_anat = eng.MapNode(spm.Coregister(),
                                name='coreg_to_anat',
                                iterfield='source')
    coreg_to_anat.inputs.write_interp = 7
    coreg_to_anat.inputs.separation = [6, 3, 2]
    # -------------------------------------------------------

    # -----------------------BiasFieldCorrection-------------
    bias_norm = eng.MapNode(ants.N4BiasFieldCorrection(),
                            name='bias_norm',
                            iterfield=['input_image'])
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
    substitutions = [('_subject_id_', 'sub-'), ('_session_id_', 'ses-')]

    subjFolders = [('ses-%ssub-%s' % (ses, sub), 'sub-%s/ses-%s' % (sub, ses))
                   for ses in session_list for sub in subject_list]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions
    datasink.inputs.regexp_substitutions = [('_coreg_to_anat.', ''),
                                            ('_bias_norm.', '')]
    # -------------------------------------------------------

    # -----------------CoregistrationWorkflow----------------
    task = 'intrasession_coregister'
    coreg_wf = eng.Workflow(name=task, base_dir=workflow_dir)

    coreg_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id'),
                                   ('session_id', 'session_id')]),
        (selectfiles, coreg_to_ute, [('qutece_mean', 'target')]),
        (selectfiles, coreg_to_ute, [('T1w', 'source')]),
        (coreg_to_ute, coreg_to_anat, [('coregistered_source', 'target')]),
        (selectfiles, coreg_to_anat, [('nonT1w', 'source')]),
        (coreg_to_ute, merge, [('coregistered_source', 'in1')]),
        (coreg_to_anat, merge, [('coregistered_source', 'in2')]),
        (merge, bias_norm, [('out', 'input_image')]),
        (bias_norm, datasink, [('output_image', task + '.@con')])
    ])
    # -------------------------------------------------------

    return coreg_wf


def intrasession_coregister_onlyT1w(working_dir, subject_list, session_list):

    # -----------------Inputs--------------------------------
    output_dir, temp_dir, workflow_dir, _, _ = cnp.set_common_dirs(working_dir)

    filestart = 'sub-{subject_id}_ses-{session_id}'

    # UTE Mean
    scantype = 'qutece'
    subdirectory = os.path.join(temp_dir, 'preprocessing', 'sub-{subject_id}',
                                'ses-{session_id}', scantype)

    qutece_mean_file = os.path.join(subdirectory,
                                    '*mean' + filestart + '*hr_*UTE*.nii')

    scantype = 'anat'
    subdirectory = os.path.join('sub-{subject_id}', 'ses-{session_id}')
    T1w_files = os.path.join(subdirectory, scantype, filestart + '_T1w.nii')

    templates = {'qutece_mean': qutece_mean_file, 'T1w': T1w_files}

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

    # -----------------------AverageImages-------------
    average_niis_hr = eng.Node(ants.AverageImages(), name='average_niis_hr')
    average_niis_hr.inputs.dimension = 3
    average_niis_hr.inputs.normalize = False
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

    # -----------------------CoregisterNodes-----------------
    coreg_to_ute = eng.Node(spm.Coregister(), name='coreg_to_ute')
    coreg_to_ute.inputs.write_interp = 7
    coreg_to_ute.inputs.separation = [6, 3, 2]
    # -------------------------------------------------------

    # -----------------------BiasFieldCorrection-------------
    bias_norm = eng.MapNode(ants.N4BiasFieldCorrection(),
                            name='bias_norm',
                            iterfield=['input_image'])
    # -------------------------------------------------------

    # ------------------------Output-------------------------
    # Datasink - creates output folder for important outputs
    datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                                     container=temp_dir),
                        name="datasink")
    # Use the following DataSink output substitutions
    substitutions = [('_subject_id_', 'sub-'), ('_session_id_', 'ses-')]

    subjFolders = [('ses-%ssub-%s' % (ses, sub), 'sub-%s/ses-%s' % (sub, ses))
                   for ses in session_list for sub in subject_list]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions
    datasink.inputs.regexp_substitutions = [('_coreg_to_anat.', ''),
                                            ('_bias_norm.', '')]
    # -------------------------------------------------------

    # -----------------CoregistrationWorkflow----------------
    task = 'intrasession_coregister_onlyT1w'
    coreg_wf = eng.Workflow(name=task, base_dir=workflow_dir)

    coreg_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id'),
                                   ('session_id', 'session_id')]),
        (selectfiles, coreg_to_ute, [('qutece_mean', 'target')]),
        (selectfiles, coreg_to_ute, [('T1w', 'source')]),
        (coreg_to_ute, bias_norm, [('coregistered_source', 'input_image')]),
        (bias_norm, datasink, [('output_image',
                                'intrasession_coregister' + '.@con')])
    ])
    # -------------------------------------------------------

    return coreg_wf
