from nipype.interfaces.matlab import MatlabCommand
from nipype.interfaces.base import TraitedSpec, \
    BaseInterface, BaseInterfaceInputSpec, File, InputMultiObject, traits
import os
from string import Template
# import re
import numpy as np
import pandas as pd
import nibabel as nib
from nipype.utils.filemanip import split_filename
import matplotlib.pyplot as plt


# ----------- UnringNii -------------------------
class UnringNiiInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True)


class UnringNiiOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='the unringed file')


class UnringNii(BaseInterface):
    input_spec = UnringNiiInputSpec
    output_spec = UnringNiiOutputSpec

    def _run_interface(self, runtime):
        in_file_name = self.inputs.in_file

        out_file_name = in_file_name.split('_')
        out_file_name.insert(-1, 'desc-unring')
        out_file_name = '_'.join(out_file_name)
        setattr(self, '_out_file', out_file_name)
        d = dict(in_file=self.inputs.in_file, out_file=out_file_name)

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


# ------------- DiffNii -------------------------
class DiffInputSpec(BaseInterfaceInputSpec):
    file1 = File(exists=True, mandatory=True)
    file2 = File(exists=True, mandatory=True)


class DiffOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='file2 minus file1')


class DiffNii(BaseInterface):
    input_spec = DiffInputSpec
    output_spec = DiffOutputSpec

    def _run_interface(self, runtime):
        file1_name = self.inputs.file1
        file2_name = self.inputs.file2

        file1_nii = nib.load(file1_name)
        file2_nii = nib.load(file2_name)

        file1_img = np.array(file1_nii.get_fdata())
        file2_img = np.array(file2_nii.get_fdata())

        #if file1_img.size()~=file2_img.size():
        #    nii2 = nil.resample_to_img(nii2, nii1)

        diff_img = file2_img - file1_img
        diff_nii = nib.Nifti1Image(diff_img, file1_nii.affine,
                                   file2_nii.header)

        # nipype.readthedocs.io/en/latest/devel/python_interface_devel.html
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
        # outputs['out_file'] = getattr(self, '_out_file')
        outputs['out_file'] = os.path.abspath(diff_file_name)
        return outputs


# -----------------------------------------------


# -------------- DivNii -------------------------
class DivInputSpec(BaseInterfaceInputSpec):
    file1 = File(exists=True, mandatory=True)
    file2 = File(exists=True, mandatory=True)


class DivOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='file1 divided by file2')


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

        file1_img = np.array(file1_nii.get_fdata())
        file2_img = np.array(file2_nii.get_fdata())

        div_img = np.divide(file1_img, file2_img)
        div_nii = nib.Nifti1Image(div_img, file1_nii.affine, file2_nii.header)

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
        # outputs['out_file'] = getattr(self, '_out_file')
        outputs['out_file'] = os.path.abspath(div_file_name)
        return outputs


# -----------------------------------------------


# -------------- FFTNii -------------------------
class FFTInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True)


class FFTOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='Fast Fourier Transform')


class FFTNii(BaseInterface):
    input_spec = FFTInputSpec
    output_spec = FFTOutputSpec

    def _run_interface(self, runtime):
        in_file_name = self.inputs.in_file
        in_file_nii = nib.load(in_file_name)
        in_file_nii.set_data_dtype(np.double)
        in_file_img = np.array(in_file_nii.get_fdata())

        fft_img = np.fft.fftn(in_file_img)
        fft_img = np.fft.fftshift(fft_img)
        fft_img = np.absolute(fft_img)

        fft_nii = nib.Nifti1Image(fft_img, in_file_nii.affine,
                                  in_file_nii.header)
        fft_nii.set_data_dtype(np.double)

        pth, fname, ext = split_filename(in_file_name)

        fft_file_name = os.path.join(fname + '_fft.nii')
        nib.save(fft_nii, fft_file_name)
        setattr(self, '_out_file', fft_file_name)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        in_file_name = self.inputs.in_file
        pth, fname, ext = split_filename(in_file_name)
        fft_file_name = os.path.join(fname + '_fft.nii')
        outputs['out_file'] = os.path.abspath(fft_file_name)
        return outputs


# -----------------------------------------------


# -------------- ROI Anlayze --------------------
class ROIAnalyzeInputSpec(BaseInterfaceInputSpec):
    roi_file = File(exists=True, mandatory=True)
    scan_file = File(exists=True, mandatory=True)


class ROIAnalyzeOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='file with statistical data')


