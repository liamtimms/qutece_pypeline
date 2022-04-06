# Preprocessing Pipelines
# These are designed to deal with the initial artefact corrections
# and realignment of QUTE-CE scans only
# -----------------Imports-------------------------------
import os
import CustomNiPype as cnp
import glob
import nipype.pipeline.engine as eng
import nipype.interfaces.fsl as fsl
import nipype.interfaces.spm as spm
import nipype.interfaces.ants as ants
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio
# -------------------------------------------------------

fsl.FSLCommand.set_default_output_type('NIFTI')


def preproc(working_dir, subject_list, seqkeyword, scantype):
    output_dir, temp_dir, workflow_dir, _, _ = cnp.set_common_dirs(working_dir)

    substring = 'sub-{subject_id}'
    subdirectory = os.path.join(working_dir, substring)

    scan_files = subdirectory + '/**/**/*' + seqkeyword + '*.nii'

    templates = {
            'scans': scan_files
            }

    # Infosource - a function free node to iterate over the list of subjects
    infosource = eng.Node(
        utl.IdentityInterface(fields=['subject_id']),
        name="infosource")
    infosource.iterables = [('subject_id', subject_list)]

    # Selectfiles to provide specific scans within a subject to other functions
    selectfiles = eng.Node(nio.SelectFiles(templates,
                                           base_directory=working_dir,
                                           sort_filelist=True,
                                           raise_on_empty=True),
                           name="selectfiles")
    # ------------------------------------------------------

    # -----------------------BiasFieldCorrection-------------
    bias_norm = eng.MapNode(ants.N4BiasFieldCorrection(),
                            name='bias_norm',
                            iterfield='input_image')
    bias_norm.inputs.rescale_intensities = True
    bias_norm.inputs.save_bias = True
    bias_norm.inputs.num_threads = 8
    # -------------------------------------------------------

    # -----------------------AverageBiasField----------------
    average_bias = eng.Node(ants.AverageImages(), name='average_bias')
    average_bias.inputs.dimension = 3
    average_bias.inputs.normalize = False
    average_bias.inputs.output_average_image = 'average_bias-' + seqkeyword + '.nii'
    # -------------------------------------------------------

    # ----------------------DivideNii------------------------
    divide_bias = eng.MapNode(interface=cnp.DivNii(),
                                 name='divide_bias',
                                 iterfield=['file1'])
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
    subjFolders = [('sub-%s' % (sub),
                    ('sub-%s/' + scantype) % (sub))
                   for sub in subject_list]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions
    datasink.inputs.regexp_substitutions = [('_bias_norm.*/', ''),
                                            ('_divide_bias.*/', ''),
                                            ('_resample.*/', '')]
    # -------------------------------------------------------

    # -----------------PreprocWorkflow------------------------
    # now we connect all of the nodes.
    task = 'preprocessing'
    preproc_wf = eng.Workflow(name=task, base_dir=workflow_dir)
    preproc_wf.connect([
        (infosource, selectfiles, [('subject_id', 'subject_id')]),
        (selectfiles, bias_norm, [('scans', 'input_image')]),
        (bias_norm, average_bias, [('bias_image', 'images')]),
        (selectfiles, divide_bias, [('scans', 'file1')]),
        (average_bias, divide_bias, [('output_average_image', 'file2')]),
        (bias_norm, merge, [('bias_image', 'in1')]),
        (average_bias, merge, [('output_average_image', 'in2')]),
        (merge, datasink, [('out', task + '_bias.@con')]),
        (divide_bias, datasink, [('out_file', task + '.@con')])
    ])
    # -------------------------------------------------------

    return preproc_wf

