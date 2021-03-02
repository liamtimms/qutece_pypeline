# The QUTE-CE Pypeline

Pipelines and helpful code for preprocessing, normalizing and analyzing QUTE-CE MRA data.

## Description

This code was developed and written primarily by Liam Timms over the course of his PhD. Additional contributions were provided by Tianyi Zhou. It is designed as is for processing QUTE-CE MRA neurovascular images but can be adapted for abdominal images, see: abdominal.md.

## Sections

### nipype_workflows

Directory containing the bulk of the actual pypeline.

### vmtk

Directory containing helpful VMTK code. Kept seperate due to needing a seperate virtual environment for this tool.

### jupyter

Directory containing jupyter notebooks for exploring and plotting data easily. (I recommend `jupyter-lab`)

## Dependencies

This pipeline is designed to run on Linux (uses non-Windows programs, has not been tested on mac). To handle dependencies, you can either use my `MRArch` script (in-progress) to provide a less stable but bleeding edge platform or I recommend following Tianyi's instructions for Ubuntu 18.04 here: https://github.com/tianyizhou1222/mr/blob/master/ubuntu_mrsetup.md

Alternatively, you can setup custom approach on your existing system.

### Core

The dependencies for the nipype based python pipeline are:

- [nipype](https://github.com/nipy/nipype)
- [nibabel](https://github.com/nipy/nibabel)
- [nilearn](https://github.com/nipy/nilearn)
- [pandas](https://github.com/pandas-dev/pandas)
- [FSL](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FSL)
- [ANTs](https://github.com/ANTsX/ANTs)
- [SPM12](https://github.com/spm/spm12)
- [MATLAB](https://www.mathworks.com/products/matlab.html) - primarily for SPM, the standalone or octave versions of SPM have not been tested
- the Reisert Unringing algorithm, availbe through dipy or a MATLAB interface - the [original repo](https://bitbucket.org/reisert/unring/src/master/matlab/)

It is theoretically possible to drop the MATLAB dependency but requires switching to another unringing implementation and using stand-alone SPM.

### Vascular Processing

- [VMTK](https://github.com/vmtk/vmtk)

### CSV Analysis

- [pandas](https://github.com/pandas-dev/pandas)

## Installation

Designed to be run as a set of scripts from inside a BIDS folder (with the QUTE-CE extension), there are not specific install instructions.

## Use

### Overview
1. organize DICOM files pulled from machine into `DCM` directory by subject and session.
2. adapt `bids_extraction.py` for the current dataset
3. edit `nipype_workflows/nipype_controller_liam.py` to select only the currently needed pipelines
3. use `./run` to run the pipelines.
3. make any manual edits to brain masks, generate

Edit `nipype_controller.py` to activate or inactivate individual pipelines.
Currently, it is fairly closely constructed around the specific data set it was initilally applied and designed for.
