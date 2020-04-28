# Interscan Coregister Pipeline
# -----------------Imports-------------------------------
import os
# import CustomNiPype as cnp
import nipype.pipeline.engine as eng
import nipype.interfaces.spm as spm
# import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
# -------------------------------------------------------


def IntersesCoreg_workflow(working_dir, subject_list, num_cores):
    # -----------------Inputs--------------------------------
    # Define subject list, session list and relevent file types

    output_dir = os.path.join(working_dir, 'derivatives/')
    temp_dir = os.path.join(output_dir, 'datasink/')

    # * realigned precontrast average
    scantype = 'qutece'
    session = 'Precon'
    subdirectory = os.path.join(temp_dir, 'preprocessing', 'sub-{subject_id}',
                                'ses-' + session, scantype)
    filestart = 'sub-{subject_id}_ses-' + session + '_'
    qutece_mean_precon_file = os.path.join(
        subdirectory, '*mean' + filestart + '*hr*UTE*.nii')

    # * realigned precontrast scans
    subdirectory = os.path.join(temp_dir, 'preprocessing', 'sub-{subject_id}',
                                'ses-' + session, scantype)
    filestart = 'sub-{subject_id}_ses-' + session + '_'
    qutece_precon_files = os.path.join(subdirectory,
                                       'r' + filestart + '*UTE*.nii')

    # * realigned postcontrast average
    session = 'Postcon'
    subdirectory = os.path.join(temp_dir, 'preprocessing', 'sub-{subject_id}',
                                'ses-' + session, scantype)
    filestart = 'sub-{subject_id}_ses-' + session + '_'
    qutece_mean_postcon_file = os.path.join(
        subdirectory, '*mean' + filestart + '*hr*UTE*.nii')

    # directory: '\WorkingBIDS\derivatives\datasink\IntrasessionCoregister_T1w\sub-11\ses-Precon'

    # * precon IntrasessionCoregister_T1w
    scantype = 'anat'
    session = 'Precon'
    subdirectory = os.path.join(temp_dir, 'IntrasessionCoregister',
                                'sub-{subject_id}', 'ses-' + session)
    filestart = 'sub-{subject_id}_ses-' + session + '_'
    anat_files = os.path.join(subdirectory, 'r' + filestart + '*.nii')

    templates = {
        'qutece_precon_mean': qutece_mean_precon_file,
        'qutece_precon': qutece_precon_files,
        'qutece_postcon_mean': qutece_mean_postcon_file,
        'anat': anat_files
    }

    # Infosource - a function free node to iterate over the list of subject names
    infosource = eng.Node(utl.IdentityInterface(fields=['subject_id']),
                          name="infosource")
    infosource.iterables = [('subject_id', subject_list)]

    # Selectfiles to provide specific scans with in a subject to other functions
    selectfiles = eng.Node(nio.SelectFiles(templates,
                                           base_directory=working_dir,
                                           sort_filelist=True,
                                           raise_on_empty=True),
                           name="SelectFiles")
    # -------------------------------------------------------

    # -----------------------CoregisterNodes-----------------
    #coreg_to_postcon = eng.JoinNode(spm.Coregister(), name = 'coreg_to_postcon', joinsource= 'selectfiles', joinfield = 'apply_to_files')
    coreg_to_postcon = eng.Node(spm.Coregister(), name='coreg_to_postcon')
    coreg_to_postcon.inputs.write_interp = 7
    coreg_to_postcon.inputs.separation = [6, 3, 2]

    coreg_to_postcon2 = eng.Node(spm.Coregister(), name='coreg_to_postcon2')
    coreg_to_postcon2.inputs.write_interp = 7
    coreg_to_postcon2.inputs.separation = [6, 3, 2]
    # -------------------------------------------------------

    # -----------------LinearRegistration--------------------
    flirt = eng.Node(fsl.FLIRT(), name='flirt')
    flirt.inputs.dof = 6  # rigid body transform
    flirt.inputs.output_type = 'NIFTI'
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
    substitutions = [('_subject_id_', 'sub-')]

    datasink.inputs.substitutions = substitutions
    # -------------------------------------------------------

    # -----------------CoregistrationWorkflow----------------
    task = 'IntersessionCoregister'
    coreg2_wf = eng.Workflow(name=task)
    coreg2_wf.base_dir = working_dir + '/workflow'

    coreg2_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id')]),
        (selectfiles, merge, [('qutece_precon', 'in1'), ('anat', 'in2')]),
        (selectfiles, coreg_to_postcon, [('qutece_postcon_mean', 'target'),
                                         ('qutece_precon_mean', 'source')]),
        (merge, coreg_to_postcon, [('out', 'apply_to_files')]),
        # (coreg_to_postcon, datasink,
        #  [('coregistered_source', task + '_preconUTEmean.@con'),
        #   ('coregistered_files', task + '_preconScans.@con')]),
        (selectfiles, coreg_to_postcon2, [('qutece_postcon_mean', 'target')]),
        (coreg_to_postcon, coreg_to_postcon2,
         [('coregistered_source', 'source'),
          ('coregistered_files', 'apply_to_files')]),
        (coreg_to_postcon2, datasink,
         [('coregistered_source', task + '_preconUTEmeanSPM_SPM.@con'),
          ('coregistered_files', task + '_preconScansSPM_SPM.@con')]),
    ])
    # -------------------------------------------------------

    # -------------------WorkflowPlotting--------------------
    coreg2_wf.write_graph(graph2use='flat')
    # -------------------------------------------------------

    if num_cores < 2:
        coreg2_wf.run()
    else:
        coreg2_wf.run(plugin='MultiProc', plugin_args={'n_procs': num_cores})
