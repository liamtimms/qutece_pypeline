from nipype.interfaces.matlab import MatlabCommand
from nipype.interfaces.base import TraitedSpec, \
    BaseInterface, BaseInterfaceInputSpec, File
import os
from string import Template
import re
import numpy as np
import nibabel as nib

class UnringNiiInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True)

class UnringNiiOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc = 'the unringed file')


class UnringNii(BaseInterface):
    input_spec = UnringNiiInputSpec
    output_spec = UnringNiiOutputSpec

    def _run_interface(self, runtime):
        in_file_name = self.inputs.in_file
        
        out_file_name = in_file_name.split('_')
        out_file_name.insert(-1, 'desc-unring')
        out_file_name = '_'.join(out_file_name)
        setattr(self, '_out_file', out_file_name) 
        d = dict(in_file=self.inputs.in_file,
                 out_file=out_file_name)
        
        # This is your MATLAB code template
        script = Template("""in_file = '$in_file';
                             out_file = '$out_file';
                             Unring_Nii(in_file, out_file);
                             exit;
                          """).substitute(d)

        # mfile = True  will create an .m file with your script and executed.
        # Alternatively
        # mfile can be set to False which will cause the matlab code to be
        # passed
        # as a commandline argument to the matlab executable
        # (without creating any files).
        # This, however, is less reliable and harder to debug
        # (code will be reduced to
        # a single line and stripped of any comments).
        mlab = MatlabCommand(script=script, mfile=False)
        result = mlab.run()
        return result.runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = getattr(self, '_out_file')
        return outputs


class CBVInputSpec(BaseInterfaceInputSpec):
    precon_file = File(exists=True, mandatory=True)
    postcon_file = File(exists=True, mandatory=True)
    mask_file = File(exists=True, mandatory=True)


class CBVOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc = 'CBV calculation')

class CBVcalc(BaseInterface):
    input_spec = CBVInputSpec
    output_spec = CBVOutputSpec

    def _run_interface(self, runtime):
        precon_file_name = self.inputs.precon_file
        postcon_file_name = self.inputs.postcon_file
        mask_file_name = self.inputs.mask_file
        
        precon_nii = nib.load(precon_file_name)
        postcon_nii = nib.load(postcon_file_name)
        blood_nii = nib.load(mask_file_name)
        
        precon_img = precon_nii.get_fdata()
        postcon_img = postcon_nii.get_fdata()

        diff_img = postcon_img - precon_img
        diff_nii = nib.Nifti1Image(diff_img, postcon_nii.affine, postcon_nii.header)
        # nib.save(diff_nii, save_file_name)
        
        lab = MatlabCommand(script=script, mfile=False)
        result = mlab.run()
        return result.runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = getattr(self, '_out_file')
        return outputs


