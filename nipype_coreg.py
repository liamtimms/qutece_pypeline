# Coregistration Pipeline
# -----------------Imports-------------------------------
import os
# import CustomNiPype as cnp
import nipype.pipeline.engine as eng
import nipype.interfaces.spm as spm
import nipype.interfaces.ants as ants
# import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
# -------------------------------------------------------


def IntrasesCoreg_workflow(working_dir, subject_list, session_list, num_cores):

    # -----------------Inputs--------------------------------
    # Define subject list, session list and relevent file types
    # working_dir = os.path.abspath(
    #    '/run/media/mri/4e43a4f6-7402-4881-bcf5-d280e54cc385/Analysis/DCM2BIDS2')
    output_dir = os.path.join(working_dir, 'derivatives/')
    temp_dir = os.path.join(output_dir, 'datasink/')

    filestart = 'sub-{subject_id}_ses-{session_id}'

    scantype = 'qutece'
    subdirectory = os.path.join(temp_dir, 'preprocessing', 'sub-{subject_id}',
                                'ses-{session_id}', scantype)

    qutece_hr_files = os.path.join(subdirectory,
                                   '*mean' + filestart + '*hr_*UTE*.nii')

    # scantype = 'qutece'
    # qutece_fast_files = os.path.join(
    #     subdirectory, scantype, filestart + '*_fast_*.nii')
    #
    # qutece_hr_files = os.path.join(subdirectory, scantype,
    #                               filestart + '*_hr_*.nii')

    scantype = 'anat'
    subdirectory = os.path.join('sub-{subject_id}', 'ses-{session_id}')
    T1w_files = os.path.join(subdirectory, scantype, filestart + '_T1w.nii')
    nonT1w_files = os.path.join(subdirectory, scantype,
                                filestart + '*_[TFS][OLW]*.nii')
    TOF_files = os.path.join(subdirectory, scantype, filestart + '*_TOF*.nii')
    FLAIR_files = os.path.join(subdirectory, scantype,
                               filestart + '*_FLAIR*.nii')
    SWI_files = os.path.join(subdirectory, scantype, filestart + '*_SWI*.nii')

    templates = {
        #   'qutece_fast': qutece_fast_files,
        'qutece_hr': qutece_hr_files,
        'T1w': T1w_files,
        'nonT1w': nonT1w_files
        #    'TOF': TOF_files,
        #    'FLAIR': FLAIR_files,
        #    'SWI': SWI_files
    }
    # Preprocessing and Realignment

    # Infosource - a function free node to iterate over the list of subject names
    infosource = eng.Node(
        utl.IdentityInterface(fields=['subject_id', 'session_id']),
        name="infosource")
    infosource.iterables = [('subject_id', subject_list),
                            ('session_id', session_list)]

    # Selectfiles to provide specific scans with in a subject to other functions
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

    # # -----------------LinearRegistration--------------------
    # flirt = eng.Node(fsl.FLIRT(), name='flirt')
    # flirt.inputs.dof = 6  # Rigid Transform
    # flirt.inputs.output_type = 'NIFTI'
    # # -------------------------------------------------------

    # # -----------------------AntsResgistration---------------
    # ants_reg = eng.Node(ants.Registration(), name='ants_reg')
    # ants_reg.inputs.metric = ['Mattes']*2
    # ants_reg.inputs.metric_weight = [1]*2 # Default (value ignored currently by ANTs)
    # # ants_reg.inputs.number_of_iterations = [[1500, 200], [100, 50, 30]]
    # ants_reg.inputs.shrink_factors = [[2,1], [3,2,1]]
    # ants_reg.inputs.smoothing_sigmas = [[1,0], [2,1,0]]
    # ants_reg.inputs.transforms = ['Rigid', 'Rigid']

    # ants_reg.inputs.transform_parameters = [(2.0,), (0.25, 3.0, 0.0)]
    # ants_reg.inputs.number_of_iterations = [[1500, 200], [100, 50, 30]]
    # # -------------------------------------------------------

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
    # datasink.inputs.regexp_substitutions = []
    # -------------------------------------------------------

    # -----------------CoregistrationWorkflow----------------
    task = 'IntrasessionCoregister'
    coreg_wf = eng.Workflow(name=task)
    coreg_wf.base_dir = working_dir + '/workflow'

    coreg_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id'),
                                   ('session_id', 'session_id')]),
        (selectfiles, coreg_to_ute, [('qutece_hr', 'target')]),
        (selectfiles, coreg_to_ute, [('T1w', 'source')]),
        (coreg_to_ute, coreg_to_anat, [('coregistered_source', 'target')]),
        (selectfiles, coreg_to_anat, [('nonT1w', 'source')]),
        (coreg_to_ute, merge, [('coregistered_source', 'in1')]),
        (coreg_to_anat, merge, [('coregistered_source', 'in2')]),
        (merge, bias_norm, [('out', 'input_image')]),
        (bias_norm, datasink, [('output_image', task + '.@con')])

        # (coreg_to_ute, datasink, [('coregistered_source', task + '_coreg.@con')]),
        # (selectfiles, flirt, [('qutece_hr', 'reference')]),
        # (selectfiles, flirt, [('T1w', 'in_file')]),
        # (flirt, datasink, [('out_file', task + '_flirt.@con')])

        # (selectfiles, ants_reg, [('qutece_hr', 'fixed_image')]),
        # (selectfiles, ants_reg, [('T1w', 'moving_image')]),
        # (ants_reg, datasink, [('warped_image', task + '_ants.@con')])
    ])
    # -------------------------------------------------------

    # -------------------WorkflowPlotting--------------------
    coreg_wf.write_graph(graph2use='flat')
    # -------------------------------------------------------

    if num_cores < 2:
        coreg_wf.run()
    else:
        coreg_wf.run(plugin='MultiProc', plugin_args={'n_procs': num_cores})
