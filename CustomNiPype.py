
from nipype.interfaces.matlab import MatlabCommand
from nipype.interfaces.base import TraitedSpec, \
    BaseInterface, BaseInterfaceInputSpec, File
import os
from string import Template
import re
import numpy as np
import nibabel as nib
from nipype.utils.filemanip import split_filename

# ----------- UnringNii -------------------------
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
# -----------------------------------------------


# TODO: is it better to have the blood value seperate from the CBV calculation?


# ------------- DiffNii -------------------------
class DiffInputSpec(BaseInterfaceInputSpec):
    file1 = File(exists=True, mandatory=True)
    file2 = File(exists=True, mandatory=True)

class DiffOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc = 'file2 minus file1')

class DiffNii(BaseInterface):
    input_spec = DiffInputSpec
    output_spec = DiffOutputSpec

    def _run_interface(self, runtime):
        file1_name = self.inputs.file1
        file2_name = self.inputs.file2

        file1_nii = nib.load(file1_name)
        file2_nii = nib.load(file2_name)

        file1_img = np.array(file1_nii.get_data())
        file2_img = np.array(file2_nii.get_data())

        diff_img = file2_img - file1_img
        diff_nii = nib.Nifti1Image(diff_img, file1_nii.affine, file2_nii.header)

        # from https://nipype.readthedocs.io/en/latest/devel/python_interface_devel.html
        pth, fname1, ext = split_filename(file1_name)
        pth, fname2, ext = split_filename(file2_name)
        diff_file_name = os.path.join(fname2 + '_minus_' + fname1 + '.nii')
        nib.save(diff_nii, diff_file_name)
        setattr(self, '_out_file', diff_file_name)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        file1_name = self.inputs.file1
        file2_name = self.inputs.file2
        pth, fname1, ext = split_filename(file1_name)
        pth, fname2, ext = split_filename(file2_name)
        diff_file_name = os.path.join(fname2 + '_minus_' + fname1 + '.nii')
        #outputs['out_file'] = getattr(self, '_out_file')
        outputs['out_file'] = os.path.abspath(diff_file_name)
        return outputs
# -----------------------------------------------

# -------------- DivNii -------------------------
class DivInputSpec(BaseInterfaceInputSpec):
    file1 = File(exists=True, mandatory=True)
    file2 = File(exists=True, mandatory=True)

class DivOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc = 'file1 divided by file2')

class DivNii(BaseInterface):
    input_spec = DivInputSpec
    output_spec = DivOutputSpec

    def _run_interface(self, runtime):
        file1_name = self.inputs.file1
        file2_name = self.inputs.file2

        file1_nii = nib.load(file1_name)
        file2_nii = nib.load(file2_name)

        file1_nii.set_data_dtype(np.double)
        file2_nii.set_data_dtype(np.double)

        file1_img = np.array(file1_nii.get_data())
        file2_img = np.array(file2_nii.get_data())

        div_img = np.divide(file1_img, file2_img)
        div_nii = nib.Nifti1Image(div_img, file1_nii.affine, file2_nii.header)

        # from https://nipype.readthedocs.io/en/latest/devel/python_interface_devel.html
        pth, fname1, ext = split_filename(file1_name)
        pth, fname2, ext = split_filename(file2_name)
        div_file_name = os.path.join(fname1 + '_divby_' + fname2 + '.nii')
        nib.save(div_nii, div_file_name)
        setattr(self, '_out_file', div_file_name)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        file1_name = self.inputs.file1
        file2_name = self.inputs.file2
        pth, fname1, ext = split_filename(file1_name)
        pth, fname2, ext = split_filename(file2_name)
        div_file_name = os.path.join(fname1 + '_divby_' + fname2 + '.nii')
        #outputs['out_file'] = getattr(self, '_out_file')
        outputs['out_file'] = os.path.abspath(div_file_name)
        return outputs
# -----------------------------------------------

# -------------- FFTNii -------------------------
class FTTInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True)

class FTTOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc = 'Fast Fourier Transform')

class FTTNii(BaseInterface):
    input_spec = FTTInputSpec
    output_spec = FTTOutputSpec

    def _run_interface(self, runtime):
        in_file_name = self.inputs.in_file

        in_file_nii = nib.load(in_file_name)

        in_file_nii.set_data_dtype(np.double)

        in_file_img = np.array(in_file_nii.get_data())

        div_nii = nib.Nifti1Image(div_img, in_file_nii.affine, in_file_nii.header)

        # from https://nipype.readthedocs.io/en/latest/devel/python_interface_devel.html
        pth, fname1, ext = split_filename(in_file_name)

        div_file_name = os.path.join(fname1 + '_divby_' + fname2 + '.nii')
        nib.save(div_nii, div_file_name)
        setattr(self, '_out_file', div_file_name)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        file1_name = self.inputs.file1
        file2_name = self.inputs.file2
        pth, fname1, ext = split_filename(file1_name)
        pth, fname2, ext = split_filename(file2_name)
        div_file_name = os.path.join(fname1 + '_divby_' + fname2 + '.nii')
        #outputs['out_file'] = getattr(self, '_out_file')
        outputs['out_file'] = os.path.abspath(div_file_name)
        return outputs
# -----------------------------------------------