class ROIAnalyze(BaseInterface):
    input_spec = ROIAnalyzeInputSpec
    output_spec = ROIAnalyzeOutputSpec

    def _run_interface(self, runtime):
        ROI_file_name = self.inputs.roi_file
        ROI_file_nii = nib.load(ROI_file_name)
        ROI_file_img = np.array(ROI_file_nii.get_fdata())

        scan_file_name = self.inputs.scan_file
        scan_file_nii = nib.load(scan_file_name)
        scan_img = np.array(scan_file_nii.get_data())
        unique_roi = np.unique(ROI_file_img)
        out_data = np.empty([np.size(unique_roi), 3])

        n = 0
        for r in unique_roi:
	    # r is label in roi
	    # n counts for number of labels

            roi = (ROI_file_img == r).astype(int)
            roi = roi.astype('float')
            # zero can be a true value so mask with nan
            roi[roi == 0] = np.nan

            crop_img = np.multiply(scan_img, roi)
            vals = np.reshape(crop_img, -1)
            ave = np.nanmean(vals)
            std = np.nanstd(vals)
            out_data[n][0] = r
            out_data[n][1] = ave
            out_data[n][2] = std
            n = n + 1

        #  pth, fname, ext = split_filename(scan_file_name)
        #  out_file_name = os.path.join(fname + '.csv')
        pth, scan_fname, ext = split_filename(scan_file_name)
        pth, roi_fname, ext = split_filename(ROI_file_name)
        out_file_name = os.path.join(scan_fname + '_ROI-' + roi_fname + '.csv')
        if len(out_file_name) > 200:
            out_file_name = os.path.join(scan_fname[0:50] + '_ROI-' +
                                         roi_fname + '.csv')

        pd.DataFrame(out_data).to_csv(out_file_name)

        # nib.save(fft_nii, fft_file_name)
        setattr(self, '_out_file', out_file_name)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()

        ROI_file_name = self.inputs.roi_file
        scan_file_name = self.inputs.scan_file
        pth, scan_fname, ext = split_filename(scan_file_name)
        pth, roi_fname, ext = split_filename(ROI_file_name)
        out_file_name = os.path.join(scan_fname + '_ROI-' + roi_fname + '.csv')
        if len(out_file_name) > 200:
            out_file_name = os.path.join(scan_fname[0:50] + '_ROI-' +
                                         roi_fname + '.csv')
        outputs['out_file'] = os.path.abspath(out_file_name)

        # scan_file_name = self.inputs.scan_file
        # pth, fname, ext = split_filename(scan_file_name)
        # out_file_name = os.path.join(fname + '.csv')
        # outputs['out_file'] = os.path.abspath(out_file_name)

        return outputs

# -----------------------------------------------

# -------------- CSV Concatenate --------------------
class CSVConcatenateInputSpec(BaseInterfaceInputSpec):
    in_files = InputMultiObject(exists=True, mandatory=True, desc='list of csvs')


class CSVConcatenateOutputSpec(TraitedSpec):
    out_csv = File(exists=True, desc='concatenated csv')
    out_fig = File(exists=True, disc='timeseries plots')

class CSVConcatenate(BaseInterface):
    input_spec = CSVConcatenateInputSpec
    output_spec = CSVConcatenateOutputSpec

    def _run_interface(self, runtime):
        in_files = self.inputs.in_files
        df_from_each_in_file = (pd.read_csv(in_file) for in_file in in_files )
        concatenated_df = pd.concat(df_from_each_in_file, ignore_index=True)
        concatenated_df.columns = ['ind', 'label', 'mean', 'std']
        concatenated_df = concatenated_df.astype({'label': 'int'})

        # grab fname info from first file in the input list
        pth, fname, ext = split_filename(in_files[0])
        out_csv_name= os.path.join(fname + '_concatenated.csv')
        concatenated_df.to_csv(out_csv_name)

        # plot time series
        unique_label = np.unique(concatenated_df['label'])
        fig = plt.figure(figsize=(6,4))
        ax = fig.add_subplot(111)
        for n in unique_label:
            condition = concatenated_df['label']==n
            mean = concatenated_df[condition]['mean']
            std = concatenated_df[condition]['std']
            plt.errorbar(range(1,len(mean)+1), mean, yerr=std, label='label = ' + str(n))
            ax.set_xlabel('Index of runs')
            ax.set_ylabel('S.I.')
            ax.legend()
        out_fig_name = os.path.join(fname + '_timeseries.png')
        plt.savefig(out_fig_name, bbox_inches='tight')

        setattr(self, '_out_csv', out_csv_name)
        setattr(self, '_out_fig', out_fig_name)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        in_files = self.inputs.in_files
        pth, fname, ext = split_filename(in_files[0])
        out_csv_name = os.path.join(fname + '_concatenated.csv')
        out_fig_name = os.path.join(fname + '_timeseries.png')
        outputs['out_csv'] = os.path.abspath(out_csv_name)
        outputs['out_fig'] = os.path.abspath(out_fig_name)
        return outputs

