# Goal: workflow that aligns all scans of the same type within each scan session
# 1. search for scans
# 2. make list of each new type
# 3. go through each type and feed them into a realignment function
# 4. save output

import os
import nipype.pipeline.engine as eng
import nipype.interfaces.spm as spm
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as utl
import nipype.interfaces.io as nio

# must define working_dir
# working_dir =

# Define subject list, session list and relevent file types
subject_list = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11']
session_list = ['Precon', 'Postcon', 'Blood']

subdirectory = os.path.join('sub-{subject_id}', 'ses-{session_id}')
filestart = 'sub-{subject_id}_ses-{session_id}_'

scantype = 'qutece'
qutece_highres_files = os.path.join(subdirectory, scantype,
                                    filestart, '_hr_run*_UTE.nii')
qutece_fast_files = os.path.join(subdirectory, scantype,
                                    filestart, '_fast*_UTE.nii')

scantype = 'anat'
anat_files = os.path.join(subdirectory, scantype,
                                    filestart, '_T1w.nii')
swi_files = os.path.join(subdirectory, scantype,
                                    filestart, '_SWI_angio.nii')

templates = {'qutece-hr': qutece_highres_files,
             'qutece_fast': qutece_fast_files,
             'anat': anat_files,
             'swi': swi_files}

        # 1. search for scans
# Infosource - a function free node to iterate over the list of subject names
infosource = eng.Node(utl.IdentityInterface(fields=['subject_id', 'session_id']),
                  name="infosource")
infosource.iterables = [('subject_id', subject_list),
                        ('session_id', session_list)]


selectfiles = eng.Node(nio.SelectFiles(templates,
                               base_directory=working_dir,
                               sort_filelist=True, raise_on_empty=True),
                   name="selectfiles")

# 2. make list of each new type
# this is done manually right now could be automated but it might actually
# be better to keep it restricted to files you explicitly choose

# 3. realignment function Node

xyz = [0, 1, 0]
intrascan_realign = eng.Node(spm.Realign(), name = "intrascan_realign")
intrascan_realign.register_to_mean = True
intrascan_realign.quality = 0.95
intrascan_realign.wrap = xyz
intrascan_realign.write_wrap = xyz
intrascan_realign.interp = 7
intrascan_realign.write_interp = 7


# 4. save output

# Datasink - creates output folder for important outputs
datasink = eng.Node(nio.DataSink(base_directory=output_dir,
                         container=temp_dir),
                name="datasink")


# Use the following DataSink output substitutions
substitutions = [('_subject_id_', 'sub-'), ('_session_id_', 'ses-')]
subjFolders = [('sub-%s_session_id_%s' % (sub, ses), 'sub-%s/ses-%s' % (sub, ses))
               for ses in session_list
               for sub in subject_list]
substitutions.extend(subjFolders)
datasink.inputs.substitutions = substitutions


# 5 now actually make a Workflow

realign_wf = eng.Workflow(name = 'Intrascan_Realign')
realign_wf.base_dir = working_dir + '/workflow'

realign_wf.connect([(infosource, selectfiles, [('subject_id', 'subject_id'),
                                              ('session_id', 'session_id')]),
                    (selectfiles, intrascan_realign,  [('qutece', 'in_files')])])

realign_wf.connect([(intrascan_realign, datasink,
                     [('realigned_files', 'realign.@con'),
                      ('mean_image', 'realignmean.@con')])])
