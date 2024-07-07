# The QUTE-CE Pypeline

Pipelines and helpful code for preprocessing, normalizing and analyzing QUTE-CE MRA data.

If any work here is used in whole or in part in research, you must cite: 

Timms L, Zhou T, Lyu Y, Qiao J, Mishra V, Lahoud RM, Jayaraman GV, Allegretti AS, Drew D, Seethamraju RT, Harisinghani M, Sridhar S. Ferumoxytol-enhanced ultrashort TE MRA and quantitative morphometry of the human kidney vasculature. Abdom Radiol (NY). 2021 Jul;46(7):3288-3300. doi: 10.1007/s00261-021-02984-2. Epub 2021 Mar 5. PMID: 33666735; PMCID: PMC8217117.

L. Timms, "Preclinical Applications and Clinical Translation of QUTE-CE MRA Technique for Vascular Imaging." Order No. 28718349, Northeastern University, United States -- Massachusetts, 2021. 

Timms L, Zhou T, Qiao J, Gharagouzloo C, Mishra V, Lahoud RM, Chen JW, Harisinghani M, Sridhar S. Super High Contrast USPIO-Enhanced Cerebrovascular Angiography Using Ultrashort Time-to-Echo MRI. Int J Biomed Imaging. 2024 Apr 13;2024:9763364. doi: 10.1155/2024/9763364. PMID: 38644981; PMCID: PMC11032209.

T. Zhou, "Clinical Translation of Quantitative Ultrashort Time-to-Echo Contrast-Enhanced MRA Technique in Renal Imaging." Order No. 31234958, Northeastern University, United States -- Massachusetts, 2024.

Note that the unringing code carries its own citation and LISCENSING if using that submodule.

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