# -----------------------------------------------

# -------------- CBV whole brain ------------------
class CBVwhBrainInputSpec(BaseInterfaceInputSpec):
    in1 = File(exists=True, mandatory=True, desc='csv of brain')
    in2 = File(exists=True, mandatory=True, desc='csv of blood')

class CBVwhBrainOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='calculated CBV')

class CBVwhBrain(BaseInterface):
    input_spec = CBVwhBrainInputSpec
    output_spec = CBVwhBrainOutputSpec

    def _run_interface(self, runtime):
        brain_csv_file = self.inputs.in1
        blood_csv_file = self.inputs.in2
        df_brain = pd.read_csv(brain_csv_file)
        df_blood = pd.read_csv(blood_csv_file)

        df_brain.columns = ['ind1', 'ind2', 'label', 'mean', 'std']
        df_blood.columns = ['ind1', 'ind2', 'label', 'mean', 'std']
        df_brain = df_brain.astype({'label': 'int'})
        df_blood = df_blood.astype({'label': 'int'})
        isbrain = df_brain['label']==1
        isblood = df_blood['label']==1

        deltaSIbrain = df_brain[isbrain]['mean'].to_numpy()
        std_deltaSIbrain = df_brain[isbrain]['std'].to_numpy()
        deltaSIblood = df_blood[isblood]['mean'].to_numpy()
        std_deltaSIblood = df_blood[isblood]['std'].to_numpy()
        cbv = deltaSIbrain / deltaSIblood
        err_cbv = np.sqrt(np.square(std_deltaSIbrain / deltaSIbrain)
                    + np.square(std_deltaSIblood / deltaSIblood))

        df_CBV = pd.DataFrame({'deltaSIbrain': deltaSIbrain,
                               'std_deltaSIbrain': std_deltaSIbrain,
                               'deltaSIblood': deltaSIblood,
                               'std_deltaSIblood': std_deltaSIblood,
                               'CBV': cbv,
                               'err_CBV': err_cbv})

        pth, fname, ext = split_filename(brain_csv_file)
        out_file_name = os.path.join(fname[0:8] + '_CBV_WholeBrain.csv')
        df_CBV.to_csv(out_file_name)

        setattr(self, '_out_file', out_file_name)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        brain_csv_file = self.inputs.in1
        pth, fname, ext = split_filename(brain_csv_file)
        out_file_name = os.path.join(fname[0:8] + '_CBV_WholeBrain.csv')
        outputs['out_file'] = os.path.abspath(out_file_name)
        return outputs

# -----------------------------------------------

# -----------------------------------------------
class LowerSNRInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True)
    std = traits.Float(mandatory=True, desc='std of noise to add')



class LowerSNROutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='Adding Gaussian Noise')



class LowerSNRNii(BaseInterface):
    input_spec = LowerSNRInputSpec
    output_spec = LowerSNROutputSpec

    def _run_interface(self, runtime):
        in_file_name = self.inputs.in_file
        in_file_nii = nib.load(in_file_name)
        in_file_nii.set_data_dtype(np.double)
        in_file_img = np.array(in_file_nii.get_fdata())

        noise = np.random.normal(0, self.inputs.std, in_file_img.shape)
        noisey_img = in_file_img + noise

        noisey_nii = nib.Nifti1Image(noisey_img, in_file_nii.affine,
                                  in_file_nii.header)
        noisey_nii.set_data_dtype(np.double)

        pth, fname, ext = split_filename(in_file_name)

        noisey_file_name = os.path.join(fname + '_noisey.nii')
        nib.save(noisey_nii, noisey_file_name)
        setattr(self, '_out_file', noisey_file_name)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        in_file_name = self.inputs.in_file
        pth, fname, ext = split_filename(in_file_name)
        noisey_file_name = os.path.join(fname + '_noisey.nii')
        outputs['out_file'] = os.path.abspath(noisey_file_name)
        return outputs

# -----------------------------------------------
